import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.architect_profile import ArchitectProfile


async def get(db: AsyncSession, user_id: uuid.UUID) -> ArchitectProfile | None:
    return await db.get(ArchitectProfile, user_id)


async def get_or_create(db: AsyncSession, user_id: uuid.UUID) -> ArchitectProfile:
    profile = await db.get(ArchitectProfile, user_id)
    if profile is None:
        profile = ArchitectProfile(user_id=user_id)
        db.add(profile)
        await db.flush()
    return profile
