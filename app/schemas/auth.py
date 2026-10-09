from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserOut


def _normalize_email(value: object) -> object:
    return value.strip().lower() if isinstance(value, str) else value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)  # NOT stripped: spaces are valid
    # "admin" is deliberately not allowed: nobody can self-register as staff.
    role: Literal["investor", "architect"]
    remember_me: bool = False

    _normalize = field_validator("email", mode="before")(_normalize_email)


class LoginRequest(BaseModel):
    email: EmailStr
    # No minimum length here: we only compare it, and rules may change after accounts exist.
    password: str = Field(min_length=1, max_length=128)
    # The tab selected on the login page. Optional: if sent, it must match the account.
    role: Literal["investor", "architect"] | None = None
    remember_me: bool = False

    _normalize = field_validator("email", mode="before")(_normalize_email)


class AuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int  # seconds
    user: UserOut


class GoogleAuthRequest(BaseModel):
    credential: str
    role: Literal["investor", "architect"] | None = None
    remember_me: bool = False


class GoogleAuthResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserOut
    is_new_user: bool

