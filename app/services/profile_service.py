from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ProfileLocked, WrongRole
from app.models.enums import UserRole, UserStatus
from app.models.investor_profile import InvestorProfile
from app.models.user import User
from app.repositories import investor_profile_repo
from app.schemas.profile import InvestorProfileIn


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
