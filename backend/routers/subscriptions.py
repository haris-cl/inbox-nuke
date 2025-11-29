"""
Subscription management API endpoints.
Provides subscription detection, unsubscribe, and cleanup.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from gmail_client import GmailClient
from models import Subscription, GmailCredentials
from schemas import (
    SubscriptionResponse,
    SubscriptionListResponse,
    SubscriptionUnsubscribeRequest,
    SubscriptionCleanupRequest,
    BulkUnsubscribeRequest,
    BulkUnsubscribeResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Subscription Endpoints
# ============================================================================


@router.get("/", response_model=SubscriptionListResponse)
async def get_subscriptions(
    limit: int = 50,
    offset: int = 0,
    unsubscribed_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    """
    Get all detected subscriptions.

    Args:
        limit: Maximum results to return (1-100)
        offset: Offset for pagination
        unsubscribed_only: Only show unsubscribed subscriptions
        db: Database session

    Returns:
        Paginated list of subscriptions

    Raises:
        HTTPException: On database errors
    """
    try:
        # Build query
        stmt = select(Subscription)

        if unsubscribed_only:
            stmt = stmt.where(Subscription.is_unsubscribed == True)

        # Get total count
        count_stmt = select(func.count()).select_from(Subscription)
        if unsubscribed_only:
            count_stmt = count_stmt.where(Subscription.is_unsubscribed == True)

        total_result = await db.execute(count_stmt)
        total = total_result.scalar()

        # Apply pagination
        stmt = stmt.order_by(Subscription.email_count.desc())
        stmt = stmt.limit(limit).offset(offset)

        # Execute query
        result = await db.execute(stmt)
        subscriptions = result.scalars().all()

        return SubscriptionListResponse(
            subscriptions=subscriptions,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        logger.error(f"Error getting subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get subscriptions: {str(e)}"
        )


@router.post("/scan", status_code=status.HTTP_202_ACCEPTED)
async def scan_subscriptions(
    db: AsyncSession = Depends(get_db),
):
    """
    Scan Gmail for subscriptions and mailing lists.

    This endpoint:
    1. Queries Gmail for emails with List-Unsubscribe headers
    2. Groups by sender
    3. Stores subscription info in database

    Returns:
        Summary of discovered subscriptions

    Raises:
        HTTPException: If Gmail not connected
    """
    try:
        # Get Gmail credentials
        stmt = select(GmailCredentials).limit(1)
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if not creds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected. Please authenticate first."
            )

        # Initialize Gmail client
        gmail_client = GmailClient(db=db, credentials=creds)

        # Get subscriptions from Gmail
        logger.info("Scanning Gmail for subscriptions")
        subscription_data = await gmail_client.get_subscriptions()

        # Save to database
        saved_count = 0
        updated_count = 0

        for sub_data in subscription_data:
            # Check if subscription exists
            stmt = select(Subscription).where(
                Subscription.sender_email == sub_data["sender_email"]
            )
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing:
                # Update existing
                existing.sender_name = sub_data.get("sender_name")
                existing.email_count = sub_data.get("email_count", 0)
                existing.unsubscribe_url = sub_data.get("unsubscribe_url")
                existing.unsubscribe_mailto = sub_data.get("unsubscribe_mailto")
                existing.last_email_date = datetime.utcnow()
                updated_count += 1
            else:
                # Create new
                subscription = Subscription(
                    sender_email=sub_data["sender_email"],
                    sender_name=sub_data.get("sender_name"),
                    email_count=sub_data.get("email_count", 0),
                    unsubscribe_url=sub_data.get("unsubscribe_url"),
                    unsubscribe_mailto=sub_data.get("unsubscribe_mailto"),
                    last_email_date=datetime.utcnow()
                )
                db.add(subscription)
                saved_count += 1

        await db.commit()

        logger.info(f"Subscription scan complete: {saved_count} new, {updated_count} updated")

        return {
            "message": "Subscription scan completed",
            "new_subscriptions": saved_count,
            "updated_subscriptions": updated_count,
            "total": saved_count + updated_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning subscriptions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Subscription scan failed: {str(e)}"
        )


@router.post("/{subscription_id}/unsubscribe", response_model=SubscriptionResponse)
async def unsubscribe(
    subscription_id: int,
    request: SubscriptionUnsubscribeRequest = SubscriptionUnsubscribeRequest(method="auto"),
    db: AsyncSession = Depends(get_db),
):
    """
    Unsubscribe from a subscription.

    Args:
        subscription_id: Subscription ID
        request: Unsubscribe method (mailto, http, auto)
        db: Database session

    Returns:
        Updated subscription

    Raises:
        HTTPException: If subscription not found or unsubscribe fails
    """
    try:
        # Get subscription
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription not found: {subscription_id}"
            )

        # Get Gmail credentials
        stmt = select(GmailCredentials).limit(1)
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if not creds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected"
            )

        # Initialize Gmail client
        gmail_client = GmailClient(db=db, credentials=creds)

        # Attempt unsubscribe
        success = await gmail_client.unsubscribe_from_sender(subscription.sender_email)

        if success:
            # Update subscription status
            subscription.is_unsubscribed = True
            subscription.unsubscribed_at = datetime.utcnow()
            await db.commit()
            await db.refresh(subscription)

            logger.info(f"Successfully unsubscribed from {subscription.sender_email}")
            return subscription
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsubscribe failed for {subscription.sender_email}. "
                       f"URL: {subscription.unsubscribe_url}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unsubscribe failed: {str(e)}"
        )


@router.post("/{subscription_id}/cleanup")
async def cleanup_subscription_emails(
    subscription_id: int,
    request: SubscriptionCleanupRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete emails from a subscription older than X days.

    Args:
        subscription_id: Subscription ID
        request: Cleanup parameters (older_than_days, delete_all)
        db: Database session

    Returns:
        Summary of deleted emails

    Raises:
        HTTPException: If subscription not found or cleanup fails
    """
    try:
        # Get subscription
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription not found: {subscription_id}"
            )

        # Get Gmail credentials
        stmt = select(GmailCredentials).limit(1)
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if not creds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected"
            )

        # Initialize Gmail client
        gmail_client = GmailClient(db=db, credentials=creds)

        # Build query for old emails
        cutoff_date = datetime.utcnow() - timedelta(days=request.older_than_days)
        date_str = cutoff_date.strftime("%Y/%m/%d")

        if request.delete_all:
            query = f"from:{subscription.sender_email}"
        else:
            query = f"from:{subscription.sender_email} before:{date_str}"

        # Get emails to delete
        messages = await gmail_client.list_messages(query=query, max_results=1000)

        if not messages:
            return {
                "message": "No emails to delete",
                "emails_deleted": 0
            }

        # Delete emails
        message_ids = [msg["id"] for msg in messages]
        deleted_count = await gmail_client.trash_messages(message_ids)

        logger.info(
            f"Cleaned up {deleted_count} emails from {subscription.sender_email} "
            f"(older than {request.older_than_days} days)"
        )

        return {
            "message": f"Successfully deleted {deleted_count} emails",
            "emails_deleted": deleted_count,
            "sender": subscription.sender_email
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up subscription emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Cleanup failed: {str(e)}"
        )


