import uuid

from pydantic import BaseModel, ConfigDict

from app.models.enums import UserRole, UserStatus


class UserOut(BaseModel):
    """What the frontend may know about a user. Never includes password_hash."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    status: UserStatus  # the frontend picks its screen from this: wizard / under review / dashboard
