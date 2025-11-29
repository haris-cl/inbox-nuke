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
    Float,
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


class EmailClassification(Base):
    """
    Store AI classification results for emails.
    Determines whether emails should be kept or deleted.
    """
    __tablename__ = "email_classifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
        # Valid values: KEEP, DELETE, REVIEW
    )
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
        # Valid values: financial, security, personal, documents, marketing, social, spam
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    user_override: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # User can override
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EmailClassification(message_id={self.message_id}, classification={self.classification})>"


# Create indexes for email classifications
Index("idx_classification_classification", EmailClassification.classification)
Index("idx_classification_category", EmailClassification.category)
Index("idx_classification_sender", EmailClassification.sender_email)


class RetentionRule(Base):
    """
    User-defined retention rules for automatic email classification.
    Allows users to create custom rules for keeping or deleting emails.
    """
    __tablename__ = "retention_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
        # Valid values: sender, domain, subject_contains, label
    )
    pattern: Mapped[str] = mapped_column(String(255), nullable=False)
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False
        # Valid values: KEEP, DELETE
    )
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<RetentionRule(type={self.rule_type}, pattern={self.pattern}, action={self.action})>"


# Create index for retention rules priority
Index("idx_retention_priority", RetentionRule.priority)


class Subscription(Base):
    """
    Track Gmail subscriptions and mailing lists.
    Stores information about detected subscriptions for management and cleanup.
    """
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_email_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    unsubscribe_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unsubscribe_mailto: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_unsubscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Subscription(sender_email={self.sender_email}, count={self.email_count})>"


# Create index for subscriptions
Index("idx_subscription_sender", Subscription.sender_email)
Index("idx_subscription_unsubscribed", Subscription.is_unsubscribed)


class SenderProfile(Base):
    """
    Tracks sender-level scoring data with aggregated scores and engagement metrics.
    Used for multi-signal email scoring system.
    """
    __tablename__ = "sender_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sender_email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    sender_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Aggregated scores
    avg_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    email_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="UNCERTAIN",
        index=True
        # Valid values: KEEP, DELETE, UNCERTAIN
    )

    # Engagement stats
    user_replied_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    starred_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Category breakdown
    primary_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    promotions_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    social_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updates_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Metadata
    has_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    first_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<SenderProfile(email={self.sender_email}, avg_score={self.avg_score}, classification={self.classification})>"


# Create indexes for sender profiles
Index("idx_sender_profile_email", SenderProfile.sender_email)
Index("idx_sender_profile_domain", SenderProfile.sender_domain)
Index("idx_sender_profile_classification", SenderProfile.classification)


class EmailScore(Base):
    """
    Stores individual email scores with multi-signal breakdown.
    Tracks classification, confidence, and detailed signal contributions.
    """
    __tablename__ = "email_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str] = mapped_column(Text, nullable=False)

    # Scoring
    total_score: Mapped[int] = mapped_column(Integer, nullable=False)  # 0-100
    classification: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True
        # Valid values: KEEP, DELETE, UNCERTAIN
    )
    confidence: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0-1.0

    # Individual signal scores
    category_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    header_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    engagement_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    keyword_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    thread_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Signal details (JSON)
    signal_details: Mapped[str] = mapped_column(Text, nullable=False, default="{}")  # JSON string with breakdown
    reasoning: Mapped[str] = mapped_column(Text, nullable=False, default="")

    # User feedback
    user_override: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # User can override

    # LLM analysis tracking (Phase 2)
    llm_analyzed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    llm_reasoning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    gmail_labels: Mapped[str] = mapped_column(Text, nullable=False, default="[]")  # JSON array of label IDs
    scored_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<EmailScore(message_id={self.message_id}, total_score={self.total_score}, classification={self.classification})>"


# Create indexes for email scores
Index("idx_email_score_message_id", EmailScore.message_id)
Index("idx_email_score_thread_id", EmailScore.thread_id)
Index("idx_email_score_sender", EmailScore.sender_email)
Index("idx_email_score_classification", EmailScore.classification)
Index("idx_email_score_total_score", EmailScore.total_score)


class UserFeedback(Base):
    """
    Store user feedback on email/sender classifications.
    Used to learn user preferences over time.
    """
    __tablename__ = "user_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # What the feedback is about
    feedback_type: Mapped[str] = mapped_column(String(50))  # email, sender
    target_id: Mapped[str] = mapped_column(String(255), index=True)  # message_id or sender_email

    # Original vs corrected classification
    original_classification: Mapped[str] = mapped_column(String(50))
    corrected_classification: Mapped[str] = mapped_column(String(50))

    # Additional context
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UserFeedback(type={self.feedback_type}, target={self.target_id}, corrected={self.corrected_classification})>"


