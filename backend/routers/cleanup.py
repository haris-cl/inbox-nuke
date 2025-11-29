"""
V2 Cleanup Router - API endpoints for cleanup wizard flow.
"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from gmail_client import GmailClient
from models import GmailCredentials
from schemas import (
    CleanupStartRequest,
    CleanupStartResponse,
    CleanupProgressResponse,
    RecommendationSummary,
    ModeSelectRequest,
    ReviewQueueResponse,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    ConfirmationSummary,
    CleanupExecuteResponse,
    CleanupResults,
    InboxHealthResponse,
    AutoProtectedResponse,
    ProtectedCategory,
    UnsubscribableSender,
    UnsubscribeSendersResponse,
    UpdateUnsubscribeSelectionsRequest,
    UpdateUnsubscribeSelectionsResponse,
    ActiveSessionResponse,
    SessionListItem,
    SessionListResponse,
)
from services import CleanupFlowService, RecommendationEngine, CleanupExecutor


router = APIRouter()


async def get_gmail_client(db: AsyncSession) -> Optional[GmailClient]:
    """Get an authenticated Gmail client if credentials exist."""
    from sqlalchemy import select
    result = await db.execute(select(GmailCredentials).limit(1))
    creds = result.scalar_one_or_none()

    if not creds:
        return None

    try:
        # Use the same pattern as other routers - GmailClient handles auth internally
        client = GmailClient(db=db, credentials=creds)
        return client
    except Exception as e:
        print(f"Error creating Gmail client: {e}")
        return None


async def run_scan_in_background(session_id: str, max_emails: int):
    """Background task to run email scanning."""
    from db import AsyncSessionLocal
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            gmail_client = await get_gmail_client(db)
            if not gmail_client:
                flow_service = CleanupFlowService(db)
                await flow_service.set_error(session_id, "Gmail not connected")
                return

            flow_service = CleanupFlowService(db)
            rec_engine = RecommendationEngine(db)

            # Fetch emails from Gmail
            messages = await gmail_client.list_messages(max_results=max_emails)

            total_emails = len(messages)
            discoveries = {
                "promotions": 0,
                "newsletters": 0,
                "social": 0,
                "updates": 0,
                "low_value": 0,
            }

            # Update initial total
            session = await flow_service.get_session(session_id)
            if session:
                session.total_emails = total_emails
                await db.commit()

            batch_size = 50
            scanned = 0
            recommendations = []

            for i, msg in enumerate(messages):
                try:
                    # Get full message details
                    full_msg = await gmail_client.get_message(msg["id"])

                    # Extract headers
                    headers = {h["name"]: h["value"] for h in full_msg.get("payload", {}).get("headers", [])}
                    sender_email = headers.get("From", "")
                    sender_name = None

                    # Parse sender
                    if "<" in sender_email:
                        parts = sender_email.split("<")
                        sender_name = parts[0].strip().strip('"')
                        sender_email = parts[1].rstrip(">")

                    subject = headers.get("Subject", "(no subject)")
                    date_str = headers.get("Date", "")

                    # Parse date
                    try:
                        received_date = datetime.utcnow()  # Fallback
                    except Exception:
                        received_date = datetime.utcnow()

                    # Get labels and size
                    gmail_labels = full_msg.get("labelIds", [])
                    size_bytes = int(full_msg.get("sizeEstimate", 0))
                    snippet = full_msg.get("snippet", "")

                    # Parse List-Unsubscribe headers (RFC 8058)
                    raw_headers = full_msg.get("payload", {}).get("headers", [])
                    unsubscribe_info = GmailClient.parse_list_unsubscribe_header(raw_headers)
                    has_unsubscribe = bool(unsubscribe_info.get("url") or unsubscribe_info.get("mailto"))
                    unsubscribe_url = unsubscribe_info.get("url")
                    unsubscribe_mailto = unsubscribe_info.get("mailto")
                    unsubscribe_one_click = unsubscribe_info.get("one_click", False)

                    # Generate recommendation
                    rec = await rec_engine.analyze_email(
                        session_id=session_id,
                        message_id=msg["id"],
                        thread_id=full_msg.get("threadId", msg["id"]),
                        sender_email=sender_email,
                        sender_name=sender_name,
                        subject=subject,
                        snippet=snippet,
                        received_date=received_date,
                        size_bytes=size_bytes,
                        gmail_labels=gmail_labels,
                        has_unsubscribe=has_unsubscribe,
                        unsubscribe_url=unsubscribe_url,
                        unsubscribe_mailto=unsubscribe_mailto,
                        unsubscribe_one_click=unsubscribe_one_click,
                    )
                    recommendations.append(rec)

                    # Update discoveries based on category
                    if rec.category in discoveries:
                        discoveries[rec.category] += 1

                    scanned += 1

                    # Save batch and update progress
                    if len(recommendations) >= batch_size:
                        await rec_engine.batch_save_recommendations(recommendations)
                        recommendations = []
                        await flow_service.update_progress(session_id, scanned, discoveries)

                except Exception as e:
                    print(f"Error processing message {msg.get('id')}: {e}")
                    continue

            # Save remaining recommendations
            if recommendations:
                await rec_engine.batch_save_recommendations(recommendations)

            # Update final progress
            await flow_service.update_progress(session_id, scanned, discoveries, status="ready_for_review")

        except Exception as e:
            print(f"Scan error: {e}")
            from db import AsyncSessionLocal
            async with AsyncSessionLocal() as db2:
                flow_service = CleanupFlowService(db2)
                await flow_service.set_error(session_id, str(e))


@router.get("/active", response_model=ActiveSessionResponse)
async def get_active_session(db: AsyncSession = Depends(get_db)):
    """
    Check for any active/incomplete cleanup sessions.
    Returns session info if one exists, allowing user to resume.
    """
    from sqlalchemy import select
    from models import CleanupSession

    # Look for sessions that aren't completed or failed (within last 24 hours)
    incomplete_statuses = ["scanning", "ready_for_review", "reviewing", "confirming"]

    stmt = (
        select(CleanupSession)
        .where(CleanupSession.status.in_(incomplete_statuses))
        .order_by(CleanupSession.created_at.desc())
        .limit(1)
    )

    result = await db.execute(stmt)
    session = result.scalar_one_or_none()

    if not session:
        return ActiveSessionResponse(has_active_session=False)

    # Determine which step to resume at based on status
    resume_step_map = {
        "scanning": "scanning",
        "ready_for_review": "report",
        "reviewing": "review",
        "confirming": "confirm",
    }
    resume_step = resume_step_map.get(session.status, "report")

    # If mode is set and status is reviewing, check if review is complete
    if session.status == "reviewing" and session.mode:
        resume_step = "review"

    progress = 0.0
    if session.total_emails > 0:
        progress = min(1.0, session.scanned_emails / session.total_emails)

    return ActiveSessionResponse(
        has_active_session=True,
        session_id=session.session_id,
        status=session.status,
        mode=session.mode,
        progress=progress,
        total_emails=session.total_emails,
        scanned_emails=session.scanned_emails,
        total_to_cleanup=session.total_to_cleanup,
        total_protected=session.total_protected,
        created_at=session.created_at,
        resume_step=resume_step,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    limit: int = 20,
    include_completed: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    List all cleanup sessions, showing which ones can still have actions taken.
    """
    from sqlalchemy import select, func
    from models import CleanupSession, EmailRecommendation

    # Build query for sessions
    stmt = select(CleanupSession).order_by(CleanupSession.created_at.desc())

    if not include_completed:
        # Only show sessions that haven't fully completed execution
        stmt = stmt.where(CleanupSession.status != "completed")

    # Exclude abandoned sessions
    stmt = stmt.where(CleanupSession.status != "abandoned")
    stmt = stmt.limit(limit)

    result = await db.execute(stmt)
    sessions = result.scalars().all()

    # For each session, check if it has actionable items
    session_items = []
    for session in sessions:
        # A session can have actions taken if:
        # 1. Scan completed (status is ready_for_review or later)
        # 2. Has recommendations that haven't been acted on
        can_take_action = False

        if session.status in ["ready_for_review", "reviewing", "confirming"]:
            # Check if there are recommendations pending action
            pending_query = await db.execute(
                select(func.count(EmailRecommendation.id))
                .where(EmailRecommendation.session_id == session.session_id)
                .where(EmailRecommendation.ai_suggestion == "delete")
            )
            pending_count = pending_query.scalar() or 0
            can_take_action = pending_count > 0

        session_items.append(
            SessionListItem(
                session_id=session.session_id,
                status=session.status,
                mode=session.mode,
                total_emails=session.total_emails,
                scanned_emails=session.scanned_emails,
                total_to_cleanup=session.total_to_cleanup,
                total_protected=session.total_protected,
                emails_deleted=session.emails_deleted,
                space_freed=session.space_freed,
                senders_unsubscribed=session.senders_unsubscribed,
                created_at=session.created_at,
                completed_at=session.completed_at,
                can_take_action=can_take_action,
            )
        )

    # Get total count
    total_query = await db.execute(
        select(func.count(CleanupSession.id)).where(CleanupSession.status != "abandoned")
    )
    total = total_query.scalar() or 0

    return SessionListResponse(sessions=session_items, total=total)


