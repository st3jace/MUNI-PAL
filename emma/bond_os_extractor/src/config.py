from __future__ import annotations

import logging
from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is bond_os_extractor/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Muni-Pal root is three levels up from src/
MUNIPAL_ROOT = PROJECT_ROOT.parent.parent

logger = logging.getLogger("bond_os_extractor")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(MUNIPAL_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-20250514"
    anthropic_max_tokens: int = 4096

    # Extraction settings
    tier1_enabled: bool = True
    tier2_enabled: bool = True
    ai_cache_enabled: bool = True
    cache_ttl_days: int = 30
    default_confidence_threshold: float = 0.85

    # Logging
    log_level: str = "INFO"

    @computed_field
    @property
    def pdf_source_dir(self) -> Path:
        return MUNIPAL_ROOT / "pdfs"

    @computed_field
    @property
    def data_dir(self) -> Path:
        return PROJECT_ROOT / "data"

    @computed_field
    @property
    def extracted_dir(self) -> Path:
        return PROJECT_ROOT / "data" / "extracted"

    @computed_field
    @property
    def cache_dir(self) -> Path:
        return PROJECT_ROOT / "data" / "cache"

    @computed_field
    @property
    def database_path(self) -> Path:
        return PROJECT_ROOT / "data" / "bond_corpus.db"

    @computed_field
    @property
    def configs_dir(self) -> Path:
        return PROJECT_ROOT / "configs"


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def setup_logging(level: str | None = None) -> None:
    effective_level = level or get_settings().log_level
    logging.basicConfig(
        level=getattr(logging, effective_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )
