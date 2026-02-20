"""Abstract base class for document extraction modules."""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Table
from sqlalchemy.engine import Engine

from ..ingestion.pdf_reader import IngestionResult

logger = logging.getLogger("bond_os_extractor.modules")


class DocumentModule(ABC):
    """Base class for all document type modules.

    Each module handles a specific category of EMMA documents
    (e.g., rating actions, event filings, financial reports).
    Modules are self-contained: they own their schema, extraction
    logic, and database tables.
    """

    name: str = ""
    display_name: str = ""
    file_patterns: list[str] = []

    @abstractmethod
    def matches(self, filename: str, first_page_text: str) -> float:
        """Return confidence 0.0-1.0 that this module handles this document.

        Args:
            filename: The PDF filename (EMMA filenames encode document type).
            first_page_text: Text from the first page for content-based matching.

        Returns:
            Confidence score. 0.0 = definitely not this type,
            1.0 = definitely this type.
        """
        ...

    @abstractmethod
    def extract(self, ingestion: IngestionResult) -> BaseModel:
        """Run the extraction pipeline for this document type.

        Args:
            ingestion: The PDF ingestion result with pages and tables.

        Returns:
            Module-specific Pydantic record (e.g., RatingActionRecord).
        """
        ...

    @abstractmethod
    def db_tables(self) -> list[Table]:
        """Return SQLAlchemy Table definitions for this module."""
        ...

    @abstractmethod
    def save(self, engine: Engine, record: BaseModel) -> str:
        """Save an extracted record to the database.

        Returns:
            The document/extraction ID.
        """
        ...

    @abstractmethod
    def get_stats(self, engine: Engine) -> dict[str, Any]:
        """Return corpus statistics for this module's documents."""
        ...

    def export_json(self, record: BaseModel, output_dir=None) -> Any:
        """Export a record to JSON. Uses shared json_export by default."""
        from ..storage.json_export import _make_serializable
        from ..config import get_settings
        import json
        from pathlib import Path

        if output_dir is None:
            output_dir = get_settings().extracted_dir / self.name
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        data = _make_serializable(record)

        # Build filename from record fields
        source_hash = getattr(record, "source_hash", "nohash")
        issuer = getattr(record, "issuer_name", None) or "unknown"
        issuer_short = "".join(
            c if c.isalnum() or c in " -_" else "_" for c in issuer[:40]
        ).strip().replace(" ", "_")
        hash_prefix = source_hash[:12]
        filename = f"{hash_prefix}_{issuer_short}.json"

        output_path = output_dir / filename
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info("Exported %s JSON: %s", self.name, output_path.name)
        return output_path
