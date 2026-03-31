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
# Filename Issuer Extractor
# ---------------------------------------------------------------------------

# Healthcare EMMA filings embed the health-system or hospital name in the
# document filename.  Pattern examples:
#   A005B8…_0004_Letter_of_Credit_Reimbursement_Agreement_pdf_3_5_M.pdf
#   A005B8…_0017_Hospital_Sisters_Health_System_monthly_Self_Liquid.pdf
#
# Two strategies are used:
# 1. Leading-word extraction: strip prefix, take words until a document-type
#    keyword is hit.
# 2. Deep health-org scan: search anywhere in the filename for a known
#    health-system anchor word with surrounding context.

_DOC_NOISE_RE = re.compile(
    r"^(?:monthly|quarterly|annual|continuing|disclosure|operating|"
    r"statistics|statisti|liquidity|summary|self|liquid|"
    r"disclosures|redacted|amendment|credit|standard|poor|downgrade|"
    r"upgrade|rating|compilation|report|cover|letter|incorporate|"
    r"preliminary|official|statement|supplement|swap|agreement|"
    r"construction|update|incurrence|obligation|financial|package|"
    r"information|government|agency|securities|purchase|bond|exhibit|"
    r"income|balance|sheet|stand|series|cfo|ceo|coo|announcement|"
    r"announces|conference|presentation|investor|barclays|jpm|citi|"
    r"truist|pnc|usbank|renewal|dated|notice|certificate|regarding|"
    r"compliance|modification|rights|bondholder|call|results|"
    r"management|discussion|voluntary|fiscal|invitation|amending|"
    r"retire|joins|quarter|certain|utilization|officers|pdf|"
    r"invest|KB|MB|GB)$",
    re.IGNORECASE,
)

_HEALTH_ORG_DEEP_RE = re.compile(
    r"((?:[A-Z][a-z]+[_ ])*"
    r"(?:Health|Hospital|Medical|Baptist|Methodist|Memorial|Children|"
    r"Community|Advent|Mercy|Trinity|Providence|Ascension|"
    r"Lifespan|Bronson|Carilion|Intermountain|Summa|"
    r"Dignity|Kaiser|Sutter|Tenet|HCA|UHS|"
    r"Sentara|Novant|WellSpan|Geisinger|UPMC|Cedars|"
    r"Sinai|Mount|Mayo|Cleveland|Duke|Johns|Hopkins|"
    r"Vanderbilt|Emory|Stanford|UCLA|NYU|Mass|General|"
    r"Cook|Baylor|Scott|White|Ochsner|SSM|Avera|"
    r"Sanford|Essentia|Atrium|Advocate|Aurora|"
    r"NorthShore|Rush|Beaumont|Spectrum|Corewell|"
    r"IU|OSF|Froedtert|Gundersen|Marshfield|"
    r"Ballad|WVU|UofL|Penn|Highlands|Hendrick|"
    r"Parkview|Genesis|Charleston|Vandalia|HonorHealth|"
    r"AdventHealth|Southeastern|Regional)"
    r"(?:[_ ][A-Za-z]+)*"
    r"(?:[_ ](?:System|Group|Network|Center|Corp|Inc|"
    r"Alliance|Clinic|Care|Healthcare|Health))*)",
    re.IGNORECASE,
)


class FilenameIssuerExtractor(BaseExtractor):
    """Tier 1 extractor that infers issuer/borrower from document filename.

    Pass source_file at construction time so it works with the standard
    safe_extract(section_text, section_id) interface.
    """

    tier = ExtractionTier.TIER_1
    name = "filename_issuer_extractor"

    def __init__(self, source_file: str | None = None) -> None:
        self._source_file = source_file

    def extract(
        self, section_text: str, section_id: str, tables=None,
    ) -> dict[str, Any]:
        if not self._source_file:
            return {}

        # Strip hex CUSIP prefix + sequence number
        cleaned = re.sub(r"^[A-F0-9]+_\d+_", "", self._source_file, flags=re.I)
        cleaned = re.sub(r"_?pdf_.*$", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\.pdf$", "", cleaned, flags=re.I)

        # Strategy 1: leading-word extraction
        name = self._leading_word_extract(cleaned)

        # Strategy 2: deep health-org scan (anywhere in filename)
        if not name:
            name = self._deep_org_scan(cleaned)

        if not name or len(name) < 4:
            return {}

        return {
            "borrower_name": name,
            "_confidence": {"borrower_name": 0.65},
        }

    @staticmethod
    def _leading_word_extract(cleaned: str) -> str | None:
        words = cleaned.split("_")
        name_words: list[str] = []
        for w in words:
            if _DOC_NOISE_RE.match(w):
                break
            if re.match(r"^\d{4}$", w):
                break
            if re.match(r"^\d+$", w) and len(w) <= 2:
                break
            if len(w) <= 1:
                break
            name_words.append(w)
        name = " ".join(name_words).strip()
        name = re.sub(
            r"\s+(?:for|the|as|of|to|in|at|by|on|and|or)$",
            "", name, flags=re.I,
        ).strip()
        return name if name and len(name) >= 4 else None

    @staticmethod
    def _deep_org_scan(cleaned: str) -> str | None:
        spaced = cleaned.replace("_", " ")
        m = _HEALTH_ORG_DEEP_RE.search(spaced)
        return m.group(0).strip() if m else None


# ---------------------------------------------------------------------------
# Registry of all Tier 1 extractors
# ---------------------------------------------------------------------------

ALL_DETERMINISTIC_EXTRACTORS: list[type[BaseExtractor]] = [
    CUSIPExtractor,
    ParAmountExtractor,
    DateExtractor,
    RatingExtractor,
    SeriesExtractor,
    FilenameIssuerExtractor,
]
