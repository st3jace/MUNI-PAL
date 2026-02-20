"""Pydantic schemas for rating action documents."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class RatingActionRecord(BaseModel):
    """Extracted data from a rating action document (Moody's, S&P, Fitch, etc.)."""

    extraction_id: str
    source_file: str
    source_hash: str
    extraction_timestamp: datetime
    doc_type: str = "rating_action"

    # Core identifiers
    cusip_references: list[str] = Field(default_factory=list)
    issuer_name: str | None = None
    obligor_name: str | None = None

    # Rating action details
    agency: str | None = None  # moodys | sp | fitch | kroll | dbrs
    action_type: str | None = None  # upgrade | downgrade | affirm | outlook_change | watch_placed | watch_removed | new_rating | withdrawal
    previous_rating: str | None = None
    new_rating: str | None = None
    previous_outlook: str | None = None
    new_outlook: str | None = None  # stable | positive | negative | developing
    action_date: date | None = None
    effective_date: date | None = None

    # Affected bonds
    bond_series_affected: list[str] = Field(default_factory=list)
    bond_type: str | None = None  # revenue | go | conduit | etc

    # Rationale
    rationale_summary: str | None = None
    key_factors: list[str] = Field(default_factory=list)
    credit_strengths: list[str] = Field(default_factory=list)
    credit_challenges: list[str] = Field(default_factory=list)

    # Classification
    sector: str | None = None  # solid_waste | water_sewer | electric | etc

    # Quality metrics
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    completeness_score: float = 0.0

    def compute_completeness(self) -> float:
        """Calculate completeness score based on key fields populated."""
        key_fields = [
            self.issuer_name,
            self.agency,
            self.action_type,
            self.new_rating,
            self.action_date,
            self.rationale_summary,
            bool(self.key_factors),
        ]
        filled = sum(1 for f in key_fields if f)
        self.completeness_score = round(filled / len(key_fields), 3)
        return self.completeness_score
