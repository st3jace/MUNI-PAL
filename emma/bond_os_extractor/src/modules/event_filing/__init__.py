"""Event Filing document module (8-K, material events, notices)."""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Table
from sqlalchemy.engine import Engine

from ..base import DocumentModule
from ...ingestion.pdf_reader import IngestionResult
from .schema import EventFilingRecord
from .extractor import extract_event_filing
from .storage import get_tables, init_tables, save_event_filing, get_event_filing_stats


class EventFilingModule(DocumentModule):
    """Module for event filings: 8-K, material event notices, tender offers, etc."""

    name = "event_filing"
    display_name = "Event Filing"
    file_patterns = [
        "*8-K*",
        "*8_K*",
        "*8K_*",
        "*Material_Event*",
        "*Event_Disclosure*",
        "*Event_Filing*",
        "*Notice_of_*",
        "*Tender_Offer*",
        "*Defeasance*",
        "*Redemption_Notice*",
        "*Bond_Call*",
        "*Senior_Note*",
        "*Term_Loan*",
        "*Revolving_Credit*",
        "*Liquidity_Facility*",
        "*Material_Acquisition*",
        "*Acquisition_*",
    ]

    _CONTENT_PATTERNS = [
        re.compile(r"material\s+event\s+notice", re.IGNORECASE),
        re.compile(r"form\s+8-?K", re.IGNORECASE),
        re.compile(r"current\s+report", re.IGNORECASE),
        re.compile(r"event\s+(disclosure|filing|notice)", re.IGNORECASE),
        re.compile(r"(tender\s+offer|defeasance|redemption\s+notice|bond\s+call)", re.IGNORECASE),
        re.compile(r"securities\s+and\s+exchange\s+commission", re.IGNORECASE),
    ]

    def matches(self, filename: str, first_page_text: str) -> float:
        score = 0.0
        fn_lower = filename.lower()

        if any(kw in fn_lower for kw in ["8-k", "8_k", "8k_", "material_event", "event_disclosure", "event_filing"]):
            score = max(score, 0.9)
        elif any(kw in fn_lower for kw in ["notice_of", "tender_offer", "defeasance", "redemption_notice", "bond_call"]):
            score = max(score, 0.85)
        elif any(kw in fn_lower for kw in ["senior_note", "term_loan", "revolving_credit",
                                            "liquidity_facility", "material_acquisition"]):
            score = max(score, 0.8)
        # Compliance certs that disclose events (defaults, liquidity issues) are event filings
        elif ("compliance_cert" in fn_lower or "compliance_report" in fn_lower) and \
             any(kw in fn_lower for kw in ["disclosing", "default", "liquidity", "violation", "failure"]):
            score = max(score, 0.9)

        if first_page_text:
            matches_count = sum(1 for p in self._CONTENT_PATTERNS if p.search(first_page_text))
            if matches_count >= 3:
                score = max(score, 0.95)
            elif matches_count >= 2:
                score = max(score, 0.8)
            elif matches_count >= 1:
                score = max(score, 0.5)

        return score

    def extract(self, ingestion: IngestionResult) -> EventFilingRecord:
        return extract_event_filing(ingestion)

    def db_tables(self) -> list[Table]:
        return get_tables()

    def save(self, engine: Engine, record: BaseModel) -> str:
        assert isinstance(record, EventFilingRecord)
        init_tables(engine)
        return save_event_filing(engine, record)

    def get_stats(self, engine: Engine) -> dict[str, Any]:
        return get_event_filing_stats(engine)


module = EventFilingModule()
