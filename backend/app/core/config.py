"""Application settings loaded from environment variables via Pydantic v2."""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import AnyUrl, EmailStr, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application configuration, sourced from .env / environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Runtime ──────────────────────────────────────────────────────────────
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    # ─── Database ─────────────────────────────────────────────────────────────
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://donehr:donehr@postgres:5432/donehr",
        description="Async SQLAlchemy connection string (asyncpg driver).",
    )

    # ─── Cache ────────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(
        default="redis://redis:6379/0",
        description="Redis connection URL.",
    )

    # ─── Security ─────────────────────────────────────────────────────────────
    SECRET_KEY: SecretStr = Field(
        ...,
        min_length=32,
        description="HMAC secret for signing user JWTs. Must be ≥ 32 chars.",
    )
    ADMIN_JWT_SECRET: SecretStr = Field(
        ...,
        min_length=32,
        description="Separate secret for admin-scoped JWTs.",
    )
    ALGORITHM: str = Field(default="HS256", description="JWT signing algorithm.")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=15, gt=0, description="Access token TTL in minutes."
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7, gt=0, description="Refresh token TTL in days."
    )

    # ─── AI ───────────────────────────────────────────────────────────────────
    OPENAI_API_KEY: SecretStr = Field(
        ...,
        description="OpenAI API key (sk-...).",
    )

    # ─── Email / SMTP ─────────────────────────────────────────────────────────
    SMTP_HOST: str = Field(default="smtp.gmail.com")
    SMTP_PORT: int = Field(default=587, gt=0, le=65535)
    SMTP_USER: EmailStr = Field(default="noreply@example.com")
    SMTP_PASSWORD: SecretStr = Field(default=SecretStr(""))

    # ─── App URLs ─────────────────────────────────────────────────────────────
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Allowed CORS origin for the Next.js frontend.",
    )

    # ─── Observability ────────────────────────────────────────────────────────
    OTEL_EXPORTER_OTLP_ENDPOINT: str = Field(
        default="http://localhost:4317",
        description="gRPC endpoint for the OpenTelemetry collector.",
    )

    # ─── Derived helpers ──────────────────────────────────────────────────────
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith("postgresql"):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string.")
        return v

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if not v.startswith("redis://"):
            raise ValueError("REDIS_URL must start with redis://")
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()


# Module-level singleton for direct imports
settings: Settings = get_settings()
