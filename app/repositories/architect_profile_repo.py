import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architect_profile import ArchitectProfile


async def get(db: AsyncSession, user_id: uuid.UUID) -> ArchitectProfile | None:
    return await db.get(ArchitectProfile, user_id)
