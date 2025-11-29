"""
Database migration script to add LLM tracking fields to EmailScore table.
Run this script once to add the llm_analyzed and llm_reasoning columns.

Usage:
    python migrate_add_llm_fields.py
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from db import async_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def migrate():
    """Add LLM tracking columns to EmailScore table."""

    async with async_engine.begin() as conn:
        # Check if columns already exist
        logger.info("Checking if LLM columns already exist...")

        try:
            # Try to query the column - if it exists, this won't fail
            result = await conn.execute(
                text("SELECT llm_analyzed FROM email_scores LIMIT 1")
            )
            logger.info("LLM columns already exist. No migration needed.")
            return
        except Exception:
            # Column doesn't exist, proceed with migration
            logger.info("LLM columns not found. Starting migration...")

        # Add llm_analyzed column
        logger.info("Adding llm_analyzed column...")
        await conn.execute(
            text("""
                ALTER TABLE email_scores
                ADD COLUMN llm_analyzed BOOLEAN NOT NULL DEFAULT 0
            """)
        )

        # Add llm_reasoning column
        logger.info("Adding llm_reasoning column...")
        await conn.execute(
            text("""
                ALTER TABLE email_scores
                ADD COLUMN llm_reasoning TEXT
            """)
        )

        logger.info("Migration complete! LLM tracking columns added successfully.")


async def main():
    """Main entry point."""
    try:
        logger.info("Starting database migration for LLM fields...")
        await migrate()
        logger.info("Migration completed successfully!")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        # Close the engine
        await async_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
