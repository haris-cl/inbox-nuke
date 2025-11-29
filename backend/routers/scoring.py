"""
Email scoring API endpoints.
Provides multi-signal email scoring and management for intelligent cleanup.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy import select, func, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db, AsyncSessionLocal
from models import EmailScore, SenderProfile, GmailCredentials
from gmail_client import GmailClient
from agent.scoring import EmailScorer
from utils.encryption import decrypt_token
from schemas import (
    ScoringStartRequest,
    ScoringProgressResponse,
    ScoringStatsResponse,
    EmailScoreResponse,
    EmailScoreListResponse,
    SenderProfileResponse,
    SenderProfileListResponse,
    ScoreOverrideRequest,
    BulkScoreActionRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Store background task status
scoring_task_status = {
    "status": "idle",
    "total_emails": 0,
    "scored_emails": 0,
    "keep_count": 0,
    "delete_count": 0,
    "uncertain_count": 0,
    "current_sender": None,
    "error": None
}


async def run_scoring_task(max_emails: int, rescan: bool):
    """
    Background task to score emails.
    Fetches emails from Gmail, scores them, and stores results.
    """
    global scoring_task_status

    try:
        logger.info(f"Starting scoring task for {max_emails} emails (rescan={rescan})")

        # Create a new database session for the background task
        async with AsyncSessionLocal() as db:
            # Get Gmail credentials
            stmt = select(GmailCredentials).limit(1)
            result = await db.execute(stmt)
            creds = result.scalar_one_or_none()

            if not creds:
                scoring_task_status["status"] = "failed"
                scoring_task_status["error"] = "Gmail not connected"
                return

            # Initialize Gmail client
            gmail_client = GmailClient(db=db, credentials=creds)

            # Get user's email address to protect their own emails
            service = await gmail_client.get_service()
            profile = await asyncio.to_thread(
                service.users().getProfile(userId="me").execute
            )
            user_email = profile.get("emailAddress", "").lower()
            logger.info(f"User email for protection: {user_email}")

            # Initialize scorer
            scorer = EmailScorer(gmail_client)

            # Fetch emails from Gmail
            logger.info("Fetching emails from Gmail...")
            messages = await gmail_client.list_messages(max_results=max_emails)

            if not messages:
                scoring_task_status["status"] = "completed"
                scoring_task_status["total_emails"] = 0
                logger.info("No emails found to score")
                return

            scoring_task_status["total_emails"] = len(messages)
            logger.info(f"Found {len(messages)} emails to score")

            # Score emails in batches
            batch_size = 50
            sender_scores = {}  # Track scores per sender for profiles

            for i in range(0, len(messages), batch_size):
                batch = messages[i:i + batch_size]
                message_ids = [m["id"] for m in batch]

                # Get full message details
                for msg_id in message_ids:
                    try:
                        # Check if already scored (skip if not rescan)
                        if not rescan:
                            existing = await db.execute(
                                select(EmailScore).where(EmailScore.message_id == msg_id)
                            )
                            if existing.scalar_one_or_none():
                                scoring_task_status["scored_emails"] += 1
                                continue

                        # Get message details
                        message = await gmail_client.get_message(msg_id)
                        if not message:
                            continue

                        # Score the email
                        score_result = await scorer.score_email(message)

                        # Extract sender info
                        headers = {h["name"].lower(): h["value"] for h in message.get("payload", {}).get("headers", [])}
                        sender_full = headers.get("from", "unknown@unknown.com")
                        # Extract email from "Name <email>" format
                        if "<" in sender_full and ">" in sender_full:
                            sender_email = sender_full.split("<")[1].split(">")[0].lower()
                            display_name = sender_full.split("<")[0].strip().strip('"')
                        else:
                            sender_email = sender_full.lower()
                            display_name = None

                        scoring_task_status["current_sender"] = sender_email

                        # Override classification if sender is the user's own email
                        final_classification = score_result.classification
                        final_score = score_result.total_score
                        final_reasoning = score_result.reasoning
                        if user_email and sender_email == user_email:
                            final_classification = "KEEP"
                            final_score = 0  # Score 0 = highest priority to keep
                            final_reasoning = "Classification: KEEP (score: 0/100)\nKey factors:\n  • Email from your own account - always keep"
                            logger.info(f"Protected user's own email from {sender_email}")

                        # Update classification counts
                        if final_classification == "KEEP":
                            scoring_task_status["keep_count"] += 1
                        elif final_classification == "DELETE":
                            scoring_task_status["delete_count"] += 1
                        else:
                            scoring_task_status["uncertain_count"] += 1

                        # Extract individual scores from signal_breakdown
                        # signal_breakdown is Dict[str, Tuple[int, str]]
                        signal_breakdown = score_result.signal_breakdown
                        category_score = signal_breakdown.get("gmail_category", (0, ""))[0]
                        header_score = signal_breakdown.get("headers", (0, ""))[0]
                        engagement_score = signal_breakdown.get("engagement", (0, ""))[0]
                        keyword_score = signal_breakdown.get("keywords", (0, ""))[0]
                        thread_score = signal_breakdown.get("thread_context", (0, ""))[0]

                        # Convert signal_breakdown to JSON-serializable format
                        signal_details = {
                            signal: {"score": score, "reason": reason}
                            for signal, (score, reason) in signal_breakdown.items()
                        }

                        # Store in database
                        email_score = EmailScore(
                            message_id=msg_id,
                            thread_id=message.get("threadId", ""),
                            sender_email=sender_email,
                            subject=headers.get("subject", "(No Subject)"),
                            total_score=final_score,
                            classification=final_classification,
                            confidence=score_result.confidence,
                            category_score=category_score,
                            header_score=header_score,
                            engagement_score=engagement_score,
                            keyword_score=keyword_score,
                            thread_score=thread_score,
                            signal_details=json.dumps(signal_details),
                            reasoning=final_reasoning,
                            llm_analyzed=False,
                            gmail_labels=json.dumps(message.get("labelIds", [])),
                            scored_at=datetime.utcnow(),
                            created_at=datetime.utcnow()
                        )

                        # Merge in case of rescan (upsert)
                        await db.merge(email_score)

                        # Track sender scores for profile
                        if sender_email not in sender_scores:
                            sender_scores[sender_email] = {
                                "scores": [],
                                "display_name": display_name,
                                "domain": sender_email.split("@")[1] if "@" in sender_email else "",
                                "labels": message.get("labelIds", []),
                                "has_unsubscribe": "List-Unsubscribe" in headers
                            }
                        sender_scores[sender_email]["scores"].append(score_result.total_score)
                        sender_scores[sender_email]["labels"].extend(message.get("labelIds", []))

                        scoring_task_status["scored_emails"] += 1

                    except Exception as e:
                        logger.error(f"Error scoring email {msg_id}: {e}")
                        continue

                # Commit batch
                await db.commit()

            # Update sender profiles
            logger.info(f"Updating {len(sender_scores)} sender profiles...")
            for sender_email, data in sender_scores.items():
                try:
                    avg_score = sum(data["scores"]) / len(data["scores"])
                    email_count = len(data["scores"])

                    # Determine classification based on average score
                    if avg_score < 30:
                        classification = "KEEP"
                    elif avg_score >= 70:
                        classification = "DELETE"
                    else:
                        classification = "UNCERTAIN"

                    # Count labels
                    labels = data["labels"]
                    primary_count = labels.count("CATEGORY_PRIMARY")
                    promotions_count = labels.count("CATEGORY_PROMOTIONS")
                    social_count = labels.count("CATEGORY_SOCIAL")
                    updates_count = labels.count("CATEGORY_UPDATES")
                    starred_count = labels.count("STARRED")

                    # Check for existing profile
                    existing_profile = await db.execute(
                        select(SenderProfile).where(SenderProfile.sender_email == sender_email)
                    )
                    profile = existing_profile.scalar_one_or_none()

                    if profile:
                        # Update existing
                        profile.avg_score = avg_score
                        profile.email_count = email_count
                        profile.classification = classification
                        profile.primary_count = primary_count
                        profile.promotions_count = promotions_count
                        profile.social_count = social_count
                        profile.updates_count = updates_count
                        profile.starred_count = starred_count
                        profile.has_unsubscribe = data["has_unsubscribe"]
                        profile.last_seen = datetime.utcnow()
                        profile.updated_at = datetime.utcnow()
                    else:
                        # Create new
                        profile = SenderProfile(
                            sender_email=sender_email,
                            sender_domain=data["domain"],
                            display_name=data["display_name"],
                            avg_score=avg_score,
                            email_count=email_count,
                            classification=classification,
                            user_replied_count=0,
                            starred_count=starred_count,
                            primary_count=primary_count,
                            promotions_count=promotions_count,
                            social_count=social_count,
                            updates_count=updates_count,
                            has_unsubscribe=data["has_unsubscribe"],
                            first_seen=datetime.utcnow(),
                            last_seen=datetime.utcnow(),
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        db.add(profile)

                except Exception as e:
                    logger.error(f"Error updating sender profile {sender_email}: {e}")

            await db.commit()

        scoring_task_status["status"] = "completed"
        scoring_task_status["current_sender"] = None
        logger.info(f"Scoring complete: {scoring_task_status['scored_emails']} emails scored")

    except Exception as e:
        logger.error(f"Scoring task failed: {e}")
        scoring_task_status["status"] = "failed"
        scoring_task_status["error"] = str(e)


# ============================================================================
# Scoring Endpoints
# ============================================================================


@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def start_scoring(
    request: ScoringStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Start email scoring in background.

    This endpoint:
    1. Fetches emails from Gmail
    2. Scores them using multi-signal system
    3. Stores results in database

    Args:
        request: Scoring configuration (max_emails, rescan)
        background_tasks: FastAPI background tasks
        db: Database session

    Returns:
        Message indicating scoring has started

    Raises:
        HTTPException: If Gmail not connected or scoring already running
    """
    global scoring_task_status

    # Check if already running
    if scoring_task_status["status"] == "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Scoring is already running. Please wait for it to complete."
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

    # Reset status
    scoring_task_status.update({
        "status": "running",
        "total_emails": 0,
        "scored_emails": 0,
        "keep_count": 0,
        "delete_count": 0,
        "uncertain_count": 0,
        "current_sender": None,
        "error": None
    })

    # Start background scoring task
    background_tasks.add_task(run_scoring_task, request.max_emails, request.rescan)

    logger.info(f"Started scoring for {request.max_emails} emails (rescan={request.rescan})")

    return {
        "message": "Email scoring started",
        "max_emails": request.max_emails,
        "rescan": request.rescan
    }


