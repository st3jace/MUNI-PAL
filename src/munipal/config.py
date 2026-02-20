"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development.
"""

from functools import lru_cache
from typing import Literal

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_name: str = "munipal"
    app_env: Literal["development", "staging", "production"] = "development"
    debug: bool = True
    secret_key: str = "change-me-in-production"

    # -------------------------------------------------------------------------
    # Database (PostgreSQL or SQLite for dev)
    # -------------------------------------------------------------------------
    use_sqlite: bool = True  # Set to False for PostgreSQL
    sqlite_path: str = "./munipal_dev.db"

    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "munipal"
    postgres_password: str = "munipal_dev_password"
    postgres_db: str = "munipal"

    @computed_field
    @property
    def database_url(self) -> str:
        """Async database URL for SQLAlchemy."""
        if self.use_sqlite:
            return f"sqlite+aiosqlite:///{self.sqlite_path}"
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def database_url_sync(self) -> str:
        """Sync database URL for Alembic migrations."""
        if self.use_sqlite:
            return f"sqlite:///{self.sqlite_path}"
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # -------------------------------------------------------------------------
    # Redis
    # -------------------------------------------------------------------------
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_url: str | None = None  # Override for Redis Cloud

    @computed_field
    @property
    def redis_connection_url(self) -> str:
        """Redis connection URL."""
        if self.redis_url:
            return self.redis_url
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"

    # -------------------------------------------------------------------------
    # Celery
    # -------------------------------------------------------------------------
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    @computed_field
    @property
    def celery_broker(self) -> str:
        """Celery broker URL."""
        return self.celery_broker_url or self.redis_connection_url

    @computed_field
    @property
    def celery_backend(self) -> str:
        """Celery result backend URL."""
        return self.celery_result_backend or self.redis_connection_url

    # -------------------------------------------------------------------------
    # Anthropic (Claude API)
    # -------------------------------------------------------------------------
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4096

    # -------------------------------------------------------------------------
    # JWT Authentication
    # -------------------------------------------------------------------------
    jwt_secret_key: str = "jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    auth_enforcement_v2: bool = False
    role_enforcement_v2: bool = False
    risk_reporting_v2_foundation: bool = False
    risk_reporting_v2_advanced_analytics: bool = False
    risk_reporting_v2_advanced_min_reliability: Literal["high", "medium", "low"] = "high"

    # -------------------------------------------------------------------------
    # File Storage
    # -------------------------------------------------------------------------
    artifact_storage_path: str = "./artifacts"

    # AWS S3 (optional, for production)
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str = "us-east-1"
    s3_bucket_name: str | None = None

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