@router.post("/bulk-unsubscribe", response_model=BulkUnsubscribeResponse)
async def bulk_unsubscribe(
    request: BulkUnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Unsubscribe from multiple subscriptions at once.

    Args:
        request: List of subscription IDs to unsubscribe from
        db: Database session

    Returns:
        Summary of unsubscribe results

    Raises:
        HTTPException: On errors
    """
    try:
        # Get Gmail credentials
        stmt = select(GmailCredentials).limit(1)
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if not creds:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gmail not connected"
            )

        # Initialize Gmail client
        gmail_client = GmailClient(db=db, credentials=creds)

        successful = 0
        failed = 0
        errors = []

        for subscription_id in request.subscription_ids:
            try:
                # Get subscription
                stmt = select(Subscription).where(Subscription.id == subscription_id)
                result = await db.execute(stmt)
                subscription = result.scalar_one_or_none()

                if not subscription:
                    failed += 1
                    errors.append(f"Subscription {subscription_id} not found")
                    continue

                # Attempt unsubscribe
                success = await gmail_client.unsubscribe_from_sender(subscription.sender_email)

                if success:
                    # Update subscription status
                    subscription.is_unsubscribed = True
                    subscription.unsubscribed_at = datetime.utcnow()
                    successful += 1
                else:
                    failed += 1
                    errors.append(f"Failed to unsubscribe from {subscription.sender_email}")

            except Exception as e:
                failed += 1
                errors.append(f"Error with subscription {subscription_id}: {str(e)}")

        # Commit all updates
        await db.commit()

        logger.info(
            f"Bulk unsubscribe complete: {successful} successful, {failed} failed"
        )

        return BulkUnsubscribeResponse(
            total_requested=len(request.subscription_ids),
            successful=successful,
            failed=failed,
            errors=errors
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk unsubscribe: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk unsubscribe failed: {str(e)}"
        )


@router.delete("/{subscription_id}")
async def delete_subscription(
    subscription_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a subscription record from the database.

    Note: This does NOT unsubscribe from the mailing list,
    it only removes the tracking record.

    Args:
        subscription_id: Subscription ID
        db: Database session

    Returns:
        Success message

    Raises:
        HTTPException: If subscription not found
    """
    try:
        # Get subscription
        stmt = select(Subscription).where(Subscription.id == subscription_id)
        result = await db.execute(stmt)
        subscription = result.scalar_one_or_none()

        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subscription not found: {subscription_id}"
            )

        # Delete subscription
        await db.delete(subscription)
        await db.commit()

        logger.info(f"Deleted subscription record for {subscription.sender_email}")

        return {
            "message": f"Subscription record deleted for {subscription.sender_email}"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting subscription: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Delete failed: {str(e)}"
        )


@router.get("/stats")
async def get_subscription_stats(
    db: AsyncSession = Depends(get_db),
):
    """
    Get subscription statistics.

    Returns:
        Statistics about subscriptions

    Raises:
        HTTPException: On database errors
    """
    try:
        # Total subscriptions
        total_stmt = select(func.count()).select_from(Subscription)
        total_result = await db.execute(total_stmt)
        total = total_result.scalar()

        # Unsubscribed count
        unsubscribed_stmt = select(func.count()).select_from(Subscription).where(
            Subscription.is_unsubscribed == True
        )
        unsubscribed_result = await db.execute(unsubscribed_stmt)
        unsubscribed = unsubscribed_result.scalar()

        # Total email count
        email_count_stmt = select(func.sum(Subscription.email_count))
        email_count_result = await db.execute(email_count_stmt)
        total_emails = email_count_result.scalar() or 0

        # Top subscriptions by email count
        top_stmt = select(Subscription).order_by(
            Subscription.email_count.desc()
        ).limit(10)
        top_result = await db.execute(top_stmt)
        top_subscriptions = top_result.scalars().all()

        return {
            "total_subscriptions": total,
            "unsubscribed": unsubscribed,
            "active": total - unsubscribed,
            "total_emails": total_emails,
            "top_subscriptions": [
                {
                    "sender": sub.sender_email,
                    "email_count": sub.email_count,
                    "is_unsubscribed": sub.is_unsubscribed
                }
                for sub in top_subscriptions
            ]
        }

    except Exception as e:
        logger.error(f"Error getting subscription stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
