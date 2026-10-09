from fastapi import APIRouter

from app.api.v1.deps import CurrentUser
from app.schemas.user import UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def read_me(user: CurrentUser) -> UserOut:
    """The frontend calls this on load and routes by `status`."""
    return UserOut.model_validate(user)
