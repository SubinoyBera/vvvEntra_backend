import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.models.enums import UserRole, UserStatus
from app.models.types import sql_in, str_enum


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        # Emails are normalized to lowercase in the app; the DB enforces it too, so
        # "A@x.com" and "a@x.com" can never become two accounts.
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        # The DB itself rejects any role/status outside our enums (not just our Python code).
        CheckConstraint(sql_in("role", UserRole), name="role_valid"),
        CheckConstraint(sql_in("status", UserStatus), name="status_valid"),
        Index("ix_users_status", "status"),  # the admin "pending review" queue filters on this
    )

    email: Mapped[str] = mapped_column(String(320), unique=True)
    # NULL for accounts that only ever signed in with Google.
    password_hash: Mapped[str | None] = mapped_column(String(255))
    # NULL until profile wizard step 1: sign-up only collects email + password + role.
    full_name: Mapped[str | None] = mapped_column(String(200))

    role: Mapped[UserRole] = mapped_column(str_enum(UserRole, "user_role", 20))
    status: Mapped[UserStatus] = mapped_column(
        str_enum(UserStatus, "user_status", 20),
        default=UserStatus.ONBOARDING,
        server_default=UserStatus.ONBOARDING.value,
    )

    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # Google's stable user id ("sub" claim). Never match Google users by email alone.
    google_sub: Mapped[str | None] = mapped_column(String(255), unique=True)

    # "Every member is reviewed before access is activated": who approved, and when.
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))