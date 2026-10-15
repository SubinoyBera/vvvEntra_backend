from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import CurrentUser, get_db
from app.schemas.verification import (
    LinkedInOAuthRequest,
    LinkedInUrlRequest,
    LinkedInVerifyResponse,
    VerificationStatusResponse,
)
from app.services import verification_service

router = APIRouter()


@router.get("/status", response_model=VerificationStatusResponse)
async def get_status(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationStatusResponse:
    """Returns the current user's 3-step verification progress."""
    return await verification_service.get_verification_status(db, user)


@router.post("/linkedin", response_model=LinkedInVerifyResponse)
@router.put("/linkedin", response_model=LinkedInVerifyResponse)
@router.post("/linkedin/url", response_model=LinkedInVerifyResponse)
@router.put("/linkedin/url", response_model=LinkedInVerifyResponse)
async def verify_linkedin_url(
    body: LinkedInUrlRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> LinkedInVerifyResponse:
    """Verifies user's LinkedIn profile URL, saves it, and marks verification complete."""
    return await verification_service.verify_and_save_linkedin_url(db, user, body.linkedin_url)


@router.post("/linkedin/connect", response_model=VerificationStatusResponse)
async def connect_linkedin_oauth(
    body: LinkedInOAuthRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> VerificationStatusResponse:
    """Connect and verify via official LinkedIn OpenID Connect (Free)."""
    return await verification_service.connect_linkedin_oauth(
        db, user, code=body.code, redirect_uri=body.redirect_uri
    )
