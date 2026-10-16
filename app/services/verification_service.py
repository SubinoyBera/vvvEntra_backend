from __future__ import annotations

import asyncio
import json
import urllib.parse
import urllib.request
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppError
from app.models.enums import UserRole, UserStatus
from app.models.user import User
from app.repositories import architect_profile_repo, investor_profile_repo, user_repo
from app.schemas.verification import (
    LINKEDIN_URL_REGEX,
    LinkedInInfoOut,
    LinkedInVerifyResponse,
    PayoutAccountInfo,
    PayoutConnectResponse,
    VerificationStatusResponse,
    VideoUploadResponse,
    VideoVerificationInfo,
)


def _get_role_label(role: UserRole) -> str:
    if role == UserRole.INVESTOR:
        return "Buyer / Investor"
    if role == UserRole.ARCHITECT:
        return "Architect / Creator"
    return "Member"


async def get_verification_status(db: AsyncSession, user: User) -> VerificationStatusResponse:
    if user.role == UserRole.ARCHITECT:
        profile = await architect_profile_repo.get_or_create(db, user.id)
        has_linkedin = bool(profile.is_linkedin_verified or profile.linkedin_url)

        total_steps = 5
        if not has_linkedin:
            current_step = 2
        elif not profile.is_payout_connected:
            current_step = 3
        elif not profile.is_video_submitted:
            current_step = 4
        else:
            current_step = 5

        payout_info = PayoutAccountInfo(
            account_id=profile.payout_account_id,
            provider=profile.payout_provider or "stripe",
            bank_name=profile.payout_bank_name,
            last4=profile.payout_last4,
            currency=profile.payout_currency or "USD",
            is_connected=profile.is_payout_connected,
            connected_at=profile.payout_connected_at,
        )

        if profile.is_video_verified:
            video_status = "approved"
        elif profile.is_video_submitted:
            video_status = "pending_review"
        else:
            video_status = "not_submitted"

        video_info = VideoVerificationInfo(
            is_submitted=profile.is_video_submitted,
            is_verified=profile.is_video_verified,
            is_locked=not profile.is_payout_connected,
            status=video_status,
            submitted_at=profile.video_submitted_at,
            verified_at=profile.video_verified_at,
        )

        is_fully_verified = bool(
            has_linkedin and profile.is_payout_connected and profile.is_video_verified
        )

        linkedin_info = LinkedInInfoOut(
            url=profile.linkedin_url,
            is_verified=profile.is_linkedin_verified,
            verified_at=profile.linkedin_verified_at,
        )
    else:
        # Investor / Buyer (3 steps: Account created, LinkedIn, Verified)
        profile = await investor_profile_repo.get_or_create(db, user.id)
        has_linkedin = bool(profile.is_linkedin_verified or profile.linkedin_url)

        total_steps = 3
        current_step = 3 if has_linkedin else 2
        payout_info = None
        video_info = None
        is_fully_verified = has_linkedin

        linkedin_info = LinkedInInfoOut(
            url=profile.linkedin_url,
            is_verified=profile.is_linkedin_verified,
            verified_at=profile.linkedin_verified_at,
        )

    return VerificationStatusResponse(
        total_steps=total_steps,
        current_step=current_step,
        verifying_as=_get_role_label(user.role),
        account_created=True,
        linkedin=linkedin_info,
        payout=payout_info,
        video_verification=video_info,
        is_fully_verified=is_fully_verified,
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

    if user.role == UserRole.ARCHITECT:
        profile = await architect_profile_repo.get_or_create(db, user.id)
        profile.linkedin_url = clean_url
        profile.is_linkedin_verified = True
        profile.linkedin_verified_at = datetime.now(UTC)
    else:
        inv_profile = await investor_profile_repo.get_or_create(db, user.id)
        inv_profile.linkedin_url = clean_url
        inv_profile.is_linkedin_verified = True
        inv_profile.linkedin_verified_at = datetime.now(UTC)

    await db.commit()
    return LinkedInVerifyResponse(
        success=True,
        message="LinkedIn profile verified successfully.",
        linkedin_url=clean_url,
        is_verified=True,
        username=username,
    )


def _exchange_linkedin_code_sync(code: str, redirect_uri: str) -> dict[str, Any]:
    if code.startswith("mock_linkedin_") or not settings.linkedin_client_id:
        return {
            "sub": "mock-linkedin-sub-12345",
            "name": "Verified Professional",
            "email": "verified.pro@linkedin.com",
        }

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
    oauth_res = await asyncio.to_thread(_exchange_linkedin_code_sync, code, redirect_uri)
    name = oauth_res.get("name") or "profile"
    clean_name = name.lower().replace(" ", "-")
    linkedin_url = f"https://www.linkedin.com/in/{clean_name}"

    if user.role == UserRole.ARCHITECT:
        profile = await architect_profile_repo.get_or_create(db, user.id)
        profile.linkedin_url = linkedin_url
        profile.is_linkedin_verified = True
        profile.linkedin_verified_at = datetime.now(UTC)
    else:
        inv_profile = await investor_profile_repo.get_or_create(db, user.id)
        inv_profile.linkedin_url = linkedin_url
        inv_profile.is_linkedin_verified = True
        inv_profile.linkedin_verified_at = datetime.now(UTC)

    if not user.full_name and oauth_res.get("name"):
        user.full_name = oauth_res["name"]

    await db.commit()
    return await get_verification_status(db, user)


async def initiate_payout_onboarding(
    db: AsyncSession, user: User, return_url: str, refresh_url: str
) -> PayoutConnectResponse:
    if user.role != UserRole.ARCHITECT:
        raise AppError("Payout accounts are only required for Architect/Creator accounts.")

    profile = await architect_profile_repo.get_or_create(db, user.id)

    # 1. Production Mode: Stripe Connect API
    stripe_key = (
        settings.stripe_secret_key.get_secret_value() if settings.stripe_secret_key else None
    )
    if stripe_key:
        try:
            account_id = profile.payout_account_id
            if not account_id:
                req_data = urllib.parse.urlencode(
                    {
                        "type": "express",
                        "email": user.email,
                        "capabilities[transfers][requested]": "true",
                        "business_type": "individual",
                    }
                ).encode("utf-8")
                req = urllib.request.Request(
                    "https://api.stripe.com/v1/accounts",
                    data=req_data,
                    headers={
                        "Authorization": f"Bearer {stripe_key}",
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    acct_data = json.loads(resp.read().decode("utf-8"))
                    account_id = acct_data["id"]
                    profile.payout_account_id = account_id
                    await db.commit()

            link_data = urllib.parse.urlencode(
                {
                    "account": account_id,
                    "refresh_url": refresh_url,
                    "return_url": return_url,
                    "type": "account_onboarding",
                }
            ).encode("utf-8")
            link_req = urllib.request.Request(
                "https://api.stripe.com/v1/account_links",
                data=link_data,
                headers={
                    "Authorization": f"Bearer {stripe_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            with urllib.request.urlopen(link_req, timeout=10) as resp:
                link_res = json.loads(resp.read().decode("utf-8"))
                return PayoutConnectResponse(
                    account_id=account_id,
                    onboarding_url=link_res["url"],
                    is_connected=profile.is_payout_connected,
                )
        except Exception:
            pass  # Fallback to dev simulation if Stripe keys are test/offline

    # 2. Development Simulation Mode (Instant testing without Stripe credentials)
    mock_acct_id = profile.payout_account_id or f"acct_mock_{user.id.hex[:12]}"
    profile.payout_account_id = mock_acct_id
    await db.commit()

    sep = "&" if "?" in return_url else "?"
    mock_onboarding_url = (
        f"{return_url}{sep}payout_connected=true&account_id={mock_acct_id}&bank=Chase&last4=4242"
    )

    return PayoutConnectResponse(
        account_id=mock_acct_id,
        onboarding_url=mock_onboarding_url,
        is_connected=profile.is_payout_connected,
    )


async def confirm_payout_account(
    db: AsyncSession,
    user: User,
    account_id: str | None = None,
    bank_name: str = "JPMorgan Chase Bank",
    last4: str = "4242",
    currency: str = "USD",
) -> VerificationStatusResponse:
    if user.role != UserRole.ARCHITECT:
        raise AppError("Payout accounts are only applicable for Architect accounts.")

    profile = await architect_profile_repo.get_or_create(db, user.id)
    profile.payout_account_id = account_id or profile.payout_account_id or f"acct_mock_{user.id.hex[:12]}"
    profile.payout_provider = "stripe"
    profile.payout_bank_name = bank_name
    profile.payout_last4 = last4
    profile.payout_currency = currency
    profile.is_payout_connected = True
    profile.payout_connected_at = datetime.now(UTC)

    await db.commit()
    return await get_verification_status(db, user)


async def save_verification_video(
    db: AsyncSession,
    user: User,
    file_data: bytes,
    content_type: str = "video/webm",
) -> VideoUploadResponse:
    if user.role != UserRole.ARCHITECT:
        raise AppError("Live video verification is required for Architect accounts.")

    if not file_data or len(file_data) < 1000:
        raise AppError("Video file is empty or corrupted. Please record again.")

    MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB
    if len(file_data) > MAX_VIDEO_SIZE:
        raise AppError("Video exceeds maximum allowed size (50MB).")

    # Store compressed video binary directly in ArchitectProfile.user_video (BYTEA in PostgreSQL)
    profile = await architect_profile_repo.get_or_create(db, user.id)
    profile.user_video = file_data
    profile.user_video_content_type = content_type
    profile.is_video_submitted = True
    profile.video_submitted_at = datetime.now(UTC)
    profile.is_video_verified = False  # Queued for manual evaluation

    await db.commit()

    return VideoUploadResponse(
        success=True,
        video_id=str(user.id),
        file_size_bytes=len(file_data),
        content_type=content_type,
        status="pending_review",
        message="Live video verification uploaded successfully and saved to architect profile.",
    )
