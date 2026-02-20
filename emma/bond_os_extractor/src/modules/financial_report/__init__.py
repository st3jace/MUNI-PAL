"""Financial Report document module (annual reports, 10-K, 10-Q, disclosures)."""
from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel
from sqlalchemy import Table
from sqlalchemy.engine import Engine

from ..base import DocumentModule
from ...ingestion.pdf_reader import IngestionResult
from .schema import FinancialReportRecord
from .extractor import extract_financial_report
from .storage import get_tables, init_tables, save_financial_report, get_financial_report_stats


class FinancialReportModule(DocumentModule):
    """Module for financial reports: annual/quarterly disclosures, 10-K, 10-Q."""

    name = "financial_report"
    display_name = "Financial Report"
    file_patterns = [
        "*Financial_Disclosure*",
        "*Financial_Report*",
        "*Financial_Operating*",
        "*Financial_Statement*",
        "*Annual_Report*",
        "*Quarterly_Report*",
        "*Monthly_Report*",
        "*Monthly_*_Report*",
        "*MONTHLY_*_REPORT*",
        "*10-K*",
        "*10_K*",
        "*10K_*",
        "*10-Q*",
        "*10_Q*",
        "*10Q_*",
        "*Audited_Financial*",
        "*ACFR*",
        "*Annual_Comprehensive*",
        "*Compliance_Report*",
        "*Compliance_Certificates*",
        "*Compliance_Cert*",
    ]

    _CONTENT_PATTERNS = [
        re.compile(r"financial\s+statement", re.IGNORECASE),
        re.compile(r"(annual|quarterly|monthly)\s+report", re.IGNORECASE),
        re.compile(r"form\s+10-?[KQ]", re.IGNORECASE),
        re.compile(r"(independent\s+)?auditor", re.IGNORECASE),
        re.compile(r"(balance\s+sheet|income\s+statement|cash\s+flow)", re.IGNORECASE),
        re.compile(r"(total\s+revenue|total\s+assets|net\s+income)", re.IGNORECASE),
    ]

    def matches(self, filename: str, first_page_text: str) -> float:
        score = 0.0
        fn_lower = filename.lower()

        if any(kw in fn_lower for kw in ["financial_disclosure", "financial_report", "financial_operating",
                                          "audited_financial", "financial_statement", "annual_report"]):
            score = max(score, 0.9)
        elif any(kw in fn_lower for kw in ["10-k", "10_k", "10k_", "10-q", "10_q", "10q_",
                                            "quarterly_report", "monthly_report", "acfr",
                                            "annual_comprehensive", "compliance_report",
                                            "compliance_certificates", "compliance_cert"]):
            score = max(score, 0.85)
        elif "monthly" in fn_lower and "report" in fn_lower:
            score = max(score, 0.8)

        if first_page_text:
            matches_count = sum(1 for p in self._CONTENT_PATTERNS if p.search(first_page_text))
            if matches_count >= 3:
                score = max(score, 0.9)
            elif matches_count >= 2:
                score = max(score, 0.7)
            elif matches_count >= 1:
                score = max(score, 0.4)

        return score

    def extract(self, ingestion: IngestionResult) -> FinancialReportRecord:
        return extract_financial_report(ingestion)

    def db_tables(self) -> list[Table]:
        return get_tables()

    def save(self, engine: Engine, record: BaseModel) -> str:
        assert isinstance(record, FinancialReportRecord)
        init_tables(engine)
        return save_financial_report(engine, record)

    def get_stats(self, engine: Engine) -> dict[str, Any]:
        return get_financial_report_stats(engine)


module = FinancialReportModule()
