import asyncio
import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

# argon2id with the library's recommended defaults.
_hasher = PasswordHasher()

# Verified against when the email doesn't exist, so "unknown email" and "wrong password"
# take the same time. Otherwise response speed reveals which emails are registered.
DUMMY_PASSWORD_HASH = _hasher.hash(secrets.token_urlsafe(16))


# ---- passwords ----------------------------------------------------------------------------
# Hashing is deliberately slow and CPU-heavy, so it runs in a worker thread to keep the
# event loop free for other requests.


async def hash_password(password: str) -> str:
    return await asyncio.to_thread(_hasher.hash, password)


async def verify_password(password: str, password_hash: str) -> bool:
    try:
        return await asyncio.to_thread(_hasher.verify, password_hash, password)
    except (VerificationError, InvalidHashError):  # VerifyMismatchError is a VerificationError
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """True when the stored hash uses weaker settings than today's defaults."""
    return _hasher.check_needs_rehash(password_hash)


# ---- access tokens (JWT) --------------------------------------------------------------------


def create_access_token(user_id: uuid.UUID, role: str) -> tuple[str, int]:
    """Returns (token, lifetime in seconds). No secrets inside: a JWT is readable by anyone."""
    now = datetime.now(UTC)
    lifetime = timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": str(user_id),
        "role": role,
        "typ": "access",
        "iat": now,
        "exp": now + lifetime,
    }
    token = jwt.encode(
        payload, settings.jwt_secret.get_secret_value(), algorithm=settings.jwt_algorithm
    )
    return token, int(lifetime.total_seconds())


def decode_access_token(token: str) -> dict[str, Any]:
    """Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError."""
    payload: dict[str, Any] = jwt.decode(
        token,
        settings.jwt_secret.get_secret_value(),
        algorithms=[settings.jwt_algorithm],  # pinned: never trust the token's own "alg"
        options={"require": ["exp", "iat", "sub"]},
    )
    if payload.get("typ") != "access":
        raise jwt.InvalidTokenError("not an access token")
    return payload


# ---- refresh tokens ----------------------------------------------------------------------------


def hash_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()


def generate_refresh_token() -> tuple[str, str]:
    """Returns (raw token for the cookie, SHA-256 hash for the database)."""
    raw = secrets.token_urlsafe(48)
    return raw, hash_token(raw)
