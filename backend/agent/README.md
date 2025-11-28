# Inbox Nuke Agent Modules

This directory contains the core agent logic for the Inbox Nuke email cleanup application.

## Module Overview

### 1. `safety.py`
Safety guardrails and protection mechanisms to prevent accidental deletion of important emails.

**Key Features:**
- Protected domain checking (banking, government, healthcare, etc.)
- Protected keyword detection (invoice, receipt, order, etc.)
- Sender pattern matching (noreply@, no-reply@, etc.)
- Whitelist integration
- Domain categorization

### 2. `unsubscribe.py`
Handles unsubscribing from email senders via List-Unsubscribe headers.

**Key Features:**
- `mailto:` protocol unsubscribe (sends email)
- HTTP GET/POST unsubscribe (web requests)
- Automatic fallback between methods
- Database tracking of unsubscribe status
- Parse List-Unsubscribe headers with parameters

**Main Functions:**
- `unsubscribe(gmail_client, sender, db)` - Main unsubscribe function
- `unsubscribe_via_mailto(gmail_client, mailto_address, sender_email)` - Email-based unsubscribe
- `unsubscribe_via_http(url, timeout)` - HTTP-based unsubscribe

**Data Classes:**
- `UnsubscribeResult` - Result with success status, method used, and error message

### 3. `filters.py`
Creates and manages Gmail filters to automatically mute emails from specific senders.

**Key Features:**
- Creates "Muted" parent label
- Creates "Muted/{domain}" sublabels for organization
- Sets up filters to skip inbox and mark as read
- Checks for existing filters to avoid duplicates
- Batch filter creation
- Label caching for performance

**Main Functions:**
- `create_mute_filter(gmail_client, sender, db)` - Create filter for a sender
- `check_filter_exists(gmail_client, sender_email)` - Check if filter exists
- `get_muted_label_id(gmail_client)` - Get or create Muted label (cached)
- `create_filters_for_senders(gmail_client, sender_ids, db)` - Batch create filters
- `delete_filter_for_sender(gmail_client, sender, db)` - Remove filter

### 4. `cleanup.py`
Handles email deletion and cleanup operations with size estimation.

**Key Features:**
- Delete emails from specific senders with age filtering
- Delete large attachments to free storage
- Delete by Gmail category (promotions, social, updates)
- Estimate bytes freed from message sizes
- Batch operations with rate limiting
- Emails moved to trash (recoverable for 30 days)

**Main Functions:**
- `delete_emails_from_sender(gmail_client, sender, older_than_days, db)` - Delete from sender
- `cleanup_large_attachments(gmail_client, older_than_days, min_size_mb, db)` - Remove large files
- `cleanup_category(gmail_client, category, older_than_days, db)` - Clean by category
- `cleanup_multiple_senders(gmail_client, senders, older_than_days, db)` - Batch cleanup

**Data Classes:**
- `CleanupResult` - Result with emails deleted, bytes freed, and errors

### 5. `discovery.py`
Discovers email senders and extracts unsubscribe information from mailbox.

**Key Features:**
- Scans promotions, social, updates categories
- Extracts sender email, domain, display name
- Parses List-Unsubscribe headers (mailto and HTTP)
- Creates or updates Sender records in database
- Tracks message counts per sender
- Progress callbacks for UI updates
- Incremental discovery for new senders

**Main Functions:**
- `discover_senders(gmail_client, db, progress_callback, max_messages)` - Full discovery scan
- `discover_new_senders(gmail_client, db, days_back, progress_callback)` - Find recent senders
- `get_sender_stats(db)` - Get statistics about discovered senders

**Statistics Returned:**
- Total senders
- Senders with unsubscribe headers
- Already unsubscribed count
- Filters created count
- Breakdown by unsubscribe method (mailto/http/none)
- Top domains by sender count

## Usage Examples

### Unsubscribe from a sender
```python
from agent.unsubscribe import unsubscribe

result = await unsubscribe(gmail_client, sender, db)
if result.success:
    print(f"Unsubscribed via {result.method}")
else:
    print(f"Failed: {result.error}")
```

### Create a mute filter
```python
from agent.filters import create_mute_filter

filter_id = await create_mute_filter(gmail_client, sender, db)
if filter_id:
    print(f"Created filter: {filter_id}")
```

### Delete old emails from a sender
```python
from agent.cleanup import delete_emails_from_sender

result = await delete_emails_from_sender(
    gmail_client,
    sender,
    older_than_days=60
)
print(f"Deleted {result.emails_deleted} emails")
print(f"Freed {result.bytes_freed / 1024**2:.2f} MB")
```

### Discover senders
```python
from agent.discovery import discover_senders, get_sender_stats

def progress(current, total, message):
    print(f"{current}/{total}: {message}")

count = await discover_senders(gmail_client, db, progress_callback=progress)
print(f"Discovered {count} senders")

stats = await get_sender_stats(db)
print(f"Total: {stats['total_senders']}")
print(f"With unsubscribe: {stats['with_unsubscribe']}")
```

### Clean up large attachments
```python
from agent.cleanup import cleanup_large_attachments

result = await cleanup_large_attachments(
    gmail_client,
    older_than_days=180,
    min_size_mb=10
)
print(f"Freed {result.bytes_freed / 1024**3:.2f} GB")
```

## Error Handling

All modules include comprehensive error handling:
- Gmail API errors (rate limits, quotas, auth)
- Network errors (timeouts, connection issues)
- Database errors (rollback on failure)
- Validation errors (invalid inputs)

Errors are logged with Python's logging module and returned in result objects where appropriate.

## Rate Limiting

The modules respect Gmail API rate limits:
- Automatic retry with exponential backoff
- Batch operations for efficiency (up to 1000 messages per batch)
- Small delays between operations in batch functions
- Uses tenacity library for retry logic

## Dependencies

All modules require:
- `gmail_client.GmailClient` - Gmail API wrapper
- `models.Sender` - Database model for senders
- `sqlalchemy.ext.asyncio.AsyncSession` - Async database session
- `httpx` - HTTP client (for unsubscribe.py)

## Testing

To test the modules:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Set up environment variables in `.env`
3. Initialize database with `init_db()`
4. Authenticate with Gmail OAuth
5. Run individual functions with test data

## Notes

- All email deletions move to trash (recoverable for 30 days)
- Filters are created in Gmail and persist independently
- Unsubscribe operations are logged but not guaranteed (depends on sender)
- Discovery can be run periodically to find new senders
- Label cache improves performance but can be cleared with `clear_label_cache()`
