import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.cookies import clear_refresh_cookie


class AppError(Exception):
    """An expected, client-facing error. Becomes {"error": {"code", "message"}, "request_id"}."""

    status_code = 400
    code = "BAD_REQUEST"
    message = "Bad request."
    clear_refresh_cookie = False  # True: the error response also deletes the refresh cookie

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.message
        super().__init__(self.message)


class EmailAlreadyRegistered(AppError):
    status_code = 409
    code = "EMAIL_ALREADY_REGISTERED"
    message = "An account with this email already exists."


class InvalidCredentials(AppError):
    status_code = 401
    code = "INVALID_CREDENTIALS"
    # One message for "no such email", "wrong password" and "Google-only account", on purpose.
    message = "Invalid email or password."


class NotAuthenticated(AppError):
    status_code = 401
    code = "NOT_AUTHENTICATED"
    message = "Authentication required."


class TokenInvalid(NotAuthenticated):
    code = "TOKEN_INVALID"
    message = "Invalid access token."


class TokenExpired(NotAuthenticated):
    code = "TOKEN_EXPIRED"  # the frontend reacts to this one by calling /auth/refresh
    message = "Access token expired."


class RefreshTokenInvalid(NotAuthenticated):
    """Missing, unknown, expired, revoked or replayed refresh token: all look the same outside."""

    code = "REFRESH_TOKEN_INVALID"
    message = "Your session has ended. Please sign in again."
    clear_refresh_cookie = True


class RefreshConflict(AppError):
    status_code = 409
    code = "REFRESH_CONFLICT"
    message = "This session was just refreshed by another request. Retry once."


class AccountSuspended(AppError):
    status_code = 403
    code = "ACCOUNT_SUSPENDED"
    message = "This account has been suspended."


class AccountPendingReview(AppError):
    status_code = 403
    code = "ACCOUNT_PENDING_REVIEW"
    message = "Your account is being reviewed. You will get access once it is approved."


class OnboardingIncomplete(AppError):
    status_code = 403
    code = "ONBOARDING_INCOMPLETE"
    message = "Please finish setting up your profile first."


class WrongRole(AppError):
    status_code = 403
    code = "WRONG_ROLE"
    message = "This action is not available for your account type."


class ProfileLocked(AppError):
    status_code = 409
    code = "PROFILE_LOCKED"
    message = "The profile can no longer be edited here."


class ForbiddenOrigin(AppError):
    status_code = 403
    code = "FORBIDDEN_ORIGIN"
    message = "Request origin is not allowed."


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
    response = JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {"code": exc.code, "message": exc.message},
            "request_id": structlog.contextvars.get_contextvars().get("request_id"),
        },
        headers=headers,
    )
    if exc.clear_refresh_cookie:
        clear_refresh_cookie(response)
    return response
