"""
Tests for V2 Cleanup Wizard functionality.
Tests the CleanupFlowService, RecommendationEngine, and CleanupExecutor.
"""

import json
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from sqlalchemy.ext.asyncio import AsyncSession

from models import CleanupSession, EmailRecommendation
from services.cleanup_flow import CleanupFlowService
from services.recommendation_engine import RecommendationEngine


# ============================================================================
# CleanupFlowService Tests
# ============================================================================


@pytest.mark.asyncio
async def test_create_session(test_db: AsyncSession):
    """Test creating a new cleanup session."""
    flow_service = CleanupFlowService(test_db)

    session_id = await flow_service.create_session(max_emails=500)

    assert session_id is not None
    assert len(session_id) == 36  # UUID format

    # Verify session exists in DB
    session = await flow_service.get_session(session_id)
    assert session is not None
    assert session.status == "scanning"
    assert session.total_emails == 500


@pytest.mark.asyncio
async def test_update_progress(test_db: AsyncSession):
    """Test updating scan progress."""
    flow_service = CleanupFlowService(test_db)
    session_id = await flow_service.create_session(max_emails=100)

    # Update progress
    await flow_service.update_progress(
        session_id,
        scanned=50,
        discoveries={"promotions": 20, "newsletters": 15, "social": 10, "other": 5}
    )

    session = await flow_service.get_session(session_id)
    assert session.scanned_emails == 50

    discoveries = json.loads(session.discoveries)
    assert discoveries["promotions"] == 20
    assert discoveries["newsletters"] == 15


@pytest.mark.asyncio
async def test_set_mode(test_db: AsyncSession):
    """Test setting cleanup mode (quick vs full)."""
    flow_service = CleanupFlowService(test_db)
    session_id = await flow_service.create_session(max_emails=100)

    await flow_service.set_mode(session_id, "quick")
    session = await flow_service.get_session(session_id)
    assert session.mode == "quick"

    await flow_service.set_mode(session_id, "full")
    session = await flow_service.get_session(session_id)
    assert session.mode == "full"


@pytest.mark.asyncio
async def test_record_decision(test_db: AsyncSession):
    """Test recording user review decisions."""
    flow_service = CleanupFlowService(test_db)
    session_id = await flow_service.create_session(max_emails=100)

    # Record decisions
    await flow_service.record_decision(session_id, "msg_001", "keep")
    await flow_service.record_decision(session_id, "msg_002", "delete")

    session = await flow_service.get_session(session_id)
    decisions = json.loads(session.review_decisions)

    assert decisions["msg_001"] == "keep"
    assert decisions["msg_002"] == "delete"


@pytest.mark.asyncio
async def test_complete_session(test_db: AsyncSession):
    """Test completing a cleanup session with results."""
    flow_service = CleanupFlowService(test_db)
    session_id = await flow_service.create_session(max_emails=100)

    await flow_service.complete_session(
        session_id,
        emails_deleted=45,
        space_freed=1024 * 1024 * 10,  # 10 MB
        senders_unsubscribed=3,
        filters_created=5
    )

    session = await flow_service.get_session(session_id)
    assert session.status == "completed"
    assert session.emails_deleted == 45
    assert session.space_freed == 1024 * 1024 * 10
    assert session.senders_unsubscribed == 3
    assert session.filters_created == 5


# ============================================================================
# RecommendationEngine Tests
# ============================================================================


