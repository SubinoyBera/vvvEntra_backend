import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    AccountSuspended,
    AppError,
    EmailAlreadyRegistered,
    InvalidCredentials,
    RefreshConflict,
    RefreshTokenInvalid,
    WrongRole,
)
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.models.enums import UserRole, UserStatus
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import refresh_token_repo, user_repo

log = structlog.get_logger()

# Two browser tabs can refresh at the same instant with the same cookie. The loser arrives
# right after the winner rotated the token. Within this window that is a race, not theft.
REFRESH_GRACE_SECONDS = 10

_ROLE_LABELS = {UserRole.INVESTOR: "Investor / Buyer", UserRole.ARCHITECT: "Architect / Creator"}


@dataclass
class SessionResult:
    user: User
    access_token: str
    expires_in: int
    refresh_token: str  # raw value: goes into the cookie, only its hash is stored
    refresh_max_age_seconds: int | None  # None = session cookie


@dataclass
class GoogleSessionResult(SessionResult):
    is_new_user: bool = False



async def issue_session(
    db: AsyncSession,
    user: User,
    *,
    remember_me: bool,
    user_agent: str | None,
    ip_address: str | None,
    family_id: uuid.UUID | None = None,
) -> SessionResult:
    """Creates an access token + a stored refresh token. Caller commits.

    family_id=None starts a new login (new rotation chain); refresh passes the existing one.
    """
    access_token, expires_in = create_access_token(user.id, user.role.value)
    raw_refresh, refresh_hash = generate_refresh_token()
    days = settings.refresh_token_remember_days if remember_me else settings.refresh_token_days
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=refresh_hash,
            family_id=family_id or uuid.uuid4(),
            remember_me=remember_me,
            expires_at=datetime.now(UTC) + timedelta(days=days),
            user_agent=(user_agent or "")[:255] or None,
            ip_address=ip_address,
        )
    )
    return SessionResult(
        user=user,
        access_token=access_token,
        expires_in=expires_in,
        refresh_token=raw_refresh,
        refresh_max_age_seconds=days * 86400 if remember_me else None,
    )


async def register_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    role: UserRole,
    remember_me: bool,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionResult:
    if await user_repo.get_by_email(db, email):
        raise EmailAlreadyRegistered()

    user = User(email=email, password_hash=await hash_password(password), role=role)
    db.add(user)
    try:
        await db.flush()  # sends the INSERT now so a duplicate email fails here
    except IntegrityError as exc:
        await db.rollback()
        # Two sign-ups with the same email at the same instant: the DB unique key wins.
        if "uq_users_email" in str(exc.orig):
            raise EmailAlreadyRegistered() from exc
        raise

    result = await issue_session(
        db, user, remember_me=remember_me, user_agent=user_agent, ip_address=ip_address
    )
    await db.commit()  # user + refresh token saved together, or not at all
    return result


