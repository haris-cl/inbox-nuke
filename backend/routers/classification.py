"""
Email classification API endpoints.
Provides AI-powered email classification and management.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import get_db
from gmail_client import GmailClient
from models import EmailClassification, GmailCredentials
from schemas import (
    ClassificationScanRequest,
    ClassificationResultResponse,
    ClassificationListResponse,
    ClassificationOverrideRequest,
    ClassificationExecuteRequest,
    ClassificationStatsResponse,
)
from agent.classifier import EmailClassifier

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Classification Endpoints
# ============================================================================


@router.post("/scan", status_code=status.HTTP_202_ACCEPTED)
async def scan_emails_for_classification(
    request: ClassificationScanRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Scan inbox and classify emails using AI.

    This endpoint:
    1. Fetches recent emails from Gmail
    2. Classifies them using OpenAI
    3. Stores results in database

    Args:
        request: Scan configuration (max_emails, force_rescan)
        db: Database session

    Returns:
        Message indicating scan has started

    Raises:
        HTTPException: If OpenAI is not configured or Gmail not connected
    """
    # Check if OpenAI is configured
    if not settings.OPENAI_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key not configured. Set OPENAI_API_KEY in environment."
        )

    # Check if Gmail is connected
    stmt = select(GmailCredentials).limit(1)
    result = await db.execute(stmt)
    creds = result.scalar_one_or_none()

    if not creds:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gmail not connected. Please authenticate first."
        )

    try:
        # Initialize Gmail client and classifier
        gmail_client = GmailClient(db=db, credentials=creds)
        classifier = EmailClassifier(db=db, gmail_client=gmail_client)

        # Get recent emails
        logger.info(f"Fetching {request.max_emails} emails for classification")
        messages = await gmail_client.list_messages(
            query="",  # Get all emails
            max_results=request.max_emails
        )

        # Get full message details
        full_messages = await gmail_client.batch_get_messages(
            message_ids=[msg["id"] for msg in messages],
            format="metadata"
        )

        logger.info(f"Classifying {len(full_messages)} emails")

        # Classify emails
        results = await classifier.classify_batch(
            messages=full_messages,
            batch_size=settings.CLASSIFICATION_BATCH_SIZE
        )

        # Save classifications
        saved_count = 0
        for result in results:
            await classifier.save_classification(result)
            saved_count += 1

        logger.info(f"Saved {saved_count} classifications")

        return {
            "message": f"Classification scan completed",
            "emails_scanned": len(full_messages),
            "classifications_saved": saved_count
        }

    except Exception as e:
        logger.error(f"Error during classification scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Classification scan failed: {str(e)}"
        )


