from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProfileLocked, WrongRole
from app.models.architect_profile import ArchitectProfile
from app.models.enums import UserRole, UserStatus
from app.models.investor_profile import InvestorProfile
from app.models.user import User
from app.repositories import architect_profile_repo, investor_profile_repo
from app.schemas.profile import ArchitectProfileIn, InvestorProfileIn


async def submit_investor_profile(
    db: AsyncSession, user: User, data: InvestorProfileIn
) -> InvestorProfile:
    if user.role != UserRole.INVESTOR:
        raise WrongRole()
    # Editable while onboarding or waiting for review; once approved/suspended it's locked here.
    if user.status not in (UserStatus.ONBOARDING, UserStatus.PENDING_REVIEW):
        raise ProfileLocked()

    values = {
        "focus": data.focus,
        "location": data.location,
        "sectors": [sector.value for sector in data.sectors],
        "additional_notes": data.additional_notes,
        "looking_for": data.looking_for,
        "capital_range": data.capital_range,
        "deployment_timeline": data.deployment_timeline,
    }
    profile = await investor_profile_repo.get(db, user.id)
    if profile is None:
        profile = InvestorProfile(user_id=user.id, **values)
        db.add(profile)
    else:
        for field, value in values.items():
            setattr(profile, field, value)

    user.full_name = data.full_name
    user.status = UserStatus.PENDING_REVIEW
    await db.commit()  # profile + name + status change: all or nothing
    return profile


async def submit_architect_profile(
    db: AsyncSession, user: User, data: ArchitectProfileIn
) -> ArchitectProfile:
    if user.role != UserRole.ARCHITECT:
        raise WrongRole()
    if user.status not in (UserStatus.ONBOARDING, UserStatus.PENDING_REVIEW):
        raise ProfileLocked()

    values = {
        "headline": data.headline,
        "location": data.location,
        "sectors": [sector.value for sector in data.sectors],
        "additional_notes": data.additional_notes,
        "opportunity_description": data.opportunity_description,
        "doc_depth": data.doc_depth.value,
        "submission_timeline": data.submission_timeline.value,
    }
    profile = await architect_profile_repo.get(db, user.id)
    if profile is None:
        profile = ArchitectProfile(user_id=user.id, **values)
        db.add(profile)
    else:
        for field, value in values.items():
            setattr(profile, field, value)

    user.full_name = data.full_name
    user.status = UserStatus.PENDING_REVIEW
    await db.commit()
    return profile