Index("idx_feedback_target", UserFeedback.feedback_type, UserFeedback.target_id)


class UserPreference(Base):
    """
    Learned user preferences from feedback.
    Automatically adjusts scoring weights based on user behavior.
    """
    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # Preference type
    pref_type: Mapped[str] = mapped_column(String(50))  # sender, domain, keyword
    pattern: Mapped[str] = mapped_column(String(255), index=True)

    # Classification and confidence
    classification: Mapped[str] = mapped_column(String(50))  # KEEP, DELETE
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # Learning stats
    feedback_count: Mapped[int] = mapped_column(Integer, default=1)
    last_feedback: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<UserPreference(type={self.pref_type}, pattern={self.pattern}, classification={self.classification})>"


Index("idx_preference_pattern", UserPreference.pref_type, UserPreference.pattern)


# ============================================================================
# V2 Cleanup Flow Models
# ============================================================================


class CleanupSession(Base):
    """
    V2: Tracks cleanup wizard sessions.
    Each time a user starts the cleanup wizard, a new session is created.
    """
    __tablename__ = "cleanup_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), unique=True, nullable=False, index=True)  # UUID
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="scanning"
        # Valid values: scanning, ready_for_review, reviewing, confirming, executing, completed, failed
    )
    mode: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # quick, full

    # Scanning progress
    total_emails: Mapped[int] = mapped_column(Integer, default=0)
    scanned_emails: Mapped[int] = mapped_column(Integer, default=0)

    # Discoveries (JSON)
    discoveries: Mapped[str] = mapped_column(Text, default="{}")  # {"promotions": 100, "newsletters": 50, ...}

    # Recommendations summary
    total_to_cleanup: Mapped[int] = mapped_column(Integer, default=0)
    total_protected: Mapped[int] = mapped_column(Integer, default=0)
    space_savings: Mapped[int] = mapped_column(BigInteger, default=0)

    # Review decisions (JSON) - {message_id: "keep"|"delete"}
    review_decisions: Mapped[str] = mapped_column(Text, default="{}")

    # Final results
    emails_deleted: Mapped[int] = mapped_column(Integer, default=0)
    space_freed: Mapped[int] = mapped_column(BigInteger, default=0)
    senders_unsubscribed: Mapped[int] = mapped_column(Integer, default=0)
    filters_created: Mapped[int] = mapped_column(Integer, default=0)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    recommendations: Mapped[List["EmailRecommendation"]] = relationship(
        "EmailRecommendation",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CleanupSession(session_id={self.session_id}, status={self.status})>"


Index("idx_cleanup_session_id", CleanupSession.session_id)
Index("idx_cleanup_session_status", CleanupSession.status)


class EmailRecommendation(Base):
    """
    V2: Stores per-email recommendations during cleanup flow.
    Each scanned email gets a recommendation (keep/delete) with reasoning.
    """
    __tablename__ = "email_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("cleanup_sessions.session_id", ondelete="CASCADE"), nullable=False)
    message_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Sender info
    sender_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sender_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Email content
    subject: Mapped[str] = mapped_column(Text, nullable=False)
    snippet: Mapped[str] = mapped_column(Text, default="")
    received_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)

    # AI recommendation
    ai_suggestion: Mapped[str] = mapped_column(String(20), nullable=False)  # keep, delete
    reasoning: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.5)

    # User decision (null if not reviewed)
    user_decision: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # keep, delete

    # Categorization
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # Valid: promotions, newsletters, social, updates, low_value, protected

    # Gmail labels
    gmail_labels: Mapped[str] = mapped_column(Text, default="[]")  # JSON array

    # Unsubscribe info (RFC 8058)
    has_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=False)
    unsubscribe_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    unsubscribe_mailto: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unsubscribe_one_click: Mapped[bool] = mapped_column(Boolean, default=False)  # RFC 8058 support
    user_wants_unsubscribe: Mapped[bool] = mapped_column(Boolean, default=False)  # User selection

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    session: Mapped["CleanupSession"] = relationship("CleanupSession", back_populates="recommendations")

    def __repr__(self) -> str:
        return f"<EmailRecommendation(message_id={self.message_id}, ai_suggestion={self.ai_suggestion})>"


Index("idx_recommendation_session", EmailRecommendation.session_id)
Index("idx_recommendation_message", EmailRecommendation.message_id)
Index("idx_recommendation_suggestion", EmailRecommendation.ai_suggestion)
Index("idx_recommendation_category", EmailRecommendation.category)
