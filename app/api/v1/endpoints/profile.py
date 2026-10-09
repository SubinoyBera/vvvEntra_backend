from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, get_db
from app.schemas.profile import (
    ArchitectProfileIn,
    ArchitectProfileOut,
    ArchitectProfileResponse,
    InvestorProfileIn,
    InvestorProfileOut,
    InvestorProfileResponse,
)
from app.schemas.user import UserOut
from app.services import profile_service

router = APIRouter()


@router.put("/investor", response_model=InvestorProfileResponse)
async def submit_investor_profile(
    body: InvestorProfileIn,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InvestorProfileResponse:
    """'Finish profile' button: saves the whole wizard and moves the user to pending_review."""
    profile = await profile_service.submit_investor_profile(db, user, body)
    return InvestorProfileResponse(
        user=UserOut.model_validate(user),
        profile=InvestorProfileOut.model_validate(profile),
    )


@router.put("/architect", response_model=ArchitectProfileResponse)
async def submit_architect_profile(
    body: ArchitectProfileIn,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchitectProfileResponse:
    """'Finish profile' button for architects: saves the 3-step wizard and moves user to pending_review."""
    profile = await profile_service.submit_architect_profile(db, user, body)
    return ArchitectProfileResponse(
        user=UserOut.model_validate(user),
        profile=ArchitectProfileOut.model_validate(profile),
    )

