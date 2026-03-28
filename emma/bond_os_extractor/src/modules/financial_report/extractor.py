"""AI extractor for financial report documents."""
from __future__ import annotations

import logging
import re
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from ...extraction.ai_extractor import AnthropicClient
from ...extraction.cache import compute_cache_key, load_from_cache, save_to_cache
from ...config import get_settings
from ...ingestion.pdf_reader import IngestionResult
from .schema import FinancialReportRecord

logger = logging.getLogger("bond_os_extractor.modules.financial_report")

SYSTEM_PROMPT = """You are a municipal bond financial analyst extracting structured financial data from annual reports, quarterly reports, and financial disclosures.

CRITICAL RULES:
- Extract ONLY what is explicitly stated in the document.
- If a field is not present, return null.
- Never infer, estimate, or hallucinate values.
- For financial amounts, extract them as numbers (no dollar signs or commas).
- When amounts are in thousands or millions, convert to actual dollar amounts.
- A null extraction is always preferable to a guessed one.
- Return valid JSON only, no markdown or commentary.

For each field, also provide a confidence score (0.0-1.0) in a parallel "_confidence" object."""

EXTRACTION_PROMPT = """Extract the financial report details from this document:

{text}

Return a JSON object with these exact fields:
{{
  "issuer_name": "legal name of the issuer or null",
  "obligor_name": "name of the obligor/borrower if different, or null",
  "report_type": "annual | quarterly | monthly | 10k | 10q | null",
  "fiscal_period_end": "YYYY-MM-DD or null",
  "fiscal_year": integer or null,
  "total_revenue": number or null,
  "total_expenses": number or null,
  "operating_income": number or null,
  "net_income": number or null,
  "total_assets": number or null,
  "total_liabilities": number or null,
  "total_equity": number or null,
  "cash_and_equivalents": number or null,
  "debt_service_coverage_ratio": number or null,
  "days_cash_on_hand": integer or null,
  "total_debt_outstanding": number or null,
  "annual_debt_service": number or null,
  "key_metrics": {{any sector-specific metrics as key-value pairs}},
  "auditor_name": "name of the audit firm or null",
  "audit_opinion": "unmodified | qualified | adverse | disclaimer | null",
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


def _dec(val: Any) -> Decimal | None:
    """Safely convert a value to Decimal."""
    if val is None:
        return None
    try:
        return Decimal(str(val))
    except Exception:
        return None


def _is_financial_table_page(page_text: str) -> bool:
    """Check if a page contains actual financial table data (not narrative references).

    Detects both corporate financial statements (ALL-CAPS "CONSOLIDATED" headers)
    and municipal government financial statements (Title Case "Statement of Net Position",
    "Balance Sheet - Governmental Funds", etc.).

    Requires a matching header AND dense numerical data (>=15 numbers) to distinguish
    actual table pages from narrative text that merely references these statements.
    """
    # Corporate: ALL-CAPS headers used for 10-K/10-Q financial statement titles
    corporate_headers = [
        re.compile(r"CONSOLIDATED\s+BALANCE\s+SHEETS?\b"),
        re.compile(r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+OPERATIONS\b"),
        re.compile(r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+INCOME\b"),
        re.compile(r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+EARNINGS\b"),
        re.compile(r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+CASH\s+FLOWS?\b"),
        re.compile(r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+(?:STOCKHOLDERS?|SHAREHOLDERS?)"),
        re.compile(r"CONSOLIDATED\s+STATEMENTS?\s+OF\s+COMPREHENSIVE"),
    ]

    # Municipal/Government: Title Case headers used in CAFRs and audited financials
    municipal_headers = [
        re.compile(r"Statement\s+of\s+Net\s+(?:Position|Assets)", re.IGNORECASE),
        re.compile(r"Statement\s+of\s+Activities", re.IGNORECASE),
        re.compile(r"Statement\s+of\s+Revenues", re.IGNORECASE),
        re.compile(r"Balance\s+Sheet\s*[-\u2013\u2014]?\s*Governmental", re.IGNORECASE),
        re.compile(r"Statement\s+of\s+(?:Changes\s+in\s+)?Fund\s+Balances?", re.IGNORECASE),
        re.compile(r"Statement\s+of\s+Cash\s+Flows", re.IGNORECASE),
        re.compile(r"Budgetary\s+Comparison\s+Schedule", re.IGNORECASE),
        re.compile(r"Statement\s+of\s+(?:Fiduciary\s+)?Net\s+Position", re.IGNORECASE),
        re.compile(r"Combining\s+(?:Balance\s+Sheet|Statement)", re.IGNORECASE),
    ]

    has_header = (
        any(pat.search(page_text) for pat in corporate_headers)
        or any(pat.search(page_text) for pat in municipal_headers)
    )

    # Dense numerical data = actual financial table, not narrative
    number_count = len(re.findall(r"[\d,]{3,}", page_text))

    return has_header and number_count >= 15


def _is_auditor_page(page_text: str) -> bool:
    """Check if a page is the auditor's report."""
    return bool(re.search(
        r"REPORT\s+OF\s+INDEPENDENT\s+(?:REGISTERED\s+)?(?:PUBLIC\s+)?ACCOUNT",
        page_text
    )) or bool(re.search(r"INDEPENDENT\s+AUDITOR", page_text, re.IGNORECASE))


