"""
Senders router for managing discovered email senders.
Provides endpoints for listing, filtering, and viewing sender information.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import Sender
from schemas import SenderResponse

router = APIRouter()


@router.get("", response_model=List[SenderResponse])
async def list_senders(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of senders to return"),
    offset: int = Query(default=0, ge=0, description="Number of senders to skip"),
    domain: Optional[str] = Query(default=None, description="Filter by domain"),
    unsubscribed: Optional[bool] = Query(default=None, description="Filter by unsubscribed status"),
    has_filter: Optional[bool] = Query(default=None, description="Filter by filter creation status"),
    search: Optional[str] = Query(default=None, description="Search by email or display name"),
    db: AsyncSession = Depends(get_db),
) -> List[SenderResponse]:
    """
    List discovered senders with filtering and pagination.

    Args:
        limit: Maximum number of senders to return
        offset: Number of senders to skip
        domain: Optional domain filter
        unsubscribed: Optional filter for unsubscribed status
        has_filter: Optional filter for filter creation status
        search: Optional search term for email or display name
        db: Database session

    Returns:
        List[SenderResponse]: List of senders matching criteria

    Raises:
        HTTPException: If query fails
    """
    try:
        # Build query
        stmt = select(Sender)

        # Apply filters
        if domain:
            stmt = stmt.where(Sender.domain == domain)

        if unsubscribed is not None:
            stmt = stmt.where(Sender.unsubscribed == unsubscribed)

        if has_filter is not None:
            stmt = stmt.where(Sender.filter_created == has_filter)

        if search:
            search_pattern = f"%{search}%"
            stmt = stmt.where(
                (Sender.email.ilike(search_pattern))
                | (Sender.display_name.ilike(search_pattern))
            )

        # Order by message count descending
        stmt = stmt.order_by(desc(Sender.message_count))

        # Apply pagination
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        senders = result.scalars().all()

        return [SenderResponse.model_validate(sender) for sender in senders]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list senders: {str(e)}",
        )


@router.get("/stats")
async def get_sender_stats(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get statistics about discovered senders.

    Args:
        db: Database session

    Returns:
        dict: Sender statistics including counts

    Raises:
        HTTPException: If query fails
    """
    try:
        # Total senders
        total_stmt = select(func.count(Sender.id))
        total_result = await db.execute(total_stmt)
        total = total_result.scalar() or 0

        # Unsubscribed senders
        unsubscribed_stmt = select(func.count(Sender.id)).where(
            Sender.unsubscribed == True
        )
        unsubscribed_result = await db.execute(unsubscribed_stmt)
        unsubscribed = unsubscribed_result.scalar() or 0

        # Senders with filters
        filtered_stmt = select(func.count(Sender.id)).where(
            Sender.filter_created == True
        )
        filtered_result = await db.execute(filtered_stmt)
        filtered = filtered_result.scalar() or 0

        # Senders with unsubscribe capability
        has_unsubscribe_stmt = select(func.count(Sender.id)).where(
            Sender.has_list_unsubscribe == True
        )
        has_unsubscribe_result = await db.execute(has_unsubscribe_stmt)
        has_unsubscribe = has_unsubscribe_result.scalar() or 0

        # Total messages across all senders
        total_messages_stmt = select(func.sum(Sender.message_count))
        total_messages_result = await db.execute(total_messages_stmt)
        total_messages = total_messages_result.scalar() or 0

        # Unique domains
        unique_domains_stmt = select(func.count(func.distinct(Sender.domain)))
        unique_domains_result = await db.execute(unique_domains_stmt)
        unique_domains = unique_domains_result.scalar() or 0

        return {
            "total_senders": total,
            "total_messages": total_messages,
            "unsubscribed_count": unsubscribed,
            "filtered_count": filtered,
            "has_unsubscribe_count": has_unsubscribe,
            "unique_domains": unique_domains,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sender statistics: {str(e)}",
        )


@router.get("/{sender_id}", response_model=SenderResponse)
async def get_sender(
    sender_id: int,
    db: AsyncSession = Depends(get_db),
) -> SenderResponse:
    """
    Get detailed information about a specific sender.

    Args:
        sender_id: ID of the sender to retrieve
        db: Database session

    Returns:
        SenderResponse: Detailed sender information

    Raises:
        HTTPException: If sender not found or query fails
    """
    try:
        stmt = select(Sender).where(Sender.id == sender_id)
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()

        if not sender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sender with ID {sender_id} not found",
            )

        return SenderResponse.model_validate(sender)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sender: {str(e)}",
        )
