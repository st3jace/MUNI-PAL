"""AI extractor for rating action documents."""
from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date, datetime
from typing import Any

from ...extraction.ai_extractor import AnthropicClient
from ...extraction.cache import compute_cache_key, load_from_cache, save_to_cache
from ...config import get_settings
from ...ingestion.pdf_reader import IngestionResult
from .schema import RatingActionRecord

logger = logging.getLogger("bond_os_extractor.modules.rating_action")

SYSTEM_PROMPT = """You are a municipal bond credit analyst extracting structured data from a rating agency report.

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the document.
- If a field is not present, return null.
- Never infer, estimate, or hallucinate values.
- A null extraction is always preferable to a guessed one.
- Return valid JSON only, no markdown or commentary.

For each field, also provide a confidence score (0.0-1.0) in a parallel "_confidence" object."""

EXTRACTION_PROMPT = """Extract the rating action details from this document:

{text}

Return a JSON object with these exact fields:
{{
  "issuer_name": "legal name of the issuer or obligor, or null",
  "obligor_name": "name of the obligor/borrower if different from issuer, or null",
  "agency": "moodys | sp | fitch | kroll | dbrs | null",
  "action_type": "upgrade | downgrade | affirm | outlook_change | watch_placed | watch_removed | new_rating | withdrawal | null",
  "previous_rating": "the prior rating (e.g. 'Baa1', 'BBB+', 'A-') or null",
  "new_rating": "the new/current rating or null",
  "previous_outlook": "stable | positive | negative | developing | null",
  "new_outlook": "stable | positive | negative | developing | null",
  "action_date": "YYYY-MM-DD or null",
  "effective_date": "YYYY-MM-DD or null",
  "bond_series_affected": ["list of affected bond series names"],
  "bond_type": "revenue | general_obligation | conduit | special_assessment | null",
  "rationale_summary": "1-3 sentence summary of why the action was taken, or null",
  "key_factors": ["list of key factors driving the action"],
  "credit_strengths": ["list of credit strengths mentioned"],
  "credit_challenges": ["list of credit challenges or weaknesses mentioned"],
  "sector": "solid_waste | water_sewer | electric | gas | transportation | healthcare | housing | education | general_government | null",
  "cusip_references": ["list of any CUSIP numbers mentioned"],
  "_confidence": {{field_name: 0.0-1.0 for each field}}
}}"""


def _date(val: Any) -> date | None:
    """Safely convert a value to a date."""
    if val is None:
        return None
    if isinstance(val, date):
        return val
    try:
        from dateutil import parser as dateparser
        return dateparser.parse(str(val)).date()
    except Exception:
        return None


MIN_TEXT_LENGTH = 100  # Minimum chars to attempt AI extraction


def extract_rating_action(ingestion: IngestionResult) -> RatingActionRecord:
    """Extract a rating action record from an ingested PDF.

    Args:
        ingestion: The PDF ingestion result.

    Returns:
        Populated RatingActionRecord.
    """
    settings = get_settings()

    # Combine all page text (rating actions are typically short documents)
    full_text = "\n".join(p.text for p in ingestion.pages if p.text)

    # Guard: skip AI extraction if no readable text
    if len(full_text.strip()) < MIN_TEXT_LENGTH:
        logger.warning(
            "Skipping AI extraction for %s: only %d chars of text (minimum %d)",
            ingestion.source_file, len(full_text.strip()), MIN_TEXT_LENGTH,
        )
        record = RatingActionRecord(
            extraction_id=str(uuid.uuid4()),
            source_file=ingestion.source_file,
            source_hash=ingestion.source_hash,
            extraction_timestamp=datetime.now(tz=None),
            confidence_scores={},
        )
        record.compute_completeness()
        return record

    # Truncate to fit in context window
    text_for_ai = full_text[:15000]

    # Check cache
    cache_key = compute_cache_key(ingestion.source_hash, "full_doc", "rating_action_v1")
    cached = None
    if settings.ai_cache_enabled:
        cached = load_from_cache(settings.cache_dir, cache_key, settings.cache_ttl_days)

    if cached is not None:
        logger.debug("Cache hit for rating action %s", ingestion.source_hash[:12])
        ai_result = cached
    else:
        # Run AI extraction
        client = AnthropicClient()
        prompt = EXTRACTION_PROMPT.format(text=text_for_ai)
        try:
            ai_result = client.extract(SYSTEM_PROMPT, prompt)
        except Exception as exc:
            logger.error("AI extraction failed for %s: %s", ingestion.source_file, exc)
            ai_result = {}

        # Cache the result
        if settings.ai_cache_enabled and ai_result:
            save_to_cache(settings.cache_dir, cache_key, ai_result)

    # Extract confidence scores
    confidence = ai_result.pop("_confidence", {})

    # Build the record
    record = RatingActionRecord(
        extraction_id=str(uuid.uuid4()),
        source_file=ingestion.source_file,
        source_hash=ingestion.source_hash,
        extraction_timestamp=datetime.now(tz=None),
        cusip_references=ai_result.get("cusip_references") or [],
        issuer_name=ai_result.get("issuer_name"),
        obligor_name=ai_result.get("obligor_name"),
        agency=ai_result.get("agency"),
        action_type=ai_result.get("action_type"),
        previous_rating=ai_result.get("previous_rating"),
        new_rating=ai_result.get("new_rating"),
        previous_outlook=ai_result.get("previous_outlook"),
        new_outlook=ai_result.get("new_outlook"),
        action_date=_date(ai_result.get("action_date")),
        effective_date=_date(ai_result.get("effective_date")),
        bond_series_affected=ai_result.get("bond_series_affected") or [],
        bond_type=ai_result.get("bond_type"),
        rationale_summary=ai_result.get("rationale_summary"),
        key_factors=ai_result.get("key_factors") or [],
        credit_strengths=ai_result.get("credit_strengths") or [],
        credit_challenges=ai_result.get("credit_challenges") or [],
        sector=ai_result.get("sector"),
        confidence_scores=confidence,
    )
    record.compute_completeness()
    return record
