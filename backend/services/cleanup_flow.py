"""
V2 Cleanup Flow Service - Manages cleanup wizard sessions.
Coordinates scanning, recommendations, review, and execution steps.
"""

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import CleanupSession, EmailRecommendation, WhitelistDomain
from schemas import (
    CleanupProgressResponse,
    CleanupDiscoveries,
    RecommendationSummary,
    SenderRecommendation,
    ReviewQueueResponse,
    ReviewItem,
    ConfirmationSummary,
    SafetyInfo,
    CleanupResults,
)


class CleanupFlowService:
    """
    Manages the V2 cleanup wizard flow.
    Handles session creation, progress tracking, and state transitions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(self, max_emails: int = 10000) -> str:
        """Create a new cleanup session and return session_id."""
        session_id = str(uuid.uuid4())

        session = CleanupSession(
            session_id=session_id,
            status="scanning",
            total_emails=max_emails,
            scanned_emails=0,
            discoveries="{}",
            started_at=datetime.utcnow(),
        )

        self.db.add(session)
        await self.db.commit()

        return session_id

    async def get_session(self, session_id: str) -> Optional[CleanupSession]:
        """Get a cleanup session by ID."""
        result = await self.db.execute(
            select(CleanupSession).where(CleanupSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_progress(self, session_id: str) -> CleanupProgressResponse:
        """Get the current progress of a cleanup session."""
        session = await self.get_session(session_id)

        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Parse discoveries JSON
        discoveries_dict = json.loads(session.discoveries) if session.discoveries else {}
        discoveries = CleanupDiscoveries(
            promotions=discoveries_dict.get("promotions", 0),
            newsletters=discoveries_dict.get("newsletters", 0),
            social=discoveries_dict.get("social", 0),
            updates=discoveries_dict.get("updates", 0),
            low_value=discoveries_dict.get("low_value", 0),
        )

        # Calculate progress
        progress = 0.0
        if session.total_emails > 0:
            progress = min(1.0, session.scanned_emails / session.total_emails)

        return CleanupProgressResponse(
            session_id=session_id,
            status=session.status,
            progress=progress,
            total_emails=session.total_emails,
            scanned_emails=session.scanned_emails,
            discoveries=discoveries,
            error=session.error_message,
        )

    async def update_progress(
        self,
        session_id: str,
        scanned_emails: int,
        discoveries: Dict[str, int],
        status: Optional[str] = None,
    ) -> None:
        """Update scanning progress for a session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.scanned_emails = scanned_emails
        session.discoveries = json.dumps(discoveries)

        if status:
            session.status = status

        await self.db.commit()

    async def get_recommendations(self, session_id: str) -> RecommendationSummary:
        """Get recommendation summary for the Inbox Report screen."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Get recommendation counts by category
        category_query = await self.db.execute(
            select(
                EmailRecommendation.category,
                func.count(EmailRecommendation.id).label("count")
            )
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.ai_suggestion == "delete")
            .group_by(EmailRecommendation.category)
        )
        category_breakdown = {row.category: row.count for row in category_query.all()}

        # Get total protected count
        protected_query = await self.db.execute(
            select(func.count(EmailRecommendation.id))
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.ai_suggestion == "keep")
        )
        total_protected = protected_query.scalar() or 0

        # Get total to cleanup
        cleanup_query = await self.db.execute(
            select(func.count(EmailRecommendation.id))
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.ai_suggestion == "delete")
        )
        total_to_cleanup = cleanup_query.scalar() or 0

        # Get space savings
        space_query = await self.db.execute(
            select(func.sum(EmailRecommendation.size_bytes))
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.ai_suggestion == "delete")
        )
        space_savings = space_query.scalar() or 0

        # Get top delete senders
        top_delete_query = await self.db.execute(
            select(
                EmailRecommendation.sender_email,
                EmailRecommendation.sender_name,
                func.count(EmailRecommendation.id).label("count")
            )
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.ai_suggestion == "delete")
            .group_by(EmailRecommendation.sender_email, EmailRecommendation.sender_name)
            .order_by(func.count(EmailRecommendation.id).desc())
            .limit(5)
        )
        top_delete_senders = [
            SenderRecommendation(
                email=row.sender_email,
                display_name=row.sender_name,
                count=row.count,
                reason="You rarely open emails from this sender"
            )
            for row in top_delete_query.all()
        ]

        # Get top keep senders
        top_keep_query = await self.db.execute(
            select(
                EmailRecommendation.sender_email,
                EmailRecommendation.sender_name,
                func.count(EmailRecommendation.id).label("count")
            )
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.ai_suggestion == "keep")
            .group_by(EmailRecommendation.sender_email, EmailRecommendation.sender_name)
            .order_by(func.count(EmailRecommendation.id).desc())
            .limit(5)
        )
        top_keep_senders = [
            SenderRecommendation(
                email=row.sender_email,
                display_name=row.sender_name,
                count=row.count,
                reason="Important sender"
            )
            for row in top_keep_query.all()
        ]

        # Protected reasons
        protected_reasons = [
            f"{total_protected} emails from important senders",
            "Emails you've replied to",
            "Emails from your contacts",
            "Financial and security emails",
        ]

        return RecommendationSummary(
            session_id=session_id,
            total_to_cleanup=total_to_cleanup,
            total_protected=total_protected,
            space_savings=space_savings,
            category_breakdown=category_breakdown,
            protected_reasons=protected_reasons,
            top_delete_senders=top_delete_senders,
            top_keep_senders=top_keep_senders,
        )

    async def set_mode(self, session_id: str, mode: str) -> None:
        """Set the cleanup mode (quick/full) for a session."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.mode = mode
        session.status = "reviewing"
        await self.db.commit()

    async def get_review_queue(self, session_id: str, mode: str) -> ReviewQueueResponse:
        """Get the review queue based on mode."""
        # For quick mode: only uncertain emails (confidence < 0.7)
        # For full mode: all emails marked for deletion

        query = select(EmailRecommendation).where(
            EmailRecommendation.session_id == session_id
        )

        if mode == "quick":
            # Only show uncertain items (low confidence)
            query = query.where(EmailRecommendation.confidence < 0.7)
            query = query.where(EmailRecommendation.ai_suggestion == "delete")
        else:
            # Show all delete suggestions
            query = query.where(EmailRecommendation.ai_suggestion == "delete")

        # Only show items without user decision
        query = query.where(EmailRecommendation.user_decision.is_(None))
        query = query.order_by(EmailRecommendation.confidence.asc())
        query = query.limit(100)  # Cap at 100 for performance

        result = await self.db.execute(query)
        recommendations = result.scalars().all()

        items = [
            ReviewItem(
                message_id=rec.message_id,
                sender_email=rec.sender_email,
                sender_name=rec.sender_name,
                subject=rec.subject,
                date=rec.received_date,
                snippet=rec.snippet,
                ai_suggestion=rec.ai_suggestion,
                reasoning=rec.reasoning,
                confidence=rec.confidence,
                category=rec.category,
            )
            for rec in recommendations
        ]

        return ReviewQueueResponse(
            session_id=session_id,
            mode=mode,
            total_items=len(items),
            items=items,
        )

    async def record_decision(
        self, session_id: str, message_id: str, decision: str
    ) -> int:
        """Record a user's review decision for an email."""
        result = await self.db.execute(
            select(EmailRecommendation)
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.message_id == message_id)
        )
        recommendation = result.scalar_one_or_none()

        if not recommendation:
            raise ValueError(f"Recommendation not found: {message_id}")

        recommendation.user_decision = decision
        await self.db.commit()

        # Get remaining items in queue
        remaining_query = await self.db.execute(
            select(func.count(EmailRecommendation.id))
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.user_decision.is_(None))
            .where(EmailRecommendation.ai_suggestion == "delete")
        )
        remaining = remaining_query.scalar() or 0

        return remaining

    async def skip_all_remaining(self, session_id: str) -> None:
        """Trust AI for all remaining unreviewed items."""
        # Update all items without user decision to use AI suggestion
        result = await self.db.execute(
            select(EmailRecommendation)
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.user_decision.is_(None))
        )
        recommendations = result.scalars().all()

        for rec in recommendations:
            rec.user_decision = rec.ai_suggestion

        await self.db.commit()

    async def get_confirmation_summary(self, session_id: str) -> ConfirmationSummary:
        """Get the confirmation summary before execution."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Count emails to delete (user_decision = delete OR (no user_decision AND ai_suggestion = delete))
        delete_query = await self.db.execute(
            select(func.count(EmailRecommendation.id))
            .where(EmailRecommendation.session_id == session_id)
            .where(
                (EmailRecommendation.user_decision == "delete") |
                (
                    EmailRecommendation.user_decision.is_(None) &
                    (EmailRecommendation.ai_suggestion == "delete")
                )
            )
        )
        emails_to_delete = delete_query.scalar() or 0

        # Count protected
        protected_query = await self.db.execute(
            select(func.count(EmailRecommendation.id))
            .where(EmailRecommendation.session_id == session_id)
            .where(
                (EmailRecommendation.user_decision == "keep") |
                (EmailRecommendation.ai_suggestion == "keep")
            )
        )
        protected_count = protected_query.scalar() or 0

        # Space to be freed
        space_query = await self.db.execute(
            select(func.sum(EmailRecommendation.size_bytes))
            .where(EmailRecommendation.session_id == session_id)
            .where(
                (EmailRecommendation.user_decision == "delete") |
                (
                    EmailRecommendation.user_decision.is_(None) &
                    (EmailRecommendation.ai_suggestion == "delete")
                )
            )
        )
        space_to_be_freed = space_query.scalar() or 0

        # Count unique senders the user wants to unsubscribe from
        unsubscribe_query = await self.db.execute(
            select(func.count(func.distinct(EmailRecommendation.sender_email)))
            .where(EmailRecommendation.session_id == session_id)
            .where(EmailRecommendation.user_wants_unsubscribe == True)
        )
        senders_to_unsubscribe = unsubscribe_query.scalar() or 0

        safety_info = SafetyInfo(
            trash_recovery_days=30,
            auto_protected_categories=[
                "Emails from your contacts",
                "Emails you've replied to",
                "Financial institutions",
                "Security and verification emails",
            ]
        )

        # Update session status
        session.status = "confirming"
        await self.db.commit()

        return ConfirmationSummary(
            session_id=session_id,
            emails_to_delete=emails_to_delete,
            senders_to_unsubscribe=senders_to_unsubscribe,
            space_to_be_freed=space_to_be_freed,
            protected_count=protected_count,
            safety_info=safety_info,
        )

    async def get_results(self, session_id: str) -> CleanupResults:
        """Get the results of a completed cleanup."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        return CleanupResults(
            session_id=session_id,
            status=session.status,
            emails_deleted=session.emails_deleted,
            space_freed=session.space_freed,
            senders_unsubscribed=session.senders_unsubscribed,
            filters_created=session.filters_created,
            errors=[],
            completed_at=session.completed_at,
        )

    async def update_results(
        self,
        session_id: str,
        emails_deleted: int,
        space_freed: int,
        senders_unsubscribed: int,
        filters_created: int,
        status: str = "completed",
    ) -> None:
        """Update session with final results."""
        session = await self.get_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        session.emails_deleted = emails_deleted
        session.space_freed = space_freed
        session.senders_unsubscribed = senders_unsubscribed
        session.filters_created = filters_created
        session.status = status
        session.completed_at = datetime.utcnow()

        await self.db.commit()

    async def set_error(self, session_id: str, error_message: str) -> None:
        """Set error status for a session."""
        session = await self.get_session(session_id)
        if not session:
            return

        session.status = "failed"
        session.error_message = error_message
        await self.db.commit()
