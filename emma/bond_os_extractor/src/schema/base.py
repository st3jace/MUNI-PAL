from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    """Wrapper for an extracted value with confidence tracking."""
    value: Any = None
    confidence: float = 0.0
    source_section: str | None = None
    extraction_method: str | None = None


class ExtractionMeta(BaseModel):
    """Metadata about how a value was extracted."""
    extraction_id: str = ""
    source_file: str = ""
    source_hash: str = ""
    extraction_timestamp: datetime | None = None
    extraction_version: str = "0.1.0"
