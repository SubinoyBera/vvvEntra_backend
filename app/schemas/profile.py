from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import (
    ArchitectDocDepth,
    ArchitectSubmissionTimeline,
    InvestorCapitalRange,
    InvestorDeploymentTimeline,
    InvestorSector,
)
from app.schemas.user import UserOut


class LanguageItem(BaseModel):
    language: str
    proficiency: str = "Fluent"


class ExperienceItem(BaseModel):
    title: str
    company: str
    dates: str
    what_you_did: str | None = None


class EducationItem(BaseModel):
    school: str
    degree: str | None = None
    field_of_study: str | None = None
    dates: str | None = None


# ---- Investor Wizard Schemas ----


class InvestorProfileIn(BaseModel):
    """The whole 3-step wizard, sent once on 'Finish profile'."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Step 1: About you
    full_name: str = Field(min_length=2, max_length=200)
    focus: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=120)
    # Step 2: Your strengths
    sectors: list[InvestorSector] = Field(min_length=1)
    additional_notes: str | None = Field(default=None, max_length=1000)
    # Step 3: Your opportunity
    looking_for: str = Field(min_length=1, max_length=2000)
    capital_range: InvestorCapitalRange
    deployment_timeline: InvestorDeploymentTimeline

    @field_validator("sectors")
    @classmethod
    def unique_sectors(cls, value: list[InvestorSector]) -> list[InvestorSector]:
        return list(dict.fromkeys(value))

    @field_validator("additional_notes")
    @classmethod
    def blank_notes_to_none(cls, value: str | None) -> str | None:
        return value or None


class InvestorProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    focus: str
    location: str
    sectors: list[InvestorSector]
    additional_notes: str | None
    looking_for: str
    capital_range: InvestorCapitalRange
    deployment_timeline: InvestorDeploymentTimeline


class InvestorProfileResponse(BaseModel):
    user: UserOut
    profile: InvestorProfileOut


# ---- Architect Wizard Schemas ----


class ArchitectProfileIn(BaseModel):
    """The initial 3-step architect onboarding wizard."""

    model_config = ConfigDict(str_strip_whitespace=True)

    # Step 1: About you
    full_name: str = Field(min_length=2, max_length=200)
    headline: str = Field(min_length=1, max_length=120)
    location: str = Field(min_length=1, max_length=120)

    # Step 2: Your strengths
    sectors: list[str] = Field(min_length=1)
    additional_notes: str | None = Field(default=None, max_length=1000)

    # Step 3: Your opportunity
    opportunity_description: str = Field(min_length=1, max_length=2000)
    doc_depth: ArchitectDocDepth
    submission_timeline: ArchitectSubmissionTimeline

    @field_validator("sectors")
    @classmethod
    def unique_sectors(cls, value: list[str]) -> list[str]:
        return list(dict.fromkeys(value))

    @field_validator("additional_notes")
    @classmethod
    def blank_notes_to_none(cls, value: str | None) -> str | None:
        return value or None


class ArchitectProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    headline: str | None = None
    location: str | None = None
    sectors: list[str] = []
    additional_notes: str | None = None
    opportunity_description: str | None = None
    doc_depth: ArchitectDocDepth | None = None
    submission_timeline: ArchitectSubmissionTimeline | None = None


class ArchitectProfileResponse(BaseModel):
    user: UserOut
    profile: ArchitectProfileOut


# ---- Architect Full Edit Profile Schemas (Anytime Edit) ----


class ArchitectProfileEditIn(BaseModel):
    """Payload sent when clicking 'Save profile' in the Edit Profile modal."""

    model_config = ConfigDict(str_strip_whitespace=True)

    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    about: str | None = None
    user_photo: str | None = None  # URL or data URI
    background_image: str | None = None
    sectors: list[str] | None = None
    skills: list[str] | None = None
    languages: list[dict[str, Any]] | None = None
    market_insight_widgets: list[str] | None = None
    experience: list[dict[str, Any]] | None = None
    education: list[dict[str, Any]] | None = None
    profile_visibility: str | None = "Private"  # "Private" | "Public"
    email_notifications: bool | None = True

    @field_validator("skills", mode="before")
    @classmethod
    def parse_skills(cls, v: Any) -> list[str] | None:
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v


class ArchitectProfileDetailsOut(BaseModel):
    """Full architect profile for the Account Overview & Edit Profile modal."""

    model_config = ConfigDict(from_attributes=True)

    # User fields
    id: str
    email: str
    full_name: str | None = None
    role: str = "architect"
    status: str = "active"

    # Profile fields
    headline: str | None = None
    location: str | None = None
    about: str | None = None
    user_photo: str | None = None
    background_image: str | None = None
    sectors: list[str] = []
    skills: list[str] = []
    languages: list[dict[str, Any]] = []
    market_insight_widgets: list[str] = []
    experience: list[dict[str, Any]] = []
    education: list[dict[str, Any]] = []
    profile_visibility: str = "Private"
    email_notifications: bool = True

    # Verification badges
    is_linkedin_verified: bool = False
    is_payout_connected: bool = False
    is_video_verified: str = "False"  # "False" | "Success" | "Invalid"
    is_fully_verified: bool = False

    # Readiness & metrics
    opportunities_listed: int = 0
    experience_entries: int = 0
    profile_completeness_percent: int = 100


class PhotoUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    photo_url: str
    message: str = "Profile photo updated successfully."
