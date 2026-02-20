from __future__ import annotations

import logging
import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

from .base_extractor import BaseExtractor, ExtractionTier

logger = logging.getLogger("bond_os_extractor.extraction.deterministic")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_currency(text: str) -> Decimal | None:
    """Parse dollar amount strings like '$123,456,789.00'."""
    m = re.search(r"\$\s*([\d,]+(?:\.\d{1,2})?)", text)
    if m:
        try:
            return Decimal(m.group(1).replace(",", ""))
        except InvalidOperation:
            pass
    return None


def _parse_date(text: str) -> date | None:
    """Try common date formats found in OS documents."""
    from dateutil import parser as dateparser
    try:
        return dateparser.parse(text, fuzzy=True).date()
    except Exception:
        return None


def _find_all_cusips(text: str) -> list[str]:
    """Find CUSIP numbers (9 alphanumeric characters with at least 2 digits)."""
    # CUSIP format: 6-char issuer + 2-char issue + 1 check digit
    # Must contain at least 2 digits to avoid matching plain words
    pattern = r"\b([0-9A-Z]{6})\s*([0-9A-Z]{2}[0-9])\b"
    matches = re.findall(pattern, text)
    cusips: list[str] = []
    seen: set[str] = set()
    for base, suffix in matches:
        cusip = base + suffix
        # Require at least 2 digits total and no lowercase
        digit_count = sum(1 for c in cusip if c.isdigit())
        if digit_count < 2:
            continue
        if cusip in seen:
            continue
        seen.add(cusip)
        cusips.append(cusip)
    return cusips


# ---------------------------------------------------------------------------
# CUSIP Extractor
# ---------------------------------------------------------------------------

class CUSIPExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "cusip_extractor"

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        cusips = _find_all_cusips(section_text)
        result: dict[str, Any] = {"cusip_series": cusips}
        if cusips:
            # Base CUSIP is first 6 characters of the first found
            result["cusip_base"] = cusips[0][:6]
        result["_confidence"] = {"cusip_series": 0.95 if cusips else 0.0}
        return result


# ---------------------------------------------------------------------------
# Par Amount Extractor
# ---------------------------------------------------------------------------

class ParAmountExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "par_amount_extractor"

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        # Look for large dollar amounts on the cover page
        # Pattern: "$123,456,789" or "$123,456,789.00"
        amounts: list[Decimal] = []
        for m in re.finditer(r"\$\s*([\d,]+(?:\.\d{1,2})?)", section_text):
            try:
                val = Decimal(m.group(1).replace(",", ""))
                if val >= 100_000:  # At least $100K to be a par amount
                    amounts.append(val)
            except InvalidOperation:
                continue

        result: dict[str, Any] = {}
        if amounts:
            # Usually the largest amount on the cover is the par amount
            result["par_amount"] = max(amounts)
            result["_confidence"] = {"par_amount": 0.85}
        return result


# ---------------------------------------------------------------------------
# Date Extractor
# ---------------------------------------------------------------------------

class DateExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "date_extractor"

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        confidence: dict[str, float] = {}

        # Dated Date pattern
        m = re.search(r"[Dd]ated\s*[Dd]ate[:\s]*(.+?)(?:\n|$)", section_text)
        if m:
            d = _parse_date(m.group(1).strip())
            if d:
                result["dated_date"] = d
                confidence["dated_date"] = 0.90

        # Delivery Date pattern
        m = re.search(
            r"(?:[Dd]elivery|[Cc]losing)\s*[Dd]ate[:\s]*(.+?)(?:\n|$)",
            section_text,
        )
        if m:
            d = _parse_date(m.group(1).strip())
            if d:
                result["delivery_date"] = d
                confidence["delivery_date"] = 0.90

        # Sale Date
        m = re.search(r"[Ss]ale\s*[Dd]ate[:\s]*(.+?)(?:\n|$)", section_text)
        if m:
            d = _parse_date(m.group(1).strip())
            if d:
                result["sale_date"] = d
                confidence["sale_date"] = 0.85

        result["_confidence"] = confidence
        return result


# ---------------------------------------------------------------------------
# Rating Extractor
# ---------------------------------------------------------------------------

class RatingExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "rating_extractor"

    PATTERNS = [
        (r"(?:Moody'?s|Moody)[:\s]*['\"]?([A-Z][a-z]{1,2}\d?)\b", "moodys"),
        (r"(?:S&P|Standard\s*(?:&|and)\s*Poor'?s?)[:\s]*['\"]?([A-Z]{1,3}[+-]?)\b", "sp"),
        (r"(?:Fitch)[:\s]*['\"]?([A-Z]{1,3}[+-]?)\b", "fitch"),
        (r"(?:Kroll|KBRA)[:\s]*['\"]?([A-Z]{1,3}[+-]?)\b", "kroll"),
    ]

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        ratings: list[dict[str, str]] = []
        for pattern, agency in self.PATTERNS:
            m = re.search(pattern, section_text)
            if m:
                ratings.append({"agency": agency, "rating": m.group(1)})

        result: dict[str, Any] = {}
        if ratings:
            result["ratings"] = ratings
            result["_confidence"] = {"ratings": 0.80}
        return result


# ---------------------------------------------------------------------------
# Series/Title Extractor
# ---------------------------------------------------------------------------

class SeriesExtractor(BaseExtractor):
    tier = ExtractionTier.TIER_1
    name = "series_extractor"

    def extract(self, section_text: str, section_id: str, tables=None) -> dict[str, Any]:
        result: dict[str, Any] = {}
        confidence: dict[str, float] = {}

        # Series pattern: "Series 2024A", "Series 2023"
        m = re.search(r"(Series\s+\d{4}[A-Z]*)", section_text, re.IGNORECASE)
        if m:
            result["series_name"] = m.group(1)
            confidence["series_name"] = 0.90

        # Document type
        if re.search(r"PRELIMINARY\s+OFFICIAL\s+STATEMENT", section_text, re.IGNORECASE):
            result["document_type"] = "POS"
            confidence["document_type"] = 0.95
        elif re.search(r"OFFICIAL\s+STATEMENT", section_text, re.IGNORECASE):
            result["document_type"] = "OS"
            confidence["document_type"] = 0.95

        result["_confidence"] = confidence
        return result


# ---------------------------------------------------------------------------
# Registry of all Tier 1 extractors
# ---------------------------------------------------------------------------

ALL_DETERMINISTIC_EXTRACTORS: list[type[BaseExtractor]] = [
    CUSIPExtractor,
    ParAmountExtractor,
    DateExtractor,
    RatingExtractor,
    SeriesExtractor,
]
