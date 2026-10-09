import uuid
from typing import Annotated

import jwt
import structlog
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountPendingReview,
    AccountSuspended,
    ForbiddenOrigin,
    NotAuthenticated,
    OnboardingIncomplete,
    TokenExpired,
    TokenInvalid,
)
from app.core.security import decode_access_token
from app.db.redis import get_redis
from app.db.session import get_db
from app.models.enums import UserStatus
from app.models.user import User
from app.repositories import user_repo

__all__ = [
    "ActiveUser",
    "CurrentUser",
    "DbSession",
    "get_active_user",
    "get_current_user",
    "get_db",
    "get_redis",
    "verify_origin",
]

_bearer = HTTPBearer(auto_error=False)  # we raise our own errors with our own error format

DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: DbSession,
) -> User:
    if credentials is None:
        raise NotAuthenticated()
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(payload["sub"])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpired() from exc
    except (jwt.InvalidTokenError, ValueError) as exc:
        raise TokenInvalid() from exc

    # One primary-key lookup per request, so suspending a user takes effect immediately.
    user = await user_repo.get_by_id(db, user_id)
    if user is None:
        raise TokenInvalid()
    if user.status == UserStatus.SUSPENDED:
        raise AccountSuspended()

    structlog.contextvars.bind_contextvars(user_id=str(user.id))  # every later log line has it
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def get_active_user(user: CurrentUser) -> User:
    """For platform features: only approved members. (Suspended is already blocked above.)"""
    if user.status == UserStatus.ONBOARDING:
        raise OnboardingIncomplete()
    if user.status == UserStatus.PENDING_REVIEW:
        raise AccountPendingReview()
    return user


ActiveUser = Annotated[User, Depends(get_active_user)]


async def verify_origin(request: Request) -> None:
    """CSRF guard for endpoints that act on the refresh cookie (refresh, logout).

    Browsers always attach an Origin header to cross-site POSTs. If it names a site that is not
    ours, refuse. Requests without an Origin (curl, mobile apps, tests) pass: they can't be
    driven by another website's JavaScript.
    """
    origin = request.headers.get("origin")
    if origin is None:
        return
    own_origin = f"{request.url.scheme}://{request.headers.get('host', '')}"  # e.g. Swagger UI
    if origin != own_origin and origin not in settings.cors_origins:
        raise ForbiddenOrigin()
