"""
SQLAlchemy database models for Inbox Nuke.
Defines all database tables and relationships.
"""

from datetime import datetime
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db import Base


class GmailCredentials(Base):
    """
    Stores encrypted Gmail OAuth credentials for accessing user's mailbox.
    """
    __tablename__ = "gmail_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), unique=True, default="default_user")
    access_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)  # Encrypted
    token_expiry: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    scopes: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<GmailCredentials(user_id={self.user_id})>"


class CleanupRun(Base):
    """
    Represents a cleanup run/session.
    Tracks progress and statistics for each cleanup operation.
    """
    __tablename__ = "cleanup_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending"
        # Valid values: pending, running, paused, completed, cancelled, failed
    )
    started_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Progress tracking
    senders_total: Mapped[int] = mapped_column(Integer, default=0)
    senders_processed: Mapped[int] = mapped_column(Integer, default=0)
    emails_deleted: Mapped[int] = mapped_column(Integer, default=0)
    bytes_freed_estimate: Mapped[int] = mapped_column(BigInteger, default=0)
    progress_cursor: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON for resuming

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    actions: Mapped[List["CleanupAction"]] = relationship(
        "CleanupAction",
        back_populates="run",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CleanupRun(id={self.id}, status={self.status}, emails_deleted={self.emails_deleted})>"


class Sender(Base):
    """
    Represents a unique email sender discovered in the mailbox.
    Tracks metadata, unsubscribe information, and cleanup status.
    """
    __tablename__ = "senders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)

    # Unsubscribe information
    has_list_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribe_header: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    unsubscribe_method: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True
        # Valid values: mailto, http, none
    )
    unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Filter information
    filter_created: Mapped[bool] = mapped_column(Boolean, default=False)
    filter_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Timestamps
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Sender(email={self.email}, message_count={self.message_count})>"


# Create indexes for common queries
Index("idx_sender_domain", Sender.domain)
Index("idx_sender_email", Sender.email)


class CleanupAction(Base):
    """
    Log of individual actions taken during cleanup runs.
    Provides audit trail and detailed analytics.
    """
    __tablename__ = "cleanup_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("cleanup_runs.id"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
        # Valid values: unsubscribe, delete, filter, skip, error
    )
    sender_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_count: Mapped[int] = mapped_column(Integer, default=0)
    bytes_freed: Mapped[int] = mapped_column(BigInteger, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    run: Mapped["CleanupRun"] = relationship("CleanupRun", back_populates="actions")

    def __repr__(self) -> str:
        return f"<CleanupAction(type={self.action_type}, sender={self.sender_email}, count={self.email_count})>"


# Create index for querying actions by run
Index("idx_action_run_id", CleanupAction.run_id)


class WhitelistDomain(Base):
    """
    Domains that should never be processed for cleanup.
    User can whitelist important senders to protect them.
    """
    __tablename__ = "whitelist_domains"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    domain: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<WhitelistDomain(domain={self.domain})>"
