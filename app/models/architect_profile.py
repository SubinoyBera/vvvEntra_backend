import uuid

from sqlalchemy import CheckConstraint, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import ArchitectDocDepth, ArchitectSubmissionTimeline
from app.models.types import sql_in, str_enum


class ArchitectProfile(TimestampMixin, Base):
    """Answers from the 3-step architect wizard. One row per architect (user_id is the PK)."""

    __tablename__ = "architect_profiles"
    __table_args__ = (
        CheckConstraint(sql_in("doc_depth", ArchitectDocDepth), name="doc_depth_valid"),
        CheckConstraint(
            sql_in("submission_timeline", ArchitectSubmissionTimeline),
            name="submission_timeline_valid",
        ),
    )

    # Primary key AND foreign key: guarantees at most one profile per user.
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Step 1: "About you" (full name lives on users.full_name)
    headline: Mapped[str] = mapped_column(String(120))  # Professional headline
    location: Mapped[str] = mapped_column(String(120))  # "City and country", free text

    # Step 2: "Your strengths"
    sectors: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), server_default=text("'{}'")
    )
    additional_notes: Mapped[str | None] = mapped_column(Text)  # optional field

    # Step 3: "Your opportunity"
    opportunity_description: Mapped[str] = mapped_column(Text)
    doc_depth: Mapped[ArchitectDocDepth] = mapped_column(
        str_enum(ArchitectDocDepth, "architect_doc_depth", 30)
    )
    submission_timeline: Mapped[ArchitectSubmissionTimeline] = mapped_column(
        str_enum(ArchitectSubmissionTimeline, "architect_submission_timeline", 30)
    )
