import asyncio
import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_redis

router = APIRouter(tags=["health"])
log = structlog.get_logger()

CHECK_TIMEOUT_SECONDS = 4


@router.get("/health", summary="Liveness check")
async def health() -> dict[str, str]:
    """Process is up. Deliberately touches no external service."""
    return {"status": "ok"}


@router.get("/ready", summary="Readiness check")
async def ready(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> JSONResponse:
    """Dependencies are reachable."""
    checks: dict[str, str] = {}

    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), CHECK_TIMEOUT_SECONDS)
        checks["database"] = "ok"
    except Exception:
        log.warning("readiness_check_failed", dependency="database", exc_info=True)
        checks["database"] = "error"

    try:
        await asyncio.wait_for(redis.ping(), CHECK_TIMEOUT_SECONDS)
        checks["redis"] = "ok"
    except Exception:
        log.warning("readiness_check_failed", dependency="redis", exc_info=True)
        checks["redis"] = "error"

    ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        status_code=200 if ok else 503,
        content={"status": "ready" if ok else "not_ready", "checks": checks},
    )