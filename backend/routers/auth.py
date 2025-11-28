"""
Authentication router for OAuth flow with Google.
Handles OAuth authorization, callback, and credential management.
"""

import json
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from db import get_db
from models import GmailCredentials
from schemas import OAuthStatusResponse, OAuthURLResponse
from utils.encryption import decrypt_token, encrypt_token

router = APIRouter()

# OAuth scopes required for Gmail operations
SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/userinfo.email",
]

# In-memory state storage for CSRF protection
# TODO: Replace with Redis or database for production
_oauth_states = {}


def _create_flow() -> Flow:
    """
    Create OAuth flow instance for Google authentication.

    Returns:
        Flow: Configured OAuth flow instance

    Raises:
        ValueError: If OAuth credentials are not configured
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError(
            "Google OAuth credentials not configured. "
            "Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables."
        )

    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    return flow


@router.get("/google/start", response_model=OAuthURLResponse)
async def start_oauth() -> OAuthURLResponse:
    """
    Generate Google OAuth authorization URL.

    Returns:
        OAuthURLResponse: Authorization URL for frontend to redirect to

    Raises:
        HTTPException: If OAuth flow creation fails
    """
    try:
        flow = _create_flow()

        # Generate CSRF state token
        state = secrets.token_urlsafe(32)

        # Store state with expiry (5 minutes)
        _oauth_states[state] = {
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(minutes=5),
        }

        # Generate authorization URL
        authorization_url, _ = flow.authorization_url(
            access_type="offline",
            state=state,
            prompt="consent",  # Force consent screen to get refresh token
        )

        return OAuthURLResponse(auth_url=authorization_url)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate OAuth URL: {str(e)}",
        )


@router.get("/google/callback")
async def oauth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str = Query(..., description="CSRF state token"),
    error: Optional[str] = Query(None, description="Error from OAuth provider"),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """
    Handle OAuth callback from Google.

    Args:
        code: Authorization code from Google
        state: CSRF state token for validation
        error: Error message if user denied or OAuth failed
        db: Database session

    Returns:
        RedirectResponse: Redirect to frontend with success/error status

    Raises:
        HTTPException: If callback processing fails
    """
    # Check if user denied access
    if error:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?error=access_denied&message={error}"
        )

    # Validate state token
    if state not in _oauth_states:
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?error=invalid_state&message=Invalid or expired state token"
        )

    # Check state expiry
    state_data = _oauth_states[state]
    if datetime.utcnow() > state_data["expires_at"]:
        del _oauth_states[state]
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?error=expired_state&message=State token expired"
        )

    # Remove used state token
    del _oauth_states[state]

    try:
        # Exchange authorization code for tokens
        flow = _create_flow()
        flow.fetch_token(code=code)

        credentials = flow.credentials

        # Get user email from Google
        service = build("oauth2", "v2", credentials=credentials)
        user_info = service.userinfo().get().execute()
        user_email = user_info.get("email")

        if not user_email:
            raise ValueError("Failed to retrieve user email from Google")

        # Encrypt tokens before storing
        encrypted_access_token = encrypt_token(credentials.token)
        encrypted_refresh_token = encrypt_token(credentials.refresh_token or "")

        # Check if credentials already exist
        stmt = select(GmailCredentials).where(
            GmailCredentials.user_id == "default_user"
        )
        result = await db.execute(stmt)
        existing_creds = result.scalar_one_or_none()

        if existing_creds:
            # Update existing credentials
            existing_creds.access_token = encrypted_access_token
            existing_creds.refresh_token = encrypted_refresh_token
            existing_creds.token_expiry = credentials.expiry
            existing_creds.scopes = json.dumps(list(credentials.scopes))
            existing_creds.updated_at = datetime.utcnow()
        else:
            # Create new credentials
            new_creds = GmailCredentials(
                user_id="default_user",
                access_token=encrypted_access_token,
                refresh_token=encrypted_refresh_token,
                token_expiry=credentials.expiry,
                scopes=json.dumps(list(credentials.scopes)),
            )
            db.add(new_creds)

        await db.commit()

        # Redirect to frontend with success
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?success=true&email={user_email}"
        )

    except Exception as e:
        await db.rollback()
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?error=token_exchange_failed&message={str(e)}"
        )


@router.get("/status", response_model=OAuthStatusResponse)
async def get_auth_status(db: AsyncSession = Depends(get_db)) -> OAuthStatusResponse:
    """
    Get current authentication status.

    Args:
        db: Database session

    Returns:
        OAuthStatusResponse: Current authentication status and user info
    """
    try:
        # Query stored credentials
        stmt = select(GmailCredentials).where(
            GmailCredentials.user_id == "default_user"
        )
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if not creds:
            return OAuthStatusResponse(
                connected=False,
                user_email=None,
                scopes=[],
                expires_at=None,
            )

        # Decrypt tokens to create credentials object
        try:
            access_token = decrypt_token(creds.access_token)
            refresh_token = decrypt_token(creds.refresh_token) if creds.refresh_token else None

            credentials = Credentials(
                token=access_token,
                refresh_token=refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=json.loads(creds.scopes),
            )

            # Get user email from Google
            service = build("oauth2", "v2", credentials=credentials)
            user_info = service.userinfo().get().execute()
            user_email = user_info.get("email")

            return OAuthStatusResponse(
                connected=True,
                user_email=user_email,
                scopes=json.loads(creds.scopes),
                expires_at=creds.token_expiry,
            )

        except Exception as e:
            # If token is invalid or expired, return disconnected status
            return OAuthStatusResponse(
                connected=False,
                user_email=None,
                scopes=[],
                expires_at=None,
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auth status: {str(e)}",
        )


@router.post("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_account(db: AsyncSession = Depends(get_db)) -> None:
    """
    Disconnect Gmail account by removing stored credentials.

    Args:
        db: Database session

    Raises:
        HTTPException: If disconnect operation fails
    """
    try:
        # Query stored credentials
        stmt = select(GmailCredentials).where(
            GmailCredentials.user_id == "default_user"
        )
        result = await db.execute(stmt)
        creds = result.scalar_one_or_none()

        if creds:
            # Optional: Revoke token with Google
            try:
                access_token = decrypt_token(creds.access_token)
                credentials = Credentials(token=access_token)
                credentials.revoke(
                    "https://oauth2.googleapis.com/revoke"
                )
            except Exception as revoke_error:
                # Log error but don't fail the disconnect operation
                print(f"Failed to revoke token with Google: {revoke_error}")

            # Delete credentials from database
            await db.delete(creds)
            await db.commit()

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to disconnect account: {str(e)}",
        )
