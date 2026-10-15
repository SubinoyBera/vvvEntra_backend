import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_verification import UserVerification


async def get(db: AsyncSession, user_id: uuid.UUID) -> UserVerification | None:
    return await db.get(UserVerification, user_id)


async def get_or_create(db: AsyncSession, user_id: uuid.UUID) -> UserVerification:
    rec = await db.get(UserVerification, user_id)
    if rec is None:
        rec = UserVerification(user_id=user_id, account_created=True)
        db.add(rec)
        await db.flush()
    return rec
