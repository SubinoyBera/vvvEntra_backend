"""Import every model here so Alembic autogenerate (migrations/env.py) can see them."""
 
from app.models.architect_profile import ArchitectProfile
from app.models.investor_profile import InvestorProfile
from app.models.refresh_token import RefreshToken
from app.models.user import User
 
__all__ = ["ArchitectProfile", "InvestorProfile", "RefreshToken", "User"]