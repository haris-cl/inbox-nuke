"""
Inbox Nuke API - Main FastAPI Application
"""

import os
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from db import init_db
from schemas import HealthResponse, ErrorResponse

# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup: Initialize database
    print("Starting up Inbox Nuke API...")
    await init_db()
    print("Database initialized successfully")

    # Initialize background task scheduler
    from agent import init_scheduler
    init_scheduler()
    print("Background task scheduler initialized")

    yield

    # Shutdown: Stop scheduler and cleanup
    print("Shutting down Inbox Nuke API...")
    from agent import shutdown_scheduler
    shutdown_scheduler()
    print("Background task scheduler stopped")


# Initialize FastAPI application
app = FastAPI(
    title="Inbox Nuke API",
    version="1.0.0",
    description="AI-powered Gmail cleanup automation API",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Basic error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    """
    Global error handling middleware.
    Catches unhandled exceptions and returns proper JSON responses.
    """
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        print(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc) if settings.APP_ENV != "production" else "An unexpected error occurred",
            },
        )


# Health check endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify API is running.

    Returns:
        HealthResponse: Status and version information
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint with API information.

    Returns:
        dict: Welcome message and API info
    """
    return {
        "message": "Welcome to Inbox Nuke API",
        "version": "1.0.0",
        "docs": "/docs",
    }


# Import routers
from routers import attachments, auth, exports, runs, senders, stats, whitelist, retention, classification, subscriptions, scoring, feedback, cleanup

# Include routers with prefixes
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(runs.router, prefix="/api/runs", tags=["Runs"])
app.include_router(senders.router, prefix="/api/senders", tags=["Senders"])
app.include_router(whitelist.router, prefix="/api/whitelist", tags=["Whitelist"])
app.include_router(stats.router, prefix="/api/stats", tags=["Statistics"])
app.include_router(exports.router, prefix="/api/exports", tags=["Exports"])
app.include_router(attachments.router, prefix="/api/attachments", tags=["Attachments"])
app.include_router(retention.router, prefix="/api/retention", tags=["Retention"])
app.include_router(classification.router, prefix="/api/classification", tags=["Classification"])
app.include_router(subscriptions.router, prefix="/api/subscriptions", tags=["Subscriptions"])
app.include_router(scoring.router, prefix="/api/scoring", tags=["Scoring"])
app.include_router(feedback.router, prefix="/api/feedback", tags=["Feedback"])

# V2 Cleanup Wizard Router
app.include_router(cleanup.router, prefix="/api/cleanup", tags=["V2 Cleanup Wizard"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.APP_ENV != "production",
    )
