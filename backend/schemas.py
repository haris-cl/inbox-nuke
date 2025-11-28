"""
Pydantic schemas for API request/response validation.
Defines the structure of data exchanged between client and server.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict


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
