from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError, ProfileLocked, WrongRole
from app.models.architect_profile import ArchitectProfile
from app.models.enums import UserRole, UserStatus
from app.models.investor_profile import InvestorProfile
from app.models.user import User
from app.repositories import architect_profile_repo, investor_profile_repo
from app.schemas.profile import (
    ArchitectProfileDetailsOut,
    ArchitectProfileEditIn,
    ArchitectProfileIn,
    InvestorProfileIn,
)


def _build_architect_details(user: User, profile: ArchitectProfile) -> ArchitectProfileDetailsOut:
    sectors = profile.sectors or []
    skills = profile.skills or []
    languages = profile.languages or []
    experience = profile.experience or []
    education = profile.education or []
    market_widgets = profile.market_insight_widgets or []

    # Calculate profile completeness percent
    checks = [
        bool(user.full_name),
        bool(profile.headline),
        bool(profile.location),
        bool(profile.about),
        bool(sectors or skills),
        bool(profile.is_linkedin_verified or profile.linkedin_url),
        bool(profile.is_payout_connected),
        bool(profile.is_video_verified == "Success"),
    ]
    completed = sum(1 for c in checks if c)
    percent = max(20, int((completed / len(checks)) * 100))

    is_fully_verified = bool(
        (profile.is_linkedin_verified or profile.linkedin_url)
        and profile.is_payout_connected
        and profile.is_video_verified == "Success"
    )

    return ArchitectProfileDetailsOut(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        role=user.role.value,
        status=user.status.value,
        headline=profile.headline,
        location=profile.location,
        about=profile.about,
        user_photo=profile.user_photo,
        background_image=profile.background_image,
        sectors=sectors,
        skills=skills,
        languages=languages,
        market_insight_widgets=market_widgets,
        experience=experience,
        education=education,
        profile_visibility=profile.profile_visibility or "Private",
        email_notifications=profile.email_notifications,
        is_linkedin_verified=profile.is_linkedin_verified,
        is_payout_connected=profile.is_payout_connected,
        is_video_verified=str(profile.is_video_verified or "False"),
        is_fully_verified=is_fully_verified,
        opportunities_listed=0,
        experience_entries=len(experience),
        profile_completeness_percent=percent,
    )


async def get_architect_profile(db: AsyncSession, user: User) -> ArchitectProfileDetailsOut:
    if user.role != UserRole.ARCHITECT:
        raise WrongRole("This profile view is for Architect accounts.")

    profile = await architect_profile_repo.get_or_create(db, user.id)
    return _build_architect_details(user, profile)


async def update_architect_profile(
    db: AsyncSession, user: User, data: ArchitectProfileEditIn
) -> ArchitectProfileDetailsOut:
    """Updates the architect's profile anytime when user clicks 'Save profile'."""
    if user.role != UserRole.ARCHITECT:
        raise WrongRole("Only Architect accounts can edit this profile.")

    profile = await architect_profile_repo.get_or_create(db, user.id)

    # Update user name if provided
    if data.full_name is not None and data.full_name.strip():
        user.full_name = data.full_name.strip()

    # Update profile fields if provided
    if data.headline is not None:
        profile.headline = data.headline
    if data.location is not None:
        profile.location = data.location
    if data.about is not None:
        profile.about = data.about
    if data.user_photo is not None:
        profile.user_photo = data.user_photo
    if data.background_image is not None:
        profile.background_image = data.background_image
    if data.sectors is not None:
        profile.sectors = data.sectors
    if data.skills is not None:
        profile.skills = data.skills
    if data.languages is not None:
        profile.languages = data.languages
    if data.market_insight_widgets is not None:
        profile.market_insight_widgets = data.market_insight_widgets
    if data.experience is not None:
        profile.experience = data.experience
    if data.education is not None:
        profile.education = data.education
    if data.profile_visibility is not None:
        profile.profile_visibility = data.profile_visibility
    if data.email_notifications is not None:
        profile.email_notifications = data.email_notifications

    await db.commit()
    return _build_architect_details(user, profile)


async def submit_investor_profile(
    db: AsyncSession, user: User, data: InvestorProfileIn
) -> InvestorProfile:
    if user.role != UserRole.INVESTOR:
        raise WrongRole()
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
    await db.commit()
    return profile


async def submit_architect_profile(
    db: AsyncSession, user: User, data: ArchitectProfileIn
) -> ArchitectProfile:
    if user.role != UserRole.ARCHITECT:
        raise WrongRole()

    values = {
        "headline": data.headline,
        "location": data.location,
        "sectors": [s.value if hasattr(s, "value") else str(s) for s in data.sectors],
        "additional_notes": data.additional_notes,
        "opportunity_description": data.opportunity_description,
        "doc_depth": data.doc_depth.value if hasattr(data.doc_depth, "value") else data.doc_depth,
        "submission_timeline": (
            data.submission_timeline.value
            if hasattr(data.submission_timeline, "value")
            else data.submission_timeline
        ),
    }
    profile = await architect_profile_repo.get_or_create(db, user.id)
    for field, value in values.items():
        setattr(profile, field, value)

    user.full_name = data.full_name
    if user.status == UserStatus.ONBOARDING:
        user.status = UserStatus.PENDING_REVIEW

    await db.commit()
    return profile