@router.post("/reopen/{session_id}")
async def reopen_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Reopen a completed scan session to take actions on it.
    Resets status to ready_for_review so user can go through the wizard.
    """
    from sqlalchemy import select
    from models import CleanupSession

    result = await db.execute(
        select(CleanupSession).where(CleanupSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Can only reopen sessions that completed scanning
    if session.status == "scanning":
        raise HTTPException(status_code=400, detail="Session is still scanning")

    if session.status == "abandoned":
        raise HTTPException(status_code=400, detail="Session was abandoned")

    # Reset to ready_for_review state
    session.status = "ready_for_review"
    session.mode = None  # Let user pick mode again
    await db.commit()

    return {
        "status": "ok",
        "session_id": session_id,
        "message": "Session reopened",
    }


@router.post("/abandon/{session_id}")
async def abandon_session(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Abandon/discard an incomplete session so user can start fresh.
    """
    from sqlalchemy import select
    from models import CleanupSession

    result = await db.execute(
        select(CleanupSession).where(CleanupSession.session_id == session_id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Mark as abandoned (or delete it)
    session.status = "abandoned"
    await db.commit()

    return {"status": "ok", "message": "Session abandoned"}


@router.post("/start", response_model=CleanupStartResponse)
async def start_cleanup(
    request: CleanupStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Start a new V2 cleanup wizard session.
    Returns session_id and begins scanning in the background.
    """
    flow_service = CleanupFlowService(db)
    session_id = await flow_service.create_session(max_emails=request.max_emails)

    # Start scanning in background
    background_tasks.add_task(run_scan_in_background, session_id, request.max_emails)

    return CleanupStartResponse(session_id=session_id, status="scanning")


@router.get("/progress/{session_id}", response_model=CleanupProgressResponse)
async def get_progress(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get the current progress of a cleanup session."""
    flow_service = CleanupFlowService(db)
    try:
        return await flow_service.get_progress(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/recommendations/{session_id}", response_model=RecommendationSummary)
async def get_recommendations(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get the recommendation summary for the Inbox Report screen."""
    flow_service = CleanupFlowService(db)
    try:
        return await flow_service.get_recommendations(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/mode/{session_id}")
async def set_mode(
    session_id: str, request: ModeSelectRequest, db: AsyncSession = Depends(get_db)
):
    """Set the cleanup mode (quick/full) for a session."""
    flow_service = CleanupFlowService(db)
    try:
        await flow_service.set_mode(session_id, request.mode)
        return {"status": "ok", "mode": request.mode}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/review-queue/{session_id}", response_model=ReviewQueueResponse)
async def get_review_queue(
    session_id: str,
    mode: str = "quick",
    db: AsyncSession = Depends(get_db),
):
    """Get the review queue for user review."""
    flow_service = CleanupFlowService(db)
    try:
        return await flow_service.get_review_queue(session_id, mode)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/review-decision/{session_id}", response_model=ReviewDecisionResponse)
async def submit_review_decision(
    session_id: str,
    request: ReviewDecisionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Submit a review decision (keep/delete) for an email."""
    flow_service = CleanupFlowService(db)
    try:
        remaining = await flow_service.record_decision(
            session_id, request.message_id, request.decision
        )
        return ReviewDecisionResponse(
            message_id=request.message_id,
            decision=request.decision,
            remaining_in_queue=remaining,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/skip-all/{session_id}")
async def skip_all_remaining(session_id: str, db: AsyncSession = Depends(get_db)):
    """Trust AI for all remaining unreviewed items."""
    flow_service = CleanupFlowService(db)
    try:
        await flow_service.skip_all_remaining(session_id)
        return {"status": "ok"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Unsubscribe Management Endpoints
# ============================================================================


@router.get("/unsubscribe-senders/{session_id}", response_model=UnsubscribeSendersResponse)
async def get_unsubscribe_senders(session_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get list of senders that can be unsubscribed from.
    Groups emails by sender and shows unsubscribe method available.
    """
    from sqlalchemy import select, func
    from models import EmailRecommendation

    # Get unique senders with unsubscribe capability
    stmt = (
        select(
            EmailRecommendation.sender_email,
            EmailRecommendation.sender_name,
            func.count(EmailRecommendation.id).label("email_count"),
            func.max(EmailRecommendation.unsubscribe_one_click).label("has_one_click"),
            func.max(EmailRecommendation.unsubscribe_url).label("unsubscribe_url"),
            func.max(EmailRecommendation.unsubscribe_mailto).label("unsubscribe_mailto"),
            func.max(EmailRecommendation.user_wants_unsubscribe).label("selected"),
        )
        .where(
            EmailRecommendation.session_id == session_id,
            EmailRecommendation.has_unsubscribe == True,
            EmailRecommendation.ai_suggestion == "delete",  # Only show for emails marked for deletion
        )
        .group_by(EmailRecommendation.sender_email)
        .order_by(func.count(EmailRecommendation.id).desc())
    )

    result = await db.execute(stmt)
    rows = result.all()

    senders = []
    for row in rows:
        # Determine best unsubscribe method
        if row.has_one_click and row.unsubscribe_url:
            method = "one_click"
        elif row.unsubscribe_url:
            method = "http"
        elif row.unsubscribe_mailto:
            method = "mailto"
        else:
            method = "unknown"

        senders.append(
            UnsubscribableSender(
                email=row.sender_email,
                display_name=row.sender_name,
                email_count=row.email_count,
                has_one_click=bool(row.has_one_click),
                unsubscribe_method=method,
                selected=bool(row.selected),
            )
        )

    return UnsubscribeSendersResponse(
        session_id=session_id,
        senders=senders,
        total_count=len(senders),
    )


@router.post("/unsubscribe-selections/{session_id}", response_model=UpdateUnsubscribeSelectionsResponse)
async def update_unsubscribe_selections(
    session_id: str,
    request: UpdateUnsubscribeSelectionsRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Update which senders the user wants to unsubscribe from.
    """
    from sqlalchemy import update
    from models import EmailRecommendation

    # First, clear all selections for this session
    await db.execute(
        update(EmailRecommendation)
        .where(EmailRecommendation.session_id == session_id)
        .values(user_wants_unsubscribe=False)
    )

    # Then set selections for specified senders
    if request.sender_emails:
        await db.execute(
            update(EmailRecommendation)
            .where(
                EmailRecommendation.session_id == session_id,
                EmailRecommendation.sender_email.in_(request.sender_emails),
                EmailRecommendation.has_unsubscribe == True,
            )
            .values(user_wants_unsubscribe=True)
        )

    await db.commit()

    return UpdateUnsubscribeSelectionsResponse(
        session_id=session_id,
        selected_count=len(request.sender_emails),
    )


@router.get("/confirmation/{session_id}", response_model=ConfirmationSummary)
async def get_confirmation(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get the confirmation summary before executing cleanup."""
    flow_service = CleanupFlowService(db)
    try:
        return await flow_service.get_confirmation_summary(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


async def run_cleanup_in_background(session_id: str):
    """Background task to execute cleanup."""
    from db import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        try:
            gmail_client = await get_gmail_client(db)
            executor = CleanupExecutor(db, gmail_client)
            await executor.execute_cleanup(session_id)
        except Exception as e:
            print(f"Cleanup execution error: {e}")
            flow_service = CleanupFlowService(db)
            await flow_service.set_error(session_id, str(e))


@router.post("/execute/{session_id}", response_model=CleanupExecuteResponse)
async def execute_cleanup(
    session_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Execute the cleanup (move emails to trash, unsubscribe, etc.)."""
    flow_service = CleanupFlowService(db)
    session = await flow_service.get_session(session_id)

    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Update status
    session.status = "executing"
    await db.commit()

    # Start execution in background
    background_tasks.add_task(run_cleanup_in_background, session_id)

    return CleanupExecuteResponse(
        session_id=session_id, status="executing", job_id=session_id
    )


@router.get("/results/{session_id}", response_model=CleanupResults)
async def get_results(session_id: str, db: AsyncSession = Depends(get_db)):
    """Get the results of a completed cleanup."""
    flow_service = CleanupFlowService(db)
    try:
        return await flow_service.get_results(session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ============================================================================
# Inbox Health Endpoints
# ============================================================================


@router.get("/inbox-health", response_model=InboxHealthResponse)
async def get_inbox_health(db: AsyncSession = Depends(get_db)):
    """
    Get inbox health status for the dashboard.
    Uses cached data if available, otherwise returns estimates.
    """
    gmail_client = await get_gmail_client(db)

    if not gmail_client:
        return InboxHealthResponse(
            status="unknown",
            potential_cleanup_count=0,
            potential_space_savings=0,
            last_scan_at=None,
            categories={},
        )

    try:
        # Quick estimate using Gmail search queries
        promo_count = await gmail_client.count_messages("category:promotions")
        social_count = await gmail_client.count_messages("category:social")
        updates_count = await gmail_client.count_messages("category:updates")

        total_potential = promo_count + social_count + updates_count

        # Estimate space (assume 50KB average per email)
        estimated_space = total_potential * 50 * 1024

        # Determine health status
        if total_potential > 5000:
            status = "critical"
        elif total_potential > 1000:
            status = "needs_attention"
        else:
            status = "healthy"

        return InboxHealthResponse(
            status=status,
            potential_cleanup_count=total_potential,
            potential_space_savings=estimated_space,
            last_scan_at=None,
            categories={
                "promotions": promo_count,
                "social": social_count,
                "updates": updates_count,
            },
        )

    except Exception as e:
        print(f"Inbox health check error: {e}")
        return InboxHealthResponse(
            status="error",
            potential_cleanup_count=0,
            potential_space_savings=0,
            last_scan_at=None,
            categories={},
        )


@router.get("/auto-protected", response_model=AutoProtectedResponse)
async def get_auto_protected():
    """Get the list of auto-protected categories."""
    return AutoProtectedResponse(
        categories=[
            ProtectedCategory(
                name="People you email with",
                description="Emails from people you've replied to or sent emails to",
                icon="users",
            ),
            ProtectedCategory(
                name="Your contacts",
                description="Emails from senders in your Google Contacts",
                icon="contact",
            ),
            ProtectedCategory(
                name="Financial institutions",
                description="Banks, credit cards, payment services, and investments",
                icon="building-bank",
            ),
            ProtectedCategory(
                name="Security emails",
                description="Password resets, verification codes, and security alerts",
                icon="shield-check",
            ),
            ProtectedCategory(
                name="Government",
                description="Emails from .gov and .mil domains",
                icon="landmark",
            ),
        ]
    )
