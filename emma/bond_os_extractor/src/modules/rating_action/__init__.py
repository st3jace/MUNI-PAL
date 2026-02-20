"""Rating Action document module."""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Table
from sqlalchemy.engine import Engine

from ..base import DocumentModule
from ...ingestion.pdf_reader import IngestionResult
from .schema import RatingActionRecord
from .extractor import extract_rating_action
from .storage import get_tables, init_tables, save_rating_action, get_rating_action_stats


class RatingActionModule(DocumentModule):
    """Module for extracting rating action documents from Moody's, S&P, Fitch, etc."""

    name = "rating_action"
    display_name = "Rating Action"
    file_patterns = [
        "*Rating_Action*",
        "*Rating_Update*",
        "*Rating_Upgrade*",
        "*Rating_Downgrade*",
        "*Rating_Affirm*",
        "*Rating_Change*",
        "*Moodys*",
        "*Moody_s*",
        "*S_P*",
        "*Fitch*",
        "*KBRA*",
        "*Kroll*",
        "*DBRS*",
        "*Credit_Opinion*",
        "*Credit_Rating*",
    ]

    # Content patterns to match on first page text
    _CONTENT_PATTERNS = [
        re.compile(r"rating\s+action", re.IGNORECASE),
        re.compile(r"(moody.s|standard\s+.?\s+poor|fitch\s+rat|kroll\s+bond)", re.IGNORECASE),
        re.compile(r"(upgrade[sd]?|downgrade[sd]?|affirm[sed])\s+(the\s+)?rating", re.IGNORECASE),
        re.compile(r"credit\s+(opinion|rating|update)", re.IGNORECASE),
        re.compile(r"outlook\s+(changed?|revised?|remains?|stable|positive|negative)", re.IGNORECASE),
    ]

    # Agency names that appear in EMMA filenames
    _AGENCY_KEYWORDS = ["moodys", "moody_s", "s_p", "fitch", "kbra", "kroll", "dbrs"]
    # Rating action keywords that appear in EMMA filenames
    _ACTION_KEYWORDS = ["rating_action", "rating_update", "rating_upgrade",
                        "rating_downgrade", "rating_affirm", "rating_change",
                        "credit_opinion", "credit_rating"]

    def matches(self, filename: str, first_page_text: str) -> float:
        """Check if this document is a rating action."""
        score = 0.0

        # Filename check
        fn_lower = filename.lower()
        has_action_kw = any(kw in fn_lower for kw in self._ACTION_KEYWORDS)
        has_agency_kw = any(kw in fn_lower for kw in self._AGENCY_KEYWORDS)

        if has_action_kw and has_agency_kw:
            # Both agency + action in filename = definitive match (e.g. "Moody_s_Rating_Upgrade")
            score = max(score, 0.98)
        elif has_action_kw:
            score = max(score, 0.9)
        elif has_agency_kw:
            score = max(score, 0.7)

        # Content check
        if first_page_text:
            matches_count = sum(1 for p in self._CONTENT_PATTERNS if p.search(first_page_text))
            if matches_count >= 3:
                score = max(score, 0.95)
            elif matches_count >= 2:
                score = max(score, 0.8)
            elif matches_count >= 1:
                score = max(score, 0.5)

        return score

    def extract(self, ingestion: IngestionResult) -> RatingActionRecord:
        """Run extraction on a rating action PDF."""
        return extract_rating_action(ingestion)

    def db_tables(self) -> list[Table]:
        return get_tables()

    def save(self, engine: Engine, record: BaseModel) -> str:
        assert isinstance(record, RatingActionRecord)
        init_tables(engine)
        return save_rating_action(engine, record)

    def get_stats(self, engine: Engine) -> dict[str, Any]:
        return get_rating_action_stats(engine)


# Auto-discovery attribute
module = RatingActionModule()
