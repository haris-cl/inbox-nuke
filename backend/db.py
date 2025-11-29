"""
Database configuration and session management.
Uses SQLAlchemy async with SQLite for data persistence.
"""

import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase

from config import settings


# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.APP_ENV == "local",  # Log SQL queries in local environment
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Base class for all models
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.

    Yields:
        AsyncSession: Database session for the request
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """
    Initialize the database.
    Creates all tables and ensures data directory exists.
    """
    # Ensure data directory exists
    data_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite+aiosqlite:///", ""))
    if data_dir and not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        print(f"Created data directory: {data_dir}")

    # Import all models to ensure they are registered
    from models import (
        GmailCredentials,
        CleanupRun,
        Sender,
        CleanupAction,
        WhitelistDomain,
        EmailClassification,
        RetentionRule,
        Subscription,
        SenderProfile,
        EmailScore
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Database tables created successfully")
