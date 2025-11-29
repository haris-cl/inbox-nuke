"""
Agent runner orchestrator for Inbox Nuke cleanup workflow.

This module coordinates the entire cleanup process, including:
- Sender discovery
- Safety checks
- Unsubscribe attempts
- Filter creation
- Email deletion
- Progress tracking and resumability
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from gmail_client import GmailClient
from models import CleanupAction, CleanupRun, Sender
from agent.safety import check_sender_safety, SafetyCheck
from agent.discovery import discover_senders as discovery_discover_senders
from agent.unsubscribe import unsubscribe as agent_unsubscribe
from agent.filters import create_mute_filter as agent_create_mute_filter
from agent.cleanup import delete_emails_from_sender as agent_delete_emails
from agent.retention import RetentionEngine, Action

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class ActionResult:
    """Result of processing a single sender."""
    action_type: str  # unsubscribe, delete, filter, skip, error
    sender_email: str
    success: bool
    emails_deleted: int = 0
    bytes_freed: int = 0
    notes: str = ""


# ============================================================================
# Cleanup Agent
# ============================================================================


class CleanupAgent:
    """
    Main orchestrator for email cleanup workflow.

    Coordinates sender discovery, safety checks, unsubscribe attempts,
    filter creation, and email deletion. Supports pause/resume functionality
    and comprehensive progress tracking.

    Attributes:
        db: AsyncSession for database operations
        run_id: ID of the current cleanup run
        gmail_client: GmailClient for Gmail API operations
        run: Current CleanupRun instance
    """

    def __init__(self, db: AsyncSession, run_id: int):
        """
        Initialize the cleanup agent.

        Args:
            db: Async database session
            run_id: ID of the cleanup run to execute
        """
        self.db = db
        self.run_id = run_id
        self.gmail_client: Optional[GmailClient] = None
        self.run: Optional[CleanupRun] = None
        self._should_stop = False
        self.retention_engine = RetentionEngine()  # Initialize retention engine

    async def initialize(self) -> None:
        """
        Initialize the agent by loading the run and setting up Gmail client.

        Raises:
            ValueError: If run not found
        """
        # Load the run
        stmt = select(CleanupRun).where(CleanupRun.id == self.run_id)
        result = await self.db.execute(stmt)
        self.run = result.scalar_one_or_none()

        if not self.run:
            raise ValueError(f"Cleanup run with ID {self.run_id} not found")

        # Initialize Gmail client
        self.gmail_client = GmailClient(db=self.db)

        logger.info(f"Initialized CleanupAgent for run {self.run_id}")

    async def run_cleanup(self) -> CleanupRun:
        """
        Execute the main cleanup workflow.

        Workflow:
        1. Update run status to "running"
        2. Discover senders (if not already discovered)
        3. Process each sender:
           a. Check safety
           b. Attempt unsubscribe (if safe)
           c. Create mute filter
           d. Delete old emails
           e. Log action
        4. Mark run as completed

        Returns:
            Updated CleanupRun instance

        Raises:
            ValueError: If agent not initialized
            Exception: Various exceptions during cleanup (logged and stored)
        """
        if not self.run or not self.gmail_client:
            raise ValueError("Agent not initialized. Call initialize() first.")

        try:
            # Update status to running
            self.run.status = "running"
            await self._update_progress()
            logger.info(f"Starting cleanup run {self.run_id}")

            # Step 1: Discover senders if not already done
            if self.run.senders_total == 0:
                await self._discover_senders()

            # Step 2: Load senders to process
            senders = await self._load_senders()

            # Load progress cursor to determine where to start
            start_index = 0
            if self.run.progress_cursor:
                try:
                    cursor_data = json.loads(self.run.progress_cursor)
                    start_index = cursor_data.get("current_index", 0)
                    logger.info(f"Resuming from sender index {start_index}")
                except Exception as e:
                    logger.warning(f"Failed to parse progress cursor: {e}. Starting from beginning.")

            # Step 3: Process each sender
            for index, sender in enumerate(senders[start_index:], start=start_index):
                # Check if we should stop (paused or cancelled)
                if self._should_stop or await self._check_should_stop():
                    logger.info(f"Cleanup stopped at sender {index}/{len(senders)}")
                    break

                try:
                    # Process the sender
                    result = await self._process_sender(sender)

                    # Log the action
                    await self._log_action(result)

                    # Update progress
                    self.run.senders_processed = index + 1
                    self.run.emails_deleted += result.emails_deleted
                    self.run.bytes_freed_estimate += result.bytes_freed

                    # Store progress cursor
                    self.run.progress_cursor = json.dumps({
                        "current_index": index + 1,
                        "last_sender": sender.email,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    # Commit progress periodically (every 10 senders)
                    if (index + 1) % 10 == 0:
                        await self._update_progress()
                        logger.info(
                            f"Progress: {self.run.senders_processed}/{self.run.senders_total} "
                            f"({self.run.senders_processed / self.run.senders_total * 100:.1f}%)"
                        )

                except Exception as e:
                    logger.error(f"Error processing sender {sender.email}: {e}", exc_info=True)
                    # Log error action
                    error_result = ActionResult(
                        action_type="error",
                        sender_email=sender.email,
                        success=False,
                        notes=f"Error: {str(e)}"
                    )
                    await self._log_action(error_result)
                    # Continue with next sender
                    continue

            # Step 4: Finalize run
            if not self._should_stop and self.run.status == "running":
                self.run.status = "completed"
                self.run.finished_at = datetime.utcnow()
                logger.info(
                    f"Cleanup run {self.run_id} completed. "
                    f"Processed {self.run.senders_processed}/{self.run.senders_total} senders, "
                    f"deleted {self.run.emails_deleted} emails, "
                    f"freed {self.run.bytes_freed_estimate / (1024*1024):.2f} MB"
                )

            await self._update_progress()
            return self.run

        except Exception as e:
            logger.error(f"Fatal error in cleanup run {self.run_id}: {e}", exc_info=True)
            self.run.status = "failed"
            self.run.error_message = str(e)
            self.run.finished_at = datetime.utcnow()
            await self._update_progress()
            raise

    async def pause(self) -> None:
        """
        Pause the cleanup run.

        Sets the internal stop flag and updates run status to "paused".
        The agent will complete the current sender and then stop.
        """
        logger.info(f"Pausing cleanup run {self.run_id}")
        self._should_stop = True

        if self.run:
            self.run.status = "paused"
            await self._update_progress()

    async def resume(self) -> CleanupRun:
        """
        Resume a paused cleanup run.

        Resets the stop flag and continues from the stored progress cursor.

        Returns:
            Updated CleanupRun instance
        """
        if not self.run:
            raise ValueError("Agent not initialized. Call initialize() first.")

        if self.run.status != "paused":
            raise ValueError(f"Cannot resume run with status '{self.run.status}'. Only paused runs can be resumed.")

        logger.info(f"Resuming cleanup run {self.run_id}")
        self._should_stop = False
        return await self.run_cleanup()

    async def cancel(self) -> None:
        """
        Cancel the cleanup run.

        Sets the stop flag and marks the run as "cancelled".
        """
        logger.info(f"Cancelling cleanup run {self.run_id}")
        self._should_stop = True

        if self.run:
            self.run.status = "cancelled"
            self.run.finished_at = datetime.utcnow()
            await self._update_progress()

    # ========================================================================
    # Internal Methods
    # ========================================================================

    async def _discover_senders(self) -> None:
        """
        Discover unique senders in the mailbox.

        Uses the discovery module to:
        1. Fetch all messages from Gmail
        2. Extract unique senders
        3. Parse unsubscribe headers
        4. Store sender information in database
        """
        logger.info("Discovering senders...")

        # Use the discovery module to find senders
        try:
            # Define progress callback to update run
            def progress_callback(current: int, total: int, message: str):
                logger.debug(f"Discovery progress: {current}/{total} - {message}")

            senders_count = await discovery_discover_senders(
                gmail_client=self.gmail_client,
                db=self.db,
                progress_callback=progress_callback,
                max_messages=10000
            )

            self.run.senders_total = senders_count
            await self._update_progress()

            logger.info(f"Discovered {self.run.senders_total} senders")

        except Exception as e:
            logger.error(f"Error during sender discovery: {e}")
            # Fall back to counting existing senders
            stmt = select(Sender)
            result = await self.db.execute(stmt)
            senders = result.scalars().all()
            self.run.senders_total = len(senders)
            await self._update_progress()
            logger.info(f"Using {self.run.senders_total} existing senders")

    async def _load_senders(self) -> List[Sender]:
        """
        Load all senders to process.

        Prioritizes senders by:
        1. High message count (more impact)
        2. Has unsubscribe header (easy to handle)
        3. Junk sender patterns (should be cleaned)

        Returns:
            List of Sender instances ordered by priority
        """
        from agent.safety import is_junk_sender

        stmt = select(Sender)
        result = await self.db.execute(stmt)
        senders = list(result.scalars().all())

        # Sort senders by priority:
        # 1. Junk senders with high message count (most impact)
        # 2. Senders with unsubscribe headers (easy to handle)
        # 3. High message count (general cleanup)
        def sender_priority(sender: Sender) -> tuple:
            is_junk = is_junk_sender(sender.email)
            has_unsub = sender.has_list_unsubscribe
            msg_count = sender.message_count

            # Return tuple for sorting (higher priority first)
            # Negate values so larger numbers come first
            return (
                -1 if is_junk else 0,           # Junk senders first
                -1 if has_unsub else 0,         # Unsubscribable second
                -msg_count,                      # High message count third
            )

        senders.sort(key=sender_priority)
        return senders

    async def _check_should_stop(self) -> bool:
        """
        Check if the run should stop (paused or cancelled).

        Refreshes the run from database to check for external status changes.

        Returns:
            True if run should stop, False otherwise
        """
        # Refresh run from database to check for external changes
        await self.db.refresh(self.run)

        if self.run.status in ["paused", "cancelled"]:
            logger.info(f"Run status changed to {self.run.status}, stopping")
            return True

        return False

    async def _process_sender(self, sender: Sender) -> ActionResult:
        """
        Process a single sender.

        Workflow:
        1. Run safety check
        2. Apply retention rules to determine action
        3. If safe to process:
           a. Attempt unsubscribe
           b. Create mute filter
           c. Delete old emails (respecting retention rules)
        4. Return result

        Args:
            sender: Sender instance to process

        Returns:
            ActionResult with processing outcome
        """
        logger.debug(f"Processing sender: {sender.email}")

        # Step 1: Safety check (highest priority)
        safety_result = await check_sender_safety(sender.email, self.db)

        if not safety_result.is_safe:
            logger.info(f"Skipping protected sender {sender.email}: {safety_result.reason}")
            return ActionResult(
                action_type="skip",
                sender_email=sender.email,
                success=True,
                notes=f"Protected: {safety_result.reason}"
            )

        # Step 2: Check retention rules for this sender
        # Build email data for retention evaluation
        email_data = {
            "sender_email": sender.email,
            "sender_domain": sender.domain,
            "subject": "",  # We'll check individual emails later
            "labels": [],
            "has_attachment": False,
            "is_conversation": False,
            "category": "",
            "date": datetime.utcnow(),
        }

        # Evaluate sender-level rules (domain, sender email)
        retention_result = self.retention_engine.evaluate(email_data)

        # If retention rules say KEEP at sender level, skip processing
        if retention_result.action == Action.KEEP:
            logger.info(
                f"Skipping sender {sender.email} due to retention rule: {retention_result.matching_rule}"
            )
            return ActionResult(
                action_type="skip",
                sender_email=sender.email,
                success=True,
                notes=f"Retention rule: {retention_result.matching_rule}"
            )

        # Step 3: Attempt unsubscribe
        unsubscribe_success = False
        if sender.has_list_unsubscribe and not sender.unsubscribed:
            try:
                unsubscribe_success = await self._attempt_unsubscribe(sender)
                if unsubscribe_success:
                    sender.unsubscribed = True
                    sender.unsubscribed_at = datetime.utcnow()
            except Exception as e:
                logger.warning(f"Unsubscribe failed for {sender.email}: {e}")

        # Step 4: Create mute filter
        filter_success = False
        if not sender.filter_created:
            try:
                filter_success = await self._create_mute_filter(sender)
                if filter_success:
                    sender.filter_created = True
            except Exception as e:
                logger.warning(f"Filter creation failed for {sender.email}: {e}")

        # Step 5: Delete old emails (with conversation protection)
        emails_deleted = 0
        bytes_freed = 0
        try:
            emails_deleted, bytes_freed = await self._delete_emails_from_sender_with_retention(sender)
        except Exception as e:
            logger.error(f"Email deletion failed for {sender.email}: {e}")

        # Commit sender updates
        await self.db.commit()

        # Build result
        notes_parts = []
        if unsubscribe_success:
            notes_parts.append("unsubscribed")
        if filter_success:
            notes_parts.append("filter created")
        notes_parts.append(f"{emails_deleted} emails deleted")

        return ActionResult(
            action_type="delete",
            sender_email=sender.email,
            success=True,
            emails_deleted=emails_deleted,
            bytes_freed=bytes_freed,
            notes=", ".join(notes_parts)
        )

    async def _attempt_unsubscribe(self, sender: Sender) -> bool:
        """
        Attempt to unsubscribe from sender.

        Uses the unsubscribe module to send unsubscribe requests via
        mailto or HTTP methods.

        Args:
            sender: Sender instance

        Returns:
            True if unsubscribe successful, False otherwise
        """
        logger.debug(f"Attempting unsubscribe from {sender.email}")

        try:
            result = await agent_unsubscribe(
                gmail_client=self.gmail_client,
                sender=sender,
                db=self.db
            )
            return result.success
        except Exception as e:
            logger.error(f"Unsubscribe error for {sender.email}: {e}")
            return False

    async def _create_mute_filter(self, sender: Sender) -> bool:
        """
        Create a Gmail filter to mute future emails from sender.

        Uses the filters module to create a mute filter with labels.

        Args:
            sender: Sender instance

        Returns:
            True if filter created successfully, False otherwise
        """
        logger.debug(f"Creating mute filter for {sender.email}")

        try:
            # Use the filters module to create a comprehensive mute filter
            filter_id = await agent_create_mute_filter(
                gmail_client=self.gmail_client,
                sender=sender,
                db=self.db
            )

            # filter_id will be None if it already existed (but still marked as created)
            # or a string if newly created
            return True

        except Exception as e:
            logger.error(f"Failed to create filter for {sender.email}: {e}")
            return False

    async def _delete_emails_from_sender(self, sender: Sender) -> tuple[int, int]:
        """
        Delete all emails from the sender.

        Uses the cleanup module to delete emails with age filtering.
        More aggressive deletion for obvious junk senders.

        Args:
            sender: Sender instance

        Returns:
            Tuple of (emails_deleted, bytes_freed)
        """
        logger.debug(f"Deleting emails from {sender.email}")

        try:
            # Import junk detection functions
            from agent.safety import is_junk_sender

            # Determine age threshold based on sender type
            # More aggressive (7 days) for obvious junk senders
            # Standard (30 days) for regular promotional senders
            if is_junk_sender(sender.email) or sender.has_list_unsubscribe:
                older_than_days = 7
            else:
                older_than_days = 30

            logger.debug(f"Using {older_than_days} day threshold for {sender.email}")

            # Use the cleanup module to delete emails
            result = await agent_delete_emails(
                gmail_client=self.gmail_client,
                sender=sender,
                older_than_days=older_than_days,
                db=self.db
            )

            if result.errors:
                logger.warning(f"Errors during deletion for {sender.email}: {result.errors}")

            logger.info(
                f"Deleted {result.emails_deleted} emails from {sender.email} "
                f"({result.bytes_freed / (1024*1024):.2f} MB)"
            )

            return result.emails_deleted, result.bytes_freed

        except Exception as e:
            logger.error(f"Failed to delete emails from {sender.email}: {e}")
            return 0, 0

    async def _delete_emails_from_sender_with_retention(self, sender: Sender) -> tuple[int, int]:
        """
        Delete emails from sender with retention rule checking.

        This method checks each email individually against retention rules,
        including conversation thread detection. Emails that match KEEP rules
        are preserved.

        Args:
            sender: Sender instance

        Returns:
            Tuple of (emails_deleted, bytes_freed)
        """
        logger.debug(f"Deleting emails from {sender.email} with retention checks")

        try:
            from agent.safety import is_junk_sender

            # Determine age threshold
            if is_junk_sender(sender.email) or sender.has_list_unsubscribe:
                older_than_days = 7
            else:
                older_than_days = 30

            # Get emails from this sender with thread info
            query = f"from:{sender.email}"
            emails = await self.gmail_client.get_emails_with_thread_info(
                query=query,
                max_results=500,  # Process in batches
            )

            # Filter emails by age and retention rules
            emails_to_delete = []
            total_bytes = 0
            kept_count = 0

            cutoff_date = datetime.utcnow() - timedelta(days=older_than_days)

            for email_msg in emails:
                try:
                    # Get full message details
                    message = await self.gmail_client.get_message(
                        email_msg["id"],
                        format="metadata"
                    )

                    # Check if it's a conversation (HIGHEST PRIORITY)
                    is_conversation = email_msg.get("is_conversation", False)
                    if is_conversation:
                        logger.debug(f"Keeping conversation email {email_msg['id']}")
                        kept_count += 1
                        continue

                    # Extract headers for retention evaluation
                    headers = message.get("payload", {}).get("headers", [])
                    subject = ""
                    date_str = ""
                    for header in headers:
                        if header.get("name", "").lower() == "subject":
                            subject = header.get("value", "")
                        elif header.get("name", "").lower() == "date":
                            date_str = header.get("value", "")

                    # Build email data for retention evaluation
                    email_data = {
                        "sender_email": sender.email,
                        "sender_domain": sender.domain,
                        "subject": subject,
                        "labels": message.get("labelIds", []),
                        "has_attachment": len(message.get("payload", {}).get("parts", [])) > 1,
                        "is_conversation": is_conversation,
                        "category": "",  # TODO: Extract from labels
                        "date": cutoff_date,  # For older_than_days rules
                    }

                    # Evaluate retention rules
                    retention_result = self.retention_engine.evaluate(email_data)

                    # Keep emails that match KEEP rules
                    if retention_result.action == Action.KEEP:
                        logger.debug(
                            f"Keeping email {email_msg['id']} due to rule: {retention_result.matching_rule}"
                        )
                        kept_count += 1
                        continue

                    # Add to delete list if passes all checks
                    emails_to_delete.append(email_msg["id"])
                    total_bytes += self.gmail_client.get_message_size(message)

                except Exception as e:
                    logger.warning(f"Error evaluating email {email_msg.get('id')}: {e}")
                    # When in doubt, keep the email (safe side)
                    kept_count += 1
                    continue

            # Delete the filtered emails
            if emails_to_delete:
                deleted_count = await self.gmail_client.trash_messages(emails_to_delete)
                logger.info(
                    f"Deleted {deleted_count}/{len(emails)} emails from {sender.email} "
                    f"({total_bytes / (1024*1024):.2f} MB freed, {kept_count} kept by retention rules)"
                )
                return deleted_count, total_bytes
            else:
                logger.info(f"No emails to delete from {sender.email} (all protected by retention rules)")
                return 0, 0

        except Exception as e:
            logger.error(f"Failed to delete emails from {sender.email} with retention: {e}")
            return 0, 0

    async def _log_action(self, result: ActionResult) -> None:
        """
        Log a cleanup action to the database.

        Args:
            result: ActionResult to log
        """
        action = CleanupAction(
            run_id=self.run_id,
            timestamp=datetime.utcnow(),
            action_type=result.action_type,
            sender_email=result.sender_email,
            email_count=result.emails_deleted,
            bytes_freed=result.bytes_freed,
            notes=result.notes
        )

        self.db.add(action)
        await self.db.commit()

    async def _update_progress(self) -> None:
        """
        Update run progress in database.

        Commits all pending changes to the run.
        """
        await self.db.commit()
        await self.db.refresh(self.run)
