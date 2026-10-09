from functools import lru_cache
from typing import Literal
import os
from dotenv import load_dotenv
load_dotenv()  # Load environment variables from .env file

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "vventra-api"
    environment: Literal["local", "staging", "production"] = "local"
    log_level: str = "INFO"
    api_v1_prefix: str = "/api/v1"

    database_url: str = Field(..., validation_alias="POSTGRES_URL")
    db_pool_size: int = 10
    db_max_overflow: int = 10
    redis_url: str = Field(..., validation_alias="REDIS_URL")

    cors_origins: list[str] = Field(default_factory=list)

    # --- auth ---
    # Generate with: python -c "import secrets; print(secrets.token_urlsafe(64))"
    jwt_secret: SecretStr = Field(..., min_length=32)
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 15
    refresh_token_days: int = 7  # normal login
    refresh_token_remember_days: int = 30  # "Keep me signed in" ticked

    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_domain: str | None = None
    cookie_secure: bool | None = None  # None = automatic: off for local, on everywhere else

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def refresh_cookie_secure(self) -> bool:
        if self.cookie_secure is not None:
            return self.cookie_secure
        return self.environment != "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()