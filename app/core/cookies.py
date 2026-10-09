from fastapi import Response

from app.core.config import settings

REFRESH_COOKIE_NAME = "refresh_token"
# The browser only sends this cookie to the auth endpoints, not on every API call.
REFRESH_COOKIE_PATH = f"{settings.api_v1_prefix}/auth"


def set_refresh_cookie(response: Response, raw_token: str, *, max_age_seconds: int | None) -> None:
    """max_age_seconds=None gives a session cookie (gone when the browser closes)."""
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=raw_token,
        max_age=max_age_seconds,
        path=REFRESH_COOKIE_PATH,
        domain=settings.cookie_domain,
        secure=settings.refresh_cookie_secure,
        httponly=True,  # JavaScript can never read it, so an XSS bug can't steal it
        samesite=settings.cookie_samesite,
    )


def clear_refresh_cookie(response: Response) -> None:
    # Path/domain must match the ones used when the cookie was set, or the browser keeps it.
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path=REFRESH_COOKIE_PATH,
        domain=settings.cookie_domain,
        secure=settings.refresh_cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