@router.get("/progress", response_model=ScoringProgressResponse)
async def get_scoring_progress():
    """
    Get current scoring progress.

    Returns:
        Current scoring progress and statistics
    """
    return ScoringProgressResponse(**scoring_task_status)


@router.get("/stats", response_model=ScoringStatsResponse)
async def get_scoring_stats(db: AsyncSession = Depends(get_db)):
    """
    Get scoring statistics.

    Returns:
        Overall statistics about scored emails

    Raises:
        HTTPException: On database errors
    """
    try:
        # Get total counts by classification
        keep_stmt = select(func.count()).select_from(EmailScore).where(
            EmailScore.classification == "KEEP"
        )
        delete_stmt = select(func.count()).select_from(EmailScore).where(
            EmailScore.classification == "DELETE"
        )
        uncertain_stmt = select(func.count()).select_from(EmailScore).where(
            EmailScore.classification == "UNCERTAIN"
        )

        keep_result = await db.execute(keep_stmt)
        delete_result = await db.execute(delete_stmt)
        uncertain_result = await db.execute(uncertain_stmt)

        keep_count = keep_result.scalar() or 0
        delete_count = delete_result.scalar() or 0
        uncertain_count = uncertain_result.scalar() or 0

        total_scored = keep_count + delete_count + uncertain_count

        # Get average score
        avg_stmt = select(func.avg(EmailScore.total_score))
        avg_result = await db.execute(avg_stmt)
        avg_score = avg_result.scalar() or 0.0

        # Get score distribution (0-10, 11-20, etc.)
        score_distribution = {}
        for i in range(0, 100, 10):
            range_stmt = select(func.count()).select_from(EmailScore).where(
                and_(
                    EmailScore.total_score >= i,
                    EmailScore.total_score < i + 10
                )
            )
            range_result = await db.execute(range_stmt)
            count = range_result.scalar() or 0
            score_distribution[f"{i}-{i+9}"] = count

        # Get top delete senders (from sender profiles)
        top_delete_stmt = select(SenderProfile).where(
            SenderProfile.classification == "DELETE"
        ).order_by(SenderProfile.email_count.desc()).limit(10)

        top_delete_result = await db.execute(top_delete_stmt)
        top_delete_senders_obj = top_delete_result.scalars().all()

        top_delete_senders = [
            {
                "email": s.sender_email,
                "score": int(s.avg_score),
                "count": s.email_count
            }
            for s in top_delete_senders_obj
        ]

        # Get top keep senders
        top_keep_stmt = select(SenderProfile).where(
            SenderProfile.classification == "KEEP"
        ).order_by(SenderProfile.email_count.desc()).limit(10)

        top_keep_result = await db.execute(top_keep_stmt)
        top_keep_senders_obj = top_keep_result.scalars().all()

        top_keep_senders = [
            {
                "email": s.sender_email,
                "score": int(s.avg_score),
                "count": s.email_count
            }
            for s in top_keep_senders_obj
        ]

        # Get categories breakdown
        categories_breakdown = {}
        for category in ["primary", "promotions", "social", "updates"]:
            category_stmt = select(func.sum(getattr(SenderProfile, f"{category}_count")))
            category_result = await db.execute(category_stmt)
            count = category_result.scalar() or 0
            categories_breakdown[category] = count

        return ScoringStatsResponse(
            total_scored=total_scored,
            keep_count=keep_count,
            delete_count=delete_count,
            uncertain_count=uncertain_count,
            avg_score=float(avg_score),
            score_distribution=score_distribution,
            top_delete_senders=top_delete_senders,
            top_keep_senders=top_keep_senders,
            categories_breakdown=categories_breakdown
        )

    except Exception as e:
        logger.error(f"Error getting scoring stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scoring stats: {str(e)}"
        )


