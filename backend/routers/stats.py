"""
Statistics router for overall system metrics.
Provides endpoint for retrieving aggregated statistics.
"""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import CleanupRun, GmailCredentials, Sender
from utils.encryption import decrypt_token

router = APIRouter()


@router.get("/current")
async def get_current_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get overall system statistics.

    Args:
        db: Database session

    Returns:
        dict: Aggregated statistics including:
            - total_runs: Total number of cleanup runs
            - total_senders: Total number of discovered senders
            - total_emails_deleted: Total emails deleted across all runs
            - total_bytes_freed: Total bytes freed across all runs
            - active_run: Information about current active run (if any)
            - gmail_connected: Whether Gmail is connected
            - gmail_email: Connected Gmail account email
            - last_run: Information about the most recent run

    Raises:
        HTTPException: If query fails
    """
    try:
        # Total runs
        total_runs_stmt = select(func.count(CleanupRun.id))
        total_runs_result = await db.execute(total_runs_stmt)
        total_runs = total_runs_result.scalar() or 0

        # Total senders
        total_senders_stmt = select(func.count(Sender.id))
        total_senders_result = await db.execute(total_senders_stmt)
        total_senders = total_senders_result.scalar() or 0

        # Total emails deleted (sum across all runs)
        total_emails_stmt = select(func.sum(CleanupRun.emails_deleted))
        total_emails_result = await db.execute(total_emails_stmt)
        total_emails_deleted = total_emails_result.scalar() or 0

        # Total bytes freed (sum across all runs)
        total_bytes_stmt = select(func.sum(CleanupRun.bytes_freed_estimate))
        total_bytes_result = await db.execute(total_bytes_stmt)
        total_bytes_freed = total_bytes_result.scalar() or 0

        # Active run (pending, running, or paused)
        active_run_stmt = (
            select(CleanupRun)
            .where(CleanupRun.status.in_(["pending", "running", "paused"]))
            .order_by(desc(CleanupRun.created_at))
        )
        active_run_result = await db.execute(active_run_stmt)
        active_run = active_run_result.scalar_one_or_none()

        active_run_info = None
        if active_run:
            active_run_info = {
                "id": active_run.id,
                "status": active_run.status,
                "started_at": active_run.started_at.isoformat(),
                "senders_total": active_run.senders_total,
                "senders_processed": active_run.senders_processed,
                "emails_deleted": active_run.emails_deleted,
                "bytes_freed_estimate": active_run.bytes_freed_estimate,
            }

        # Last run (most recent completed or failed run)
        last_run_stmt = (
            select(CleanupRun)
            .where(CleanupRun.status.in_(["completed", "failed", "cancelled"]))
            .order_by(desc(CleanupRun.finished_at))
            .limit(1)
        )
        last_run_result = await db.execute(last_run_stmt)
        last_run = last_run_result.scalar_one_or_none()

        last_run_info = None
        if last_run:
            last_run_info = {
                "id": last_run.id,
                "status": last_run.status,
                "started_at": last_run.started_at.isoformat(),
                "finished_at": last_run.finished_at.isoformat() if last_run.finished_at else None,
                "emails_deleted": last_run.emails_deleted,
                "bytes_freed_estimate": last_run.bytes_freed_estimate,
            }

        # Gmail connection status
        gmail_connected = False
        gmail_email = None
        token_expires_at = None

        creds_stmt = select(GmailCredentials).where(
            GmailCredentials.user_id == "default_user"
        )
        creds_result = await db.execute(creds_stmt)
        creds = creds_result.scalar_one_or_none()

        if creds:
            try:
                # Try to decrypt token to verify it's valid
                decrypt_token(creds.access_token)
                gmail_connected = True
                token_expires_at = creds.token_expiry.isoformat() if creds.token_expiry else None

                # Get email from token scopes (stored in scopes field)
                # Note: We don't make an API call here to keep stats endpoint fast
                # Email is returned in the auth status endpoint
            except Exception:
                # Token decryption failed, credentials invalid
                gmail_connected = False

        # Completed runs count
        completed_runs_stmt = select(func.count(CleanupRun.id)).where(
            CleanupRun.status == "completed"
        )
        completed_runs_result = await db.execute(completed_runs_stmt)
        completed_runs = completed_runs_result.scalar() or 0

        # Failed runs count
        failed_runs_stmt = select(func.count(CleanupRun.id)).where(
            CleanupRun.status == "failed"
        )
        failed_runs_result = await db.execute(failed_runs_stmt)
        failed_runs = failed_runs_result.scalar() or 0

        # Unsubscribed senders count
        unsubscribed_senders_stmt = select(func.count(Sender.id)).where(
            Sender.unsubscribed == True
        )
        unsubscribed_result = await db.execute(unsubscribed_senders_stmt)
        unsubscribed_senders = unsubscribed_result.scalar() or 0

        # Senders with filters count
        filtered_senders_stmt = select(func.count(Sender.id)).where(
            Sender.filter_created == True
        )
        filtered_result = await db.execute(filtered_senders_stmt)
        filtered_senders = filtered_result.scalar() or 0

        return {
            "total_runs": total_runs,
            "completed_runs": completed_runs,
            "failed_runs": failed_runs,
            "total_senders": total_senders,
            "unsubscribed_senders": unsubscribed_senders,
            "filtered_senders": filtered_senders,
            "total_emails_deleted": total_emails_deleted,
            "total_bytes_freed": total_bytes_freed,
            "active_run": active_run_info,
            "last_run": last_run_info,
            "gmail_connected": gmail_connected,
            "gmail_email": gmail_email,
            "token_expires_at": token_expires_at,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )
