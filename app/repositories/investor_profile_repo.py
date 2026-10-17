import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import InvestorCapitalRange, InvestorDeploymentTimeline
from app.models.investor_profile import InvestorProfile


async def get(db: AsyncSession, user_id: uuid.UUID) -> InvestorProfile | None:
    return await db.get(InvestorProfile, user_id)


async def get_or_create(db: AsyncSession, user_id: uuid.UUID) -> InvestorProfile:
    profile = await db.get(InvestorProfile, user_id)
    if profile is None:
        profile = InvestorProfile(
            user_id=user_id,
            focus="",
            location="",
            looking_for="",
            capital_range=InvestorCapitalRange.EXPLORING,
            deployment_timeline=InvestorDeploymentTimeline.EXPLORING,
        )
        db.add(profile)
        await db.flush()
    return profile