def _build_financial_text(ingestion: IngestionResult, budget: int = 40000) -> str:
    """Build a targeted text window for financial report AI extraction.

    For short documents (<budget chars), sends everything.
    For long documents (10-K, annual reports), uses page-level detection
    to find actual financial statement tables (ALL-CAPS headers + dense
    numbers) rather than narrative references.
    """
    full_text = "\n".join(p.text for p in ingestion.pages if p.text)

    if len(full_text) <= budget:
        return full_text

    # Phase 1: Collect the first few pages for header/metadata (issuer, type, dates)
    header_pages: list[str] = []
    header_chars = 0
    header_budget = 8000
    for p in ingestion.pages:
        if not p.text:
            continue
        if header_chars + len(p.text) > header_budget:
            header_pages.append(p.text[:header_budget - header_chars])
            break
        header_pages.append(p.text)
        header_chars += len(p.text)
    header = "\n".join(header_pages)

    # Phase 2: Find financial table pages and auditor report using page-level detection
    table_pages: list[int] = []  # page indices with actual financial tables
    auditor_pages: list[int] = []

    for i, p in enumerate(ingestion.pages):
        if not p.text:
            continue
        if _is_financial_table_page(p.text):
            table_pages.append(i)
        elif _is_auditor_page(p.text):
            auditor_pages.append(i)

    if not table_pages and not auditor_pages:
        # No structured financial pages found — fall back to first+last chunks
        logger.debug("No financial table pages detected, using first+last fallback")
        tail = full_text[-15000:]
        return header + "\n\n[...document truncated...]\n\n" + tail

    # Phase 3: Build text from financial pages + their neighbors
    # Include each financial table page plus the next page (tables often span 2 pages)
    pages_to_include: set[int] = set()
    for idx in table_pages:
        pages_to_include.add(idx)
        if idx + 1 < len(ingestion.pages):
            pages_to_include.add(idx + 1)
    for idx in auditor_pages:
        pages_to_include.add(idx)

    # Collect text from selected pages, respecting budget
    remaining = budget - len(header) - 200  # separator overhead
    section_parts: list[str] = []
    chars_used = 0

    for idx in sorted(pages_to_include):
        page = ingestion.pages[idx]
        if not page.text:
            continue
        if chars_used + len(page.text) > remaining:
            # Include partial page to fill remaining budget
            section_parts.append(page.text[:remaining - chars_used])
            break
        section_parts.append(page.text)
        chars_used += len(page.text)

    logger.debug(
        "Financial text: %d header chars + %d pages (%d chars) of financial tables",
        len(header), len(section_parts), chars_used,
    )

    sections = "\n\n".join(section_parts)
    return header + "\n\n[...skipping to financial statements...]\n\n" + sections


MIN_TEXT_LENGTH = 100  # Minimum chars to attempt AI extraction


def extract_financial_report(ingestion: IngestionResult) -> FinancialReportRecord:
    """Extract a financial report record from an ingested PDF."""
    settings = get_settings()

    # Guard: skip AI extraction if no readable text
    full_text_check = "".join(p.text for p in ingestion.pages if p.text)
    if len(full_text_check.strip()) < MIN_TEXT_LENGTH:
        logger.warning(
            "Skipping AI extraction for %s: only %d chars of text (minimum %d)",
            ingestion.source_file, len(full_text_check.strip()), MIN_TEXT_LENGTH,
        )
        record = FinancialReportRecord(
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
        record = FinancialReportRecord(
            extraction_id=str(uuid.uuid4()),
            source_file=ingestion.source_file,
            source_hash=ingestion.source_hash,
            extraction_timestamp=datetime.now(tz=None),
            confidence_scores={},
        )
        record.compute_completeness()
        return record

    text_for_ai = _build_financial_text(ingestion)

    cache_key = compute_cache_key(ingestion.source_hash, "full_doc", "financial_report_v4")
    cached = None
    if settings.ai_cache_enabled:
        cached = load_from_cache(settings.cache_dir, cache_key, settings.cache_ttl_days)

    if cached is not None:
        logger.debug("Cache hit for financial report %s", ingestion.source_hash[:12])
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

    record = FinancialReportRecord(
        extraction_id=str(uuid.uuid4()),
        source_file=ingestion.source_file,
        source_hash=ingestion.source_hash,
        extraction_timestamp=datetime.now(tz=None),
        cusip_references=ai_result.get("cusip_references") or [],
        issuer_name=ai_result.get("issuer_name"),
        obligor_name=ai_result.get("obligor_name"),
        report_type=ai_result.get("report_type"),
        fiscal_period_end=_date(ai_result.get("fiscal_period_end")),
        fiscal_year=ai_result.get("fiscal_year"),
        total_revenue=_dec(ai_result.get("total_revenue")),
        total_expenses=_dec(ai_result.get("total_expenses")),
        operating_income=_dec(ai_result.get("operating_income")),
        net_income=_dec(ai_result.get("net_income")),
        total_assets=_dec(ai_result.get("total_assets")),
        total_liabilities=_dec(ai_result.get("total_liabilities")),
        total_equity=_dec(ai_result.get("total_equity")),
        cash_and_equivalents=_dec(ai_result.get("cash_and_equivalents")),
        debt_service_coverage_ratio=_dec(ai_result.get("debt_service_coverage_ratio")),
        days_cash_on_hand=ai_result.get("days_cash_on_hand"),
        total_debt_outstanding=_dec(ai_result.get("total_debt_outstanding")),
        annual_debt_service=_dec(ai_result.get("annual_debt_service")),
        key_metrics=ai_result.get("key_metrics") or {},
        auditor_name=ai_result.get("auditor_name"),
        audit_opinion=ai_result.get("audit_opinion"),
        confidence_scores=confidence,
    )
    record.compute_completeness()
    return record