@router.get("/emails", response_model=EmailScoreListResponse)
async def get_scored_emails(
    classification: Optional[str] = None,
    min_score: Optional[int] = None,
    max_score: Optional[int] = None,
    sender: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get scored emails with filtering.

    Args:
        classification: Filter by classification (KEEP, DELETE, UNCERTAIN)
        min_score: Minimum score threshold
        max_score: Maximum score threshold
        sender: Filter by sender email
        limit: Maximum results to return (1-100)
        offset: Offset for pagination
        db: Database session

    Returns:
        Paginated list of scored emails

    Raises:
        HTTPException: On database errors
    """
    try:
        # Build query
        stmt = select(EmailScore)
        count_stmt = select(func.count()).select_from(EmailScore)

        # Apply filters
        filters = []
        if classification:
            filters.append(EmailScore.classification == classification)
        if min_score is not None:
            filters.append(EmailScore.total_score >= min_score)
        if max_score is not None:
            filters.append(EmailScore.total_score <= max_score)
        if sender:
            filters.append(EmailScore.sender_email == sender)

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(EmailScore.scored_at.desc())
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        emails = result.scalars().all()

        return EmailScoreListResponse(
            emails=emails,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error getting scored emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scored emails: {str(e)}"
        )


@router.get("/emails/{message_id}", response_model=EmailScoreResponse)
async def get_email_score(message_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get score details for a specific email.

    Args:
        message_id: Gmail message ID
        db: Database session

    Returns:
        Email score details

    Raises:
        HTTPException: If email score not found
    """
    try:
        stmt = select(EmailScore).where(EmailScore.message_id == message_id)
        result = await db.execute(stmt)
        email_score = result.scalar_one_or_none()

        if not email_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email score not found for message: {message_id}"
            )

        return email_score

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email score: {str(e)}"
        )


