"""
Cleanup runs router for managing email cleanup operations.
Handles creation, monitoring, and control of cleanup runs.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import CleanupAction, CleanupRun
from schemas import ActionResponse, RunCreate, RunResponse

router = APIRouter()
logger = logging.getLogger(__name__)


async def _create_run_impl(db: AsyncSession) -> RunResponse:
    """
    Internal implementation for creating a cleanup run.

    Args:
        db: Database session

    Returns:
        RunResponse: Created run with initial status

    Raises:
        HTTPException: If run creation fails
    """
    try:
        # Check if there's already an active run
        stmt = select(CleanupRun).where(
            CleanupRun.status.in_(["pending", "running", "paused"])
        )
        result = await db.execute(stmt)
        active_run = result.scalar_one_or_none()

        if active_run:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"An active run already exists (ID: {active_run.id}, Status: {active_run.status})",
            )

        # Create new run
        new_run = CleanupRun(
            status="pending",
            started_at=datetime.utcnow(),
        )
        db.add(new_run)
        await db.commit()
        await db.refresh(new_run)

        # Schedule the cleanup run to execute immediately
        from agent import schedule_cleanup_run
        try:
            job_id = await schedule_cleanup_run(new_run.id, delay_seconds=0)
            logger.info(f"Scheduled cleanup run {new_run.id} with job ID: {job_id}")
        except Exception as e:
            logger.error(f"Failed to schedule cleanup run {new_run.id}: {e}")
            # Don't fail the request - run is created, just not scheduled
            # User can manually trigger it later

        return RunResponse.model_validate(new_run)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create cleanup run: {str(e)}",
        )


@router.post("/start", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def start_run(
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Start a new cleanup run.

    Args:
        db: Database session

    Returns:
        RunResponse: Created run with initial status

    Raises:
        HTTPException: If run creation fails
    """
    return await _create_run_impl(db)


@router.post("", response_model=RunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    run_data: RunCreate,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Create a new cleanup run and schedule it for execution.

    Args:
        run_data: Run creation data (currently empty)
        db: Database session

    Returns:
        RunResponse: Created run with initial status

    Raises:
        HTTPException: If run creation fails
    """
    return await _create_run_impl(db)


@router.get("")
async def list_runs(
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of runs to return"),
    offset: int = Query(default=0, ge=0, description="Number of runs to skip"),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by status (pending, running, paused, completed, cancelled, failed)",
    ),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List cleanup runs with pagination and filtering.

    Args:
        limit: Maximum number of runs to return
        offset: Number of runs to skip
        status_filter: Optional status filter
        db: Database session

    Returns:
        dict: RunListResponse with runs, total, limit, offset

    Raises:
        HTTPException: If query fails
    """
    try:
        # Build query for counting total
        count_stmt = select(func.count(CleanupRun.id))

        # Build query for fetching runs
        stmt = select(CleanupRun)

        # Apply status filter if provided
        if status_filter:
            valid_statuses = ["pending", "running", "paused", "completed", "cancelled", "failed"]
            if status_filter not in valid_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter. Must be one of: {', '.join(valid_statuses)}",
                )
            stmt = stmt.where(CleanupRun.status == status_filter)
            count_stmt = count_stmt.where(CleanupRun.status == status_filter)

        # Get total count
        count_result = await db.execute(count_stmt)
        total = count_result.scalar()

        # Order by created_at descending
        stmt = stmt.order_by(desc(CleanupRun.created_at))

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        runs = result.scalars().all()

        # Return in the expected format
        return {
            "runs": [RunResponse.model_validate(run) for run in runs],
            "total": total,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list cleanup runs: {str(e)}",
        )


@router.get("/{run_id}", response_model=RunResponse)
async def get_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Get detailed information about a specific cleanup run.

    Args:
        run_id: ID of the run to retrieve
        db: Database session

    Returns:
        RunResponse: Detailed run information

    Raises:
        HTTPException: If run not found or query fails
    """
    try:
        stmt = select(CleanupRun).where(CleanupRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cleanup run with ID {run_id} not found",
            )

        return RunResponse.model_validate(run)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cleanup run: {str(e)}",
        )


@router.post("/{run_id}/pause", response_model=RunResponse)
async def pause_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Pause a running cleanup operation.

    Args:
        run_id: ID of the run to pause
        db: Database session

    Returns:
        RunResponse: Updated run information

    Raises:
        HTTPException: If run not found, not running, or update fails
    """
    try:
        stmt = select(CleanupRun).where(CleanupRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cleanup run with ID {run_id} not found",
            )

        if run.status != "running":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot pause run with status '{run.status}'. Only running runs can be paused.",
            )

        # Update status to paused
        run.status = "paused"
        await db.commit()
        await db.refresh(run)

        return RunResponse.model_validate(run)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to pause cleanup run: {str(e)}",
        )


