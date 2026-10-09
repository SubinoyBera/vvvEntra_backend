import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.investor_profile import InvestorProfile


async def get(db: AsyncSession, user_id: uuid.UUID) -> InvestorProfile | None:
    return await db.get(InvestorProfile, user_id)