class TestRecommendationEngine:
    """Tests for the AI recommendation engine."""

    def test_protected_domains(self):
        """Test that financial/gov domains are protected."""
        engine = RecommendationEngine()

        # These should be protected
        protected_domains = [
            "chase.com",
            "wellsfargo.com",
            "bankofamerica.com",
            "paypal.com",
            "irs.gov",
            "ssa.gov",
        ]

        for domain in protected_domains:
            assert engine.is_protected_domain(domain), f"{domain} should be protected"

    def test_non_protected_domains(self):
        """Test that marketing domains are not protected."""
        engine = RecommendationEngine()

        non_protected = [
            "marketing.com",
            "newsletter.io",
            "promo-emails.net",
        ]

        for domain in non_protected:
            assert not engine.is_protected_domain(domain), f"{domain} should not be protected"

    def test_protected_keywords_in_subject(self):
        """Test that sensitive subjects are protected."""
        engine = RecommendationEngine()

        protected_subjects = [
            "Your verification code is 123456",
            "Password reset requested",
            "Two-factor authentication",
            "Your invoice #12345",
            "Payment confirmation",
            "Security alert: New sign-in",
        ]

        for subject in protected_subjects:
            assert engine.has_protected_keywords(subject), f"Subject '{subject}' should be protected"

    def test_promotional_subjects_not_protected(self):
        """Test that promotional subjects are not protected by keywords."""
        engine = RecommendationEngine()

        promo_subjects = [
            "50% off sale ends today!",
            "Weekly newsletter",
            "Check out our new products",
            "Don't miss this deal",
        ]

        for subject in promo_subjects:
            assert not engine.has_protected_keywords(subject), f"Subject '{subject}' should not be protected"

    def test_analyze_email_protected(self):
        """Test that protected emails get 'keep' recommendation."""
        engine = RecommendationEngine()

        # Bank email
        email = {
            "id": "msg_001",
            "from": "alerts@chase.com",
            "subject": "Your account statement is ready",
            "date": "2024-01-01",
            "size": 5000,
            "labels": ["INBOX"],
        }

        result = engine.analyze_email(email)
        assert result["suggestion"] == "keep"
        assert result["confidence"] >= 0.9
        assert "protected" in result["category"].lower() or "financial" in result["reasoning"].lower()

    def test_analyze_email_promotional(self):
        """Test that promotional emails get 'delete' recommendation."""
        engine = RecommendationEngine()

        email = {
            "id": "msg_002",
            "from": "newsletter@marketing.com",
            "subject": "Weekly deals - 50% off everything!",
            "date": "2024-01-01",
            "size": 50000,
            "labels": ["CATEGORY_PROMOTIONS"],
            "has_unsubscribe": True,
        }

        result = engine.analyze_email(email)
        assert result["suggestion"] == "delete"
        assert result["confidence"] >= 0.7
        assert result["category"] in ["promotions", "newsletters", "marketing"]

    def test_analyze_email_uncertain(self):
        """Test that ambiguous emails have lower confidence."""
        engine = RecommendationEngine()

        email = {
            "id": "msg_003",
            "from": "info@company.com",
            "subject": "Update from Company",
            "date": "2024-01-01",
            "size": 3000,
            "labels": ["INBOX"],
        }

        result = engine.analyze_email(email)
        # Should have moderate confidence for ambiguous emails
        assert result["confidence"] <= 0.8


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.asyncio
async def test_full_cleanup_flow(test_db: AsyncSession):
    """Test the complete cleanup wizard flow."""
    flow_service = CleanupFlowService(test_db)

    # Step 1: Create session
    session_id = await flow_service.create_session(max_emails=100)
    session = await flow_service.get_session(session_id)
    assert session.status == "scanning"

    # Step 2: Simulate scan progress
    await flow_service.update_progress(
        session_id,
        scanned=100,
        discoveries={"promotions": 30, "newsletters": 20, "social": 10, "protected": 40}
    )
    await flow_service.mark_ready_for_review(session_id)

    session = await flow_service.get_session(session_id)
    assert session.status == "ready_for_review"

    # Step 3: Set mode
    await flow_service.set_mode(session_id, "quick")

    # Step 4: Record some decisions
    await flow_service.record_decision(session_id, "msg_001", "delete")
    await flow_service.record_decision(session_id, "msg_002", "keep")

    # Step 5: Mark confirming
    await flow_service.mark_confirming(session_id)
    session = await flow_service.get_session(session_id)
    assert session.status == "confirming"

    # Step 6: Complete
    await flow_service.complete_session(
        session_id,
        emails_deleted=50,
        space_freed=1024 * 1024 * 25,
        senders_unsubscribed=2,
        filters_created=3
    )

    session = await flow_service.get_session(session_id)
    assert session.status == "completed"
    assert session.emails_deleted == 50


@pytest.mark.asyncio
async def test_session_not_found(test_db: AsyncSession):
    """Test handling of non-existent session."""
    flow_service = CleanupFlowService(test_db)

    session = await flow_service.get_session("non-existent-id")
    assert session is None