async def login_user(
    db: AsyncSession,
    *,
    email: str,
    password: str,
    expected_role: UserRole | None,
    remember_me: bool,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionResult:
    user = await user_repo.get_by_email(db, email)
    stored_hash = user.password_hash if user else None

    # Always run one argon2 verification, even for unknown emails (see DUMMY_PASSWORD_HASH).
    password_ok = await verify_password(password, stored_hash or DUMMY_PASSWORD_HASH)
    if user is None or stored_hash is None or not password_ok:
        raise InvalidCredentials()

    # Everything below runs only for someone who proved they know the password, so these
    # specific messages cannot be used to discover which emails are registered.
    if user.status == UserStatus.SUSPENDED:
        raise AccountSuspended()
    if expected_role is not None and expected_role != user.role:
        label = _ROLE_LABELS.get(user.role, user.role.value)
        raise WrongRole(f"This email is registered as an {label} account.")

    if password_needs_rehash(stored_hash):
        user.password_hash = await hash_password(password)
    user.last_login_at = datetime.now(UTC)

    result = await issue_session(
        db, user, remember_me=remember_me, user_agent=user_agent, ip_address=ip_address
    )
    await db.commit()
    return result


async def refresh_session(
    db: AsyncSession,
    *,
    raw_token: str | None,
    user_agent: str | None,
    ip_address: str | None,
) -> SessionResult:
    """Rotation: every refresh token works exactly once and is replaced by a new one."""
    if not raw_token:
        raise RefreshTokenInvalid()
    token = await refresh_token_repo.get_by_hash_for_update(db, hash_token(raw_token))
    if token is None:
        raise RefreshTokenInvalid()

    now = datetime.now(UTC)
    if token.revoked_at is not None or token.expires_at <= now:
        raise RefreshTokenInvalid()

    if token.used_at is not None:
        if (now - token.used_at).total_seconds() <= REFRESH_GRACE_SECONDS:
            raise RefreshConflict()  # a racing tab; the client retries with its new cookie
        # An already-used token coming back later means someone kept a copy. Kill the family.
        revoked = await refresh_token_repo.revoke_family(db, token.family_id)
        await db.commit()
        log.warning(
            "refresh_token_reuse_detected",
            user_id=str(token.user_id),
            family_id=str(token.family_id),
            revoked_tokens=revoked,
        )
        raise RefreshTokenInvalid()

    user = await user_repo.get_by_id(db, token.user_id)
    if user is None:
        raise RefreshTokenInvalid()
    if user.status == UserStatus.SUSPENDED:
        await refresh_token_repo.revoke_family(db, token.family_id)
        await db.commit()
        raise AccountSuspended()

    token.used_at = now
    result = await issue_session(
        db,
        user,
        remember_me=token.remember_me,
        user_agent=user_agent,
        ip_address=ip_address,
        family_id=token.family_id,
    )
    await db.commit()
    return result


async def logout(db: AsyncSession, *, raw_token: str | None) -> None:
    """Ends this browser's session. Always succeeds: logging out twice is not an error."""
    if not raw_token:
        return
    token = await refresh_token_repo.get_by_hash(db, hash_token(raw_token))
    if token is not None:
        await refresh_token_repo.revoke_family(db, token.family_id)
        await db.commit()


def _verify_google_token_sync(credential: str) -> dict[str, Any]:
    import json
    import urllib.request
    from urllib.parse import quote

    url = f"https://oauth2.googleapis.com/tokeninfo?id_token={quote(credential)}"
    req = urllib.request.Request(url, headers={"User-Agent": "vvvEntra-Backend"})
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise AppError("Invalid or expired Google authentication token.") from exc


async def authenticate_with_google(
    db: AsyncSession,
    *,
    credential: str,
    expected_role: UserRole | None,
    remember_me: bool,
    user_agent: str | None,
    ip_address: str | None,
) -> GoogleSessionResult:
    payload = await asyncio.to_thread(_verify_google_token_sync, credential)
    sub = str(payload.get("sub", ""))
    email = str(payload.get("email", "")).strip().lower()
    name = payload.get("name")
    email_verified = payload.get("email_verified") in (True, "true")

    if not sub or not email:
        raise AppError("Google token is missing essential profile claims.")
    if not email_verified:
        raise AppError("Google account email must be verified.")

    is_new_user = False
    user = await user_repo.get_by_google_sub(db, sub)

    if user is None:
        user = await user_repo.get_by_email(db, email)
        if user is not None:
            user.google_sub = sub
            if not user.email_verified_at and email_verified:
                user.email_verified_at = datetime.now(UTC)
            if not user.full_name and name:
                user.full_name = name
            user.last_login_at = datetime.now(UTC)

    if user is None:
        is_new_user = True
        target_role = expected_role or UserRole.INVESTOR
        user = User(
            email=email,
            password_hash=None,
            full_name=name,
            role=target_role,
            status=UserStatus.ONBOARDING,
            google_sub=sub,
            email_verified_at=datetime.now(UTC) if email_verified else None,
            last_login_at=datetime.now(UTC),
        )
        db.add(user)
        await db.flush()
    else:
        if user.status == UserStatus.SUSPENDED:
            raise AccountSuspended()
        if expected_role is not None and expected_role != user.role:
            label = _ROLE_LABELS.get(user.role, user.role.value)
            raise WrongRole(f"This Google account is registered as an {label} account.")
        user.last_login_at = datetime.now(UTC)

    session = await issue_session(
        db, user, remember_me=remember_me, user_agent=user_agent, ip_address=ip_address
    )
    await db.commit()
    return GoogleSessionResult(
        user=session.user,
        access_token=session.access_token,
        expires_in=session.expires_in,
        refresh_token=session.refresh_token,
        refresh_max_age_seconds=session.refresh_max_age_seconds,
        is_new_user=is_new_user,
    )

