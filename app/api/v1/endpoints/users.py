from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, get_db
from app.models.enums import UserRole, UserStatus
from app.repositories import architect_profile_repo, investor_profile_repo
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def read_me(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserOut:
    """The frontend calls this on load and routes by `status`.
    Automatically activates user to 'active' if verification is completed."""
    if user.status != UserStatus.ACTIVE:
        if user.role == UserRole.ARCHITECT:
            profile = await architect_profile_repo.get(db, user.id)
            if profile and profile.is_video_verified == "Success" and profile.is_payout_connected:
                user.status = UserStatus.ACTIVE
                await db.commit()
        elif user.role == UserRole.INVESTOR:
            inv = await investor_profile_repo.get(db, user.id)
            if inv and inv.is_linkedin_verified:
                user.status = UserStatus.ACTIVE
                await db.commit()

    return UserOut.model_validate(user)
