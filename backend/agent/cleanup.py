"""
Email cleanup operations for Inbox Nuke Agent.

This module provides functionality to delete emails and estimate storage freed:
- Delete emails from specific senders with age filtering
- Delete large attachments to free up storage
- Delete emails by Gmail category (promotions, social, updates)
- Track cleanup statistics and storage freed
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from gmail_client import GmailClient, GmailAPIError
from models import Sender

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class CleanupResult:
    """
    Result of a cleanup operation.

    Attributes:
        emails_deleted: Number of emails deleted
        bytes_freed: Estimated bytes freed
        errors: List of error messages encountered
    """
    emails_deleted: int = 0
    bytes_freed: int = 0
    errors: List[str] = field(default_factory=list)

    def merge(self, other: "CleanupResult") -> None:
        """
        Merge another CleanupResult into this one.

        Args:
            other: Another CleanupResult to merge
        """
        self.emails_deleted += other.emails_deleted
        self.bytes_freed += other.bytes_freed
        self.errors.extend(other.errors)


# ============================================================================
# Sender-Based Cleanup
# ============================================================================


async def delete_emails_from_sender(
    gmail_client: GmailClient,
    sender: Sender,
    older_than_days: int = 30,
    db: Optional[AsyncSession] = None,
) -> CleanupResult:
    """
    Delete all emails from a specific sender older than specified days.

    Emails are moved to trash (not permanently deleted) and can be recovered
    for 30 days from Gmail's trash.

    Args:
        gmail_client: Authenticated Gmail client
        sender: Sender object from database
        older_than_days: Only delete emails older than this many days (default: 30)
        db: Optional async database session for updates

    Returns:
        CleanupResult with deletion statistics

    Example:
        >>> result = await delete_emails_from_sender(gmail_client, sender, older_than_days=60)
        >>> print(f"Deleted {result.emails_deleted} emails, freed {result.bytes_freed / 1024**2:.2f} MB")
    """
    result = CleanupResult()

    try:
        # Build search query
        query = f"from:{sender.email} older_than:{older_than_days}d"
        logger.info(f"Searching for emails with query: {query}")

        # List all matching messages
        messages = await gmail_client.list_messages(query=query, max_results=10000)

        if not messages:
            logger.info(f"No emails found from {sender.email} older than {older_than_days} days")
            return result

        logger.info(f"Found {len(messages)} emails from {sender.email} to delete")

        # Get full message details to calculate size
        # We'll batch this to avoid overwhelming the API
        message_ids = [msg["id"] for msg in messages]
        total_size = 0

        # Process in batches of 100
        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i:i + 100]

            try:
                # Get message details to calculate size
                full_messages = await gmail_client.batch_get_messages(
                    batch_ids,
                    format="metadata"
                )

                # Sum up sizes
                for msg in full_messages:
                    size = gmail_client.get_message_size(msg)
                    total_size += size

            except GmailAPIError as e:
                error_msg = f"Error fetching message details: {str(e)}"
                logger.warning(error_msg)
                result.errors.append(error_msg)
                # Continue anyway - we'll still try to delete

        # Trash messages in batches
        try:
            trashed_count = await gmail_client.trash_messages(message_ids)
            result.emails_deleted = trashed_count
            result.bytes_freed = total_size

            logger.info(
                f"Deleted {trashed_count} emails from {sender.email}, "
                f"freed approximately {total_size / 1024**2:.2f} MB"
            )

        except GmailAPIError as e:
            error_msg = f"Error trashing messages from {sender.email}: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during cleanup for {sender.email}: {str(e)}"
        logger.error(error_msg)
        result.errors.append(error_msg)

    return result


# ============================================================================
# Attachment-Based Cleanup
# ============================================================================


async def cleanup_large_attachments(
    gmail_client: GmailClient,
    older_than_days: int = 365,
    min_size_mb: int = 5,
    db: Optional[AsyncSession] = None,
) -> CleanupResult:
    """
    Delete emails with large attachments to free up storage.

    Args:
        gmail_client: Authenticated Gmail client
        older_than_days: Only delete emails older than this many days (default: 365)
        min_size_mb: Minimum email size in MB (default: 5)
        db: Optional async database session

    Returns:
        CleanupResult with deletion statistics

    Example:
        >>> result = await cleanup_large_attachments(gmail_client, older_than_days=180, min_size_mb=10)
        >>> print(f"Freed {result.bytes_freed / 1024**3:.2f} GB")
    """
    result = CleanupResult()

    try:
        # Build search query
        # Gmail uses 'larger:' operator with bytes
        size_bytes = min_size_mb * 1024 * 1024
        query = f"larger:{size_bytes} older_than:{older_than_days}d"
        logger.info(f"Searching for large attachments with query: {query}")

        # List matching messages
        messages = await gmail_client.list_messages(query=query, max_results=5000)

        if not messages:
            logger.info(f"No large attachments found older than {older_than_days} days")
            return result

        logger.info(f"Found {len(messages)} emails with large attachments to delete")

        # Get message sizes
        message_ids = [msg["id"] for msg in messages]
        total_size = 0

        # Process in batches
        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i:i + 100]

            try:
                full_messages = await gmail_client.batch_get_messages(
                    batch_ids,
                    format="metadata"
                )

                for msg in full_messages:
                    size = gmail_client.get_message_size(msg)
                    total_size += size

            except GmailAPIError as e:
                error_msg = f"Error fetching message details: {str(e)}"
                logger.warning(error_msg)
                result.errors.append(error_msg)

        # Trash messages
        try:
            trashed_count = await gmail_client.trash_messages(message_ids)
            result.emails_deleted = trashed_count
            result.bytes_freed = total_size

            logger.info(
                f"Deleted {trashed_count} emails with large attachments, "
                f"freed approximately {total_size / 1024**3:.2f} GB"
            )

        except GmailAPIError as e:
            error_msg = f"Error trashing large attachments: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during large attachment cleanup: {str(e)}"
        logger.error(error_msg)
        result.errors.append(error_msg)

    return result


# ============================================================================
# Category-Based Cleanup
# ============================================================================


async def cleanup_category(
    gmail_client: GmailClient,
    category: str,
    older_than_days: int,
    db: Optional[AsyncSession] = None,
) -> CleanupResult:
    """
    Delete emails from a specific Gmail category.

    Gmail categories: promotions, social, updates, forums, personal

    Args:
        gmail_client: Authenticated Gmail client
        category: Gmail category (promotions, social, updates, forums, personal)
        older_than_days: Only delete emails older than this many days
        db: Optional async database session

    Returns:
        CleanupResult with deletion statistics

    Example:
        >>> result = await cleanup_category(gmail_client, "promotions", older_than_days=90)
        >>> print(f"Cleaned up {result.emails_deleted} promotional emails")
    """
    result = CleanupResult()

    # Validate category
    valid_categories = ["promotions", "social", "updates", "forums", "personal"]
    if category.lower() not in valid_categories:
        error_msg = f"Invalid category: {category}. Must be one of {valid_categories}"
        logger.error(error_msg)
        result.errors.append(error_msg)
        return result

    try:
        # Build search query
        query = f"category:{category.lower()} older_than:{older_than_days}d"
        logger.info(f"Searching for {category} emails with query: {query}")

        # List matching messages
        messages = await gmail_client.list_messages(query=query, max_results=10000)

        if not messages:
            logger.info(f"No {category} emails found older than {older_than_days} days")
            return result

        logger.info(f"Found {len(messages)} {category} emails to delete")

        # Get message sizes
        message_ids = [msg["id"] for msg in messages]
        total_size = 0

        # Process in batches
        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i:i + 100]

            try:
                full_messages = await gmail_client.batch_get_messages(
                    batch_ids,
                    format="metadata"
                )

                for msg in full_messages:
                    size = gmail_client.get_message_size(msg)
                    total_size += size

            except GmailAPIError as e:
                error_msg = f"Error fetching message details: {str(e)}"
                logger.warning(error_msg)
                result.errors.append(error_msg)

        # Trash messages
        try:
            trashed_count = await gmail_client.trash_messages(message_ids)
            result.emails_deleted = trashed_count
            result.bytes_freed = total_size

            logger.info(
                f"Deleted {trashed_count} {category} emails, "
                f"freed approximately {total_size / 1024**2:.2f} MB"
            )

        except GmailAPIError as e:
            error_msg = f"Error trashing {category} emails: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)

    except Exception as e:
        error_msg = f"Unexpected error during {category} cleanup: {str(e)}"
        logger.error(error_msg)
        result.errors.append(error_msg)

    return result


# ============================================================================
# Batch Cleanup Operations
# ============================================================================


async def cleanup_multiple_senders(
    gmail_client: GmailClient,
    senders: List[Sender],
    older_than_days: int = 30,
    db: Optional[AsyncSession] = None,
) -> CleanupResult:
    """
    Delete emails from multiple senders.

    Args:
        gmail_client: Authenticated Gmail client
        senders: List of Sender objects
        older_than_days: Only delete emails older than this many days
        db: Optional async database session

    Returns:
        Combined CleanupResult for all senders

    Example:
        >>> result = await cleanup_multiple_senders(gmail_client, senders, older_than_days=60)
        >>> print(f"Total deleted: {result.emails_deleted}")
    """
    combined_result = CleanupResult()

    for sender in senders:
        result = await delete_emails_from_sender(
            gmail_client,
            sender,
            older_than_days=older_than_days,
            db=db,
        )
        combined_result.merge(result)

        # Add small delay to avoid rate limiting
        await asyncio.sleep(0.5)

    logger.info(
        f"Batch cleanup complete: {combined_result.emails_deleted} emails deleted, "
        f"{combined_result.bytes_freed / 1024**2:.2f} MB freed"
    )

    return combined_result


# ============================================================================
# Large Attachment Scanning (Non-Destructive)
# ============================================================================


async def scan_large_attachments(
    gmail_client: GmailClient,
    min_size_mb: int = 5,
    older_than_days: int = 365,
) -> List[dict]:
    """
    Scan for large attachments without deleting them.

    This is a non-destructive discovery function that returns metadata
    about large emails for user review. The user can then selectively
    delete them via the attachments endpoint.

    Args:
        gmail_client: Authenticated Gmail client
        min_size_mb: Minimum email size in MB (default: 5)
        older_than_days: Only scan emails older than this many days (default: 365)

    Returns:
        List of dicts with message metadata:
        - message_id: Gmail message ID
        - subject: Email subject
        - from_email: Sender email
        - size: Size in bytes
        - date: Email date

    Example:
        >>> attachments = await scan_large_attachments(gmail_client, min_size_mb=10)
        >>> print(f"Found {len(attachments)} large emails")
        >>> for email in attachments[:5]:
        >>>     print(f"{email['subject']}: {email['size'] / 1024**2:.2f} MB")
    """
    result_list = []

    try:
        # Build search query
        size_bytes = min_size_mb * 1024 * 1024
        query = f"larger:{size_bytes} older_than:{older_than_days}d"
        logger.info(f"Scanning for large attachments with query: {query}")

        # List matching messages
        messages = await gmail_client.list_messages(query=query, max_results=500)

        if not messages:
            logger.info(f"No large attachments found (>= {min_size_mb}MB, >= {older_than_days} days old)")
            return result_list

        logger.info(f"Found {len(messages)} emails with large attachments")

        # Get full message details in batches
        message_ids = [msg["id"] for msg in messages]

        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i:i + 100]

            try:
                full_messages = await gmail_client.batch_get_messages(
                    batch_ids,
                    format="metadata"
                )

                for msg in full_messages:
                    # Extract headers
                    headers = msg.get('payload', {}).get('headers', [])
                    subject = ""
                    from_email = ""
                    date = ""

                    for header in headers:
                        name = header['name'].lower()
                        if name == 'subject':
                            subject = header['value']
                        elif name == 'from':
                            from email.utils import parseaddr
                            _, from_email = parseaddr(header['value'])
                        elif name == 'date':
                            date = header['value']

                    # Get size
                    size = gmail_client.get_message_size(msg)

                    result_list.append({
                        'message_id': msg['id'],
                        'subject': subject or "(No Subject)",
                        'from_email': from_email or "unknown",
                        'size': size,
                        'date': date or "unknown",
                    })

            except GmailAPIError as e:
                logger.warning(f"Error fetching message details in batch: {str(e)}")
                # Continue with next batch

        # Sort by size (largest first)
        result_list.sort(key=lambda x: x['size'], reverse=True)

        logger.info(
            f"Scan complete: found {len(result_list)} large emails, "
            f"total size: {sum(e['size'] for e in result_list) / 1024**3:.2f} GB"
        )

    except Exception as e:
        logger.error(f"Unexpected error during large attachment scan: {str(e)}")

    return result_list
