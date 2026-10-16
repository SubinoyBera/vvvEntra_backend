from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.endpoints import health_check
from app.api.v1.router import router
from app.core.config import settings
from app.core.logging import configure_logging
from app.db.redis import redis_client
from app.db.session import engine
from app.core.exceptions import AppError, app_error_handler
from app.middleware.request_context import RequestContextMiddleware
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio

import app.models  # noqa: F401
from app.models.base import Base

STARTUP_TIMEOUT_SECONDS = 15


async def _check_database() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Auto-heal: Ensure all verification, payout, and video columns exist on profiles
        cols = [
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500);",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS is_linkedin_verified BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS linkedin_verified_at TIMESTAMPTZ;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS payout_account_id VARCHAR(255);",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS payout_provider VARCHAR(50) DEFAULT 'stripe';",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS payout_bank_name VARCHAR(100);",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS payout_last4 VARCHAR(10);",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS payout_currency VARCHAR(10) DEFAULT 'USD';",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS is_payout_connected BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS payout_connected_at TIMESTAMPTZ;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS user_video BYTEA;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS user_video_content_type VARCHAR(50) DEFAULT 'video/webm';",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS is_video_submitted BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS video_submitted_at TIMESTAMPTZ;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS is_video_verified BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE architect_profiles ADD COLUMN IF NOT EXISTS video_verified_at TIMESTAMPTZ;",
            "ALTER TABLE investor_profiles ADD COLUMN IF NOT EXISTS linkedin_url VARCHAR(500);",
            "ALTER TABLE investor_profiles ADD COLUMN IF NOT EXISTS is_linkedin_verified BOOLEAN DEFAULT FALSE;",
            "ALTER TABLE investor_profiles ADD COLUMN IF NOT EXISTS linkedin_verified_at TIMESTAMPTZ;",
        ]
        for query in cols:
            try:
                await conn.execute(text(query))
            except Exception:
                pass
        await conn.execute(text("SELECT 1"))

async def _warm_up_dependencies(log: structlog.stdlib.BoundLogger) -> None:
    """
    Open the first DB/Redis connections now. 
    Never block or crash startup on failure.
    """
    results = await asyncio.gather(
        asyncio.wait_for(_check_database(), STARTUP_TIMEOUT_SECONDS),
        asyncio.wait_for(redis_client.ping(), STARTUP_TIMEOUT_SECONDS),
        return_exceptions=True,
    )
    for name, result in zip(("database", "redis"), results, strict=True):
        if isinstance(result, BaseException):
            log.warning("warmup_failed", dependency=name, error=type(result).__name__)
        else:
            log.info("warmup_ok", dependency=name)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    log = structlog.get_logger()
    log.info("startup", app=settings.app_name, environment=settings.environment)
    await _warm_up_dependencies(log)
    try:
        yield
    finally:
        await engine.dispose()
        await redis_client.aclose()
        log.info("shutdown")


def create_app() -> FastAPI:
    configure_logging()
    app = FastAPI(
        title="vvvEntra backend API server",
        lifespan=lifespan,
        docs_url=None if settings.is_production else "/docs",
        redoc_url=None,
        openapi_url=None if settings.is_production else "/openapi.json",
    )

    # Last added = outermost. Request context wraps everything, including CORS responses.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,  # needed for the httpOnly refresh cookie
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    app.add_middleware(RequestContextMiddleware)
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore[arg-type]

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Full traceback goes to the logs; the client only gets a generic message + request_id.
        structlog.get_logger().error(
            "unhandled_exception", method=request.method, path=request.url.path, exc_info=exc
        )
        request_id = structlog.contextvars.get_contextvars().get("request_id")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    # Register routes
    app.include_router(health_check.router)  # /health, /ready (unversioned, for infra)
    app.include_router(router, prefix=settings.api_v1_prefix)
    return app


app = create_app()