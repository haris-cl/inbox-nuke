"""
Gmail API client wrapper for Inbox Nuke Agent.

This module provides a comprehensive Gmail API wrapper with:
- Automatic token refresh and credential management
- Retry logic with exponential backoff for rate limiting
- Batch operations for efficient API usage
- Message listing, retrieval, and manipulation
- Filter and label management
- Unsubscribe header parsing
- Proper error handling and rate limit respect

Gmail API Quotas:
- 250 quota units per user per second
- 1,000,000,000 quota units per day
- list(): 5 units, get(): 5 units, batchModify(): 50 units
"""

import asyncio
import base64
import json
import re
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from typing import Dict, List, Optional, Any
from urllib.parse import unquote

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import BatchHttpRequest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

from config import settings
from models import GmailCredentials
from utils.encryption import encrypt_token, decrypt_token

import logging

logger = logging.getLogger(__name__)


# ============================================================================
# Custom Exceptions
# ============================================================================


class GmailAPIError(Exception):
    """Base exception for Gmail API errors."""
    pass


class GmailAuthError(GmailAPIError):
    """Raised when authentication fails or credentials are invalid."""
    pass


class GmailRateLimitError(GmailAPIError):
    """Raised when Gmail API rate limit is exceeded."""
    pass


class GmailQuotaExceededError(GmailAPIError):
    """Raised when Gmail API quota is exceeded."""
    pass


# ============================================================================
# Gmail Client
# ============================================================================


