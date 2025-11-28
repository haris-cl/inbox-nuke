"""
Unsubscribe handlers for Inbox Nuke Agent.

This module provides functionality to unsubscribe from email senders using:
- mailto: protocol for email-based unsubscribe
- HTTP GET/POST requests for web-based unsubscribe
- Automatic fallback between methods
- Database tracking of unsubscribe status
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import parse_qs, urlparse

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gmail_client import GmailClient
from models import Sender

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class UnsubscribeResult:
    """
    Result of an unsubscribe attempt.

    Attributes:
        success: Whether the unsubscribe was successful
        method: The method used (mailto, http, none)
        error: Optional error message if failed
    """
    success: bool
    method: str  # mailto, http, none
    error: Optional[str] = None


# ============================================================================
# Mailto Unsubscribe
# ============================================================================


def parse_mailto_address(mailto_url: str) -> dict:
    """
    Parse a mailto: URL to extract address, subject, and body.

    Args:
        mailto_url: mailto: URL (e.g., "mailto:unsub@example.com?subject=unsubscribe")

    Returns:
        Dictionary with 'address', 'subject', and 'body' keys

    Example:
        >>> result = parse_mailto_address("mailto:unsub@example.com?subject=Unsubscribe")
        >>> print(result)
        {'address': 'unsub@example.com', 'subject': 'Unsubscribe', 'body': ''}
    """
    result = {
        "address": "",
        "subject": "Unsubscribe",
        "body": "",
    }

    # Remove 'mailto:' prefix
    if mailto_url.lower().startswith("mailto:"):
        mailto_url = mailto_url[7:]

    # Split address from parameters
    if "?" in mailto_url:
        address, params = mailto_url.split("?", 1)
        result["address"] = address.strip()

        # Parse query parameters
        parsed_params = parse_qs(params)

        if "subject" in parsed_params:
            result["subject"] = parsed_params["subject"][0]

        if "body" in parsed_params:
            result["body"] = parsed_params["body"][0]
    else:
        result["address"] = mailto_url.strip()

    return result


async def unsubscribe_via_mailto(
    gmail_client: GmailClient,
    mailto_address: str,
    sender_email: str,
) -> bool:
    """
    Unsubscribe via mailto: protocol by sending an email.

    Args:
        gmail_client: Authenticated Gmail client
        mailto_address: The mailto: URL from List-Unsubscribe header
        sender_email: The sender's email address (for logging)

    Returns:
        True if email was sent successfully, False otherwise

    Example:
        >>> success = await unsubscribe_via_mailto(
        ...     gmail_client,
        ...     "mailto:unsub@example.com?subject=unsubscribe",
        ...     "newsletter@example.com"
        ... )
    """
    try:
        # Parse mailto URL
        parsed = parse_mailto_address(mailto_address)

        if not parsed["address"]:
            logger.error(f"Invalid mailto address: {mailto_address}")
            return False

        # Get user's email for body
        service = await gmail_client.get_service()
        profile = await asyncio.to_thread(
            service.users().getProfile(userId="me").execute
        )
        user_email = profile.get("emailAddress", "")

        # Build email body
        if parsed["body"]:
            body = parsed["body"]
        else:
            body = (
                f"Please unsubscribe me from your mailing list.\n\n"
                f"Email: {user_email}\n"
            )

        # Send unsubscribe email
        await gmail_client.send_message(
            to=parsed["address"],
            subject=parsed["subject"],
            body=body,
        )

        logger.info(f"Sent mailto unsubscribe to {parsed['address']} for sender {sender_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to unsubscribe via mailto for {sender_email}: {str(e)}")
        return False


# ============================================================================
# HTTP Unsubscribe
# ============================================================================


async def unsubscribe_via_http(
    url: str,
    timeout: int = 10,
) -> bool:
    """
    Unsubscribe via HTTP GET request to unsubscribe URL.

    Makes an HTTP GET request to the unsubscribe URL, follows redirects,
    and checks for success indicators.

    Args:
        url: The HTTP unsubscribe URL from List-Unsubscribe header
        timeout: Request timeout in seconds (default: 10)

    Returns:
        True if request was successful, False otherwise

    Example:
        >>> success = await unsubscribe_via_http("https://example.com/unsubscribe?id=123")
    """
    try:
        # Validate URL
        parsed_url = urlparse(url)
        if not parsed_url.scheme in ["http", "https"]:
            logger.error(f"Invalid URL scheme: {url}")
            return False

        # Set up HTTP client with reasonable defaults
        async with httpx.AsyncClient(
            follow_redirects=True,
            max_redirects=5,
            timeout=timeout,
        ) as client:
            # Set a realistic User-Agent
            headers = {
                "User-Agent": "Mozilla/5.0 (Inbox Nuke Email Manager)",
            }

            # Make GET request
            response = await client.get(url, headers=headers)

            # Check for success
            # Accept 200-299 status codes as success
            if 200 <= response.status_code < 300:
                logger.info(f"HTTP unsubscribe successful: {url} (status: {response.status_code})")
                return True

            # Some unsubscribe pages redirect to confirmation with 3xx
            # If we got here after redirects, consider it a success
            elif response.status_code in [301, 302, 303, 307, 308]:
                logger.info(f"HTTP unsubscribe redirected: {url} (status: {response.status_code})")
                return True

            else:
                logger.warning(f"HTTP unsubscribe returned status {response.status_code}: {url}")
                return False

    except httpx.TimeoutException:
        logger.error(f"HTTP unsubscribe timed out: {url}")
        return False
    except httpx.RequestError as e:
        logger.error(f"HTTP unsubscribe request failed for {url}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during HTTP unsubscribe for {url}: {str(e)}")
        return False


# ============================================================================
# Main Unsubscribe Function
# ============================================================================


async def unsubscribe(
    gmail_client: GmailClient,
    sender: Sender,
    db: AsyncSession,
) -> UnsubscribeResult:
    """
    Unsubscribe from a sender using available methods.

    Tries mailto method first if available, then falls back to HTTP.
    Updates sender record in database with unsubscribe status.

    Args:
        gmail_client: Authenticated Gmail client
        sender: Sender object from database
        db: Async database session

    Returns:
        UnsubscribeResult with success status and method used

    Example:
        >>> result = await unsubscribe(gmail_client, sender, db)
        >>> if result.success:
        ...     print(f"Unsubscribed via {result.method}")
    """
    # Check if sender has unsubscribe information
    if not sender.has_list_unsubscribe or not sender.unsubscribe_header:
        logger.warning(f"No unsubscribe information for sender: {sender.email}")
        return UnsubscribeResult(
            success=False,
            method="none",
            error="No List-Unsubscribe header available"
        )

    # Parse unsubscribe header (stored as JSON string)
    import json
    try:
        unsubscribe_info = json.loads(sender.unsubscribe_header)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse unsubscribe header for {sender.email}")
        return UnsubscribeResult(
            success=False,
            method="none",
            error="Invalid unsubscribe header format"
        )

    mailto_addr = unsubscribe_info.get("mailto")
    http_url = unsubscribe_info.get("url")

    # Try mailto method first (more reliable)
    if mailto_addr:
        logger.info(f"Attempting mailto unsubscribe for {sender.email}")
        success = await unsubscribe_via_mailto(gmail_client, mailto_addr, sender.email)

        if success:
            # Update sender in database
            sender.unsubscribed = True
            sender.unsubscribed_at = datetime.utcnow()
            sender.unsubscribe_method = "mailto"

            await db.commit()
            await db.refresh(sender)

            logger.info(f"Successfully unsubscribed from {sender.email} via mailto")
            return UnsubscribeResult(success=True, method="mailto")

    # Fall back to HTTP method
    if http_url:
        logger.info(f"Attempting HTTP unsubscribe for {sender.email}")
        success = await unsubscribe_via_http(http_url)

        if success:
            # Update sender in database
            sender.unsubscribed = True
            sender.unsubscribed_at = datetime.utcnow()
            sender.unsubscribe_method = "http"

            await db.commit()
            await db.refresh(sender)

            logger.info(f"Successfully unsubscribed from {sender.email} via HTTP")
            return UnsubscribeResult(success=True, method="http")

    # Both methods failed or unavailable
    error_msg = "All unsubscribe methods failed"
    if not mailto_addr and not http_url:
        error_msg = "No unsubscribe methods available"

    logger.error(f"Failed to unsubscribe from {sender.email}: {error_msg}")
    return UnsubscribeResult(
        success=False,
        method="none",
        error=error_msg
    )
