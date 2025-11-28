"""
Export router for generating CSV exports of cleanup data.
Provides endpoints for exporting run data and sender information.
"""

import csv
import io
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import CleanupAction, CleanupRun, Sender

router = APIRouter()


@router.get("/runs/{run_id}/csv")
async def export_run_csv(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Generate CSV export of cleanup run data.

    Exports all actions from a specific cleanup run with the following columns:
    - action_type: Type of action (unsubscribe, delete, filter, skip, error)
    - sender_email: Email address of the sender
    - email_count: Number of emails affected
    - bytes_freed: Estimated bytes freed
    - timestamp: When the action occurred
    - notes: Additional notes or details

    Args:
        run_id: ID of the run to export
        db: Database session

    Returns:
        StreamingResponse: CSV file download

    Raises:
        HTTPException: If run not found or export fails
    """
    try:
        # Verify run exists
        stmt = select(CleanupRun).where(CleanupRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cleanup run with ID {run_id} not found",
            )

        # Query all actions for this run
        actions_stmt = (
            select(CleanupAction)
            .where(CleanupAction.run_id == run_id)
            .order_by(CleanupAction.timestamp)
        )
        actions_result = await db.execute(actions_stmt)
        actions = actions_result.scalars().all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "action_type",
            "sender_email",
            "email_count",
            "bytes_freed",
            "timestamp",
            "notes",
        ])

        # Write data rows
        for action in actions:
            writer.writerow([
                action.action_type,
                action.sender_email or "",
                action.email_count,
                action.bytes_freed,
                action.timestamp.isoformat(),
                action.notes or "",
            ])

        # Prepare response
        output.seek(0)
        filename = f"cleanup_run_{run_id}_{run.started_at.strftime('%Y%m%d')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export run data: {str(e)}",
        )


@router.get("/senders/csv")
async def export_senders_csv(
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    """
    Export all discovered senders to CSV.

    Exports all sender information with the following columns:
    - email: Sender email address
    - domain: Domain portion of email
    - message_count: Number of messages from this sender
    - unsubscribed: Whether unsubscribed (True/False)
    - filter_created: Whether a filter was created (True/False)
    - last_seen: Date when last email was received
    - display_name: Display name if available
    - has_list_unsubscribe: Whether sender provides List-Unsubscribe header

    Args:
        db: Database session

    Returns:
        StreamingResponse: CSV file download

    Raises:
        HTTPException: If export fails
    """
    try:
        # Query all senders ordered by message count
        stmt = select(Sender).order_by(desc(Sender.message_count))
        result = await db.execute(stmt)
        senders = result.scalars().all()

        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header
        writer.writerow([
            "email",
            "domain",
            "message_count",
            "unsubscribed",
            "filter_created",
            "last_seen",
            "display_name",
            "has_list_unsubscribe",
        ])

        # Write data rows
        for sender in senders:
            writer.writerow([
                sender.email,
                sender.domain,
                sender.message_count,
                sender.unsubscribed,
                sender.filter_created,
                sender.last_seen_at.isoformat(),
                sender.display_name or "",
                sender.has_list_unsubscribe,
            ])

        # Prepare response
        output.seek(0)
        from datetime import datetime
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"inbox_nuke_senders_{timestamp}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export senders: {str(e)}",
        )
