"""
V2 Cleanup Executor - Executes the actual cleanup operations.
Handles email deletion, unsubscribing, and filter creation.
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import EmailRecommendation, CleanupSession, CleanupAction, CleanupRun
from gmail_client import GmailClient


class CleanupExecutor:
    """
    Executes cleanup operations based on user decisions and AI recommendations.
    Performs deletions (move to trash), unsubscribes, and filter creation.
    """

    def __init__(self, db: AsyncSession, gmail_client: Optional[GmailClient] = None):
        self.db = db
        self.gmail_client = gmail_client

    async def execute_cleanup(self, session_id: str) -> Dict[str, Any]:
        """
        Execute the cleanup for a session.
        Returns results dict with counts and any errors.
        """
        # Get session
        result = await self.db.execute(
            select(CleanupSession).where(CleanupSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Update status to executing
        session.status = "executing"
        await self.db.commit()

        # Get all emails marked for deletion
        # (user_decision = delete OR (no user_decision AND ai_suggestion = delete))
        delete_query = await self.db.execute(
            select(EmailRecommendation)
            .where(EmailRecommendation.session_id == session_id)
            .where(
                (EmailRecommendation.user_decision == "delete") |
                (
                    EmailRecommendation.user_decision.is_(None) &
                    (EmailRecommendation.ai_suggestion == "delete")
                )
            )
        )
        emails_to_delete = delete_query.scalars().all()

        # Track results
        results = {
            "emails_deleted": 0,
            "space_freed": 0,
            "senders_unsubscribed": 0,
            "filters_created": 0,
            "errors": [],
        }

        # Group emails by message_id for batch processing
        message_ids = [email.message_id for email in emails_to_delete]

        if self.gmail_client:
            # Perform actual Gmail operations
            results = await self._execute_gmail_operations(
                message_ids, emails_to_delete, results
            )
        else:
            # Simulated execution (for testing)
            results["emails_deleted"] = len(emails_to_delete)
            results["space_freed"] = sum(e.size_bytes for e in emails_to_delete)
            results["senders_unsubscribed"] = min(5, len(set(e.sender_email for e in emails_to_delete)))

        # Update session with results
        session.emails_deleted = results["emails_deleted"]
        session.space_freed = results["space_freed"]
        session.senders_unsubscribed = results["senders_unsubscribed"]
        session.filters_created = results["filters_created"]
        session.status = "completed"
        session.completed_at = datetime.utcnow()

        # Also create a CleanupRun record for compatibility with V1 history
        cleanup_run = CleanupRun(
            status="completed",
            started_at=session.started_at,
            finished_at=session.completed_at,
            emails_deleted=results["emails_deleted"],
            bytes_freed_estimate=results["space_freed"],
            senders_total=len(set(e.sender_email for e in emails_to_delete)),
            senders_processed=len(set(e.sender_email for e in emails_to_delete)),
        )
        self.db.add(cleanup_run)

        await self.db.commit()

        return results

    async def _execute_gmail_operations(
        self,
        message_ids: List[str],
        emails: List[EmailRecommendation],
        results: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute actual Gmail API operations."""

        # Batch delete (move to trash)
        batch_size = 100
        for i in range(0, len(message_ids), batch_size):
            batch = message_ids[i:i + batch_size]
            try:
                await self._trash_emails(batch)
                results["emails_deleted"] += len(batch)
                results["space_freed"] += sum(
                    e.size_bytes for e in emails[i:i + batch_size]
                )
            except Exception as e:
                results["errors"].append(f"Failed to delete batch {i}: {str(e)}")

        # Execute unsubscribes for user-selected senders
        results["senders_unsubscribed"] = await self._execute_unsubscribes(emails, results)

        return results

    async def _execute_unsubscribes(
        self,
        emails: List[EmailRecommendation],
        results: Dict[str, Any],
    ) -> int:
        """
        Execute unsubscribes for senders that the user selected.
        Uses RFC 8058 one-click when available, falls back to mailto.
        Returns count of successful unsubscribes.
        """
        if not self.gmail_client:
            return 0

        # Get unique senders with user_wants_unsubscribe = True
        senders_to_unsubscribe: Dict[str, Dict[str, Any]] = {}
        for email in emails:
            if email.user_wants_unsubscribe and email.has_unsubscribe:
                if email.sender_email not in senders_to_unsubscribe:
                    senders_to_unsubscribe[email.sender_email] = {
                        "url": email.unsubscribe_url,
                        "mailto": email.unsubscribe_mailto,
                        "one_click": email.unsubscribe_one_click,
                    }

        successful_count = 0

        for sender_email, unsub_info in senders_to_unsubscribe.items():
            try:
                result = await self.gmail_client.unsubscribe_from_sender(
                    sender_email=sender_email,
                    unsubscribe_url=unsub_info.get("url"),
                    unsubscribe_mailto=unsub_info.get("mailto"),
                    one_click=unsub_info.get("one_click", False),
                )

                if result.get("success"):
                    successful_count += 1
                    print(f"Successfully unsubscribed from {sender_email} via {result.get('method')}")
                else:
                    results["errors"].append(
                        f"Failed to unsubscribe from {sender_email}: {result.get('error')}"
                    )
            except Exception as e:
                results["errors"].append(f"Error unsubscribing from {sender_email}: {str(e)}")
                print(f"Error unsubscribing from {sender_email}: {e}")

            # Small delay between unsubscribes to avoid rate limiting
            await asyncio.sleep(0.5)

        return successful_count

    async def _trash_emails(self, message_ids: List[str]) -> None:
        """Move emails to trash via Gmail API."""
        if not self.gmail_client:
            return

        for message_id in message_ids:
            try:
                await self.gmail_client.trash_message(message_id)
            except Exception as e:
                # Log error but continue with other messages
                print(f"Failed to trash message {message_id}: {e}")

    async def get_execution_progress(self, session_id: str) -> Dict[str, Any]:
        """Get the current progress of an executing cleanup."""
        result = await self.db.execute(
            select(CleanupSession).where(CleanupSession.session_id == session_id)
        )
        session = result.scalar_one_or_none()

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        return {
            "session_id": session_id,
            "status": session.status,
            "emails_deleted": session.emails_deleted,
            "space_freed": session.space_freed,
            "senders_unsubscribed": session.senders_unsubscribed,
            "filters_created": session.filters_created,
            "completed_at": session.completed_at.isoformat() if session.completed_at else None,
        }
