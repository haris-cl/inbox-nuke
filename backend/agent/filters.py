"""
Gmail filter management for Inbox Nuke Agent.

This module provides functionality to create and manage Gmail filters
that automatically mute emails from specific senders by:
- Creating "Muted" parent label and domain-specific sublabels
- Setting up filters to skip inbox and mark as read
- Checking for existing filters to avoid duplicates
- Updating sender records with filter information
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gmail_client import GmailClient, GmailAPIError
from models import Sender

logger = logging.getLogger(__name__)


# ============================================================================
# Label Cache
# ============================================================================

# Cache label IDs to reduce API calls
_label_cache = {}


# ============================================================================
# Label Management
# ============================================================================


async def get_muted_label_id(gmail_client: GmailClient) -> str:
    """
    Get or create the "Muted" parent label.

    Caches the label ID for performance to reduce API calls.

    Args:
        gmail_client: Authenticated Gmail client

    Returns:
        Label ID for "Muted" label

    Raises:
        GmailAPIError: If label creation fails

    Example:
        >>> label_id = await get_muted_label_id(gmail_client)
        >>> print(label_id)
        'Label_123'
    """
    # Check cache first
    if "Muted" in _label_cache:
        return _label_cache["Muted"]

    # Get or create label
    label_id = await gmail_client.get_or_create_label("Muted")
    _label_cache["Muted"] = label_id

    return label_id


async def get_or_create_domain_label(
    gmail_client: GmailClient,
    domain: str,
) -> str:
    """
    Get or create a domain-specific sublabel under "Muted".

    Creates nested labels like "Muted/example.com" for organization.

    Args:
        gmail_client: Authenticated Gmail client
        domain: Domain name for the sublabel

    Returns:
        Label ID for the domain-specific label

    Raises:
        GmailAPIError: If label creation fails

    Example:
        >>> label_id = await get_or_create_domain_label(gmail_client, "example.com")
        >>> print(label_id)
        'Label_456'
    """
    label_name = f"Muted/{domain}"

    # Check cache first
    if label_name in _label_cache:
        return _label_cache[label_name]

    # Get or create label
    label_id = await gmail_client.get_or_create_label(label_name)
    _label_cache[label_name] = label_id

    return label_id


# ============================================================================
# Filter Management
# ============================================================================


async def check_filter_exists(
    gmail_client: GmailClient,
    sender_email: str,
) -> bool:
    """
    Check if a filter already exists for a sender email.

    Args:
        gmail_client: Authenticated Gmail client
        sender_email: Email address to check

    Returns:
        True if a filter exists for this sender, False otherwise

    Example:
        >>> exists = await check_filter_exists(gmail_client, "spam@example.com")
        >>> if exists:
        ...     print("Filter already exists")
    """
    try:
        filters = await gmail_client.list_filters()

        # Check if any filter matches this sender
        for filter_data in filters:
            criteria = filter_data.get("criteria", {})
            if criteria.get("from") == sender_email:
                logger.info(f"Filter already exists for {sender_email}")
                return True

        return False

    except Exception as e:
        logger.error(f"Error checking for existing filter for {sender_email}: {str(e)}")
        # If we can't check, assume it doesn't exist to avoid blocking
        return False


async def create_mute_filter(
    gmail_client: GmailClient,
    sender: Sender,
    db: AsyncSession,
) -> Optional[str]:
    """
    Create a Gmail filter to mute emails from a sender.

    The filter will:
    - Skip inbox (archive)
    - Mark as read
    - Apply "Muted" label
    - Apply "Muted/{domain}" sublabel

    Args:
        gmail_client: Authenticated Gmail client
        sender: Sender object from database
        db: Async database session

    Returns:
        Filter ID if successful, None if failed

    Example:
        >>> filter_id = await create_mute_filter(gmail_client, sender, db)
        >>> if filter_id:
        ...     print(f"Created filter: {filter_id}")
    """
    try:
        # Check if filter already exists
        if await check_filter_exists(gmail_client, sender.email):
            logger.info(f"Filter already exists for {sender.email}, skipping creation")
            # Still mark as created in our database
            sender.filter_created = True
            await db.commit()
            await db.refresh(sender)
            return None

        # Get or create labels
        muted_label_id = await get_muted_label_id(gmail_client)
        domain_label_id = await get_or_create_domain_label(gmail_client, sender.domain)

        # Create filter with actions
        filter_actions = {
            "skip_inbox": True,
            "mark_as_read": True,
            "add_label_ids": [muted_label_id, domain_label_id],
        }

        created_filter = await gmail_client.create_filter(
            sender_email=sender.email,
            actions=filter_actions,
        )

        filter_id = created_filter.get("id")

        # Update sender in database
        sender.filter_created = True
        sender.filter_id = filter_id

        await db.commit()
        await db.refresh(sender)

        logger.info(f"Created mute filter for {sender.email} (ID: {filter_id})")
        return filter_id

    except GmailAPIError as e:
        logger.error(f"Gmail API error creating filter for {sender.email}: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error creating filter for {sender.email}: {str(e)}")
        return None


# ============================================================================
# Batch Filter Operations
# ============================================================================


async def create_filters_for_senders(
    gmail_client: GmailClient,
    sender_ids: list[int],
    db: AsyncSession,
) -> dict:
    """
    Create mute filters for multiple senders.

    Args:
        gmail_client: Authenticated Gmail client
        sender_ids: List of sender IDs to create filters for
        db: Async database session

    Returns:
        Dictionary with 'created', 'failed', and 'skipped' counts

    Example:
        >>> result = await create_filters_for_senders(gmail_client, [1, 2, 3], db)
        >>> print(f"Created {result['created']} filters")
    """
    result = {
        "created": 0,
        "failed": 0,
        "skipped": 0,
    }

    for sender_id in sender_ids:
        # Fetch sender from database
        stmt = select(Sender).where(Sender.id == sender_id)
        db_result = await db.execute(stmt)
        sender = db_result.scalar_one_or_none()

        if not sender:
            logger.warning(f"Sender not found: {sender_id}")
            result["failed"] += 1
            continue

        # Skip if filter already created
        if sender.filter_created:
            logger.info(f"Filter already exists for {sender.email}, skipping")
            result["skipped"] += 1
            continue

        # Create filter
        filter_id = await create_mute_filter(gmail_client, sender, db)

        if filter_id:
            result["created"] += 1
        else:
            # Could be skipped (already exists) or failed
            if sender.filter_created:
                result["skipped"] += 1
            else:
                result["failed"] += 1

    logger.info(
        f"Batch filter creation complete: "
        f"{result['created']} created, "
        f"{result['skipped']} skipped, "
        f"{result['failed']} failed"
    )

    return result


# ============================================================================
# Filter Cleanup
# ============================================================================


async def delete_filter_for_sender(
    gmail_client: GmailClient,
    sender: Sender,
    db: AsyncSession,
) -> bool:
    """
    Delete a filter for a sender.

    Args:
        gmail_client: Authenticated Gmail client
        sender: Sender object from database
        db: Async database session

    Returns:
        True if successful, False otherwise

    Example:
        >>> success = await delete_filter_for_sender(gmail_client, sender, db)
    """
    if not sender.filter_id:
        logger.warning(f"No filter ID for sender {sender.email}")
        return False

    try:
        success = await gmail_client.delete_filter(sender.filter_id)

        if success:
            # Update sender in database
            sender.filter_created = False
            sender.filter_id = None

            await db.commit()
            await db.refresh(sender)

            logger.info(f"Deleted filter for {sender.email}")
            return True
        else:
            return False

    except Exception as e:
        logger.error(f"Error deleting filter for {sender.email}: {str(e)}")
        return False


async def clear_label_cache():
    """
    Clear the label ID cache.

    Call this when labels might have been deleted or recreated.
    """
    global _label_cache
    _label_cache = {}
    logger.info("Cleared label cache")
