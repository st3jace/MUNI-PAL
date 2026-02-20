"""Pydantic schemas for financial report documents (annual/quarterly reports, 10-K/10-Q)."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class FinancialReportRecord(BaseModel):
    """Extracted data from a financial report / annual disclosure / 10-K/10-Q."""

    extraction_id: str
    source_file: str
    source_hash: str
    extraction_timestamp: datetime
    doc_type: str = "financial_report"

    # Core identifiers
    cusip_references: list[str] = Field(default_factory=list)
    issuer_name: str | None = None
    obligor_name: str | None = None

    # Report metadata
    report_type: str | None = None  # annual | quarterly | monthly | 10k | 10q
    fiscal_period_end: date | None = None
    fiscal_year: int | None = None

    # Key financial data
    total_revenue: Decimal | None = None
    total_expenses: Decimal | None = None
    operating_income: Decimal | None = None
    net_income: Decimal | None = None
    total_assets: Decimal | None = None
    total_liabilities: Decimal | None = None
    total_equity: Decimal | None = None
    cash_and_equivalents: Decimal | None = None

    # Bond-relevant metrics
    debt_service_coverage_ratio: Decimal | None = None
    days_cash_on_hand: int | None = None
    total_debt_outstanding: Decimal | None = None
    annual_debt_service: Decimal | None = None

    # Additional metrics (flexible key-value for sector-specific data)
    key_metrics: dict[str, Any] = Field(default_factory=dict)

    # Audit info
    auditor_name: str | None = None
    audit_opinion: str | None = None  # unmodified | qualified | adverse | disclaimer

    # Quality metrics
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    completeness_score: float = 0.0

    def compute_completeness(self) -> float:
        """Calculate completeness score based on report type.

        Full financial statements (annual, 10k, 10q) are measured against
        balance-sheet fields. Monthly/quarterly project reports and compliance
        certs are measured against a lighter set of fields since they rarely
        contain full income statements.
        """
        rt = (self.report_type or "").lower()

        if rt in ("monthly", "compliance"):
            # Project status reports / compliance certs — lighter bar
            key_fields = [
                self.issuer_name,
                self.report_type,
                self.fiscal_period_end or self.fiscal_year,
                bool(self.key_metrics),  # sector-specific data present
            ]
        else:
            # Annual / 10-K / 10-Q / quarterly — full financial bar
            key_fields = [
                self.issuer_name,
                self.report_type,
                self.fiscal_period_end or self.fiscal_year,
                self.total_revenue,
                self.net_income,
                self.total_assets,
                self.total_liabilities,
                self.debt_service_coverage_ratio,
            ]

        filled = sum(1 for f in key_fields if f is not None)
        self.completeness_score = round(filled / len(key_fields), 3)
        return self.completeness_score
