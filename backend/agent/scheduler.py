"""
Background task scheduler for Inbox Nuke cleanup runs.

Uses APScheduler to manage background cleanup jobs with:
- Job scheduling and execution
- Job status tracking
- Graceful shutdown
- Error handling and logging
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlalchemy import select

from db import AsyncSessionLocal
from models import CleanupRun
from agent.runner import CleanupAgent

logger = logging.getLogger(__name__)


# ============================================================================
# Scheduler Configuration
# ============================================================================

# Job stores configuration
jobstores = {
    'default': MemoryJobStore()
}

# Executors configuration
executors = {
    'default': AsyncIOExecutor()
}

# Job defaults
job_defaults = {
    'coalesce': False,  # Don't combine missed executions
    'max_instances': 1,  # Only one instance per job
    'misfire_grace_time': 60  # 60 seconds grace time for misfires
}

# Initialize scheduler (singleton)
_scheduler: Optional[AsyncIOScheduler] = None


# ============================================================================
# Scheduler Lifecycle Management
# ============================================================================


def init_scheduler() -> AsyncIOScheduler:
    """
    Initialize and start the background task scheduler.

    Creates a singleton AsyncIOScheduler instance with memory-based
    job storage and async execution.

    Returns:
        AsyncIOScheduler: Initialized and running scheduler instance

    Example:
        >>> scheduler = init_scheduler()
        >>> print(scheduler.running)
        True
    """
    global _scheduler

    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler already initialized and running")
        return _scheduler

    logger.info("Initializing APScheduler...")

    # Create scheduler
    _scheduler = AsyncIOScheduler(
        jobstores=jobstores,
        executors=executors,
        job_defaults=job_defaults,
        timezone='UTC'
    )

    # Add event listeners
    _scheduler.add_listener(
        _job_executed_listener,
        EVENT_JOB_EXECUTED
    )

    _scheduler.add_listener(
        _job_error_listener,
        EVENT_JOB_ERROR
    )

    # Start scheduler
    _scheduler.start()

    logger.info("APScheduler started successfully")
    return _scheduler


def shutdown_scheduler() -> None:
    """
    Gracefully shutdown the scheduler.

    Waits for all running jobs to complete before shutting down.

    Example:
        >>> shutdown_scheduler()
        # All jobs will complete before shutdown
    """
    global _scheduler

    if _scheduler is None:
        logger.warning("Scheduler not initialized, nothing to shutdown")
        return

    if not _scheduler.running:
        logger.warning("Scheduler already stopped")
        return

    logger.info("Shutting down APScheduler...")

    # Wait for jobs to complete
    _scheduler.shutdown(wait=True)

    logger.info("APScheduler shutdown complete")
    _scheduler = None


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """
    Get the current scheduler instance.

    Returns:
        Optional[AsyncIOScheduler]: Scheduler instance or None if not initialized
    """
    return _scheduler


# ============================================================================
# Job Management
# ============================================================================


async def schedule_cleanup_run(run_id: int, delay_seconds: int = 0) -> str:
    """
    Schedule a new cleanup run job.

    Creates a background job that will execute the cleanup run.
    The job can start immediately or after a specified delay.

    Args:
        run_id: ID of the cleanup run to execute
        delay_seconds: Delay in seconds before starting (default: 0 for immediate)

    Returns:
        str: Job ID that can be used to track or cancel the job

    Raises:
        RuntimeError: If scheduler not initialized
        ValueError: If run_id is invalid

    Example:
        >>> job_id = await schedule_cleanup_run(run_id=123)
        >>> print(f"Job scheduled with ID: {job_id}")
        Job scheduled with ID: cleanup_run_123
    """
    if _scheduler is None or not _scheduler.running:
        raise RuntimeError("Scheduler not initialized. Call init_scheduler() first.")

    # Validate run exists
    async with AsyncSessionLocal() as db:
        stmt = select(CleanupRun).where(CleanupRun.id == run_id)
        result = await db.execute(stmt)
        run = result.scalar_one_or_none()

        if not run:
            raise ValueError(f"Cleanup run with ID {run_id} not found")

        if run.status not in ["pending", "paused"]:
            raise ValueError(
                f"Cannot schedule run with status '{run.status}'. "
                "Only pending or paused runs can be scheduled."
            )

    # Generate job ID
    job_id = f"cleanup_run_{run_id}"

    # Calculate run time
    if delay_seconds > 0:
        run_date = datetime.utcnow().replace(microsecond=0)
        from datetime import timedelta
        run_date += timedelta(seconds=delay_seconds)
    else:
        run_date = None  # Run immediately

    # Schedule job
    _scheduler.add_job(
        _run_cleanup_job,
        'date',  # Run once at specified date
        run_date=run_date,
        args=[run_id],
        id=job_id,
        name=f"Cleanup Run {run_id}",
        replace_existing=True
    )

    logger.info(
        f"Scheduled cleanup run {run_id} "
        f"({'immediate' if delay_seconds == 0 else f'in {delay_seconds}s'})"
    )

    return job_id


async def get_running_jobs() -> List[Dict]:
    """
    Get list of all running cleanup jobs.

    Returns:
        List of dictionaries with job information:
        - job_id: str
        - run_id: int
        - name: str
        - next_run_time: datetime or None
        - pending: bool

    Example:
        >>> jobs = await get_running_jobs()
        >>> for job in jobs:
        ...     print(f"Job {job['job_id']}: Run {job['run_id']}")
    """
    if _scheduler is None:
        return []

    jobs = []
    for job in _scheduler.get_jobs():
        # Extract run_id from job_id (format: cleanup_run_{run_id})
        try:
            run_id = int(job.id.replace("cleanup_run_", ""))
        except ValueError:
            run_id = None

        jobs.append({
            "job_id": job.id,
            "run_id": run_id,
            "name": job.name,
            "next_run_time": job.next_run_time,
            "pending": job.pending
        })

    return jobs


async def cancel_job(job_id: str) -> bool:
    """
    Cancel a scheduled or running job.

    Note: This removes the job from the scheduler but does not
    immediately stop a running job. The job will complete its
    current operation and then check for cancellation.

    Args:
        job_id: Job ID to cancel

    Returns:
        bool: True if job was cancelled, False if job not found

    Example:
        >>> success = await cancel_job("cleanup_run_123")
        >>> print("Job cancelled" if success else "Job not found")
    """
    if _scheduler is None:
        return False

    try:
        _scheduler.remove_job(job_id)
        logger.info(f"Cancelled job {job_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to cancel job {job_id}: {e}")
        return False


async def pause_job(job_id: str) -> bool:
    """
    Pause a scheduled job.

    The job will remain in the scheduler but won't execute until resumed.

    Args:
        job_id: Job ID to pause

    Returns:
        bool: True if job was paused, False if job not found

    Example:
        >>> success = await pause_job("cleanup_run_123")
    """
    if _scheduler is None:
        return False

    try:
        _scheduler.pause_job(job_id)
        logger.info(f"Paused job {job_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to pause job {job_id}: {e}")
        return False


async def resume_job(job_id: str) -> bool:
    """
    Resume a paused job.

    Args:
        job_id: Job ID to resume

    Returns:
        bool: True if job was resumed, False if job not found

    Example:
        >>> success = await resume_job("cleanup_run_123")
    """
    if _scheduler is None:
        return False

    try:
        _scheduler.resume_job(job_id)
        logger.info(f"Resumed job {job_id}")
        return True
    except Exception as e:
        logger.warning(f"Failed to resume job {job_id}: {e}")
        return False


# ============================================================================
# Internal Job Execution
# ============================================================================


async def _run_cleanup_job(run_id: int) -> None:
    """
    Internal function to execute a cleanup run job.

    Creates a database session, initializes the CleanupAgent,
    and runs the cleanup workflow. Handles errors and updates
    run status accordingly.

    Args:
        run_id: ID of the cleanup run to execute
    """
    logger.info(f"Starting cleanup job for run {run_id}")

    async with AsyncSessionLocal() as db:
        agent = None
        try:
            # Initialize agent
            agent = CleanupAgent(db=db, run_id=run_id)
            await agent.initialize()

            # Check if run should be resumed
            if agent.run.status == "paused":
                logger.info(f"Resuming paused run {run_id}")
                await agent.resume()
            else:
                # Run cleanup
                await agent.run_cleanup()

            logger.info(
                f"Cleanup job completed for run {run_id}. "
                f"Status: {agent.run.status}, "
                f"Processed: {agent.run.senders_processed}/{agent.run.senders_total}"
            )

        except Exception as e:
            logger.error(f"Cleanup job failed for run {run_id}: {e}", exc_info=True)

            # Update run status to failed
            try:
                if agent and agent.run:
                    agent.run.status = "failed"
                    agent.run.error_message = str(e)
                    agent.run.finished_at = datetime.utcnow()
                    await db.commit()
            except Exception as update_error:
                logger.error(f"Failed to update run status: {update_error}")


# ============================================================================
# Event Listeners
# ============================================================================


def _job_executed_listener(event) -> None:
    """
    Event listener for successful job execution.

    Args:
        event: APScheduler event object
    """
    logger.info(
        f"Job {event.job_id} executed successfully "
        f"(runtime: {event.retval})"
    )


def _job_error_listener(event) -> None:
    """
    Event listener for job execution errors.

    Args:
        event: APScheduler event object with exception info
    """
    logger.error(
        f"Job {event.job_id} failed with error: {event.exception}",
        exc_info=True
    )


# ============================================================================
# Utility Functions
# ============================================================================


def get_scheduler_status() -> Dict:
    """
    Get current scheduler status information.

    Returns:
        Dictionary with:
        - running: bool
        - jobs_count: int
        - pending_jobs: int
        - next_run_time: datetime or None

    Example:
        >>> status = get_scheduler_status()
        >>> print(f"Scheduler running: {status['running']}")
        >>> print(f"Active jobs: {status['jobs_count']}")
    """
    if _scheduler is None:
        return {
            "running": False,
            "jobs_count": 0,
            "pending_jobs": 0,
            "next_run_time": None
        }

    jobs = _scheduler.get_jobs()
    pending_jobs = [j for j in jobs if j.pending]
    next_run_times = [j.next_run_time for j in jobs if j.next_run_time]
    next_run = min(next_run_times) if next_run_times else None

    return {
        "running": _scheduler.running,
        "jobs_count": len(jobs),
        "pending_jobs": len(pending_jobs),
        "next_run_time": next_run
    }
