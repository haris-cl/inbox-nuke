"""
Pytest configuration and fixtures for Inbox Nuke tests.
Provides common test fixtures including test database and mock Gmail client.
"""

import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from db import Base, get_db
from gmail_client import GmailClient
from models import GmailCredentials, CleanupRun, Sender, WhitelistDomain


# ============================================================================
# Pytest Configuration
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """
    Create an event loop for async tests.
    This fixture is session-scoped to allow async fixtures.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Database Fixtures
# ============================================================================


@pytest.fixture
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session using SQLite in-memory database.

    Yields:
        AsyncSession: Test database session

    Notes:
        - Uses SQLite in-memory for fast, isolated tests
        - Database is created fresh for each test
        - All tables are dropped after test completes
    """
    # Create in-memory SQLite database
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        echo=False,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def test_db_with_data(test_db: AsyncSession) -> AsyncSession:
    """
    Create a test database with sample data.

    Args:
        test_db: Test database session

    Returns:
        AsyncSession: Database session with sample data
    """
    # Add sample Gmail credentials
    creds = GmailCredentials(
        user_id="test_user",
        access_token="encrypted_test_access_token",
        refresh_token="encrypted_test_refresh_token",
        token_expiry=asyncio.get_event_loop().time() + 3600,  # 1 hour from now
        scopes='["https://www.googleapis.com/auth/gmail.modify"]',
    )
    test_db.add(creds)

    # Add sample senders
    senders_data = [
        {
            "email": "newsletter@example.com",
            "domain": "example.com",
            "display_name": "Example Newsletter",
            "message_count": 100,
            "has_list_unsubscribe": True,
            "unsubscribe_method": "mailto",
            "unsubscribed": False,
        },
        {
            "email": "noreply@bank.com",
            "domain": "bank.com",
            "display_name": "Bank Alerts",
            "message_count": 25,
            "has_list_unsubscribe": False,
            "unsubscribed": False,
        },
        {
            "email": "spam@marketing.com",
            "domain": "marketing.com",
            "display_name": "Marketing Corp",
            "message_count": 500,
            "has_list_unsubscribe": True,
            "unsubscribe_method": "http",
            "unsubscribed": True,
        },
    ]

    for sender_data in senders_data:
        sender = Sender(**sender_data)
        test_db.add(sender)

    # Add sample whitelist domains
    whitelist_domains = [
        {"domain": "important.com", "reason": "Important business emails"},
        {"domain": "family.com", "reason": "Family emails"},
    ]

    for domain_data in whitelist_domains:
        domain = WhitelistDomain(**domain_data)
        test_db.add(domain)

    # Add sample cleanup run
    run = CleanupRun(
        status="completed",
        senders_total=10,
        senders_processed=10,
        emails_deleted=150,
        bytes_freed_estimate=1024 * 1024 * 50,  # 50 MB
    )
    test_db.add(run)

    await test_db.commit()

    return test_db


# ============================================================================
# Gmail Client Fixtures
# ============================================================================


@pytest.fixture
def mock_gmail_service():
    """
    Create a mock Gmail API service.

    Returns:
        MagicMock: Mock Gmail service
    """
    service = MagicMock()

    # Mock users().messages() methods
    messages = MagicMock()
    service.users.return_value.messages.return_value = messages

    # Mock list method
    messages.list.return_value.execute.return_value = {
        "messages": [
            {"id": "msg1", "threadId": "thread1"},
            {"id": "msg2", "threadId": "thread2"},
        ],
        "resultSizeEstimate": 2,
    }

    # Mock get method
    messages.get.return_value.execute.return_value = {
        "id": "msg1",
        "threadId": "thread1",
        "labelIds": ["INBOX"],
        "snippet": "This is a test email",
        "payload": {
            "headers": [
                {"name": "From", "value": "test@example.com"},
                {"name": "Subject", "value": "Test Email"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
            ],
        },
        "sizeEstimate": 1024,
    }

    # Mock batchModify method
    messages.batchModify.return_value.execute.return_value = {}

    # Mock trash method
    messages.trash.return_value.execute.return_value = {}

    return service


@pytest.fixture
async def mock_gmail_client(test_db: AsyncSession, mock_gmail_service):
    """
    Create a mock Gmail client for testing.

    Args:
        test_db: Test database session
        mock_gmail_service: Mock Gmail service

    Returns:
        GmailClient: Gmail client with mocked service
    """
    client = GmailClient(db=test_db, user_id="test_user")
    client._service = mock_gmail_service
    return client


# ============================================================================
# Sample Data Fixtures
# ============================================================================


@pytest.fixture
def sample_gmail_message():
    """
    Create a sample Gmail message dict for testing.

    Returns:
        dict: Sample Gmail message
    """
    return {
        "id": "test_msg_123",
        "threadId": "test_thread_123",
        "labelIds": ["INBOX", "UNREAD"],
        "snippet": "This is a test email snippet for testing purposes",
        "payload": {
            "headers": [
                {"name": "From", "value": "Test Sender <test@example.com>"},
                {"name": "Subject", "value": "Test Email Subject"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
                {
                    "name": "List-Unsubscribe",
                    "value": "<mailto:unsubscribe@example.com?subject=unsubscribe>",
                },
            ],
            "mimeType": "text/plain",
        },
        "sizeEstimate": 2048,
    }


@pytest.fixture
def sample_protected_message():
    """
    Create a sample protected Gmail message (e.g., from bank) for testing.

    Returns:
        dict: Sample protected Gmail message
    """
    return {
        "id": "bank_msg_456",
        "threadId": "bank_thread_456",
        "labelIds": ["INBOX"],
        "snippet": "Your account statement is ready for review",
        "payload": {
            "headers": [
                {"name": "From", "value": "Bank Alerts <noreply@chase.com>"},
                {"name": "Subject", "value": "Account Statement Ready"},
                {"name": "Date", "value": "Mon, 1 Jan 2024 12:00:00 +0000"},
            ],
            "mimeType": "text/html",
        },
        "sizeEstimate": 4096,
    }


# ============================================================================
# Helper Fixtures
# ============================================================================


@pytest.fixture
def mock_datetime(monkeypatch):
    """
    Mock datetime for consistent testing.

    Usage:
        def test_something(mock_datetime):
            # datetime.utcnow() will return fixed time
            pass
    """
    from datetime import datetime
    from unittest.mock import Mock

    mock_dt = Mock()
    mock_dt.utcnow.return_value = datetime(2024, 1, 1, 12, 0, 0)
    monkeypatch.setattr("datetime.datetime", mock_dt)
    return mock_dt
