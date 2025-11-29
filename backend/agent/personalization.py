"""
Personalization engine that learns from user feedback.
Adjusts email scoring based on user-specific preferences.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models import UserFeedback, UserPreference, EmailScore

logger = logging.getLogger(__name__)


class PersonalizationEngine:
    """
    Learns user preferences from feedback and applies them to scoring.

    Learning strategies:
    1. Sender-level: User marks emails from sender@example.com as KEEP/DELETE
    2. Domain-level: Learns from patterns across senders (e.g., all @newsletter.* = DELETE)
    3. Keyword-level: Learns from subject patterns (e.g., "deal" in subject = DELETE)
    """

    # Minimum feedback count before applying learned preference
    MIN_FEEDBACK_THRESHOLD = 2

    # Confidence decay factor (older feedback less important)
    DECAY_FACTOR = 0.95

    async def record_feedback(
        self,
        db: AsyncSession,
        feedback_type: str,  # "email" or "sender"
        target_id: str,
        original_classification: str,
        corrected_classification: str,
        reason: Optional[str] = None
    ) -> UserFeedback:
        """
        Record user feedback on a classification.
        Also updates learned preferences.
        """
        try:
            # Create feedback record
            feedback = UserFeedback(
                feedback_type=feedback_type,
                target_id=target_id,
                original_classification=original_classification,
                corrected_classification=corrected_classification,
                reason=reason,
                created_at=datetime.utcnow()
            )
            db.add(feedback)

            # Update learned preferences
            await self._update_preferences(db, feedback_type, target_id, corrected_classification)

            await db.commit()
            await db.refresh(feedback)

            logger.info(f"Recorded feedback: {target_id} -> {corrected_classification}")
            return feedback
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            await db.rollback()
            raise

    async def _update_preferences(
        self,
        db: AsyncSession,
        feedback_type: str,
        target_id: str,
        classification: str
    ):
        """Update user preferences based on feedback."""

        try:
            # Determine preference type and pattern
            if feedback_type == "sender":
                pref_type = "sender"
                pattern = target_id.lower()
            elif feedback_type == "email":
                # For email feedback, extract sender from EmailScore
                stmt = select(EmailScore).where(EmailScore.message_id == target_id)
                result = await db.execute(stmt)
                email = result.scalar_one_or_none()
                if email:
                    pref_type = "sender"
                    pattern = email.sender_email.lower()
                else:
                    logger.warning(f"Email not found for feedback: {target_id}")
                    return
            else:
                logger.warning(f"Unknown feedback type: {feedback_type}")
                return

            # Check if preference exists
            stmt = select(UserPreference).where(
                UserPreference.pref_type == pref_type,
                UserPreference.pattern == pattern
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing preference
                if existing.classification == classification:
                    # Same classification - increase confidence
                    existing.confidence = min(1.0, existing.confidence + 0.1)
                    existing.feedback_count += 1
                else:
                    # Different classification - adjust based on counts
                    if existing.feedback_count <= 2:
                        # Flip classification if few previous feedbacks
                        existing.classification = classification
                        existing.confidence = 0.6
                        existing.feedback_count = 1
                    else:
                        # Decrease confidence for established preference
                        existing.confidence = max(0.3, existing.confidence - 0.2)
                existing.last_feedback = datetime.utcnow()
                existing.updated_at = datetime.utcnow()
            else:
                # Create new preference
                new_pref = UserPreference(
                    pref_type=pref_type,
                    pattern=pattern,
                    classification=classification,
                    confidence=0.7,  # Start with moderate confidence
                    feedback_count=1,
                    last_feedback=datetime.utcnow()
                )
                db.add(new_pref)

            logger.info(f"Updated preference: {pref_type}:{pattern} -> {classification}")
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            # Don't raise - we still want to save the feedback even if preference update fails

    async def get_preferences(
        self,
        db: AsyncSession,
        pref_types: Optional[List[str]] = None
    ) -> List[UserPreference]:
        """Get all learned preferences."""
        try:
            stmt = select(UserPreference)
            if pref_types:
                stmt = stmt.where(UserPreference.pref_type.in_(pref_types))
            stmt = stmt.order_by(UserPreference.confidence.desc())

            result = await db.execute(stmt)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return []

    async def apply_preferences_to_score(
        self,
        db: AsyncSession,
        sender_email: str,
        current_score: int
    ) -> Tuple[int, str]:
        """
        Apply learned preferences to adjust a score.

        Returns:
            Tuple of (adjusted_score, reason)
        """
        try:
            # Check sender preference
            stmt = select(UserPreference).where(
                UserPreference.pref_type == "sender",
                UserPreference.pattern == sender_email.lower()
            )
            result = await db.execute(stmt)
            sender_pref = result.scalar_one_or_none()

            if sender_pref and sender_pref.feedback_count >= self.MIN_FEEDBACK_THRESHOLD:
                if sender_pref.classification == "KEEP":
                    adjusted = max(0, current_score - 30)
                    return adjusted, f"User preference: KEEP (confidence: {sender_pref.confidence:.0%})"
                elif sender_pref.classification == "DELETE":
                    adjusted = min(100, current_score + 30)
                    return adjusted, f"User preference: DELETE (confidence: {sender_pref.confidence:.0%})"

            # Check domain preference
            domain = sender_email.split("@")[1] if "@" in sender_email else ""
            if domain:
                stmt = select(UserPreference).where(
                    UserPreference.pref_type == "domain",
                    UserPreference.pattern == domain.lower()
                )
                result = await db.execute(stmt)
                domain_pref = result.scalar_one_or_none()

                if domain_pref and domain_pref.feedback_count >= self.MIN_FEEDBACK_THRESHOLD:
                    adjustment = int(20 * domain_pref.confidence)
                    if domain_pref.classification == "KEEP":
                        return max(0, current_score - adjustment), f"Domain preference: KEEP"
                    else:
                        return min(100, current_score + adjustment), f"Domain preference: DELETE"

            return current_score, "No user preference applied"
        except Exception as e:
            logger.error(f"Error applying preferences to score: {e}")
            # Return original score if there's an error
            return current_score, f"Error applying preferences: {str(e)}"

    async def get_feedback_stats(self, db: AsyncSession) -> Dict:
        """Get statistics about user feedback."""
        try:
            # Count total feedback
            total_stmt = select(func.count(UserFeedback.id))
            total_result = await db.execute(total_stmt)
            total = total_result.scalar() or 0

            # Count by type
            type_stmt = select(
                UserFeedback.feedback_type,
                func.count(UserFeedback.id)
            ).group_by(UserFeedback.feedback_type)
            type_result = await db.execute(type_stmt)
            by_type = {row[0]: row[1] for row in type_result}

            # Count learned preferences
            pref_stmt = select(func.count(UserPreference.id))
            pref_result = await db.execute(pref_stmt)
            preferences_count = pref_result.scalar() or 0

            # Count preferences by type
            pref_type_stmt = select(
                UserPreference.pref_type,
                func.count(UserPreference.id)
            ).group_by(UserPreference.pref_type)
            pref_type_result = await db.execute(pref_type_stmt)
            preferences_by_type = {row[0]: row[1] for row in pref_type_result}

            return {
                "total_feedback": total,
                "feedback_by_type": by_type,
                "learned_preferences": preferences_count,
                "preferences_by_type": preferences_by_type
            }
        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            return {
                "total_feedback": 0,
                "feedback_by_type": {},
                "learned_preferences": 0,
                "preferences_by_type": {}
            }

    async def clear_preference(self, db: AsyncSession, pref_id: int) -> bool:
        """Delete a specific learned preference."""
        try:
            stmt = select(UserPreference).where(UserPreference.id == pref_id)
            result = await db.execute(stmt)
            pref = result.scalar_one_or_none()

            if not pref:
                logger.warning(f"Preference not found: {pref_id}")
                return False

            await db.delete(pref)
            await db.commit()
            logger.info(f"Deleted preference: {pref_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting preference: {e}")
            await db.rollback()
            return False
