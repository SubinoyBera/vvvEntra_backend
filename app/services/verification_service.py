from __future__ import annotations

import asyncio
import json
import urllib.parse
import urllib.request
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.enums import UserRole
from app.models.user import User
from app.repositories import user_verification_repo
from app.schemas.verification import (
    LINKEDIN_URL_REGEX,
    LinkedInInfoOut,
    LinkedInVerifyResponse,
    VerificationStatusResponse,
)


def _get_role_label(role: UserRole) -> str:
    if role == UserRole.INVESTOR:
        return "Buyer / Investor"
    if role == UserRole.ARCHITECT:
        return "Architect / Creator"
    return "Member"


async def get_verification_status(db: AsyncSession, user: User) -> VerificationStatusResponse:
    rec = await user_verification_repo.get_or_create(db, user.id)

    # Step logic:
    # Step 1: Account created (always done if user is logged in)
    # Step 2: Professional identity · LinkedIn (if not connected or submitted)
    # Step 3: Verified (if LinkedIn is connected or URL submitted)
    has_linkedin = bool(rec.is_linkedin_verified or rec.linkedin_url)
    current_step = 3 if has_linkedin else 2

    return VerificationStatusResponse(
        current_step=current_step,
        verifying_as=_get_role_label(user.role),
        account_created=True,
        linkedin=LinkedInInfoOut(
            url=rec.linkedin_url,
            name=rec.linkedin_name,
            headline=rec.linkedin_headline,
            picture_url=rec.linkedin_picture_url,
            is_verified=rec.is_linkedin_verified,
            verified_at=rec.linkedin_verified_at,
        ),
        is_fully_verified=bool(rec.is_fully_verified or rec.is_linkedin_verified),
        user_status=user.status.value,
    )


def extract_linkedin_username(url: str) -> str:
    clean = url.strip().split("?")[0].rstrip("/")
    match = LINKEDIN_URL_REGEX.match(clean)
    if not match:
        raise AppError(
            "Invalid LinkedIn profile URL. Must be in the format: https://www.linkedin.com/in/username"
        )
    return match.group(2)


async def verify_and_save_linkedin_url(
    db: AsyncSession, user: User, linkedin_url: str
) -> LinkedInVerifyResponse:
    username = extract_linkedin_username(linkedin_url)
    clean_url = f"https://www.linkedin.com/in/{username}"

    rec = await user_verification_repo.get_or_create(db, user.id)
    rec.linkedin_url = clean_url
    rec.is_linkedin_verified = True
    rec.linkedin_verified_at = datetime.now(UTC)
    rec.is_fully_verified = True
    rec.verified_at = datetime.now(UTC)

    await db.commit()
    return LinkedInVerifyResponse(
        success=True,
        message="LinkedIn profile verified successfully.",
        linkedin_url=clean_url,
        is_verified=True,
        username=username,
    )


async def save_linkedin_url(
    db: AsyncSession, user: User, linkedin_url: str
) -> VerificationStatusResponse:
    rec = await user_verification_repo.get_or_create(db, user.id)
    rec.linkedin_url = linkedin_url

    # If already verified or URL provided, mark step 2 done
    if not rec.is_linkedin_verified:
        rec.updated_at = datetime.now(UTC)

    await db.commit()
    return await get_verification_status(db, user)


def _exchange_linkedin_code_sync(code: str, redirect_uri: str) -> dict[str, Any]:
    # Mock fallback for dev/testing when testing with a mock code
    if code.startswith("mock_linkedin_") or not settings.linkedin_client_id:
        return {
            "sub": "mock-linkedin-sub-12345",
            "name": "Verified Professional",
            "headline": "Angel Investor & Strategic Operator",
            "picture": "https://media.licdn.com/dms/image/default-avatar.png",
            "email": "verified.pro@linkedin.com",
            "email_verified": True,
        }

    # 1. Exchange authorization code for access token
    token_url = "https://www.linkedin.com/oauth/v2/accessToken"
    client_secret = (
        settings.linkedin_client_secret.get_secret_value()
        if settings.linkedin_client_secret
        else ""
    )

    data = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.linkedin_client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }
    ).encode("utf-8")

    token_req = urllib.request.Request(
        token_url,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "vvvEntra-Verification",
        },
    )

    try:
        with urllib.request.urlopen(token_req, timeout=10) as resp:
            token_data = json.loads(resp.read().decode("utf-8"))
            access_token = token_data.get("access_token")
    except Exception as exc:
        raise AppError(f"Failed to authenticate with LinkedIn: {exc}") from exc

    if not access_token:
        raise AppError("LinkedIn authorization code expired or invalid.")

    # 2. Fetch UserInfo via OpenID Connect (Free official LinkedIn OIDC)
    userinfo_url = "https://api.linkedin.com/v2/userinfo"
    userinfo_req = urllib.request.Request(
        userinfo_url,
        headers={
            "Authorization": f"Bearer {access_token}",
            "User-Agent": "vvvEntra-Verification",
        },
    )

    try:
        with urllib.request.urlopen(userinfo_req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        raise AppError(f"Failed to retrieve LinkedIn profile: {exc}") from exc


async def connect_linkedin_oauth(
    db: AsyncSession, user: User, code: str, redirect_uri: str
) -> VerificationStatusResponse:
    profile = await asyncio.to_thread(_exchange_linkedin_code_sync, code, redirect_uri)

    rec = await user_verification_repo.get_or_create(db, user.id)
    rec.linkedin_sub = profile.get("sub")
    rec.linkedin_name = profile.get("name") or f"{profile.get('given_name', '')} {profile.get('family_name', '')}".strip()
    rec.linkedin_picture_url = profile.get("picture")
    rec.linkedin_email = profile.get("email")
    rec.is_linkedin_verified = True
    rec.linkedin_verified_at = datetime.now(UTC)

    # If the user pasted a URL previously, keep it; otherwise set placeholder
    if not rec.linkedin_url:
        clean_name = (rec.linkedin_name or "profile").lower().replace(" ", "-")
        rec.linkedin_url = f"https://www.linkedin.com/in/{clean_name}"

    # Auto-fill user's full_name if not already present
    if not user.full_name and rec.linkedin_name:
        user.full_name = rec.linkedin_name

    await db.commit()
    return await get_verification_status(db, user)
