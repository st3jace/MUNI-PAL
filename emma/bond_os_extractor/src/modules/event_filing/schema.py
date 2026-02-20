"""Pydantic schemas for event filing documents (8-K, material events, notices)."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class EventFilingRecord(BaseModel):
    """Extracted data from an event filing / material event notice / 8-K."""

    extraction_id: str
    source_file: str
    source_hash: str
    extraction_timestamp: datetime
    doc_type: str = "event_filing"

    # Core identifiers
    cusip_references: list[str] = Field(default_factory=list)
    issuer_name: str | None = None

    # Event details
    event_type: str | None = None  # material_event | 8k | notice | supplement | tender | defeasance | redemption
    filing_date: date | None = None
    event_date: date | None = None
    event_category: str | None = None  # payment_default | rating_change | defeasance | redemption | tender | bankruptcy | merger | disclosure_failure | tax_status_change | bond_call | other
    event_summary: str | None = None
    financial_impact: str | None = None
    action_required: bool = False

    # Affected bonds
    affected_series: list[str] = Field(default_factory=list)
    affected_par_amount: str | None = None

    # Additional context
    related_parties: list[str] = Field(default_factory=list)
    next_steps: str | None = None

    # Quality metrics
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    completeness_score: float = 0.0

    def compute_completeness(self) -> float:
        """Calculate completeness score based on key fields populated."""
        key_fields = [
            self.issuer_name,
            self.event_type,
            self.event_category,
            self.event_summary,
            self.filing_date or self.event_date,
            bool(self.cusip_references) or bool(self.affected_series),
        ]
        filled = sum(1 for f in key_fields if f)
        self.completeness_score = round(filled / len(key_fields), 3)
        return self.completeness_score
