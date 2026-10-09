import uuid
from typing import Any, cast

from sqlalchemy import CursorResult, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


async def get_by_hash_for_update(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    """FOR UPDATE: two requests presenting the same token are processed one after the other."""
    return await db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash).with_for_update()
    )


async def get_by_hash(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    return await db.scalar(select(RefreshToken).where(RefreshToken.token_hash == token_hash))


async def revoke_family(db: AsyncSession, family_id: uuid.UUID) -> int:
    """Kills every token descended from one login. Returns how many were still active."""
    result = cast(
        "CursorResult[Any]",
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
            .values(revoked_at=func.now())
        ),
    )
    return result.rowcount
