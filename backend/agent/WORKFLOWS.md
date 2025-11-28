# Inbox Nuke Agent Workflows

This document outlines common workflows and usage patterns for the Inbox Nuke Agent modules.

## Workflow 1: Complete Inbox Cleanup

A complete cleanup workflow that discovers senders, unsubscribes, creates filters, and deletes old emails.

```python
from agent import (
    discover_senders,
    unsubscribe,
    create_mute_filter,
    delete_emails_from_sender,
    check_sender_safety,
)
from gmail_client import GmailClient
from db import get_db
from models import Sender
from sqlalchemy import select

async def complete_cleanup_workflow(user_id: str = "default_user"):
    """Complete inbox cleanup workflow."""

    async with get_db() as db:
        # Step 1: Initialize Gmail client
        gmail_client = GmailClient(db=db, user_id=user_id)

        # Step 2: Discover senders
        print("Discovering senders...")
        def progress(current, total, msg):
            print(f"  [{current}/{total}] {msg}")

        sender_count = await discover_senders(
            gmail_client,
            db,
            progress_callback=progress,
            max_messages=5000
        )
        print(f"Discovered {sender_count} senders\n")

        # Step 3: Get all senders with unsubscribe capability
        stmt = select(Sender).where(
            Sender.has_list_unsubscribe == True,
            Sender.unsubscribed == False
        )
        result = await db.execute(stmt)
        senders = result.scalars().all()

        print(f"Found {len(senders)} senders to unsubscribe from\n")

        # Step 4: Unsubscribe from each (with safety checks)
        unsubscribed_count = 0
        for sender in senders:
            # Safety check
            safety_result = await check_sender_safety(sender.email, db)
            if not safety_result.safe:
                print(f"  ⚠️  Skipping {sender.email}: {safety_result.reason}")
                continue

            # Unsubscribe
            result = await unsubscribe(gmail_client, sender, db)
            if result.success:
                print(f"  ✓ Unsubscribed from {sender.email} via {result.method}")
                unsubscribed_count += 1
            else:
                print(f"  ✗ Failed to unsubscribe from {sender.email}: {result.error}")

        print(f"\nUnsubscribed from {unsubscribed_count} senders\n")

        # Step 5: Create filters for all senders
        stmt = select(Sender).where(Sender.filter_created == False)
        result = await db.execute(stmt)
        senders = result.scalars().all()

        filter_count = 0
        for sender in senders:
            filter_id = await create_mute_filter(gmail_client, sender, db)
            if filter_id:
                print(f"  ✓ Created filter for {sender.email}")
                filter_count += 1

        print(f"\nCreated {filter_count} filters\n")

        # Step 6: Delete old emails
        stmt = select(Sender)
        result = await db.execute(stmt)
        all_senders = result.scalars().all()

        total_deleted = 0
        total_freed = 0

        for sender in all_senders:
            # Safety check
            safety_result = await check_sender_safety(sender.email, db)
            if not safety_result.safe:
                continue

            # Delete emails older than 90 days
            cleanup_result = await delete_emails_from_sender(
                gmail_client,
                sender,
                older_than_days=90,
                db=db
            )

            if cleanup_result.emails_deleted > 0:
                total_deleted += cleanup_result.emails_deleted
                total_freed += cleanup_result.bytes_freed
                print(f"  ✓ Deleted {cleanup_result.emails_deleted} emails from {sender.email}")

        print(f"\nTotal: {total_deleted} emails deleted, {total_freed / 1024**3:.2f} GB freed")
```

## Workflow 2: Periodic Maintenance

Run periodically (e.g., weekly) to discover new senders and maintain cleanup.

```python
from agent import discover_new_senders, get_sender_stats

async def periodic_maintenance():
    """Discover new senders and show stats."""

    async with get_db() as db:
        gmail_client = GmailClient(db=db)

        # Find senders from last 7 days
        new_count = await discover_new_senders(
            gmail_client,
            db,
            days_back=7
        )

        print(f"Found {new_count} new senders in the last week")

        # Get updated stats
        stats = await get_sender_stats(db)
        print(f"\nInbox Statistics:")
        print(f"  Total senders: {stats['total_senders']}")
        print(f"  With unsubscribe: {stats['with_unsubscribe']}")
        print(f"  Already unsubscribed: {stats['unsubscribed']}")
        print(f"  Filters created: {stats['with_filters']}")
        print(f"\nUnsubscribe methods:")
        print(f"  mailto: {stats['by_method']['mailto']}")
        print(f"  http: {stats['by_method']['http']}")
        print(f"  none: {stats['by_method']['none']}")
```

## Workflow 3: Storage Cleanup

Focus on freeing up storage by removing large attachments and old promotional emails.

```python
from agent import cleanup_large_attachments, cleanup_category

async def storage_cleanup():
    """Free up storage space."""

    async with get_db() as db:
        gmail_client = GmailClient(db=db)

        # Remove large attachments older than 1 year
        print("Cleaning up large attachments...")
        result = await cleanup_large_attachments(
            gmail_client,
            older_than_days=365,
            min_size_mb=10
        )
        print(f"  Deleted {result.emails_deleted} emails with large attachments")
        print(f"  Freed {result.bytes_freed / 1024**3:.2f} GB\n")

        # Clean up promotional emails older than 3 months
        print("Cleaning up promotional emails...")
        result = await cleanup_category(
            gmail_client,
            category="promotions",
            older_than_days=90
        )
        print(f"  Deleted {result.emails_deleted} promotional emails")
        print(f"  Freed {result.bytes_freed / 1024**2:.2f} MB\n")

        # Clean up social emails older than 6 months
        print("Cleaning up social emails...")
        result = await cleanup_category(
            gmail_client,
            category="social",
            older_than_days=180
        )
        print(f"  Deleted {result.emails_deleted} social emails")
        print(f"  Freed {result.bytes_freed / 1024**2:.2f} MB")
```

