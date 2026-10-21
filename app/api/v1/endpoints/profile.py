import base64
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, get_db
from app.models.enums import UserRole
from app.schemas.profile import (
    ArchitectProfileDetailsOut,
    ArchitectProfileEditIn,
    ArchitectProfileIn,
    ArchitectProfileOut,
    ArchitectProfileResponse,
    InvestorProfileIn,
    InvestorProfileOut,
    InvestorProfileResponse,
    PhotoUploadResponse,
)
from app.schemas.user import UserOut
from app.services import profile_service

router = APIRouter()


@router.get("/architect", response_model=ArchitectProfileDetailsOut)
@router.get("/me", response_model=ArchitectProfileDetailsOut)
async def get_my_architect_profile(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchitectProfileDetailsOut:
    """Returns the full architect profile details to populate the Account Overview and Edit Profile modal."""
    return await profile_service.get_architect_profile(db, user)


@router.patch("/architect", response_model=ArchitectProfileDetailsOut)
@router.post("/architect/save", response_model=ArchitectProfileDetailsOut)
async def edit_architect_profile(
    body: ArchitectProfileEditIn,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ArchitectProfileDetailsOut:
    """Called on clicking 'Save profile' in the Edit Profile modal. Updates profile in database."""
    return await profile_service.update_architect_profile(db, user, body)


@router.post("/photo", response_model=PhotoUploadResponse)
@router.post("/architect/photo", response_model=PhotoUploadResponse)
async def upload_profile_photo(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    photo: UploadFile = File(...),
) -> PhotoUploadResponse:
    """Uploads profile photo and stores as data URI or URL in architect_profiles."""
    file_bytes = await photo.read()
    mime = photo.content_type or "image/jpeg"
    b64_str = base64.b64encode(file_bytes).decode("utf-8")
    data_uri = f"data:{mime};base64,{b64_str}"

    await profile_service.update_architect_profile(
        db, user, ArchitectProfileEditIn(user_photo=data_uri)
    )

    return PhotoUploadResponse(
        success=True,
        photo_url=data_uri,
        message="Profile photo uploaded and saved successfully.",
    )


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