@router.post("/emails/{message_id}/override", response_model=EmailScoreResponse)
async def override_email_score(
    message_id: str,
    request: ScoreOverrideRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Override email classification.

    Args:
        message_id: Gmail message ID
        request: New classification
        db: Database session

    Returns:
        Updated email score

    Raises:
        HTTPException: If email score not found
    """
    try:
        stmt = select(EmailScore).where(EmailScore.message_id == message_id)
        result = await db.execute(stmt)
        email_score = result.scalar_one_or_none()

        if not email_score:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Email score not found for message: {message_id}"
            )

        # Update with user override
        email_score.user_override = request.classification
        await db.commit()
        await db.refresh(email_score)

        logger.info(
            f"User overrode classification for {message_id}: "
            f"{email_score.classification} -> {request.classification}"
        )

        return email_score

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error overriding email score: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to override email score: {str(e)}"
        )


@router.get("/senders", response_model=SenderProfileListResponse)
async def get_sender_profiles(
    classification: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get sender profiles with aggregated scores.

    Args:
        classification: Filter by classification (KEEP, DELETE, UNCERTAIN)
        min_score: Minimum average score threshold
        limit: Maximum results to return (1-100)
        offset: Offset for pagination
        db: Database session

    Returns:
        Paginated list of sender profiles

    Raises:
        HTTPException: On database errors
    """
    try:
        # Build query
        stmt = select(SenderProfile)
        count_stmt = select(func.count()).select_from(SenderProfile)

        # Apply filters
        filters = []
        if classification:
            filters.append(SenderProfile.classification == classification)
        if min_score is not None:
            filters.append(SenderProfile.avg_score >= min_score)

        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))

        # Get total count
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Apply pagination
        stmt = stmt.order_by(SenderProfile.email_count.desc())
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        senders = result.scalars().all()

        return SenderProfileListResponse(
            senders=senders,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error getting sender profiles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sender profiles: {str(e)}"
        )