## Workflow 4: Targeted Sender Cleanup

Clean up emails from specific senders or domains.

```python
from sqlalchemy import select
from models import Sender

async def targeted_cleanup(domain: str = None, sender_email: str = None):
    """Clean up emails from specific sender or domain."""

    async with get_db() as db:
        gmail_client = GmailClient(db=db)

        # Build query
        if sender_email:
            stmt = select(Sender).where(Sender.email == sender_email)
        elif domain:
            stmt = select(Sender).where(Sender.domain == domain)
        else:
            raise ValueError("Must provide either sender_email or domain")

        result = await db.execute(stmt)
        senders = result.scalars().all()

        if not senders:
            print(f"No senders found for {sender_email or domain}")
            return

        print(f"Found {len(senders)} sender(s) to clean up\n")

        for sender in senders:
            # Unsubscribe
            unsub_result = await unsubscribe(gmail_client, sender, db)
            if unsub_result.success:
                print(f"✓ Unsubscribed from {sender.email}")

            # Create filter
            filter_id = await create_mute_filter(gmail_client, sender, db)
            if filter_id:
                print(f"✓ Created filter for {sender.email}")

            # Delete all emails (any age)
            cleanup_result = await delete_emails_from_sender(
                gmail_client,
                sender,
                older_than_days=0,  # All emails
                db=db
            )

            if cleanup_result.emails_deleted > 0:
                print(f"✓ Deleted {cleanup_result.emails_deleted} emails from {sender.email}")
                print(f"  Freed {cleanup_result.bytes_freed / 1024**2:.2f} MB\n")
```

## Workflow 5: Batch Filter Creation

Create filters for multiple senders at once.

```python
from agent import create_filters_for_senders

async def batch_create_filters():
    """Create filters for all senders without filters."""

    async with get_db() as db:
        gmail_client = GmailClient(db=db)

        # Get all senders without filters
        stmt = select(Sender.id).where(Sender.filter_created == False)
        result = await db.execute(stmt)
        sender_ids = [row[0] for row in result.all()]

        print(f"Creating filters for {len(sender_ids)} senders...")

        # Batch create
        result = await create_filters_for_senders(
            gmail_client,
            sender_ids,
            db
        )

        print(f"\nResults:")
        print(f"  Created: {result['created']}")
        print(f"  Skipped: {result['skipped']}")
        print(f"  Failed: {result['failed']}")
```

## Workflow 6: Safe Unsubscribe with Confirmation

Unsubscribe with safety checks and user confirmation.

```python
from agent import check_sender_safety, is_whitelisted

async def safe_unsubscribe_workflow():
    """Unsubscribe with safety checks."""

    async with get_db() as db:
        gmail_client = GmailClient(db=db)

        # Get senders to process
        stmt = select(Sender).where(
            Sender.has_list_unsubscribe == True,
            Sender.unsubscribed == False
        )
        result = await db.execute(stmt)
        senders = result.scalars().all()

        for sender in senders:
            # Check if whitelisted
            if await is_whitelisted(sender.domain, db):
                print(f"⚠️  Skipping whitelisted sender: {sender.email}")
                continue

            # Safety check
            safety = await check_sender_safety(sender.email, db)
            if not safety.safe:
                print(f"⚠️  Skipping protected sender: {sender.email}")
                print(f"    Reason: {safety.reason}")
                continue

            # Show sender info
            print(f"\nSender: {sender.email}")
            print(f"  Display name: {sender.display_name or 'N/A'}")
            print(f"  Message count: {sender.message_count}")
            print(f"  Method: {sender.unsubscribe_method}")

            # In a real app, you'd ask for user confirmation here
            # For example, using a CLI prompt or web UI
            confirm = True  # Replace with actual confirmation

            if confirm:
                result = await unsubscribe(gmail_client, sender, db)
                if result.success:
                    print(f"  ✓ Successfully unsubscribed via {result.method}")
                else:
                    print(f"  ✗ Failed: {result.error}")
```

## Error Handling Best Practices

All workflows should include proper error handling:

```python
import logging
from gmail_client import GmailAPIError, GmailRateLimitError

logger = logging.getLogger(__name__)

async def robust_workflow():
    """Example with proper error handling."""

    try:
        async with get_db() as db:
            gmail_client = GmailClient(db=db)

            # Your workflow here
            result = await discover_senders(gmail_client, db)

    except GmailRateLimitError as e:
        logger.error(f"Hit Gmail API rate limit: {e}")
        # Maybe schedule a retry later

    except GmailAPIError as e:
        logger.error(f"Gmail API error: {e}")
        # Handle API errors

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        # Handle other errors
```

## Integration with FastAPI

Example of integrating workflows into FastAPI endpoints:

```python
from fastapi import APIRouter, Depends
from db import get_db

router = APIRouter(prefix="/api/cleanup")

@router.post("/discover")
async def discover_endpoint(db: AsyncSession = Depends(get_db)):
    """Discover senders endpoint."""
    gmail_client = GmailClient(db=db)

    count = await discover_senders(gmail_client, db, max_messages=1000)

    return {"senders_discovered": count}

@router.post("/unsubscribe/{sender_id}")
async def unsubscribe_endpoint(
    sender_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Unsubscribe from a specific sender."""
    # Get sender
    sender = await db.get(Sender, sender_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")

    # Unsubscribe
    gmail_client = GmailClient(db=db)
    result = await unsubscribe(gmail_client, sender, db)

    return {
        "success": result.success,
        "method": result.method,
        "error": result.error
    }
```
