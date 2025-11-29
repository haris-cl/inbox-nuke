"""
User feedback API endpoints.
Allows users to provide feedback on email classifications and learn preferences.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import UserFeedback, UserPreference, EmailScore
from agent.personalization import PersonalizationEngine

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Schemas
# ============================================================================


class FeedbackRequest(BaseModel):
    """Request schema for submitting user feedback."""
    feedback_type: str  # "email" or "sender"
    target_id: str  # message_id or sender_email
    corrected_classification: str  # "KEEP" or "DELETE"
    reason: Optional[str] = None


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    id: int
    feedback_type: str
    target_id: str
    original_classification: str
    corrected_classification: str
    reason: Optional[str]
    created_at: str


class FeedbackListResponse(BaseModel):
    """Response schema for feedback history list."""
    feedbacks: list[FeedbackResponse]
    total: int


class PreferenceResponse(BaseModel):
    """Response schema for a learned preference."""
    id: int
    pref_type: str
    pattern: str
    classification: str
    confidence: float
    feedback_count: int
    last_feedback: str
    created_at: str


class PreferenceListResponse(BaseModel):
    """Response schema for preferences list."""
    preferences: list[PreferenceResponse]
    total: int


class FeedbackStatsResponse(BaseModel):
    """Response schema for feedback statistics."""
    total_feedback: int
    feedback_by_type: dict[str, int]
    learned_preferences: int
    preferences_by_type: dict[str, int]


# ============================================================================
# Feedback Endpoints
# ============================================================================


@router.post("/submit", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Submit user feedback on a classification.

    This endpoint:
    1. Records the user's correction to a classification
    2. Updates learned preferences based on feedback
    3. Returns the created feedback record

    Args:
        request: Feedback details
        db: Database session

    Returns:
        Message and feedback ID

    Raises:
        HTTPException: If feedback type is invalid or email not found
    """
    # Validate feedback type
    if request.feedback_type not in ["email", "sender"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="feedback_type must be 'email' or 'sender'"
        )

    # Validate classification
    if request.corrected_classification not in ["KEEP", "DELETE"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="corrected_classification must be 'KEEP' or 'DELETE'"
        )

    # Get original classification
    original = "UNKNOWN"
    if request.feedback_type == "email":
        stmt = select(EmailScore).where(EmailScore.message_id == request.target_id)
        result = await db.execute(stmt)
        email = result.scalar_one_or_none()
        if email:
            original = email.classification
        else:
            logger.warning(f"Email not found for feedback: {request.target_id}")

    # Record feedback using personalization engine
    engine = PersonalizationEngine()
    try:
        feedback = await engine.record_feedback(
            db=db,
            feedback_type=request.feedback_type,
            target_id=request.target_id,
            original_classification=original,
            corrected_classification=request.corrected_classification,
            reason=request.reason
        )

        logger.info(f"Feedback submitted: {request.target_id} -> {request.corrected_classification}")

        return {
            "message": "Feedback recorded successfully",
            "id": feedback.id,
            "learning_applied": True
        }
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record feedback: {str(e)}"
        )


@router.get("/history")
async def get_feedback_history(
    limit: int = 50,
    offset: int = 0,
    feedback_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get user feedback history.

    Args:
        limit: Maximum number of feedbacks to return
        offset: Number of feedbacks to skip
        feedback_type: Optional filter by type (email, sender)
        db: Database session

    Returns:
        List of feedback records with pagination info
    """
    try:
        # Build query
        stmt = select(UserFeedback)
        if feedback_type:
            stmt = stmt.where(UserFeedback.feedback_type == feedback_type)

        stmt = stmt.order_by(desc(UserFeedback.created_at)).limit(limit).offset(offset)

        result = await db.execute(stmt)
        feedbacks = result.scalars().all()

        # Count total
        count_stmt = select(UserFeedback)
        if feedback_type:
            count_stmt = count_stmt.where(UserFeedback.feedback_type == feedback_type)
        count_result = await db.execute(count_stmt)
        total = len(count_result.scalars().all())

        return {
            "feedbacks": [
                {
                    "id": f.id,
                    "feedback_type": f.feedback_type,
                    "target_id": f.target_id,
                    "original_classification": f.original_classification,
                    "corrected_classification": f.corrected_classification,
                    "reason": f.reason,
                    "created_at": f.created_at.isoformat()
                }
                for f in feedbacks
            ],
            "total": total,
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        logger.error(f"Error getting feedback history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback history: {str(e)}"
        )


@router.get("/preferences")
async def get_learned_preferences(
    pref_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all learned user preferences.

    Args:
        pref_type: Optional filter by type (sender, domain, keyword)
        db: Database session

    Returns:
        List of learned preferences
    """
    try:
        engine = PersonalizationEngine()

        # Get preferences
        pref_types = [pref_type] if pref_type else None
        preferences = await engine.get_preferences(db, pref_types)

        return {
            "preferences": [
                {
                    "id": p.id,
                    "pref_type": p.pref_type,
                    "pattern": p.pattern,
                    "classification": p.classification,
                    "confidence": p.confidence,
                    "feedback_count": p.feedback_count,
                    "last_feedback": p.last_feedback.isoformat(),
                    "created_at": p.created_at.isoformat()
                }
                for p in preferences
            ],
            "total": len(preferences)
        }
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.delete("/preferences/{pref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_preference(
    pref_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a learned preference.

    Args:
        pref_id: ID of preference to delete
        db: Database session

    Returns:
        No content on success

    Raises:
        HTTPException: If preference not found
    """
    try:
        engine = PersonalizationEngine()
        success = await engine.clear_preference(db, pref_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Preference {pref_id} not found"
            )

        logger.info(f"Preference deleted: {pref_id}")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting preference: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete preference: {str(e)}"
        )


@router.get("/stats")
async def get_feedback_stats(db: AsyncSession = Depends(get_db)):
    """
    Get feedback statistics.

    Args:
        db: Database session

    Returns:
        Statistics about user feedback and learned preferences
    """
    try:
        engine = PersonalizationEngine()
        stats = await engine.get_feedback_stats(db)

        return {
            "total_feedback": stats.get("total_feedback", 0),
            "feedback_by_type": stats.get("feedback_by_type", {}),
            "learned_preferences": stats.get("learned_preferences", 0),
            "preferences_by_type": stats.get("preferences_by_type", {})
        }
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback stats: {str(e)}"
        )
