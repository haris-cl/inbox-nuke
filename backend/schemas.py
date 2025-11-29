"""
Pydantic schemas for API request/response validation.
Defines the structure of data exchanged between client and server.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
import json
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


# ============================================================================
# Health Check Schemas
# ============================================================================

class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    status: str = Field(..., examples=["healthy"])
    version: str = Field(..., examples=["1.0.0"])


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., examples=["Bad Request"])
    detail: Optional[str] = Field(None, examples=["Invalid input data"])


# ============================================================================
# Cleanup Run Schemas
# ============================================================================

class RunCreate(BaseModel):
    """Schema for creating a new cleanup run."""
    # No fields required for initial creation
    # Run is created in 'pending' status
    pass


class RunStatusUpdate(BaseModel):
    """Schema for updating run status."""
    status: str = Field(
        ...,
        pattern="^(pending|running|paused|completed|cancelled|failed)$",
        examples=["running"]
    )
    error_message: Optional[str] = Field(None, examples=["API rate limit exceeded"])


class RunResponse(BaseModel):
    """Response model for cleanup run information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    senders_total: int
    senders_processed: int
    emails_deleted: int
    bytes_freed_estimate: int
    error_message: Optional[str] = None
    created_at: datetime


# ============================================================================
# Sender Schemas
# ============================================================================

class SenderResponse(BaseModel):
    """Response model for sender information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    domain: str
    display_name: Optional[str] = None
    message_count: int
    has_list_unsubscribe: bool
    unsubscribe_method: Optional[str] = None
    unsubscribed: bool
    unsubscribed_at: Optional[datetime] = None
    filter_created: bool
    filter_id: Optional[str] = None
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime


class SenderListResponse(BaseModel):
    """Response model for paginated list of senders."""
    senders: List[SenderResponse]
    total: int
    page: int = Field(..., ge=1)
    page_size: int = Field(..., ge=1, le=100)
    total_pages: int


# ============================================================================
# Cleanup Action Schemas
# ============================================================================

class ActionResponse(BaseModel):
    """Response model for cleanup action information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: int
    timestamp: datetime
    action_type: str
    sender_email: Optional[str] = None
    email_count: int
    bytes_freed: int
    notes: Optional[str] = None


# ============================================================================
# Whitelist Schemas
# ============================================================================

class WhitelistCreate(BaseModel):
    """Schema for creating a whitelist entry."""
    domain: str = Field(
        ...,
        min_length=3,
        max_length=255,
        examples=["example.com"]
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        examples=["Important business communications"]
    )


class WhitelistResponse(BaseModel):
    """Response model for whitelist entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    reason: Optional[str] = None
    created_at: datetime


# ============================================================================
# Statistics Schemas
# ============================================================================

class StatsResponse(BaseModel):
    """Response model for overall statistics."""
    total_senders: int = Field(..., examples=[1234])
    total_emails_deleted: int = Field(..., examples=[45678])
    total_bytes_freed: int = Field(..., examples=[1234567890])
    total_unsubscribed: int = Field(..., examples=[567])
    total_filters_created: int = Field(..., examples=[234])
    total_runs: int = Field(..., examples=[12])
    last_run_at: Optional[datetime] = None


# ============================================================================
# OAuth Schemas
# ============================================================================

class OAuthURLResponse(BaseModel):
    """Response model for OAuth authorization URL."""
    auth_url: str = Field(..., examples=["https://accounts.google.com/o/oauth2/auth?..."])


class OAuthCallbackRequest(BaseModel):
    """Request model for OAuth callback."""
    code: str = Field(..., min_length=10)
    state: Optional[str] = None


class OAuthStatusResponse(BaseModel):
    """Response model for OAuth connection status."""
    connected: bool
    user_email: Optional[str] = None
    scopes: List[str] = []
    expires_at: Optional[datetime] = None


# ============================================================================
# Email Classification Schemas
# ============================================================================

class ClassificationScanRequest(BaseModel):
    """Request model for starting email classification scan."""
    max_emails: int = Field(default=100, ge=1, le=1000, examples=[100])
    force_rescan: bool = Field(default=False, examples=[False])


class ClassificationResultResponse(BaseModel):
    """Response model for email classification result."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: str
    sender_email: str
    subject: str
    classification: str  # KEEP, DELETE, REVIEW
    category: str  # financial, security, personal, documents, marketing, social, spam
    confidence: float
    reasoning: str
    user_override: Optional[str] = None
    processed_at: datetime
    created_at: datetime


class ClassificationListResponse(BaseModel):
    """Response model for paginated list of classifications."""
    classifications: List[ClassificationResultResponse]
    total: int
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


