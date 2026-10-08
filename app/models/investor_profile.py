import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import InvestorCapitalRange, InvestorDeploymentTimeline
from app.models.types import sql_in, str_enum


class InvestorProfile(TimestampMixin, Base):
    """Answers from the 3-step investor wizard. One row per investor (user_id is the PK)."""

    __tablename__ = "investor_profiles"
    __table_args__ = (
        CheckConstraint(sql_in("capital_range", InvestorCapitalRange), name="capital_range_valid"),
        CheckConstraint(
            sql_in("deployment_timeline", InvestorDeploymentTimeline),
            name="deployment_timeline_valid",
        ),
    )

    # Primary key AND foreign key: guarantees at most one profile per user.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Step 1: "About you" (full name lives on users.full_name)
    focus: Mapped[str] = mapped_column(String(120))  # "Investment or operating focus"
    location: Mapped[str] = mapped_column(String(120))  # "City and country", free text

    # Step 2: "Your strengths". Values must be InvestorSector members; validated in the API
    # layer (Pydantic), not by a DB CHECK, because the chip list is product copy that will
    # change more often than roles/statuses do.
    sectors: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), server_default=text("'{}'")
    )
    additional_notes: Mapped[str | None] = mapped_column(Text)  # optional field

    # Step 3: "Your opportunity"
    looking_for: Mapped[str] = mapped_column(Text)
    capital_range: Mapped[InvestorCapitalRange] = mapped_column(
        str_enum(InvestorCapitalRange, "investor_capital_range", 20)
    )
    deployment_timeline: Mapped[InvestorDeploymentTimeline] = mapped_column(
        str_enum(InvestorDeploymentTimeline, "investor_deployment_timeline", 20)
    )