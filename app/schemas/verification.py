import re
import uuid
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


class PayoutAccountInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    account_id: str | None = None
    provider: str = "stripe"
    bank_name: str | None = None
    last4: str | None = None
    currency: str | None = "USD"
    is_connected: bool = False
    connected_at: datetime | None = None


class PayoutConnectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    return_url: str = Field(
        default="http://localhost:3000/verify",
        description="URL to return to after completing Stripe Connect onboarding",
    )
    refresh_url: str = Field(
        default="http://localhost:3000/verify",
        description="URL to return to if the Stripe Connect link expires",
    )


class PayoutConnectResponse(BaseModel):
    success: bool = True
    message: str = "Payout account connected successfully."
    account_id: str
    onboarding_url: str | None = None
    is_connected: bool = True


class VideoUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: str = (
        "Live video verification uploaded successfully and queued for human review. "
        "Verification process is usually completed within 24 hours."
    )
    video_id: str
    file_size_bytes: int
    content_type: str
    status: str = "pending_review"


class VideoRequirementsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    max_duration_seconds: int = 120
    min_duration_seconds: int = 5
    max_file_size_bytes: int = 50 * 1024 * 1024
    allowed_mime_types: list[str] = ["video/webm", "video/mp4"]
    title: str = "Live Webcam Identity Verification"
    checklist: list[str] = [
        "Position yourself in a well-lit room with your face clearly visible",
        "Enable webcam and microphone when prompted by your browser",
        "State your full legal name and role as registered on your profile",
        "Present a valid government-issued photo ID (Passport, Driving License, National ID) clearly in front of the camera",
        "The video automatically terminates and submits after 2 minutes (120 seconds)",
    ]
    instructions: list[str] = [
        "1. Click 'Start Live Recording' to activate camera preview.",
        "2. Review framing and audio level before recording commences.",
        "3. Once recording begins, state your name and display your ID clearly.",
        "4. Recording will auto-stop and compress at 2:00 minutes, or you may click 'Finish Early' once complete.",
        "5. The compressed video is stored securely in PostgreSQL BYTEA storage.",
    ]
    privacy_notice: str = (
        "Human Review Only: To safeguard your privacy and sensitive biometric/ID information, "
        "your recording is never sent to third-party AI APIs or external vision models. "
        "Only vetted internal compliance officers review submissions manually."
    )


class VideoReviewRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    target_user_id: uuid.UUID | None = None
    approved: bool
    rejection_reason: str | None = None


class VideoStatusUpdateRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    status: str = Field(..., description="'Success' to approve, 'Invalid' to reject, or 'False'")
    rejection_reason: str | None = None


class VideoVerificationInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    is_submitted: bool = False
    is_verified: str = "False"  # "False" | "Success" | "Invalid"
    is_locked: bool = True
    status: str = "not_submitted"  # "not_submitted" | "pending_review" | "Success" | "Invalid"
    submitted_at: datetime | None = None
    verified_at: datetime | None = None
    rejection_reason: str | None = None


class VerificationStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_steps: int  # 3 for Investor, 5 for Architect
    current_step: int  # Active step index
    verifying_as: str  # e.g. "Buyer / Investor" or "Architect / Creator"
    account_created: bool = True
    linkedin: LinkedInInfoOut
    payout: PayoutAccountInfo | None = None
    video_verification: VideoVerificationInfo | None = None
    is_fully_verified: bool = False
    user_status: str

