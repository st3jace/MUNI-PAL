"""
Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve project root (.env lives next to pyproject.toml, one level above src/)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_ENV_FILE = _PROJECT_ROOT / ".env"


def _normalize_redis_url(url: str, ssl_cert_reqs: str) -> str:
    """Ensure hosted Redis TLS URLs carry the ssl_cert_reqs query Celery expects."""
    parsed = urlparse(url)
    if parsed.scheme != "rediss":
        return url

    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.setdefault("ssl_cert_reqs", ssl_cert_reqs)
    return urlunparse(parsed._replace(query=urlencode(query)))


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
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
    redis_username: str | None = None
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    redis_tls: bool = False
    redis_ssl_cert_reqs: Literal["required", "optional", "none"] = "required"
    redis_url: str | None = None  # Override for Redis Cloud

    @computed_field
    @property
    def redis_connection_url(self) -> str:
        """Redis connection URL."""
        if self.redis_url:
            return _normalize_redis_url(self.redis_url, self.redis_ssl_cert_reqs)

        scheme = "rediss" if self.redis_tls else "redis"
        host = self.redis_host.strip()
        auth = ""
        if self.redis_username and self.redis_password:
            auth = f"{quote(self.redis_username, safe='')}:{quote(self.redis_password, safe='')}@"
        elif self.redis_password:
            auth = f":{quote(self.redis_password, safe='')}@"
        elif self.redis_username:
            auth = f"{quote(self.redis_username, safe='')}@"

        url = f"{scheme}://{auth}{host}:{self.redis_port}/{self.redis_db}"
        return _normalize_redis_url(url, self.redis_ssl_cert_reqs)

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
    # Sensing Microservice
    # -------------------------------------------------------------------------
    # Comma-separated list of allowed CORS origins for the public sensing API.
    # Example: "https://assess.launchshop.io,https://launchshop.io"
    sensing_cors_origins: str = ""
    # Rate limit for sensing endpoints (requests per minute per IP)
    sensing_rate_limit: str = "60/minute"

    # -------------------------------------------------------------------------
    # JWT Authentication
    # -------------------------------------------------------------------------
    jwt_secret_key: str = "jwt-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    auth_enforcement_v2: bool = False
    role_enforcement_v2: bool = False
    tenant_isolation_v2: bool = False
    risk_reporting_v2_foundation: bool = False
    risk_reporting_v2_advanced_analytics: bool = False
    risk_reporting_v2_advanced_min_reliability: Literal["high", "medium", "low"] = "high"
    risk_reporting_v2_age_weighting: bool = False
    risk_reporting_v2_age_weighting_full_weight_days: int = 365
    risk_reporting_v2_age_weighting_max_penalty: float = 0.20

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
    # Document Management System
    # -------------------------------------------------------------------------
    document_storage_path: str = "./documents"
    max_document_size_mb: int = 100

    # Dropbox Sign (e-signatures)
    dropbox_sign_api_key: str = ""
    dropbox_sign_client_id: str = ""
    dropbox_sign_webhook_secret: str = ""
    dropbox_sign_test_mode: bool = True

    # Virtual Data Room
    vdr_base_url: str = "http://localhost:5173/vdr"
    vdr_watermark_font_size: int = 12
    legal_template_catalog_path: str = "reports/legal_corpus/legal_template_catalog_latest.json"

    # Feature flags — Document Management
    document_management_v1: bool = False
    esignature_v1: bool = False
    vdr_v1: bool = False

    # -------------------------------------------------------------------------
    # OPS-1001 HTTP Telemetry
    # -------------------------------------------------------------------------
    telemetry_enabled: bool = True
    telemetry_jsonl_path: str = "reports/phase10_postlaunch/ops1001_telemetry_events.jsonl"

    # -------------------------------------------------------------------------
    # Logging
    # -------------------------------------------------------------------------
    log_level: str = "INFO"
    log_format: Literal["json", "console"] = "json"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