@router.get("/senders/{sender_email}", response_model=SenderProfileResponse)
async def get_sender_profile(sender_email: str, db: AsyncSession = Depends(get_db)):
    """
    Get detailed sender profile.

    Args:
        sender_email: Sender email address
        db: Database session

    Returns:
        Sender profile details

    Raises:
        HTTPException: If sender profile not found
    """
    try:
        stmt = select(SenderProfile).where(SenderProfile.sender_email == sender_email)
        result = await db.execute(stmt)
        sender_profile = result.scalar_one_or_none()

        if not sender_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sender profile not found: {sender_email}"
            )

        return sender_profile

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sender profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sender profile: {str(e)}"
        )


@router.post("/refine-uncertain")
async def refine_uncertain_emails(db: AsyncSession = Depends(get_db)):
    """
    Use LLM to classify uncertain emails.
    This is Phase 2 - called after initial scoring.

    Args:
        db: Database session

    Returns:
        Summary of LLM refinement results

    Raises:
        HTTPException: If LLM not available or on errors
    """
    try:
        # Check if LLM is available
        from agent.llm_classifier import LLMClassifier
        llm_classifier = LLMClassifier()

        if not llm_classifier.is_available():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LLM classification not available. Please configure OPENAI_API_KEY."
            )

        # Get uncertain emails from database
        stmt = select(EmailScore).where(
            and_(
                EmailScore.classification == "UNCERTAIN",
                or_(
                    EmailScore.llm_analyzed == False,
                    EmailScore.llm_analyzed == None
                )
            )
        )
        result = await db.execute(stmt)
        uncertain_emails = result.scalars().all()

        if not uncertain_emails:
            return {
                "message": "No uncertain emails to refine",
                "refined_count": 0,
                "keep_count": 0,
                "delete_count": 0,
                "uncertain_count": 0
            }

        logger.info(f"Found {len(uncertain_emails)} uncertain emails to refine with LLM")

        # Group by sender and get sample subjects
        senders_data = {}
        email_to_sender = {}  # Map email_id to sender for later update

        for email in uncertain_emails:
            sender = email.sender_email
            email_to_sender[email.id] = sender

            if sender not in senders_data:
                senders_data[sender] = {
                    'email': sender,
                    'name': None,
                    'subjects': [],
                    'count': 0,
                    'engagement': {
                        'replied_count': 0,
                        'starred_count': 0,
                        'has_unsubscribe': False
                    },
                    'email_ids': []
                }

            senders_data[sender]['subjects'].append(email.subject)
            senders_data[sender]['count'] += 1
            senders_data[sender]['email_ids'].append(email.id)

        # Classify senders with LLM
        sender_classifications = await llm_classifier.classify_senders_batch(
            list(senders_data.values())
        )

        # Build lookup
        sender_lookup = {sc.sender_email: sc for sc in sender_classifications}

        # Update database with refined classifications
        keep_count = 0
        delete_count = 0
        still_uncertain_count = 0

        for email in uncertain_emails:
            sender_analysis = sender_lookup.get(email.sender_email)
            if sender_analysis:
                # Update classification
                email.classification = sender_analysis.classification
                email.confidence = sender_analysis.confidence
                email.llm_analyzed = True
                email.llm_reasoning = sender_analysis.reasoning

                # Update counters
                if sender_analysis.classification == "KEEP":
                    keep_count += 1
                elif sender_analysis.classification == "DELETE":
                    delete_count += 1
                else:
                    still_uncertain_count += 1

        # Commit changes
        await db.commit()

        logger.info(
            f"LLM refinement complete: {keep_count} KEEP, "
            f"{delete_count} DELETE, {still_uncertain_count} still UNCERTAIN"
        )

        return {
            "message": "LLM refinement complete",
            "refined_count": len(uncertain_emails),
            "keep_count": keep_count,
            "delete_count": delete_count,
            "uncertain_count": still_uncertain_count,
            "unique_senders": len(senders_data)
        }

    except HTTPException:
        raise
    except ImportError as e:
        logger.error(f"Failed to import LLM classifier: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LLM classifier not available. Please ensure OpenAI package is installed."
        )
    except Exception as e:
        logger.error(f"Error refining uncertain emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM refinement failed: {str(e)}"
        )