@router.post("/{run_id}/resume", response_model=RunResponse)
async def resume_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Resume a paused cleanup operation.

    Args:
        run_id: ID of the run to resume
        db: Database session

    Returns:
        RunResponse: Updated run information

    Raises:
        HTTPException: If run not found, not paused, or update fails
    """
    try:
        stmt = select(CleanupRun).where(CleanupRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cleanup run with ID {run_id} not found",
            )

        if run.status != "paused":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot resume run with status '{run.status}'. Only paused runs can be resumed.",
            )

        # Update status to running
        run.status = "running"
        await db.commit()
        await db.refresh(run)

        # Schedule the run to resume immediately
        from agent import schedule_cleanup_run
        try:
            job_id = await schedule_cleanup_run(run.id, delay_seconds=0)
            logger.info(f"Scheduled resume for run {run.id} with job ID: {job_id}")
        except Exception as e:
            logger.error(f"Failed to schedule resume for run {run.id}: {e}")

        return RunResponse.model_validate(run)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resume cleanup run: {str(e)}",
        )


async def _cancel_run_impl(run_id: int, db: AsyncSession) -> RunResponse:
    """
    Internal implementation for cancelling a cleanup run.

    Args:
        run_id: ID of the run to cancel
        db: Database session

    Returns:
        RunResponse: Updated run information

    Raises:
        HTTPException: If run not found or update fails
    """
    try:
        stmt = select(CleanupRun).where(CleanupRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Cleanup run with ID {run_id} not found",
            )

        if run.status in ["completed", "cancelled"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot cancel run with status '{run.status}'",
            )

        # Update status to cancelled
        run.status = "cancelled"
        run.finished_at = datetime.utcnow()
        await db.commit()
        await db.refresh(run)

        return RunResponse.model_validate(run)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel cleanup run: {str(e)}",
        )


@router.post("/{run_id}/cancel", response_model=RunResponse)
async def cancel_run_post(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> RunResponse:
    """
    Cancel a cleanup run (POST method for compatibility).

    Args:
        run_id: ID of the run to cancel
        db: Database session

    Returns:
        RunResponse: Updated run information

    Raises:
        HTTPException: If run not found or update fails
    """
    return await _cancel_run_impl(run_id, db)


@router.delete("/{run_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_run(
    run_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Cancel a cleanup run (DELETE method).

    Args:
        run_id: ID of the run to cancel
        db: Database session

    Raises:
        HTTPException: If run not found or update fails
    """
    await _cancel_run_impl(run_id, db)


@router.get("/scheduler/status")
async def get_scheduler_status() -> dict:
    """
    Get the status of the background task scheduler.

    Returns:
        Dictionary with scheduler status information
    """
    from agent import get_scheduler_status
    return get_scheduler_status()


@router.get("/scheduler/jobs")
async def get_scheduler_jobs() -> dict:
    """
    Get list of currently scheduled jobs.

    Returns:
        Dictionary with job information
    """
    from agent import get_running_jobs
    jobs = await get_running_jobs()
    return {"jobs": jobs, "count": len(jobs)}


@router.get("/{run_id}/actions", response_model=List[ActionResponse])
async def get_run_actions(
    run_id: int,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of actions to return"),
    offset: int = Query(default=0, ge=0, description="Number of actions to skip"),
    db: AsyncSession = Depends(get_db),
) -> List[ActionResponse]:
    """
    Get cleanup actions for a specific run.

    Args:
        run_id: ID of the run
        limit: Maximum number of actions to return
        offset: Number of actions to skip
        db: Database session

    Returns:
        List[ActionResponse]: List of cleanup actions

    Raises:
        HTTPException: If run not found or query fails
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

        # Query actions
        stmt = (
            select(CleanupAction)
            .where(CleanupAction.run_id == run_id)
            .order_by(desc(CleanupAction.timestamp))
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        actions = result.scalars().all()

        return [ActionResponse.model_validate(action) for action in actions]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get cleanup actions: {str(e)}",
        )
