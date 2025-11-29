"""
Retention rules API endpoints.

Provides endpoints for managing and evaluating retention rules.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from gmail_client import GmailClient
from models import Sender
from schemas import (
    RetentionRuleCreate,
    RetentionRuleUpdate,
    RetentionRuleResponse,
    RetentionRuleListResponse,
    SenderEvaluationRequest,
    SenderEvaluationResponse,
    CleanupPreviewResponse,
)
from agent.retention import (
    RetentionEngine,
    RetentionRule,
    RuleType,
    Action,
    evaluate_sender_emails,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Global retention engine instance
# In production, this could be stored in database or cache
_retention_engine = RetentionEngine()


@router.get("/rules", response_model=RetentionRuleListResponse)
async def get_retention_rules():
    """
    Get all retention rules (default + custom).

    Returns list of all rules sorted by priority (highest first).
    """
    try:
        rules = _retention_engine.get_rules()
        return RetentionRuleListResponse(
            rules=rules,
            total=len(rules),
        )
    except Exception as e:
        logger.error(f"Error getting retention rules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get retention rules: {str(e)}",
        )


@router.post("/rules", response_model=RetentionRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_retention_rule(rule_data: RetentionRuleCreate):
    """
    Create a custom retention rule.

    The rule will be added to the retention engine and evaluated
    during cleanup operations.
    """
    try:
        # Create rule from request data
        rule = RetentionRule(
            rule_type=RuleType(rule_data.rule_type),
            pattern=rule_data.pattern,
            action=Action(rule_data.action),
            priority=rule_data.priority,
            enabled=rule_data.enabled,
            description=rule_data.description,
        )

        # Add to engine
        _retention_engine.add_rule(rule)

        # Get the index of the newly added rule
        rules = _retention_engine.get_rules()
        new_rule = rules[-1]  # Last rule is the newly added one

        return RetentionRuleResponse(**new_rule)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid rule data: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Error creating retention rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create retention rule: {str(e)}",
        )


@router.patch("/rules/{rule_index}", response_model=RetentionRuleResponse)
async def update_retention_rule(rule_index: int, update_data: RetentionRuleUpdate):
    """
    Update a retention rule.

    Only enabled, priority, and description can be updated.
    To change rule_type, pattern, or action, delete and create a new rule.
    """
    try:
        rules = _retention_engine.get_rules()

        if rule_index < 0 or rule_index >= len(rules):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with index {rule_index} not found",
            )

        # Update the rule
        rule = _retention_engine.rules[rule_index]

        if update_data.enabled is not None:
            rule.enabled = update_data.enabled

        if update_data.priority is not None:
            rule.priority = update_data.priority

        if update_data.description is not None:
            rule.description = update_data.description

        # Get updated rule
        updated_rules = _retention_engine.get_rules()
        return RetentionRuleResponse(**updated_rules[rule_index])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating retention rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update retention rule: {str(e)}",
        )


@router.delete("/rules/{rule_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_retention_rule(rule_index: int):
    """
    Delete a custom retention rule.

    Note: Default rules cannot be deleted, but they can be disabled.
    """
    try:
        success = _retention_engine.remove_rule(rule_index)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with index {rule_index} not found",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting retention rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete retention rule: {str(e)}",
        )


@router.post("/evaluate", response_model=SenderEvaluationResponse)
async def evaluate_sender(
    request: SenderEvaluationRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate emails from a sender against retention rules.

    This endpoint analyzes emails from a specific sender and shows
    how many would be kept, deleted, or flagged for review based on
    current retention rules.
    """
    try:
        # Get sender from database
        stmt = select(Sender).where(Sender.email == request.sender_email)
        result = await db.execute(stmt)
        sender = result.scalar_one_or_none()

        if not sender:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sender {request.sender_email} not found",
            )

        # Initialize Gmail client
        gmail_client = GmailClient(db=db)

        # Evaluate sender's emails
        evaluation_result = await evaluate_sender_emails(
            sender=sender,
            gmail_client=gmail_client,
            retention_engine=_retention_engine,
            max_emails=request.max_emails,
        )

        return SenderEvaluationResponse(**evaluation_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating sender {request.sender_email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to evaluate sender: {str(e)}",
        )


@router.get("/preview", response_model=CleanupPreviewResponse)
async def preview_cleanup(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    """
    Preview what would be kept/deleted based on current rules.

    This endpoint provides a summary of how retention rules would
    affect the top senders in the mailbox. Useful for understanding
    the impact before running a cleanup.
    """
    try:
        # Get top senders by message count
        stmt = select(Sender).order_by(Sender.message_count.desc()).limit(limit)
        result = await db.execute(stmt)
        top_senders = result.scalars().all()

        if not top_senders:
            return CleanupPreviewResponse(
                total_senders=0,
                estimated_keep=0,
                estimated_delete=0,
                estimated_review=0,
                top_delete_senders=[],
                top_keep_senders=[],
            )

        # Initialize Gmail client
        gmail_client = GmailClient(db=db)

        # Evaluate each sender (quick preview - limit to 10 emails per sender)
        total_keep = 0
        total_delete = 0
        total_review = 0
        sender_results = []

        for sender in top_senders:
            try:
                evaluation = await evaluate_sender_emails(
                    sender=sender,
                    gmail_client=gmail_client,
                    retention_engine=_retention_engine,
                    max_emails=10,  # Quick preview
                )

                total_keep += evaluation["keep_count"]
                total_delete += evaluation["delete_count"]
                total_review += evaluation["review_count"]

                sender_results.append({
                    "sender_email": sender.email,
                    "message_count": sender.message_count,
                    "keep_count": evaluation["keep_count"],
                    "delete_count": evaluation["delete_count"],
                    "review_count": evaluation["review_count"],
                })

            except Exception as e:
                logger.warning(f"Error evaluating sender {sender.email}: {e}")
                continue

        # Sort by delete count for top deleters
        top_delete = sorted(
            sender_results,
            key=lambda x: x["delete_count"],
            reverse=True,
        )[:5]

        # Sort by keep count for top keepers
        top_keep = sorted(
            sender_results,
            key=lambda x: x["keep_count"],
            reverse=True,
        )[:5]

        return CleanupPreviewResponse(
            total_senders=len(top_senders),
            estimated_keep=total_keep,
            estimated_delete=total_delete,
            estimated_review=total_review,
            top_delete_senders=top_delete,
            top_keep_senders=top_keep,
        )

    except Exception as e:
        logger.error(f"Error previewing cleanup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview cleanup: {str(e)}",
        )


@router.post("/rules/{rule_index}/enable", response_model=RetentionRuleResponse)
async def enable_rule(rule_index: int):
    """
    Enable a retention rule.

    Enabled rules are evaluated during cleanup operations.
    """
    try:
        success = _retention_engine.enable_rule(rule_index)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with index {rule_index} not found",
            )

        rules = _retention_engine.get_rules()
        return RetentionRuleResponse(**rules[rule_index])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error enabling rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enable rule: {str(e)}",
        )


@router.post("/rules/{rule_index}/disable", response_model=RetentionRuleResponse)
async def disable_rule(rule_index: int):
    """
    Disable a retention rule.

    Disabled rules are not evaluated during cleanup operations.
    Useful for temporarily disabling a rule without deleting it.
    """
    try:
        success = _retention_engine.disable_rule(rule_index)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with index {rule_index} not found",
            )

        rules = _retention_engine.get_rules()
        return RetentionRuleResponse(**rules[rule_index])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disabling rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disable rule: {str(e)}",
        )
