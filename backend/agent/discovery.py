"""
Sender discovery for Inbox Nuke Agent.

This module provides functionality to discover email senders and extract
unsubscribe information:
- Scan inbox for promotional/social/updates emails
- Extract sender information from messages
- Parse List-Unsubscribe headers
- Create or update Sender records in database
- Track message counts and statistics
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Callable, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from gmail_client import GmailClient, GmailAPIError
from models import Sender

logger = logging.getLogger(__name__)


# ============================================================================
# Sender Discovery
# ============================================================================


async def discover_senders(
    gmail_client: GmailClient,
    db: AsyncSession,
    progress_callback: Optional[Callable] = None,
    max_messages: int = 10000,
) -> int:
    """
    Discover email senders from promotional/social/updates categories.

    Scans the user's inbox for messages in common bulk email categories,
    extracts sender information and unsubscribe headers, and creates or
    updates Sender records in the database.

    Args:
        gmail_client: Authenticated Gmail client
        db: Async database session
        progress_callback: Optional callback function for progress updates
                          Called with (current, total, message) parameters
        max_messages: Maximum number of messages to scan (default: 5000)

    Returns:
        Total number of unique senders discovered

    Example:
        >>> def progress(current, total, msg):
        ...     print(f"{current}/{total}: {msg}")
        >>> count = await discover_senders(gmail_client, db, progress_callback=progress)
        >>> print(f"Discovered {count} senders")
    """
    senders_found = {}  # email -> sender_info
    messages_processed = 0

    try:
        # Build query to find bulk emails
        # Focus on categories and emails with unsubscribe headers
        queries = [
            "category:promotions",
            "category:social",
            "category:updates",
        ]

        # Also search for emails with List-Unsubscribe header
        # This catches newsletters that might not be categorized
        queries.append("has:unsubscribe")

        # Add searches for common promotional sender patterns
        # These catch marketing emails that might not be categorized
        promotional_patterns = [
            "from:noreply@",
            "from:no-reply@",
            "from:newsletter@",
            "from:marketing@",
            "from:promo@",
            "from:promotions@",
            "from:offers@",
            "from:deals@",
            "from:updates@",
            "from:notifications@",
        ]

        # Add promotional pattern searches (limit results per pattern)
        for pattern in promotional_patterns:
            queries.append(pattern)

        for query_idx, query in enumerate(queries):
            logger.info(f"Discovering senders with query: {query}")

            if progress_callback:
                progress_callback(
                    query_idx * (max_messages // len(queries)),
                    max_messages,
                    f"Scanning {query}..."
                )

            try:
                # List messages matching query
                messages = await gmail_client.list_messages(
                    query=query,
                    max_results=max_messages // len(queries)
                )

                if not messages:
                    logger.info(f"No messages found for query: {query}")
                    continue

                logger.info(f"Found {len(messages)} messages for {query}, fetching details...")

                # Fetch message details in batches
                message_ids = [msg["id"] for msg in messages]

                for batch_start in range(0, len(message_ids), 100):
                    batch_ids = message_ids[batch_start:batch_start + 100]

                    try:
                        # Get message metadata including headers
                        full_messages = await gmail_client.batch_get_messages(
                            batch_ids,
                            format="metadata"
                        )

                        # Process each message
                        for message in full_messages:
                            messages_processed += 1

                            # Extract headers
                            headers = message.get("payload", {}).get("headers", [])

                            # Get sender information
                            sender_info = gmail_client.get_sender_from_headers(headers)

                            if not sender_info.get("email"):
                                logger.warning(f"No sender email found in message {message['id']}")
                                continue

                            sender_email = sender_info["email"]

                            # Parse List-Unsubscribe header
                            unsubscribe_info = gmail_client.parse_list_unsubscribe_header(headers)

                            # Add or update sender
                            if sender_email not in senders_found:
                                senders_found[sender_email] = {
                                    "email": sender_email,
                                    "domain": sender_info.get("domain", ""),
                                    "display_name": sender_info.get("display_name", ""),
                                    "message_count": 1,
                                    "has_list_unsubscribe": bool(
                                        unsubscribe_info.get("mailto") or unsubscribe_info.get("url")
                                    ),
                                    "unsubscribe_info": unsubscribe_info,
                                    "first_seen": datetime.utcnow(),
                                    "last_seen": datetime.utcnow(),
                                }
                            else:
                                # Update message count and last seen
                                senders_found[sender_email]["message_count"] += 1
                                senders_found[sender_email]["last_seen"] = datetime.utcnow()

                                # Update unsubscribe info if we found it this time
                                if (unsubscribe_info.get("mailto") or unsubscribe_info.get("url")):
                                    senders_found[sender_email]["has_list_unsubscribe"] = True
                                    senders_found[sender_email]["unsubscribe_info"] = unsubscribe_info

                            # Progress update
                            if progress_callback and messages_processed % 50 == 0:
                                progress_callback(
                                    messages_processed,
                                    max_messages,
                                    f"Processed {messages_processed} messages, found {len(senders_found)} senders"
                                )

                    except GmailAPIError as e:
                        logger.warning(f"Error fetching batch of messages: {str(e)}")
                        continue

                    # Small delay to avoid rate limiting
                    await asyncio.sleep(0.1)

            except GmailAPIError as e:
                logger.error(f"Error listing messages for query '{query}': {str(e)}")
                continue

        # Save all discovered senders to database
        logger.info(f"Saving {len(senders_found)} senders to database...")

        for sender_email, sender_data in senders_found.items():
            try:
                # Check if sender already exists
                stmt = select(Sender).where(Sender.email == sender_email)
                result = await db.execute(stmt)
                existing_sender = result.scalar_one_or_none()

                if existing_sender:
                    # Update existing sender
                    existing_sender.message_count = sender_data["message_count"]
                    existing_sender.last_seen_at = sender_data["last_seen"]

                    # Update display name if we have a better one
                    if sender_data.get("display_name") and not existing_sender.display_name:
                        existing_sender.display_name = sender_data["display_name"]

                    # Update unsubscribe info if we found it
                    if sender_data["has_list_unsubscribe"]:
                        existing_sender.has_list_unsubscribe = True
                        existing_sender.unsubscribe_header = json.dumps(
                            sender_data["unsubscribe_info"]
                        )

                        # Determine unsubscribe method
                        if sender_data["unsubscribe_info"].get("mailto"):
                            existing_sender.unsubscribe_method = "mailto"
                        elif sender_data["unsubscribe_info"].get("url"):
                            existing_sender.unsubscribe_method = "http"

                else:
                    # Create new sender
                    new_sender = Sender(
                        email=sender_email,
                        domain=sender_data["domain"],
                        display_name=sender_data.get("display_name"),
                        message_count=sender_data["message_count"],
                        has_list_unsubscribe=sender_data["has_list_unsubscribe"],
                        unsubscribe_header=json.dumps(sender_data["unsubscribe_info"]) if sender_data["has_list_unsubscribe"] else None,
                        unsubscribe_method=(
                            "mailto" if sender_data["unsubscribe_info"].get("mailto")
                            else "http" if sender_data["unsubscribe_info"].get("url")
                            else None
                        ),
                        first_seen_at=sender_data["first_seen"],
                        last_seen_at=sender_data["last_seen"],
                    )
                    db.add(new_sender)

                # Commit after each sender to avoid losing progress
                await db.commit()

            except Exception as e:
                logger.error(f"Error saving sender {sender_email}: {str(e)}")
                await db.rollback()
                continue

        if progress_callback:
            progress_callback(
                max_messages,
                max_messages,
                f"Discovery complete! Found {len(senders_found)} senders"
            )

        logger.info(
            f"Discovery complete: processed {messages_processed} messages, "
            f"found {len(senders_found)} unique senders"
        )

        return len(senders_found)

    except Exception as e:
        logger.error(f"Unexpected error during sender discovery: {str(e)}")
        raise


# ============================================================================
# Incremental Discovery
# ============================================================================


async def discover_new_senders(
    gmail_client: GmailClient,
    db: AsyncSession,
    days_back: int = 30,
    progress_callback: Optional[Callable] = None,
) -> int:
    """
    Discover new senders from recent emails.

    Similar to discover_senders but focuses on recent messages only.
    Useful for periodic updates to find new senders.

    Args:
        gmail_client: Authenticated Gmail client
        db: Async database session
        days_back: How many days back to search (default: 30)
        progress_callback: Optional callback for progress updates

    Returns:
        Number of new senders discovered

    Example:
        >>> count = await discover_new_senders(gmail_client, db, days_back=7)
        >>> print(f"Found {count} new senders in the last week")
    """
    senders_found = {}
    messages_processed = 0

    try:
        # Build query for recent bulk emails
        base_query = f"newer_than:{days_back}d"
        queries = [
            f"{base_query} category:promotions",
            f"{base_query} category:social",
            f"{base_query} category:updates",
            f"{base_query} has:unsubscribe",
        ]

        for query in queries:
            logger.info(f"Discovering new senders with query: {query}")

            try:
                messages = await gmail_client.list_messages(query=query, max_results=1000)

                if not messages:
                    continue

                message_ids = [msg["id"] for msg in messages]

                # Process in batches
                for batch_start in range(0, len(message_ids), 100):
                    batch_ids = message_ids[batch_start:batch_start + 100]

                    try:
                        full_messages = await gmail_client.batch_get_messages(
                            batch_ids,
                            format="metadata"
                        )

                        for message in full_messages:
                            messages_processed += 1

                            headers = message.get("payload", {}).get("headers", [])
                            sender_info = gmail_client.get_sender_from_headers(headers)

                            if not sender_info.get("email"):
                                continue

                            sender_email = sender_info["email"]

                            # Check if sender already exists in database
                            stmt = select(Sender).where(Sender.email == sender_email)
                            result = await db.execute(stmt)
                            existing = result.scalar_one_or_none()

                            if existing:
                                # Already know about this sender
                                continue

                            # New sender!
                            unsubscribe_info = gmail_client.parse_list_unsubscribe_header(headers)

                            if sender_email not in senders_found:
                                senders_found[sender_email] = {
                                    "email": sender_email,
                                    "domain": sender_info.get("domain", ""),
                                    "display_name": sender_info.get("display_name", ""),
                                    "message_count": 1,
                                    "has_list_unsubscribe": bool(
                                        unsubscribe_info.get("mailto") or unsubscribe_info.get("url")
                                    ),
                                    "unsubscribe_info": unsubscribe_info,
                                }
                            else:
                                senders_found[sender_email]["message_count"] += 1

                    except GmailAPIError as e:
                        logger.warning(f"Error fetching batch: {str(e)}")
                        continue

                    await asyncio.sleep(0.1)

            except GmailAPIError as e:
                logger.error(f"Error listing messages: {str(e)}")
                continue

        # Save new senders
        for sender_email, sender_data in senders_found.items():
            new_sender = Sender(
                email=sender_email,
                domain=sender_data["domain"],
                display_name=sender_data.get("display_name"),
                message_count=sender_data["message_count"],
                has_list_unsubscribe=sender_data["has_list_unsubscribe"],
                unsubscribe_header=json.dumps(sender_data["unsubscribe_info"]) if sender_data["has_list_unsubscribe"] else None,
                unsubscribe_method=(
                    "mailto" if sender_data["unsubscribe_info"].get("mailto")
                    else "http" if sender_data["unsubscribe_info"].get("url")
                    else None
                ),
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
            )
            db.add(new_sender)

        await db.commit()

        logger.info(f"Found {len(senders_found)} new senders")
        return len(senders_found)

    except Exception as e:
        logger.error(f"Error during new sender discovery: {str(e)}")
        await db.rollback()
        raise


# ============================================================================
# Statistics
# ============================================================================


async def get_sender_stats(db: AsyncSession) -> dict:
    """
    Get statistics about discovered senders.

    Returns counts and statistics about senders in the database.

    Args:
        db: Async database session

    Returns:
        Dictionary with sender statistics:
        - total_senders: Total number of senders
        - with_unsubscribe: Senders with List-Unsubscribe header
        - unsubscribed: Senders already unsubscribed from
        - with_filters: Senders with filters created
        - by_method: Breakdown by unsubscribe method
        - top_domains: Most common domains

    Example:
        >>> stats = await get_sender_stats(db)
        >>> print(f"Total senders: {stats['total_senders']}")
        >>> print(f"Can unsubscribe from: {stats['with_unsubscribe']}")
    """
    try:
        # Total senders
        total_stmt = select(func.count(Sender.id))
        total_result = await db.execute(total_stmt)
        total_senders = total_result.scalar()

        # Senders with unsubscribe headers
        unsubscribe_stmt = select(func.count(Sender.id)).where(
            Sender.has_list_unsubscribe == True
        )
        unsubscribe_result = await db.execute(unsubscribe_stmt)
        with_unsubscribe = unsubscribe_result.scalar()

        # Already unsubscribed
        unsubscribed_stmt = select(func.count(Sender.id)).where(
            Sender.unsubscribed == True
        )
        unsubscribed_result = await db.execute(unsubscribed_stmt)
        unsubscribed = unsubscribed_result.scalar()

        # Filters created
        filters_stmt = select(func.count(Sender.id)).where(
            Sender.filter_created == True
        )
        filters_result = await db.execute(filters_stmt)
        with_filters = filters_result.scalar()

        # By method
        mailto_stmt = select(func.count(Sender.id)).where(
            Sender.unsubscribe_method == "mailto"
        )
        mailto_result = await db.execute(mailto_stmt)
        mailto_count = mailto_result.scalar()

        http_stmt = select(func.count(Sender.id)).where(
            Sender.unsubscribe_method == "http"
        )
        http_result = await db.execute(http_stmt)
        http_count = http_result.scalar()

        # Top domains
        top_domains_stmt = (
            select(Sender.domain, func.count(Sender.id).label("count"))
            .group_by(Sender.domain)
            .order_by(func.count(Sender.id).desc())
            .limit(10)
        )
        top_domains_result = await db.execute(top_domains_stmt)
        top_domains = [
            {"domain": domain, "count": count}
            for domain, count in top_domains_result.all()
        ]

        stats = {
            "total_senders": total_senders,
            "with_unsubscribe": with_unsubscribe,
            "unsubscribed": unsubscribed,
            "with_filters": with_filters,
            "by_method": {
                "mailto": mailto_count,
                "http": http_count,
                "none": total_senders - mailto_count - http_count,
            },
            "top_domains": top_domains,
        }

        return stats

    except Exception as e:
        logger.error(f"Error getting sender stats: {str(e)}")
        return {
            "total_senders": 0,
            "with_unsubscribe": 0,
            "unsubscribed": 0,
            "with_filters": 0,
            "by_method": {"mailto": 0, "http": 0, "none": 0},
            "top_domains": [],
        }
