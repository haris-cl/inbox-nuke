"""
Configuration management using Pydantic settings.
Loads environment variables and provides type-safe configuration.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses pydantic-settings for validation and type safety.
    """

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/auth/callback"

    # OpenAI Configuration (optional)
    OPENAI_API_KEY: Optional[str] = None

    # Encryption Configuration
    ENCRYPTION_KEY: str = ""

    # Application Configuration
    APP_ENV: str = "local"  # local, development, staging, production
    FRONTEND_URL: str = "http://localhost:3000"

    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/inbox_nuke.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"

    def is_local(self) -> bool:
        """Check if running in local environment."""
        return self.APP_ENV == "local"


# Global settings instance
settings = Settings()
