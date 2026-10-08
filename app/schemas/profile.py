from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.enums import InvestorCapitalRange, InvestorDeploymentTimeline, InvestorSector
from app.schemas.user import UserOut


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
        return list(dict.fromkeys(value))  # drop duplicates, keep order

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
    user: UserOut  # status is now "pending_review"
    profile: InvestorProfileOut
