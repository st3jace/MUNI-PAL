from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any

logger = logging.getLogger("bond_os_extractor.extraction")


class ExtractionTier(str, Enum):
    TIER_1 = "deterministic"
    TIER_2 = "ai_assisted"


class BaseExtractor(ABC):
    """Abstract base class for all field extractors."""

    tier: ExtractionTier
    name: str = "base"

    @abstractmethod
    def extract(
        self,
        section_text: str,
        section_id: str,
        tables: list[list[list[str]]] | None = None,
    ) -> dict[str, Any]:
        """
        Extract fields from a section of text.

        Returns a dict of field_name -> value.
        Each extractor should also return confidence scores
        via a parallel key like "_confidence".
        """
        ...

    def safe_extract(
        self,
        section_text: str,
        section_id: str,
        tables: list[list[list[str]]] | None = None,
    ) -> dict[str, Any]:
        """Fault-tolerant wrapper: returns empty dict on failure."""
        try:
            return self.extract(section_text, section_id, tables)
        except Exception as exc:
            logger.warning(
                "Extractor %s failed on section %s: %s",
                self.name, section_id, exc,
            )
            return {}
