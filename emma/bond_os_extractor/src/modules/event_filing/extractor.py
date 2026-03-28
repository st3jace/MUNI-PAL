"""AI extractor for event filing documents."""
from __future__ import annotations

import logging
import uuid
from datetime import date, datetime
from typing import Any

from ...extraction.ai_extractor import AnthropicClient
from ...extraction.cache import compute_cache_key, load_from_cache, save_to_cache
from ...config import get_settings
from ...ingestion.pdf_reader import IngestionResult
from .schema import EventFilingRecord

logger = logging.getLogger("bond_os_extractor.modules.event_filing")

SYSTEM_PROMPT = """You are a municipal bond compliance analyst extracting structured data from event filings, material event notices, 8-K filings, and other regulatory disclosures.

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the document.
- If a field is not present, return null.
- Never infer, estimate, or hallucinate values.
- A null extraction is always preferable to a guessed one.
- Return valid JSON only, no markdown or commentary.

For each field, also provide a confidence score (0.0-1.0) in a parallel "_confidence" object."""

EXTRACTION_PROMPT = """Extract the event filing details from this document:

{text}

Return a JSON object with these exact fields:
{{
  "issuer_name": "legal name of the issuer or null",
  "event_type": "material_event | 8k | notice | supplement | tender | defeasance | redemption | null",
  "filing_date": "YYYY-MM-DD or null",
  "event_date": "YYYY-MM-DD (when the event occurred) or null",
  "event_category": "payment_default | rating_change | defeasance | redemption | tender | bankruptcy | merger | disclosure_failure | tax_status_change | bond_call | financial_obligation | other | null",
  "event_summary": "2-4 sentence summary of the event, or null",
  "financial_impact": "description of financial impact if any, or null",
  "action_required": true/false,
  "affected_series": ["list of affected bond series"],
  "affected_par_amount": "dollar amount affected or null",
  "cusip_references": ["list of CUSIP numbers mentioned"],
  "related_parties": ["list of parties involved (trustee, issuer, borrower, etc.)"],
  "next_steps": "any next steps or follow-up actions mentioned, or null",
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


def extract_event_filing(ingestion: IngestionResult) -> EventFilingRecord:
    """Extract an event filing record from an ingested PDF."""
    settings = get_settings()

    full_text = "\n".join(p.text for p in ingestion.pages if p.text)

    # Guard: skip AI extraction if no readable text
    if len(full_text.strip()) < MIN_TEXT_LENGTH:
        logger.warning(
            "Skipping AI extraction for %s: only %d chars of text (minimum %d)",
            ingestion.source_file, len(full_text.strip()), MIN_TEXT_LENGTH,
        )
        record = EventFilingRecord(
            extraction_id=str(uuid.uuid4()),
            source_file=ingestion.source_file,
            source_hash=ingestion.source_hash,
            extraction_timestamp=datetime.now(tz=None),
            confidence_scores={},
        )
        record.compute_completeness()
        return record

    # Guard: skip AI extraction if Tier 2 is disabled
    if not settings.tier2_enabled:
        logger.info("Tier 2 (AI) disabled, skipping AI extraction for %s", ingestion.source_file)
        record = EventFilingRecord(
            extraction_id=str(uuid.uuid4()),
            source_file=ingestion.source_file,
            source_hash=ingestion.source_hash,
            extraction_timestamp=datetime.now(tz=None),
            confidence_scores={},
        )
        record.compute_completeness()
        return record

    text_for_ai = full_text[:15000]

    # Check cache
    cache_key = compute_cache_key(ingestion.source_hash, "full_doc", "event_filing_v1")
    cached = None
    if settings.ai_cache_enabled:
        cached = load_from_cache(settings.cache_dir, cache_key, settings.cache_ttl_days)

    if cached is not None:
        logger.debug("Cache hit for event filing %s", ingestion.source_hash[:12])
        ai_result = cached
    else:
        client = AnthropicClient()
        prompt = EXTRACTION_PROMPT.format(text=text_for_ai)
        try:
            ai_result = client.extract(SYSTEM_PROMPT, prompt)
        except Exception as exc:
            logger.error("AI extraction failed for %s: %s", ingestion.source_file, exc)
            ai_result = {}

        if settings.ai_cache_enabled and ai_result:
            save_to_cache(settings.cache_dir, cache_key, ai_result)

    confidence = ai_result.pop("_confidence", {})

    record = EventFilingRecord(
        extraction_id=str(uuid.uuid4()),
        source_file=ingestion.source_file,
        source_hash=ingestion.source_hash,
        extraction_timestamp=datetime.now(tz=None),
        cusip_references=ai_result.get("cusip_references") or [],
        issuer_name=ai_result.get("issuer_name"),
        event_type=ai_result.get("event_type"),
        filing_date=_date(ai_result.get("filing_date")),
        event_date=_date(ai_result.get("event_date")),
        event_category=ai_result.get("event_category"),
        event_summary=ai_result.get("event_summary"),
        financial_impact=ai_result.get("financial_impact"),
        action_required=bool(ai_result.get("action_required")),
        affected_series=ai_result.get("affected_series") or [],
        affected_par_amount=ai_result.get("affected_par_amount"),
        related_parties=ai_result.get("related_parties") or [],
        next_steps=ai_result.get("next_steps"),
        confidence_scores=confidence,
    )
    record.compute_completeness()
    return record