class GmailClient:
    """
    Comprehensive Gmail API client with retry logic and rate limiting.

    This client handles:
    - Automatic token refresh
    - Database credential storage
    - Rate limiting and retry logic
    - Batch operations
    - Message operations (list, get, trash, delete)
    - Filter and label management
    - Unsubscribe header parsing

    Attributes:
        db: AsyncSession for database operations
        credentials: Optional GmailCredentials from database
        user_id: User identifier for multi-user support
    """

    # Gmail API scopes required
    SCOPES = [
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/gmail.settings.basic",
    ]

    def __init__(
        self,
        db: AsyncSession,
        credentials: Optional[GmailCredentials] = None,
        user_id: str = "default_user",
    ):
        """
        Initialize Gmail client.

        Args:
            db: Async database session
            credentials: Optional pre-loaded GmailCredentials
            user_id: User identifier (default: "default_user")
        """
        self.db = db
        self.credentials = credentials
        self.user_id = user_id
        self._service = None

    async def get_service(self):
        """
        Get or create authenticated Gmail API service.

        Loads credentials from database, refreshes if expired,
        and updates database with new tokens.

        Returns:
            Resource: Authenticated Gmail API service

        Raises:
            GmailAuthError: If credentials are missing or invalid
        """
        # Load credentials if not already loaded
        if not self.credentials:
            stmt = select(GmailCredentials).where(
                GmailCredentials.user_id == self.user_id
            )
            result = await self.db.execute(stmt)
            self.credentials = result.scalar_one_or_none()

        if not self.credentials:
            raise GmailAuthError(
                f"No Gmail credentials found for user: {self.user_id}. "
                "Please authenticate via OAuth flow."
            )

        # Decrypt tokens
        try:
            access_token = decrypt_token(self.credentials.access_token)
            refresh_token = decrypt_token(self.credentials.refresh_token)
        except Exception as e:
            raise GmailAuthError(f"Failed to decrypt credentials: {str(e)}")

        # Parse scopes
        scopes = json.loads(self.credentials.scopes)

        # Create credentials object
        creds = Credentials(
            token=access_token,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=scopes,
        )

        # Set expiry
        creds.expiry = self.credentials.token_expiry

        # Refresh if expired
        if creds.expired and creds.refresh_token:
            try:
                await asyncio.to_thread(creds.refresh, Request())

                # Update database with new tokens
                self.credentials.access_token = encrypt_token(creds.token)
                self.credentials.token_expiry = creds.expiry
                self.credentials.updated_at = datetime.utcnow()

                await self.db.commit()
                await self.db.refresh(self.credentials)

                logger.info(f"Refreshed Gmail credentials for user: {self.user_id}")
            except Exception as e:
                raise GmailAuthError(f"Failed to refresh credentials: {str(e)}")

        # Build service (use thread pool for sync API)
        if not self._service:
            self._service = await asyncio.to_thread(
                build, "gmail", "v1", credentials=creds
            )

        return self._service

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def list_messages(
        self,
        query: str = "",
        max_results: int = 100,
        label_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List messages matching query with automatic pagination.

        Args:
            query: Gmail search query (e.g., "from:example.com")
            max_results: Maximum number of messages to return
            label_ids: Optional list of label IDs to filter by

        Returns:
            List of message metadata dictionaries with 'id' and 'threadId'

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> messages = await client.list_messages("is:unread", max_results=50)
            >>> print(len(messages))
            50
        """
        service = await self.get_service()
        messages = []
        page_token = None

        try:
            while len(messages) < max_results:
                # Calculate how many to fetch in this batch
                batch_size = min(500, max_results - len(messages))

                # Build request
                request_params = {
                    "userId": "me",
                    "maxResults": batch_size,
                }

                if query:
                    request_params["q"] = query

                if label_ids:
                    request_params["labelIds"] = label_ids

                if page_token:
                    request_params["pageToken"] = page_token

                # Execute request
                response = await asyncio.to_thread(
                    service.users().messages().list(**request_params).execute
                )

                # Add messages to result
                batch_messages = response.get("messages", [])
                messages.extend(batch_messages)

                # Check for next page
                page_token = response.get("nextPageToken")
                if not page_token or len(messages) >= max_results:
                    break

            return messages[:max_results]

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                error_details = json.loads(e.content.decode())
                if "rateLimitExceeded" in str(error_details):
                    raise GmailRateLimitError("Gmail API quota exceeded")
                raise GmailAuthError(f"Permission denied: {str(e)}")
            else:
                raise GmailAPIError(f"Failed to list messages: {str(e)}")

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(5),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def get_message(
        self,
        message_id: str,
        format: str = "metadata",
    ) -> Dict[str, Any]:
        """
        Get a single message by ID.

        Args:
            message_id: Gmail message ID
            format: Response format - "minimal", "metadata", "full", or "raw"
                   - minimal: id, threadId only
                   - metadata: + headers, snippet, size (default)
                   - full: + body parts
                   - raw: full RFC 2822 message

        Returns:
            Message dictionary with requested fields

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> msg = await client.get_message("abc123", format="metadata")
            >>> print(msg['snippet'])
            'This is a preview of the email...'
        """
        service = await self.get_service()

        try:
            message = await asyncio.to_thread(
                service.users()
                .messages()
                .get(userId="me", id=message_id, format=format)
                .execute
            )
            return message

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                error_details = json.loads(e.content.decode())
                if "rateLimitExceeded" in str(error_details):
                    raise GmailRateLimitError("Gmail API quota exceeded")
                raise GmailAuthError(f"Permission denied: {str(e)}")
            elif e.resp.status == 404:
                raise GmailAPIError(f"Message not found: {message_id}")
            else:
                raise GmailAPIError(f"Failed to get message: {str(e)}")

    async def batch_get_messages(
        self,
        message_ids: List[str],
        format: str = "metadata",
    ) -> List[Dict[str, Any]]:
        """
        Get multiple messages in batch (max 100 per batch).

        Uses Gmail batch API for efficiency. Automatically splits
        into multiple batches if more than 100 messages.

        Args:
            message_ids: List of Gmail message IDs
            format: Response format (see get_message)

        Returns:
            List of message dictionaries

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> ids = ["abc123", "def456", "ghi789"]
            >>> messages = await client.batch_get_messages(ids)
            >>> print(len(messages))
            3
        """
        if not message_ids:
            return []

        service = await self.get_service()
        all_messages = []

        # Split into batches of 100 (Gmail API limit)
        for i in range(0, len(message_ids), 100):
            batch_ids = message_ids[i : i + 100]
            batch_messages = []
            errors = []

            def create_callback(batch_idx):
                """Create callback for batch request."""
                def callback(request_id, response, exception):
                    if exception:
                        errors.append((request_id, exception))
                        logger.warning(f"Batch get error for {request_id}: {exception}")
                    else:
                        batch_messages.append(response)
                return callback

            # Create batch request
            batch = service.new_batch_http_request()

            for idx, msg_id in enumerate(batch_ids):
                batch.add(
                    service.users().messages().get(
                        userId="me", id=msg_id, format=format
                    ),
                    callback=create_callback(idx),
                )

            # Execute batch
            try:
                await asyncio.to_thread(batch.execute)
            except HttpError as e:
                if e.resp.status == 429:
                    raise GmailRateLimitError("Gmail API rate limit exceeded")
                elif e.resp.status == 403:
                    raise GmailRateLimitError("Gmail API quota exceeded")
                else:
                    raise GmailAPIError(f"Batch get failed: {str(e)}")

            all_messages.extend(batch_messages)

            # Log errors but continue
            if errors:
                logger.warning(f"Batch get had {len(errors)} errors out of {len(batch_ids)}")

        return all_messages

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def trash_messages(self, message_ids: List[str]) -> int:
        """
        Move messages to trash using batchModify.

        More efficient than individual delete calls. Gmail allows
        up to 1000 messages per batchModify call.

        Args:
            message_ids: List of message IDs to trash

        Returns:
            Count of successfully trashed messages

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> count = await client.trash_messages(["id1", "id2", "id3"])
            >>> print(f"Trashed {count} messages")
            Trashed 3 messages
        """
        if not message_ids:
            return 0

        service = await self.get_service()
        total_trashed = 0

        # Process in batches of 1000 (Gmail API limit)
        for i in range(0, len(message_ids), 1000):
            batch_ids = message_ids[i : i + 1000]

            try:
                await asyncio.to_thread(
                    service.users()
                    .messages()
                    .batchModify(
                        userId="me",
                        body={
                            "ids": batch_ids,
                            "addLabelIds": ["TRASH"],
                        },
                    )
                    .execute
                )
                total_trashed += len(batch_ids)
                logger.info(f"Trashed {len(batch_ids)} messages")

            except HttpError as e:
                if e.resp.status == 429:
                    raise GmailRateLimitError("Gmail API rate limit exceeded")
                elif e.resp.status == 403:
                    raise GmailRateLimitError("Gmail API quota exceeded")
                else:
                    logger.error(f"Failed to trash batch: {str(e)}")
                    raise GmailAPIError(f"Failed to trash messages: {str(e)}")

        return total_trashed

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def delete_messages(self, message_ids: List[str]) -> int:
        """
        Permanently delete messages (use with caution!).

        This is irreversible. Consider using trash_messages instead.

        Args:
            message_ids: List of message IDs to delete

        Returns:
            Count of successfully deleted messages

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Warning:
            This operation is IRREVERSIBLE. Deleted messages cannot be recovered.
        """
        if not message_ids:
            return 0

        service = await self.get_service()
        total_deleted = 0

        # Delete individually (no batch delete in Gmail API)
        for msg_id in message_ids:
            try:
                await asyncio.to_thread(
                    service.users().messages().delete(userId="me", id=msg_id).execute
                )
                total_deleted += 1

            except HttpError as e:
                if e.resp.status == 429:
                    raise GmailRateLimitError("Gmail API rate limit exceeded")
                elif e.resp.status == 403:
                    raise GmailRateLimitError("Gmail API quota exceeded")
                elif e.resp.status == 404:
                    logger.warning(f"Message not found: {msg_id}")
                else:
                    logger.error(f"Failed to delete {msg_id}: {str(e)}")

        logger.info(f"Permanently deleted {total_deleted} messages")
        return total_deleted

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an email message.

        Used primarily for mailto: unsubscribe requests.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Email body (plain text)
            from_email: Optional sender email (defaults to authenticated user)

        Returns:
            Sent message info including id and threadId

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> result = await client.send_message(
            ...     to="unsubscribe@example.com",
            ...     subject="unsubscribe",
            ...     body="Please unsubscribe me"
            ... )
        """
        service = await self.get_service()

        # Create message
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        if from_email:
            message["from"] = from_email

        # Encode message
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

        try:
            sent_message = await asyncio.to_thread(
                service.users()
                .messages()
                .send(userId="me", body={"raw": raw})
                .execute
            )
            logger.info(f"Sent message to {to}: {subject}")
            return sent_message

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                raise GmailRateLimitError("Gmail API quota exceeded")
            else:
                raise GmailAPIError(f"Failed to send message: {str(e)}")

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def create_filter(
        self,
        sender_email: str,
        actions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a Gmail filter for a sender.

        Args:
            sender_email: Email address to filter
            actions: Filter actions dict with keys:
                - skip_inbox (bool): Skip inbox (archive)
                - mark_as_read (bool): Mark as read
                - add_label_ids (List[str]): Labels to add
                - remove_label_ids (List[str]): Labels to remove

        Returns:
            Created filter info including filter ID

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> filter_info = await client.create_filter(
            ...     sender_email="spam@example.com",
            ...     actions={"skip_inbox": True, "mark_as_read": True}
            ... )
            >>> print(filter_info['id'])
            'ANe1BmjK...'
        """
        service = await self.get_service()

        # Build filter criteria
        criteria = {"from": sender_email}

        # Build filter action
        action = {}

        if actions.get("skip_inbox"):
            action["removeLabelIds"] = ["INBOX"]

        if actions.get("mark_as_read"):
            action["removeLabelIds"] = action.get("removeLabelIds", [])
            action["removeLabelIds"].append("UNREAD")

        if actions.get("add_label_ids"):
            action["addLabelIds"] = actions["add_label_ids"]

        if actions.get("remove_label_ids"):
            action["removeLabelIds"] = action.get("removeLabelIds", [])
            action["removeLabelIds"].extend(actions["remove_label_ids"])

        # Create filter
        filter_body = {
            "criteria": criteria,
            "action": action,
        }

        try:
            created_filter = await asyncio.to_thread(
                service.users()
                .settings()
                .filters()
                .create(userId="me", body=filter_body)
                .execute
            )
            logger.info(f"Created filter for {sender_email}")
            return created_filter

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                raise GmailRateLimitError("Gmail API quota exceeded")
            else:
                raise GmailAPIError(f"Failed to create filter: {str(e)}")

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def list_filters(self) -> List[Dict[str, Any]]:
        """
        List all existing Gmail filters.

        Returns:
            List of filter dictionaries with criteria and actions

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> filters = await client.list_filters()
            >>> for f in filters:
            ...     print(f['id'], f['criteria'])
        """
        service = await self.get_service()

        try:
            response = await asyncio.to_thread(
                service.users().settings().filters().list(userId="me").execute
            )
            return response.get("filter", [])

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                raise GmailRateLimitError("Gmail API quota exceeded")
            else:
                raise GmailAPIError(f"Failed to list filters: {str(e)}")

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def delete_filter(self, filter_id: str) -> bool:
        """
        Delete a Gmail filter by ID.

        Args:
            filter_id: Gmail filter ID to delete

        Returns:
            True if successful, False otherwise

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors
        """
        service = await self.get_service()

        try:
            await asyncio.to_thread(
                service.users()
                .settings()
                .filters()
                .delete(userId="me", id=filter_id)
                .execute
            )
            logger.info(f"Deleted filter: {filter_id}")
            return True

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                raise GmailRateLimitError("Gmail API quota exceeded")
            elif e.resp.status == 404:
                logger.warning(f"Filter not found: {filter_id}")
                return False
            else:
                raise GmailAPIError(f"Failed to delete filter: {str(e)}")

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def create_label(self, name: str) -> Dict[str, Any]:
        """
        Create a new Gmail label.

        Args:
            name: Label name

        Returns:
            Created label info including label ID

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors
        """
        service = await self.get_service()

        label_body = {
            "name": name,
            "messageListVisibility": "show",
            "labelListVisibility": "labelShow",
        }

        try:
            created_label = await asyncio.to_thread(
                service.users().labels().create(userId="me", body=label_body).execute
            )
            logger.info(f"Created label: {name}")
            return created_label

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                raise GmailRateLimitError("Gmail API quota exceeded")
            elif e.resp.status == 409:
                raise GmailAPIError(f"Label already exists: {name}")
            else:
                raise GmailAPIError(f"Failed to create label: {str(e)}")

    @retry(
        retry=retry_if_exception_type((GmailRateLimitError, GmailQuotaExceededError)),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        stop=stop_after_attempt(3),
        before_sleep=before_sleep_log(logger, logging.WARNING),
    )
    async def list_labels(self) -> List[Dict[str, Any]]:
        """
        List all Gmail labels.

        Returns:
            List of label dictionaries with id, name, type

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors
        """
        service = await self.get_service()

        try:
            response = await asyncio.to_thread(
                service.users().labels().list(userId="me").execute
            )
            return response.get("labels", [])

        except HttpError as e:
            if e.resp.status == 429:
                raise GmailRateLimitError("Gmail API rate limit exceeded")
            elif e.resp.status == 403:
                raise GmailRateLimitError("Gmail API quota exceeded")
            else:
                raise GmailAPIError(f"Failed to list labels: {str(e)}")

    async def get_or_create_label(self, name: str) -> str:
        """
        Get existing label ID or create if doesn't exist.

        Args:
            name: Label name

        Returns:
            Label ID

        Raises:
            GmailRateLimitError: If rate limit is exceeded
            GmailAPIError: For other API errors

        Example:
            >>> label_id = await client.get_or_create_label("Newsletters")
            >>> print(label_id)
            'Label_123'
        """
        # List existing labels
        labels = await self.list_labels()

        # Check if label exists
        for label in labels:
            if label["name"] == name:
                return label["id"]

        # Create label if it doesn't exist
        created_label = await self.create_label(name)
        return created_label["id"]

    # ========================================================================
    # Helper Methods
    # ========================================================================

    @staticmethod
    def parse_list_unsubscribe_header(headers: List[Dict[str, str]]) -> Dict[str, Optional[str]]:
        """
        Parse List-Unsubscribe header from message headers.

        Extracts mailto and URL unsubscribe methods from the header.

        Args:
            headers: List of header dictionaries with 'name' and 'value'

        Returns:
            Dictionary with 'mailto' and 'url' keys (None if not found)

        Example:
            >>> headers = [{"name": "List-Unsubscribe", "value": "<mailto:unsub@ex.com>, <http://ex.com/unsub>"}]
            >>> result = GmailClient.parse_list_unsubscribe_header(headers)
            >>> print(result)
            {'mailto': 'unsub@ex.com', 'url': 'http://ex.com/unsub'}
        """
        result = {"mailto": None, "url": None}

        # Find List-Unsubscribe header
        unsubscribe_header = None
        for header in headers:
            if header.get("name", "").lower() == "list-unsubscribe":
                unsubscribe_header = header.get("value", "")
                break

        if not unsubscribe_header:
            return result

        # Parse mailto
        mailto_match = re.search(r"<mailto:([^>]+)>", unsubscribe_header)
        if mailto_match:
            mailto_addr = mailto_match.group(1)
            # Handle query parameters
            if "?" in mailto_addr:
                mailto_addr = mailto_addr.split("?")[0]
            result["mailto"] = unquote(mailto_addr)

        # Parse URL
        url_match = re.search(r"<(https?://[^>]+)>", unsubscribe_header)
        if url_match:
            result["url"] = unquote(url_match.group(1))

        return result

    @staticmethod
    def get_sender_from_headers(headers: List[Dict[str, str]]) -> Dict[str, str]:
        """
        Extract sender email and display name from From header.

        Args:
            headers: List of header dictionaries with 'name' and 'value'

        Returns:
            Dictionary with 'email', 'display_name', and 'domain' keys

        Example:
            >>> headers = [{"name": "From", "value": "John Doe <john@example.com>"}]
            >>> result = GmailClient.get_sender_from_headers(headers)
            >>> print(result)
            {'email': 'john@example.com', 'display_name': 'John Doe', 'domain': 'example.com'}
        """
        result = {"email": "", "display_name": "", "domain": ""}

        # Find From header
        from_header = None
        for header in headers:
            if header.get("name", "").lower() == "from":
                from_header = header.get("value", "")
                break

        if not from_header:
            return result

        # Parse email and display name
        # Format: "Display Name <email@example.com>" or "email@example.com"
        email_match = re.search(r"<([^>]+)>", from_header)
        if email_match:
            email = email_match.group(1).strip().lower()
            # Extract display name (everything before <email>)
            display_name = from_header.split("<")[0].strip().strip('"')
        else:
            # No angle brackets, just email
            email = from_header.strip().lower()
            display_name = ""

        result["email"] = email
        result["display_name"] = display_name

        # Extract domain
        if "@" in email:
            result["domain"] = email.split("@")[1]

        return result

    @staticmethod
    def get_message_size(message: Dict[str, Any]) -> int:
        """
        Get estimated message size in bytes.

        Args:
            message: Message dictionary from Gmail API

        Returns:
            Message size in bytes (0 if not available)

        Example:
            >>> size = GmailClient.get_message_size(message)
            >>> print(f"{size / 1024:.2f} KB")
            15.23 KB
        """
        return message.get("sizeEstimate", 0)
