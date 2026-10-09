
from fastapi import APIRouter, Depends, Request, Response

from app.api.v1.deps import DbSession, verify_origin
from app.core.cookies import REFRESH_COOKIE_NAME, clear_refresh_cookie, set_refresh_cookie
from app.models.enums import UserRole
from app.schemas.auth import (
    AuthResponse,
    GoogleAuthRequest,
    GoogleAuthResponse,
    LoginRequest,
    RegisterRequest,
)
from app.schemas.user import UserOut
from app.services import auth_service
from app.services.auth_service import SessionResult

router = APIRouter()


def _client_info(request: Request) -> dict[str, str | None]:
    return {
        "user_agent": request.headers.get("user-agent"),
        "ip_address": request.client.host if request.client else None,
    }


def _session_response(result: SessionResult, response: Response) -> AuthResponse:
    set_refresh_cookie(
        response, result.refresh_token, max_age_seconds=result.refresh_max_age_seconds
    )
    return AuthResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        user=UserOut.model_validate(result.user),
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest, request: Request, response: Response, db: DbSession
) -> AuthResponse:
    """Step 0 of sign-up: creates the account (status 'onboarding') and logs the user in."""
    result = await auth_service.register_user(
        db,
        email=body.email,
        password=body.password,
        role=UserRole(body.role),
        remember_me=body.remember_me,
        **_client_info(request),
    )
    return _session_response(result, response)


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest, request: Request, response: Response, db: DbSession
) -> AuthResponse:
    """Email + password sign-in. The user's `status` in the response decides the next screen."""
    result = await auth_service.login_user(
        db,
        email=body.email,
        password=body.password,
        expected_role=UserRole(body.role) if body.role else None,
        remember_me=body.remember_me,
        **_client_info(request),
    )
    return _session_response(result, response)


@router.post("/google", response_model=GoogleAuthResponse)
async def google_auth(
    body: GoogleAuthRequest, request: Request, response: Response, db: DbSession
) -> GoogleAuthResponse:
    """Unified Google authentication: signs up new users or logs in existing ones."""
    result = await auth_service.authenticate_with_google(
        db,
        credential=body.credential,
        expected_role=UserRole(body.role) if body.role else None,
        remember_me=body.remember_me,
        **_client_info(request),
    )
    set_refresh_cookie(
        response, result.refresh_token, max_age_seconds=result.refresh_max_age_seconds
    )
    return GoogleAuthResponse(
        access_token=result.access_token,
        expires_in=result.expires_in,
        user=UserOut.model_validate(result.user),
        is_new_user=result.is_new_user,
    )


@router.post("/refresh", response_model=AuthResponse, dependencies=[Depends(verify_origin)])
async def refresh(request: Request, response: Response, db: DbSession) -> AuthResponse:
    """Swaps the refresh cookie for a new access token and a new refresh cookie."""
    result = await auth_service.refresh_session(
        db, raw_token=request.cookies.get(REFRESH_COOKIE_NAME), **_client_info(request)
    )
    return _session_response(result, response)


@router.post(
    "/logout", status_code=204, response_class=Response, dependencies=[Depends(verify_origin)]
)
async def logout(request: Request, db: DbSession) -> Response:
    """Ends this browser's session and clears the cookie. Safe to call when already signed out."""
    await auth_service.logout(db, raw_token=request.cookies.get(REFRESH_COOKIE_NAME))
    response = Response(status_code=204)
    clear_refresh_cookie(response)
    return response