@router.get("/results", response_model=ClassificationListResponse)
async def get_classification_results(
    classification: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """
    Get classification results with filtering.

    Args:
        classification: Filter by classification (KEEP, DELETE, REVIEW)
        category: Filter by category (financial, security, marketing, etc.)
        limit: Maximum results to return (1-100)
        offset: Offset for pagination
        db: Database session

    Returns:
        Paginated list of classification results

    Raises:
        HTTPException: On database errors
    """
    try:
        # Build query
        stmt = select(EmailClassification)

        # Apply filters
        if classification:
            stmt = stmt.where(EmailClassification.classification == classification)
        if category:
            stmt = stmt.where(EmailClassification.category == category)

        # Get total count
        count_stmt = select(func.count()).select_from(EmailClassification)
        if classification:
            count_stmt = count_stmt.where(EmailClassification.classification == classification)
        if category:
            count_stmt = count_stmt.where(EmailClassification.category == category)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # Apply pagination
        stmt = stmt.order_by(EmailClassification.processed_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        classifications = result.scalars().all()

        return ClassificationListResponse(
            classifications=classifications,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error getting classification results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get classifications: {str(e)}"
        )


@router.post("/override/{message_id}", response_model=ClassificationResultResponse)
async def override_classification(
    message_id: str,
    request: ClassificationOverrideRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Allow user to override AI classification.

    Args:
        message_id: Gmail message ID
        request: New classification
        db: Database session

    Returns:
        Updated classification result

    Raises:
        HTTPException: If classification not found
    """
    try:
        # Find existing classification
        stmt = select(EmailClassification).where(
            EmailClassification.message_id == message_id
        )
        result = await db.execute(stmt)
        classification = result.scalar_one_or_none()

        if not classification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Classification not found for message: {message_id}"
            )

        # Update with user override
        classification.user_override = request.new_classification
        await db.commit()
        await db.refresh(classification)

        logger.info(
            f"User overrode classification for {message_id}: "
            f"{classification.classification} -> {request.new_classification}"
        )

        return classification

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding classification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to override classification: {str(e)}"
        )


@router.post("/execute")
async def execute_cleanup(
    request: ClassificationExecuteRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Execute cleanup based on classifications (delete all DELETE emails).

    Args:
        request: Execution parameters (dry_run, older_than_days)
        db: Database session

    Returns:
        Summary of deletion results

    Raises:
        HTTPException: On errors
    """
    try:
        # Get all DELETE classifications
        stmt = select(EmailClassification).where(
            EmailClassification.classification == "DELETE"
        )

        # Apply user overrides
        # If user_override is set, use that instead
        result = await db.execute(stmt)
        classifications = result.scalars().all()

        # Filter by user override
        delete_classifications = [
            c for c in classifications
            if (c.user_override == "DELETE" if c.user_override else c.classification == "DELETE")
        ]

        if request.dry_run:
            return {
                "dry_run": True,
                "total_to_delete": len(delete_classifications),
                "message": f"Would delete {len(delete_classifications)} emails"
            }

        # Get Gmail client
        stmt_creds = select(GmailCredentials).limit(1)
        result_creds = await db.execute(stmt_creds)
        creds = result_creds.scalar_one_or_none()

        if not creds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected"
            )

        gmail_client = GmailClient(db=db, credentials=creds)

        # Delete emails
        message_ids = [c.message_id for c in delete_classifications]
        deleted_count = await gmail_client.trash_messages(message_ids)

        # Remove from classifications table
        delete_stmt = delete(EmailClassification).where(
            EmailClassification.message_id.in_(message_ids)
        )
        await db.execute(delete_stmt)
        await db.commit()

        logger.info(f"Executed cleanup: deleted {deleted_count} emails")

        return {
            "dry_run": False,
            "emails_deleted": deleted_count,
            "message": f"Successfully deleted {deleted_count} emails"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup execution failed: {str(e)}"
        )


@router.get("/stats", response_model=ClassificationStatsResponse)
async def get_classification_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get classification statistics.

    Returns:
        Statistics about classifications

    Raises:
        HTTPException: On database errors
    """
    try:
        # Get total counts by classification
        keep_stmt = select(func.count()).select_from(EmailClassification).where(
            EmailClassification.classification == "KEEP"
        )
        delete_stmt = select(func.count()).select_from(EmailClassification).where(
            EmailClassification.classification == "DELETE"
        )
        review_stmt = select(func.count()).select_from(EmailClassification).where(
            EmailClassification.classification == "REVIEW"
        )

        keep_result = await db.execute(keep_stmt)
        delete_result = await db.execute(delete_stmt)
        review_result = await db.execute(review_stmt)

        keep_count = keep_result.scalar()
        delete_count = delete_result.scalar()
        review_count = review_result.scalar()

        # Get counts by category
        category_stmt = select(
            EmailClassification.category,
            func.count(EmailClassification.id)
        ).group_by(EmailClassification.category)

        category_result = await db.execute(category_stmt)
        category_counts = {row[0]: row[1] for row in category_result}

        return ClassificationStatsResponse(
            total_classified=keep_count + delete_count + review_count,
            keep_count=keep_count,
            delete_count=delete_count,
            review_count=review_count,
            by_category=category_counts
        )

    except Exception as e:
        logger.error(f"Error getting classification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.delete("/clear")
async def clear_classifications(
    db: AsyncSession = Depends(get_db),
):
    """
    Clear all classification results.

    Returns:
        Number of classifications deleted

    Raises:
        HTTPException: On database errors
    """
    try:
        stmt = delete(EmailClassification)
        result = await db.execute(stmt)
        await db.commit()

        deleted_count = result.rowcount

        logger.info(f"Cleared {deleted_count} classifications")

        return {
            "message": f"Cleared {deleted_count} classifications",
            "deleted": deleted_count
        }

    except Exception as e:
        logger.error(f"Error clearing classifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear classifications: {str(e)}"
        )
