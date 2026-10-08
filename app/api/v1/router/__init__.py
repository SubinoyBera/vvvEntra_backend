from fastapi import APIRouter
from app.api.v1.endpoints import auth, profile, users

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(profile.router, prefix="/profile", tags=["profile"])