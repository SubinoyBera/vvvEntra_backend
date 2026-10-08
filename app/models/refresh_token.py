import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDPrimaryKeyMixin


class RefreshToken(UUIDPrimaryKeyMixin, Base):
    """One row per issued refresh token. We store a hash, never the token itself."""

    __tablename__ = "refresh_tokens"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    # SHA-256 hex of the random token. A DB leak must not hand out working sessions.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True)
    # All tokens descended from one login share a family_id (rotation chain).
    # If an already-used token is replayed, we revoke the whole family.
    family_id: Mapped[uuid.UUID] = mapped_column(index=True)

    # "Keep me signed in": persistent cookie + longer lifetime vs. a session cookie.
    remember_me: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))

    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user_agent: Mapped[str | None] = mapped_column(String(255))
    ip_address: Mapped[str | None] = mapped_column(String(45))  # fits IPv6