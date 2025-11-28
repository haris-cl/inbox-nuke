"""
Attachments router for large file detection and cleanup.
Provides endpoints for discovering and cleaning up emails with large attachments.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from gmail_client import GmailClient, GmailAPIError
from models import GmailCredentials

router = APIRouter()
logger = logging.getLogger(__name__)


# ============================================================================
# Schemas
# ============================================================================


class LargeEmailResponse(BaseModel):
    """Response model for a large email."""
    message_id: str = Field(..., description="Gmail message ID")
    subject: str = Field(..., description="Email subject")
    from_email: str = Field(..., description="Sender email address")
    from_name: Optional[str] = Field(None, description="Sender display name")
    size: int = Field(..., description="Email size in bytes")
    size_mb: float = Field(..., description="Email size in megabytes")
    date: str = Field(..., description="Email date")


class LargeEmailsListResponse(BaseModel):
    """Response model for list of large emails."""
    emails: List[LargeEmailResponse]
    total_count: int
    total_size_bytes: int
    total_size_mb: float


class CleanupRequest(BaseModel):
    """Request model for cleaning up specific messages."""
    message_ids: List[str] = Field(..., min_items=1, description="List of message IDs to delete")


class CleanupResponse(BaseModel):
    """Response model for cleanup operation."""
    deleted_count: int = Field(..., description="Number of emails deleted")
    bytes_freed: int = Field(..., description="Total bytes freed")
    mb_freed: float = Field(..., description="Total MB freed")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


# ============================================================================
# Helper Functions
# ============================================================================


def parse_message_headers(message: dict) -> tuple[str, str, str, str]:
    """
    Parse message headers to extract subject, from, and date.

    Args:
        message: Gmail message dict

    Returns:
        Tuple of (subject, from_email, from_name, date)
    """
    headers = message.get('payload', {}).get('headers', [])
    subject = ""
    from_email = ""
    from_name = ""
    date = ""

    for header in headers:
        name = header['name'].lower()
        value = header['value']

        if name == 'subject':
            subject = value
        elif name == 'from':
            # Parse "Display Name <email@domain.com>" format
            from email.utils import parseaddr
            from_name, from_email = parseaddr(value)
        elif name == 'date':
            date = value

    return subject, from_email, from_name, date


# ============================================================================
# Endpoints
# ============================================================================


@router.get("/large", response_model=LargeEmailsListResponse)
async def get_large_attachments(
    min_size_mb: int = Query(default=5, ge=1, le=100, description="Minimum email size in MB"),
    older_than_days: int = Query(default=365, ge=0, le=3650, description="Only show emails older than this many days"),
    max_results: int = Query(default=100, ge=1, le=500, description="Maximum number of results to return"),
    db: AsyncSession = Depends(get_db),
) -> LargeEmailsListResponse:
    """
    Query Gmail for large emails for targeted cleanup.

    Searches for emails larger than specified size and older than specified age.
    Useful for freeing up storage by removing large attachments.

    Args:
        min_size_mb: Minimum email size in megabytes (default: 5)
        older_than_days: Only show emails older than this many days (default: 365)
        max_results: Maximum number of results to return (default: 100)
        db: Database session

    Returns:
        LargeEmailsListResponse: List of large emails with metadata

    Raises:
        HTTPException: If Gmail API fails or user not authenticated
    """
    try:
        # Initialize Gmail client
        gmail_client = GmailClient(db=db)

        # Build search query
        # Gmail uses 'larger:' operator with bytes
        size_bytes = min_size_mb * 1024 * 1024
        query = f"larger:{size_bytes}"

        if older_than_days > 0:
            query += f" older_than:{older_than_days}d"

        logger.info(f"Searching for large emails with query: {query}")

        # Search for messages
        messages = await gmail_client.list_messages(query=query, max_results=max_results)

        if not messages:
            return LargeEmailsListResponse(
                emails=[],
                total_count=0,
                total_size_bytes=0,
                total_size_mb=0.0,
            )

        # Get full message details in batches
        message_ids = [msg["id"] for msg in messages]
        full_messages = await gmail_client.batch_get_messages(
            message_ids,
            format="metadata"
        )

        # Parse and format response
        large_emails = []
        total_size_bytes = 0

        for msg in full_messages:
            # Get message size
            size = gmail_client.get_message_size(msg)
            total_size_bytes += size

            # Parse headers
            subject, from_email, from_name, date = parse_message_headers(msg)

            large_emails.append(LargeEmailResponse(
                message_id=msg['id'],
                subject=subject or "(No Subject)",
                from_email=from_email or "unknown",
                from_name=from_name if from_name else None,
                size=size,
                size_mb=round(size / (1024 * 1024), 2),
                date=date or "unknown",
            ))

        # Sort by size (largest first)
        large_emails.sort(key=lambda x: x.size, reverse=True)

        return LargeEmailsListResponse(
            emails=large_emails,
            total_count=len(large_emails),
            total_size_bytes=total_size_bytes,
            total_size_mb=round(total_size_bytes / (1024 * 1024), 2),
        )

    except GmailAPIError as e:
        logger.error(f"Gmail API error while fetching large attachments: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Gmail API error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error while fetching large attachments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch large attachments: {str(e)}",
        )


@router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_attachments(
    request: CleanupRequest,
    db: AsyncSession = Depends(get_db),
) -> CleanupResponse:
    """
    Trash specified messages to free up storage.

    Accepts a list of message IDs and moves them to trash.
    Messages can be recovered from trash for 30 days.

    Args:
        request: Cleanup request with message IDs
        db: Database session

    Returns:
        CleanupResponse: Cleanup statistics including bytes freed

    Raises:
        HTTPException: If cleanup fails
    """
    try:
        # Initialize Gmail client
        gmail_client = GmailClient(db=db)

        # Get message details first to calculate size
        logger.info(f"Getting details for {len(request.message_ids)} messages before deletion")

        full_messages = await gmail_client.batch_get_messages(
            request.message_ids,
            format="metadata"
        )

        # Calculate total size
        total_size = sum(gmail_client.get_message_size(msg) for msg in full_messages)

        # Trash messages
        logger.info(f"Trashing {len(request.message_ids)} messages")
        deleted_count = await gmail_client.trash_messages(request.message_ids)

        logger.info(
            f"Successfully trashed {deleted_count} emails, "
            f"freed approximately {total_size / (1024 * 1024):.2f} MB"
        )

        return CleanupResponse(
            deleted_count=deleted_count,
            bytes_freed=total_size,
            mb_freed=round(total_size / (1024 * 1024), 2),
            errors=[],
        )

    except GmailAPIError as e:
        error_msg = f"Gmail API error during cleanup: {str(e)}"
        logger.error(error_msg)

        # Return partial success if some deletions succeeded
        return CleanupResponse(
            deleted_count=0,
            bytes_freed=0,
            mb_freed=0.0,
            errors=[error_msg],
        )

    except Exception as e:
        logger.error(f"Unexpected error during cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup attachments: {str(e)}",
        )
