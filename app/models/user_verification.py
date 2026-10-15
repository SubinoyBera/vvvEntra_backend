import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin


class UserVerification(TimestampMixin, Base):
    """Stores professional identity verification progress (LinkedIn, etc.) per user."""

    __tablename__ = "user_verifications"

    # One verification record per user (user_id is PK & FK)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )

    # Step 1: Account created
    account_created: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Step 2: Professional identity · LinkedIn
    linkedin_url: Mapped[str | None] = mapped_column(String(500))
    linkedin_sub: Mapped[str | None] = mapped_column(String(255), unique=True)
    linkedin_name: Mapped[str | None] = mapped_column(String(200))
    linkedin_headline: Mapped[str | None] = mapped_column(String(255))
    linkedin_picture_url: Mapped[str | None] = mapped_column(String(1000))
    linkedin_email: Mapped[str | None] = mapped_column(String(320))
    is_linkedin_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    linkedin_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Step 3: Final verified status
    is_fully_verified: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false"
    )
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