@router.post("/execute")
async def execute_cleanup(
    request: BulkScoreActionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Execute cleanup based on scores (delete emails marked DELETE).

    Args:
        request: Bulk action parameters
        db: Database session

    Returns:
        Summary of action results

    Raises:
        HTTPException: On errors
    """
    try:
        # Build query for emails to process
        stmt = select(EmailScore).where(EmailScore.classification == request.classification)

        # Apply filters
        filters = []
        if request.sender_emails:
            filters.append(EmailScore.sender_email.in_(request.sender_emails))
        if request.min_score is not None:
            filters.append(EmailScore.total_score >= request.min_score)
        if request.max_score is not None:
            filters.append(EmailScore.total_score <= request.max_score)

        if filters:
            stmt = stmt.where(and_(*filters))

        # Get matching emails
        result = await db.execute(stmt)
        emails = result.scalars().all()

        # Apply user overrides
        final_emails = [
            e for e in emails
            if (e.user_override == request.classification if e.user_override else e.classification == request.classification)
        ]

        logger.info(f"Executing cleanup for {len(final_emails)} emails with classification={request.classification}")

        # TODO: Implement actual Gmail deletion
        # For now, just return the count
        return {
            "action": request.classification,
            "total_matched": len(final_emails),
            "message": f"Would process {len(final_emails)} emails (implementation pending)"
        }

    except Exception as e:
        logger.error(f"Error executing cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup execution failed: {str(e)}"
        )
