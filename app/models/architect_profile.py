import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, LargeBinary, String, Text, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin
from app.models.enums import ArchitectDocDepth, ArchitectSubmissionTimeline
from app.models.types import sql_in, str_enum


class ArchitectProfile(TimestampMixin, Base):
    """Answers from the 3-step architect wizard + verification, payout & video. One row per architect."""

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
    headline: Mapped[str | None] = mapped_column(String(120), nullable=True)  # Professional headline
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)  # "City and country", free text

    # Step 2: "Your strengths"
    sectors: Mapped[list[str]] = mapped_column(
        ARRAY(String(40)), server_default=text("'{}'")
    )
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # optional field

    # Step 3: "Your opportunity"
    opportunity_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    doc_depth: Mapped[ArchitectDocDepth | None] = mapped_column(
        str_enum(ArchitectDocDepth, "architect_doc_depth", 30), nullable=True
    )
    submission_timeline: Mapped[ArchitectSubmissionTimeline | None] = mapped_column(
        str_enum(ArchitectSubmissionTimeline, "architect_submission_timeline", 30), nullable=True
    )

    # Verification: LinkedIn
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_linkedin_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    linkedin_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Verification: Payout details (Stripe Connect)
    payout_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payout_provider: Mapped[str | None] = mapped_column(
        String(50), default="stripe", server_default="stripe", nullable=True
    )
    payout_bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payout_last4: Mapped[str | None] = mapped_column(String(10), nullable=True)
    payout_currency: Mapped[str | None] = mapped_column(
        String(10), default="USD", server_default="USD", nullable=True
    )
    is_payout_connected: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    payout_connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Verification: Video details & binary storage (BYTEA in PostgreSQL)
    user_video: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    user_video_content_type: Mapped[str | None] = mapped_column(
        String(50), default="video/webm", server_default="video/webm", nullable=True
    )
    is_video_submitted: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    video_submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_video_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    video_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
