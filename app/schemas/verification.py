import re
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator


LINKEDIN_URL_REGEX = re.compile(
    r"^https?://([a-zA-Z0-9_\-]+\.)?linkedin\.com/in/([a-zA-Z0-9_\-%]+)/?$", re.IGNORECASE
)


class LinkedInUrlRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    linkedin_url: str = Field(
        ...,
        description="Public LinkedIn profile URL, e.g. https://www.linkedin.com/in/your-profile",
        examples=["https://www.linkedin.com/in/subinoybera"],
    )

    @field_validator("linkedin_url")
    @classmethod
    def validate_linkedin_url(cls, v: str) -> str:
        clean = v.strip().split("?")[0].rstrip("/")  # Remove query parameters and trailing slash
        if not LINKEDIN_URL_REGEX.match(clean):
            raise ValueError(
                "Invalid LinkedIn profile URL. Must be in the format: https://www.linkedin.com/in/username"
            )
        return clean


class LinkedInVerifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: str = "LinkedIn profile verified successfully."
    linkedin_url: str
    is_verified: bool = True
    username: str | None = None


class LinkedInOAuthRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    code: str = Field(..., description="Authorization code from LinkedIn OAuth")
    redirect_uri: str = Field(..., description="Redirect URI registered in LinkedIn Developer portal")


class LinkedInInfoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    url: str | None = None
    name: str | None = None
    headline: str | None = None
    picture_url: str | None = None
    is_verified: bool = False
    verified_at: datetime | None = None


class VerificationStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    current_step: int  # 1: Account Created, 2: LinkedIn, 3: Verified
    verifying_as: str  # e.g. "Buyer / Investor" or "Architect / Creator"
    account_created: bool = True
    linkedin: LinkedInInfoOut
    is_fully_verified: bool = False
    user_status: str