class ClassificationOverrideRequest(BaseModel):
    """Request model for overriding classification."""
    new_classification: str = Field(
        ...,
        pattern="^(KEEP|DELETE|REVIEW)$",
        examples=["KEEP"]
    )


class ClassificationExecuteRequest(BaseModel):
    """Request model for executing cleanup based on classifications."""
    dry_run: bool = Field(default=True, examples=[True])
    older_than_days: int = Field(default=30, ge=1, le=365, examples=[30])


class ClassificationStatsResponse(BaseModel):
    """Response model for classification statistics."""
    total_classified: int
    keep_count: int
    delete_count: int
    review_count: int
    by_category: dict  # category -> count mapping


# ============================================================================
# Subscription Schemas
# ============================================================================

class SubscriptionResponse(BaseModel):
    """Response model for subscription information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_email: str
    sender_name: Optional[str] = None
    email_count: int
    last_email_date: Optional[datetime] = None
    unsubscribe_url: Optional[str] = None
    unsubscribe_mailto: Optional[str] = None
    is_unsubscribed: bool
    unsubscribed_at: Optional[datetime] = None
    created_at: datetime


class SubscriptionListResponse(BaseModel):
    """Response model for paginated list of subscriptions."""
    subscriptions: List[SubscriptionResponse]
    total: int
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


class SubscriptionUnsubscribeRequest(BaseModel):
    """Request model for unsubscribing from a subscription."""
    method: Optional[str] = Field(
        None,
        pattern="^(mailto|http|auto)$",
        examples=["auto"]
    )


class SubscriptionCleanupRequest(BaseModel):
    """Request model for cleaning up subscription emails."""
    older_than_days: int = Field(default=30, ge=1, le=365, examples=[30])
    delete_all: bool = Field(default=False, examples=[False])


class BulkUnsubscribeRequest(BaseModel):
    """Request model for bulk unsubscribe."""
    subscription_ids: List[int] = Field(..., min_length=1, max_length=100)


class BulkUnsubscribeResponse(BaseModel):
    """Response model for bulk unsubscribe results."""
    total_requested: int
    successful: int
    failed: int
    errors: List[str] = []


# ============================================================================
# Retention Rule Schemas
# ============================================================================

class RetentionRuleCreate(BaseModel):
    """Schema for creating a retention rule."""
    rule_type: str = Field(
        ...,
        pattern="^(sender_email|sender_domain|subject_contains|label|has_attachment|is_conversation|older_than_days|category)$",
        examples=["sender_domain"]
    )
    pattern: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["example.com", "receipt", "true", "30"]
    )
    action: str = Field(
        ...,
        pattern="^(KEEP|DELETE|REVIEW)$",
        examples=["KEEP"]
    )
    priority: int = Field(
        default=50,
        ge=0,
        le=100,
        examples=[50]
    )
    enabled: bool = Field(default=True)
    description: str = Field(
        default="",
        max_length=500,
        examples=["Keep all emails from this domain"]
    )


class RetentionRuleUpdate(BaseModel):
    """Schema for updating a retention rule."""
    enabled: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
    description: Optional[str] = Field(None, max_length=500)


class RetentionRuleResponse(BaseModel):
    """Response model for retention rule."""
    index: int
    rule_type: str
    pattern: str
    action: str
    priority: int
    enabled: bool
    description: str


class RetentionRuleListResponse(BaseModel):
    """Response model for list of retention rules."""
    rules: List[RetentionRuleResponse]
    total: int


class EvaluationResultResponse(BaseModel):
    """Response model for email evaluation result."""
    action: str
    matching_rule: str
    priority: int
    confidence: int


class SenderEvaluationRequest(BaseModel):
    """Request model for evaluating a sender's emails."""
    sender_email: str = Field(..., examples=["newsletter@example.com"])
    max_emails: int = Field(default=100, ge=1, le=1000)


class SenderEvaluationResponse(BaseModel):
    """Response model for sender email evaluation."""
    sender_email: str
    total_emails: int
    keep_count: int
    delete_count: int
    review_count: int
    breakdown: Dict[str, int]
    error: Optional[str] = None


class CleanupPreviewResponse(BaseModel):
    """Response model for cleanup preview."""
    total_senders: int
    estimated_keep: int
    estimated_delete: int
    estimated_review: int
    top_delete_senders: List[Dict[str, Any]] = []
    top_keep_senders: List[Dict[str, Any]] = []


# ============================================================================
# Email Scoring Schemas (Multi-Signal System)
# ============================================================================

