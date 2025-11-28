"""
Tests for database models.
Tests CleanupRun, Sender, CleanupAction, and WhitelistDomain models.
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import CleanupAction, CleanupRun, Sender, WhitelistDomain


# ============================================================================
# CleanupRun Model Tests
# ============================================================================


class TestCleanupRunModel:
    """Tests for CleanupRun model."""

    @pytest.mark.asyncio
    async def test_create_cleanup_run(self, test_db: AsyncSession):
        """Test creating a new cleanup run."""
        run = CleanupRun(
            status="pending",
            started_at=datetime.utcnow(),
        )
        test_db.add(run)
        await test_db.commit()
        await test_db.refresh(run)

        assert run.id is not None
        assert run.status == "pending"
        assert run.senders_total == 0
        assert run.senders_processed == 0
        assert run.emails_deleted == 0
        assert run.bytes_freed_estimate == 0

    @pytest.mark.asyncio
    async def test_update_cleanup_run_status(self, test_db: AsyncSession):
        """Test updating cleanup run status."""
        run = CleanupRun(status="pending")
        test_db.add(run)
        await test_db.commit()

        # Update to running
        run.status = "running"
        await test_db.commit()
        await test_db.refresh(run)

        assert run.status == "running"

        # Update to completed
        run.status = "completed"
        run.finished_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(run)

        assert run.status == "completed"
        assert run.finished_at is not None

    @pytest.mark.asyncio
    async def test_update_cleanup_run_progress(self, test_db: AsyncSession):
        """Test updating cleanup run progress."""
        run = CleanupRun(
            status="running",
            senders_total=100,
        )
        test_db.add(run)
        await test_db.commit()

        # Update progress
        run.senders_processed = 50
        run.emails_deleted = 1000
        run.bytes_freed_estimate = 1024 * 1024 * 100  # 100 MB
        await test_db.commit()
        await test_db.refresh(run)

        assert run.senders_processed == 50
        assert run.emails_deleted == 1000
        assert run.bytes_freed_estimate == 1024 * 1024 * 100

    @pytest.mark.asyncio
    async def test_cleanup_run_with_error(self, test_db: AsyncSession):
        """Test cleanup run with error message."""
        run = CleanupRun(
            status="failed",
            error_message="API rate limit exceeded",
        )
        test_db.add(run)
        await test_db.commit()
        await test_db.refresh(run)

        assert run.status == "failed"
        assert run.error_message == "API rate limit exceeded"

    @pytest.mark.asyncio
    async def test_cleanup_run_progress_cursor(self, test_db: AsyncSession):
        """Test cleanup run with progress cursor for resuming."""
        import json

        cursor_data = {"last_sender_id": 123, "page_token": "abc123"}
        run = CleanupRun(
            status="paused",
            progress_cursor=json.dumps(cursor_data),
        )
        test_db.add(run)
        await test_db.commit()
        await test_db.refresh(run)

        assert run.progress_cursor is not None
        loaded_cursor = json.loads(run.progress_cursor)
        assert loaded_cursor["last_sender_id"] == 123


# ============================================================================
# Sender Model Tests
# ============================================================================


class TestSenderModel:
    """Tests for Sender model."""

    @pytest.mark.asyncio
    async def test_create_sender(self, test_db: AsyncSession):
        """Test creating a new sender."""
        sender = Sender(
            email="test@example.com",
            domain="example.com",
            display_name="Test Sender",
            message_count=10,
        )
        test_db.add(sender)
        await test_db.commit()
        await test_db.refresh(sender)

        assert sender.id is not None
        assert sender.email == "test@example.com"
        assert sender.domain == "example.com"
        assert sender.display_name == "Test Sender"
        assert sender.message_count == 10
        assert sender.has_list_unsubscribe is False
        assert sender.unsubscribed is False
        assert sender.filter_created is False

    @pytest.mark.asyncio
    async def test_sender_unique_email_constraint(self, test_db: AsyncSession):
        """Test that email must be unique."""
        sender1 = Sender(email="test@example.com", domain="example.com")
        test_db.add(sender1)
        await test_db.commit()

        # Try to add another sender with same email
        sender2 = Sender(email="test@example.com", domain="example.com")
        test_db.add(sender2)

        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_update_sender_unsubscribe_info(self, test_db: AsyncSession):
        """Test updating sender unsubscribe information."""
        sender = Sender(
            email="newsletter@example.com",
            domain="example.com",
            message_count=50,
        )
        test_db.add(sender)
        await test_db.commit()

        # Update unsubscribe info
        sender.has_list_unsubscribe = True
        sender.unsubscribe_method = "mailto"
        sender.unsubscribe_header = '{"mailto": "unsubscribe@example.com"}'
        sender.unsubscribed = True
        sender.unsubscribed_at = datetime.utcnow()
        await test_db.commit()
        await test_db.refresh(sender)

        assert sender.has_list_unsubscribe is True
        assert sender.unsubscribe_method == "mailto"
        assert sender.unsubscribed is True
        assert sender.unsubscribed_at is not None

    @pytest.mark.asyncio
    async def test_update_sender_filter_info(self, test_db: AsyncSession):
        """Test updating sender filter information."""
        sender = Sender(email="spam@example.com", domain="example.com")
        test_db.add(sender)
        await test_db.commit()

        # Create filter
        sender.filter_created = True
        sender.filter_id = "filter_123"
        await test_db.commit()
        await test_db.refresh(sender)

        assert sender.filter_created is True
        assert sender.filter_id == "filter_123"

    @pytest.mark.asyncio
    async def test_sender_timestamps(self, test_db: AsyncSession):
        """Test sender timestamp fields."""
        now = datetime.utcnow()
        sender = Sender(
            email="test@example.com",
            domain="example.com",
            first_seen_at=now - timedelta(days=30),
            last_seen_at=now,
        )
        test_db.add(sender)
        await test_db.commit()
        await test_db.refresh(sender)

        assert sender.first_seen_at is not None
        assert sender.last_seen_at is not None
        assert sender.created_at is not None
        assert sender.last_seen_at > sender.first_seen_at


# ============================================================================
# CleanupAction Model Tests
# ============================================================================


class TestCleanupActionModel:
    """Tests for CleanupAction model."""

    @pytest.mark.asyncio
    async def test_create_cleanup_action(self, test_db: AsyncSession):
        """Test creating a cleanup action."""
        # First create a run
        run = CleanupRun(status="running")
        test_db.add(run)
        await test_db.commit()

        # Create action
        action = CleanupAction(
            run_id=run.id,
            action_type="delete",
            sender_email="spam@example.com",
            email_count=100,
            bytes_freed=1024 * 1024 * 5,  # 5 MB
            notes="Deleted promotional emails",
        )
        test_db.add(action)
        await test_db.commit()
        await test_db.refresh(action)

        assert action.id is not None
        assert action.run_id == run.id
        assert action.action_type == "delete"
        assert action.sender_email == "spam@example.com"
        assert action.email_count == 100
        assert action.bytes_freed == 1024 * 1024 * 5
        assert action.notes == "Deleted promotional emails"

    @pytest.mark.asyncio
    async def test_cleanup_action_types(self, test_db: AsyncSession):
        """Test different cleanup action types."""
        run = CleanupRun(status="running")
        test_db.add(run)
        await test_db.commit()

        action_types = ["unsubscribe", "delete", "filter", "skip", "error"]

        for action_type in action_types:
            action = CleanupAction(
                run_id=run.id,
                action_type=action_type,
                sender_email=f"{action_type}@example.com",
                email_count=10,
            )
            test_db.add(action)

        await test_db.commit()

        # Query all actions
        stmt = select(CleanupAction).where(CleanupAction.run_id == run.id)
        result = await test_db.execute(stmt)
        actions = result.scalars().all()

        assert len(actions) == len(action_types)
        action_type_set = {a.action_type for a in actions}
        assert action_type_set == set(action_types)

    @pytest.mark.asyncio
    async def test_cleanup_action_relationship(self, test_db: AsyncSession):
        """Test relationship between CleanupAction and CleanupRun."""
        run = CleanupRun(status="running")
        test_db.add(run)
        await test_db.commit()

        # Add multiple actions
        for i in range(5):
            action = CleanupAction(
                run_id=run.id,
                action_type="delete",
                sender_email=f"sender{i}@example.com",
                email_count=10 * i,
            )
            test_db.add(action)

        await test_db.commit()
        await test_db.refresh(run)

        # Access actions through relationship
        assert len(run.actions) == 5

    @pytest.mark.asyncio
    async def test_cleanup_action_cascade_delete(self, test_db: AsyncSession):
        """Test that actions are deleted when run is deleted."""
        run = CleanupRun(status="completed")
        test_db.add(run)
        await test_db.commit()

        # Add actions
        for i in range(3):
            action = CleanupAction(
                run_id=run.id,
                action_type="delete",
                sender_email=f"sender{i}@example.com",
            )
            test_db.add(action)

        await test_db.commit()

        # Verify actions exist
        stmt = select(CleanupAction).where(CleanupAction.run_id == run.id)
        result = await test_db.execute(stmt)
        assert len(result.scalars().all()) == 3

        # Delete run
        await test_db.delete(run)
        await test_db.commit()

        # Verify actions were cascade deleted
        stmt = select(CleanupAction).where(CleanupAction.run_id == run.id)
        result = await test_db.execute(stmt)
        assert len(result.scalars().all()) == 0


# ============================================================================
# WhitelistDomain Model Tests
# ============================================================================


class TestWhitelistDomainModel:
    """Tests for WhitelistDomain model."""

    @pytest.mark.asyncio
    async def test_create_whitelist_domain(self, test_db: AsyncSession):
        """Test creating a whitelist domain."""
        domain = WhitelistDomain(
            domain="important.com",
            reason="Important business emails",
        )
        test_db.add(domain)
        await test_db.commit()
        await test_db.refresh(domain)

        assert domain.id is not None
        assert domain.domain == "important.com"
        assert domain.reason == "Important business emails"
        assert domain.created_at is not None

    @pytest.mark.asyncio
    async def test_whitelist_domain_unique_constraint(self, test_db: AsyncSession):
        """Test that domain must be unique."""
        domain1 = WhitelistDomain(domain="example.com")
        test_db.add(domain1)
        await test_db.commit()

        # Try to add same domain again
        domain2 = WhitelistDomain(domain="example.com")
        test_db.add(domain2)

        with pytest.raises(Exception):  # Should raise integrity error
            await test_db.commit()

    @pytest.mark.asyncio
    async def test_whitelist_domain_without_reason(self, test_db: AsyncSession):
        """Test creating whitelist domain without reason."""
        domain = WhitelistDomain(domain="test.com")
        test_db.add(domain)
        await test_db.commit()
        await test_db.refresh(domain)

        assert domain.domain == "test.com"
        assert domain.reason is None

    @pytest.mark.asyncio
    async def test_query_whitelist_domains(self, test_db: AsyncSession):
        """Test querying whitelist domains."""
        domains_to_add = ["example.com", "test.com", "important.com"]

        for domain_name in domains_to_add:
            domain = WhitelistDomain(domain=domain_name)
            test_db.add(domain)

        await test_db.commit()

        # Query all domains
        stmt = select(WhitelistDomain)
        result = await test_db.execute(stmt)
        domains = result.scalars().all()

        assert len(domains) == len(domains_to_add)
        domain_names = {d.domain for d in domains}
        assert domain_names == set(domains_to_add)

    @pytest.mark.asyncio
    async def test_delete_whitelist_domain(self, test_db: AsyncSession):
        """Test deleting a whitelist domain."""
        domain = WhitelistDomain(domain="temporary.com")
        test_db.add(domain)
        await test_db.commit()

        # Verify it exists
        stmt = select(WhitelistDomain).where(WhitelistDomain.domain == "temporary.com")
        result = await test_db.execute(stmt)
        assert result.scalar_one_or_none() is not None

        # Delete it
        await test_db.delete(domain)
        await test_db.commit()

        # Verify it's gone
        stmt = select(WhitelistDomain).where(WhitelistDomain.domain == "temporary.com")
        result = await test_db.execute(stmt)
        assert result.scalar_one_or_none() is None


# ============================================================================
# Integration Tests
# ============================================================================


class TestModelIntegration:
    """Integration tests for multiple models."""

    @pytest.mark.asyncio
    async def test_complete_cleanup_run_workflow(self, test_db: AsyncSession):
        """Test a complete cleanup run workflow with all models."""
        # Create senders
        sender1 = Sender(
            email="spam@marketing.com",
            domain="marketing.com",
            message_count=200,
        )
        sender2 = Sender(
            email="news@newsletter.com",
            domain="newsletter.com",
            message_count=150,
        )
        test_db.add_all([sender1, sender2])
        await test_db.commit()

        # Create cleanup run
        run = CleanupRun(
            status="running",
            senders_total=2,
        )
        test_db.add(run)
        await test_db.commit()

        # Process sender1 - delete
        action1 = CleanupAction(
            run_id=run.id,
            action_type="delete",
            sender_email=sender1.email,
            email_count=sender1.message_count,
            bytes_freed=1024 * 1024 * 10,  # 10 MB
        )
        test_db.add(action1)

        # Process sender2 - unsubscribe
        action2 = CleanupAction(
            run_id=run.id,
            action_type="unsubscribe",
            sender_email=sender2.email,
            email_count=0,
        )
        test_db.add(action2)
        sender2.unsubscribed = True

        # Update run status
        run.senders_processed = 2
        run.emails_deleted = 200
        run.bytes_freed_estimate = 1024 * 1024 * 10
        run.status = "completed"
        run.finished_at = datetime.utcnow()

        await test_db.commit()
        await test_db.refresh(run)

        # Verify complete workflow
        assert run.status == "completed"
        assert run.senders_processed == 2
        assert run.emails_deleted == 200
        assert len(run.actions) == 2
        assert sender2.unsubscribed is True
