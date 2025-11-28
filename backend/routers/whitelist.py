"""
Whitelist router for managing protected domains.
Handles adding, listing, and removing whitelisted domains.
"""

import re
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from models import WhitelistDomain
from schemas import WhitelistCreate, WhitelistResponse

router = APIRouter()

# Domain validation regex pattern
DOMAIN_PATTERN = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$"
)


def validate_domain(domain: str) -> bool:
    """
    Validate domain format.

    Args:
        domain: Domain to validate

    Returns:
        bool: True if valid, False otherwise
    """
    if not domain or len(domain) > 255:
        return False
    return bool(DOMAIN_PATTERN.match(domain))


@router.get("", response_model=List[WhitelistResponse])
async def list_whitelist(
    db: AsyncSession = Depends(get_db),
) -> List[WhitelistResponse]:
    """
    List all whitelisted domains.

    Args:
        db: Database session

    Returns:
        List[WhitelistResponse]: List of whitelisted domains

    Raises:
        HTTPException: If query fails
    """
    try:
        stmt = select(WhitelistDomain).order_by(WhitelistDomain.domain)
        result = await db.execute(stmt)
        domains = result.scalars().all()

        return [WhitelistResponse.model_validate(domain) for domain in domains]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list whitelist: {str(e)}",
        )


@router.post("", response_model=WhitelistResponse, status_code=status.HTTP_201_CREATED)
async def add_to_whitelist(
    whitelist_data: WhitelistCreate,
    db: AsyncSession = Depends(get_db),
) -> WhitelistResponse:
    """
    Add a domain to the whitelist.

    Args:
        whitelist_data: Domain and optional reason
        db: Database session

    Returns:
        WhitelistResponse: Created whitelist entry

    Raises:
        HTTPException: If domain is invalid or already exists
    """
    try:
        # Validate domain format
        domain_lower = whitelist_data.domain.lower().strip()

        if not validate_domain(domain_lower):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid domain format: {whitelist_data.domain}",
            )

        # Check if domain already exists
        stmt = select(WhitelistDomain).where(WhitelistDomain.domain == domain_lower)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Domain '{domain_lower}' is already whitelisted",
            )

        # Create whitelist entry
        new_entry = WhitelistDomain(
            domain=domain_lower,
            reason=whitelist_data.reason,
        )
        db.add(new_entry)
        await db.commit()
        await db.refresh(new_entry)

        return WhitelistResponse.model_validate(new_entry)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add domain to whitelist: {str(e)}",
        )


@router.delete("/{domain}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_whitelist(
    domain: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a domain from the whitelist.

    Args:
        domain: Domain to remove
        db: Database session

    Raises:
        HTTPException: If domain not found or deletion fails
    """
    try:
        domain_lower = domain.lower().strip()

        # Find whitelist entry
        stmt = select(WhitelistDomain).where(WhitelistDomain.domain == domain_lower)
        result = await db.execute(stmt)
        entry = result.scalar_one_or_none()

        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Domain '{domain_lower}' not found in whitelist",
            )

        # Delete entry
        await db.delete(entry)
        await db.commit()

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove domain from whitelist: {str(e)}",
        )