class EmailScoreResponse(BaseModel):
    """Response model for individual email score."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_id: str
    thread_id: str
    sender_email: str
    subject: str
    total_score: int
    classification: str
    confidence: float
    category_score: int
    header_score: int
    engagement_score: int
    keyword_score: int
    thread_score: int
    signal_details: Dict[str, Any]
    reasoning: str
    user_override: Optional[str]
    llm_analyzed: bool
    llm_reasoning: Optional[str]
    gmail_labels: List[str]
    scored_at: datetime
    created_at: datetime

    @field_validator("signal_details", mode="before")
    @classmethod
    def parse_signal_details(cls, v):
        """Parse signal_details from JSON string to dict."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return {}
        return v if v else {}

    @field_validator("gmail_labels", mode="before")
    @classmethod
    def parse_gmail_labels(cls, v):
        """Parse gmail_labels from JSON string to list."""
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return []
        return v if v else []


class SenderProfileResponse(BaseModel):
    """Response model for sender profile with aggregated scores."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_email: str
    sender_domain: str
    display_name: Optional[str]
    avg_score: float
    email_count: int
    classification: str
    user_replied_count: int
    starred_count: int
    primary_count: int
    promotions_count: int
    social_count: int
    updates_count: int
    has_unsubscribe: bool
    first_seen: datetime
    last_seen: datetime
    created_at: datetime
    updated_at: datetime


class ScoringStartRequest(BaseModel):
    """Request model for starting email scoring scan."""
    max_emails: int = Field(default=10000, ge=1, le=50000, examples=[10000])
    rescan: bool = Field(default=False, examples=[False])


class ScoringProgressResponse(BaseModel):
    """Response model for scoring progress tracking."""
    status: str  # idle, running, completed, failed
    total_emails: int
    scored_emails: int
    keep_count: int
    delete_count: int
    uncertain_count: int
    current_sender: Optional[str]
    error: Optional[str]


class ScoringStatsResponse(BaseModel):
    """Response model for scoring statistics."""
    total_scored: int
    keep_count: int
    delete_count: int
    uncertain_count: int
    avg_score: float
    score_distribution: Dict[str, int]  # {0-10: count, 11-20: count, ...}
    top_delete_senders: List[Dict[str, Any]]
    top_keep_senders: List[Dict[str, Any]]
    categories_breakdown: Dict[str, int]


class ScoreOverrideRequest(BaseModel):
    """Request model for overriding email score classification."""
    classification: str = Field(
        ...,
        pattern="^(KEEP|DELETE)$",
        examples=["KEEP"]
    )


class BulkScoreActionRequest(BaseModel):
    """Request model for bulk cleanup based on scores."""
    classification: str = Field(
        ...,
        pattern="^(DELETE|KEEP)$",
        examples=["DELETE"]
    )
    sender_emails: Optional[List[str]] = Field(
        None,
        examples=[["newsletter@example.com", "promo@shop.com"]]
    )
    min_score: Optional[int] = Field(None, ge=0, le=100, examples=[0])
    max_score: Optional[int] = Field(None, ge=0, le=100, examples=[30])


class EmailScoreListResponse(BaseModel):
    """Response model for paginated list of email scores."""
    emails: List[EmailScoreResponse]
    total: int
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


class SenderProfileListResponse(BaseModel):
    """Response model for paginated list of sender profiles."""
    senders: List[SenderProfileResponse]
    total: int
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)


# ============================================================================
# V2 Cleanup Flow Schemas
# ============================================================================


class CleanupStartRequest(BaseModel):
    """Request model for starting V2 cleanup wizard."""
    max_emails: int = Field(default=10000, ge=100, le=50000, examples=[10000])


class CleanupStartResponse(BaseModel):
    """Response model for starting cleanup wizard."""
    session_id: str
    status: str = "scanning"


class ActiveSessionResponse(BaseModel):
    """Response model for checking active/incomplete sessions."""
    has_active_session: bool
    session_id: Optional[str] = None
    status: Optional[str] = None
    mode: Optional[str] = None
    progress: float = 0.0
    total_emails: int = 0
    scanned_emails: int = 0
    total_to_cleanup: int = 0
    total_protected: int = 0
    created_at: Optional[datetime] = None
    # Where in the wizard flow the user can resume
    resume_step: Optional[str] = None  # scanning, report, review, unsubscribe, confirm


class SessionListItem(BaseModel):
    """Single session in the sessions list."""
    session_id: str
    status: str
    mode: Optional[str] = None
    total_emails: int = 0
    scanned_emails: int = 0
    total_to_cleanup: int = 0
    total_protected: int = 0
    emails_deleted: int = 0
    space_freed: int = 0
    senders_unsubscribed: int = 0
    created_at: datetime
    completed_at: Optional[datetime] = None
    can_take_action: bool = False  # True if scan completed and has pending actions


class SessionListResponse(BaseModel):
    """Response model for listing cleanup sessions."""
    sessions: List[SessionListItem]
    total: int


class CleanupDiscoveries(BaseModel):
    """Model for scan discoveries breakdown."""
    promotions: int = 0
    newsletters: int = 0
    social: int = 0
    updates: int = 0
    low_value: int = 0


class CleanupProgressResponse(BaseModel):
    """Response model for cleanup progress polling."""
    session_id: str
    status: str  # scanning, ready_for_review, reviewing, confirming, executing, completed, failed
    progress: float  # 0.0 to 1.0
    total_emails: int
    scanned_emails: int
    discoveries: CleanupDiscoveries
    error: Optional[str] = None


class SenderRecommendation(BaseModel):
    """Model for sender recommendation in report."""
    email: str
    display_name: Optional[str] = None
    count: int
    reason: str


class RecommendationSummary(BaseModel):
    """Response model for cleanup recommendations summary (Inbox Report)."""
    session_id: str
    total_to_cleanup: int
    total_protected: int
    space_savings: int  # bytes
    category_breakdown: Dict[str, int]  # {"promotions": 2100, "newsletters": 1400, ...}
    protected_reasons: List[str]  # ["892 emails from people you email with", ...]
    top_delete_senders: List[SenderRecommendation]
    top_keep_senders: List[SenderRecommendation]


class ReviewItem(BaseModel):
    """Model for single review queue item."""
    message_id: str
    sender_email: str
    sender_name: Optional[str] = None
    subject: str
    date: datetime
    snippet: str
    ai_suggestion: str  # keep, delete
    reasoning: str
    confidence: float
    category: str


class ReviewQueueResponse(BaseModel):
    """Response model for review queue."""
    session_id: str
    mode: str  # quick, full
    total_items: int
    items: List[ReviewItem]


class ReviewDecisionRequest(BaseModel):
    """Request model for review decision."""
    message_id: str
    decision: str = Field(..., pattern="^(keep|delete)$", examples=["keep"])


class ReviewDecisionResponse(BaseModel):
    """Response model for review decision."""
    message_id: str
    decision: str
    remaining_in_queue: int


class ModeSelectRequest(BaseModel):
    """Request model for selecting cleanup mode."""
    mode: str = Field(..., pattern="^(quick|full)$", examples=["quick"])


class SafetyInfo(BaseModel):
    """Model for safety information in confirmation."""
    trash_recovery_days: int = 30
    auto_protected_categories: List[str]


class ConfirmationSummary(BaseModel):
    """Response model for confirmation screen."""
    session_id: str
    emails_to_delete: int
    senders_to_unsubscribe: int
    space_to_be_freed: int  # bytes
    protected_count: int
    safety_info: SafetyInfo


class CleanupExecuteRequest(BaseModel):
    """Request model for executing cleanup."""
    confirmed: bool = True


class CleanupExecuteResponse(BaseModel):
    """Response model for cleanup execution start."""
    session_id: str
    status: str  # executing
    job_id: str


class CleanupResults(BaseModel):
    """Response model for cleanup results."""
    session_id: str
    status: str  # executing, completed, failed
    emails_deleted: int
    space_freed: int  # bytes
    senders_unsubscribed: int
    filters_created: int
    errors: List[str] = []
    completed_at: Optional[datetime] = None


# ============================================================================
# V2 Inbox Health Schemas
# ============================================================================


class InboxHealthResponse(BaseModel):
    """Response model for inbox health status."""
    status: str  # healthy, needs_attention, critical
    potential_cleanup_count: int
    potential_space_savings: int  # bytes
    last_scan_at: Optional[datetime] = None
    categories: Dict[str, int] = {}  # {"promotions": 1200, "social": 450, ...}


class ProtectedCategory(BaseModel):
    """Model for auto-protected category."""
    name: str
    description: str
    icon: str


class AutoProtectedResponse(BaseModel):
    """Response model for auto-protected categories."""
    categories: List[ProtectedCategory]


# ============================================================================
# V2 Unsubscribe Schemas
# ============================================================================


class UnsubscribableSender(BaseModel):
    """Model for a sender that can be unsubscribed from."""
    email: str
    display_name: Optional[str] = None
    email_count: int
    has_one_click: bool  # RFC 8058 one-click support
    unsubscribe_method: str  # "one_click", "mailto", "http"
    selected: bool = False  # User's selection


class UnsubscribeSendersResponse(BaseModel):
    """Response model for unsubscribable senders list."""
    session_id: str
    senders: List[UnsubscribableSender]
    total_count: int


class UpdateUnsubscribeSelectionsRequest(BaseModel):
    """Request model for updating unsubscribe selections."""
    sender_emails: List[str]  # List of sender emails to unsubscribe from


class UpdateUnsubscribeSelectionsResponse(BaseModel):
    """Response model for updating unsubscribe selections."""
    session_id: str
    selected_count: int
