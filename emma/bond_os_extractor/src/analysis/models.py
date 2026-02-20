"""Pydantic models for the Fundamental Scoring Engine.

Follows Summers' Standard Model (Section 4.2) — five screening dimensions
adapted for the municipal bond + equity dual-data context.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field


class DimensionScore(BaseModel):
    """Score for a single screening dimension."""
    name: str
    weight: float
    raw_score: float = 0.0          # 0-100 scale
    weighted_score: float = 0.0     # raw * weight
    components: dict[str, float | None] = Field(default_factory=dict)
    data_source: str = ""           # "bond" | "equity" | "blended"
    defaulted: bool = False         # True if score is a default (no real data)


class FundamentalScore(BaseModel):
    """Complete fundamental score for one obligor/issuer."""
    obligor_id: str                 # Canonical key (ticker or issuer slug)
    obligor_name: str
    ticker: str | None = None
    cusips: list[str] = Field(default_factory=list)

    # Aggregate
    f_score: float = 0.0            # Composite 0-100
    investable: bool = False        # F_i >= threshold
    threshold: float = 50.0

    # Dimension breakdown (Summers Section 4.2)
    financial_stability: DimensionScore | None = None
    profitability: DimensionScore | None = None
    credit_quality: DimensionScore | None = None
    structural_quality: DimensionScore | None = None
    growth_momentum: DimensionScore | None = None

    # Data provenance
    data_sources: dict[str, int] = Field(default_factory=dict)
    data_quality: str = ""          # "full" | "partial" | "thin"
    defaulted_dimensions: int = 0   # Count of dimensions using default scores
    scored_at: datetime = Field(default_factory=datetime.now)

    def compute_composite(self) -> float:
        """Sum weighted dimension scores into F_i.

        Investability requires:
          1. F_i >= threshold
          2. At least 2 distinct data source types (e.g., OS + financial reports,
             or OS + equity data). Pure-equity or single-OS obligors are excluded.
          3. Fewer than 3 defaulted dimensions.
        """
        total = 0.0
        n_defaulted = 0
        for dim in [
            self.financial_stability,
            self.profitability,
            self.credit_quality,
            self.structural_quality,
            self.growth_momentum,
        ]:
            if dim is not None:
                dim.weighted_score = round(dim.raw_score * dim.weight, 4)
                total += dim.weighted_score
                if dim.defaulted:
                    n_defaulted += 1
        self.f_score = round(total, 2)
        self.defaulted_dimensions = n_defaulted

        # Count distinct data source types with actual data
        source_types = 0
        if self.data_sources.get("os_records", 0) > 0:
            source_types += 1
        if self.data_sources.get("financial_reports", 0) > 0:
            source_types += 1
        if self.data_sources.get("rating_actions", 0) > 0:
            source_types += 1
        if self.data_sources.get("os_ratings", 0) > 0:
            source_types += 1
        if self.data_sources.get("has_equity_data"):
            source_types += 1

        # Classify data quality
        if source_types >= 3:
            self.data_quality = "full"
        elif source_types >= 2:
            self.data_quality = "partial"
        else:
            self.data_quality = "thin"

        # Investable requires score + data quality
        self.investable = (
            self.f_score >= self.threshold
            and source_types >= 2
            and n_defaulted < 3
        )
        return self.f_score


class ScoredUniverse(BaseModel):
    """The full scored universe — input to Phase 2 (S_Omega)."""
    scores: list[FundamentalScore] = Field(default_factory=list)
    threshold: float = 50.0
    scored_at: datetime = Field(default_factory=datetime.now)

    @property
    def investable(self) -> list[FundamentalScore]:
        return [s for s in self.scores if s.investable]

    @property
    def avg_score(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.f_score for s in self.scores) / len(self.scores), 2)

    def summary(self) -> dict[str, Any]:
        return {
            "total_obligors": len(self.scores),
            "investable_count": len(self.investable),
            "avg_f_score": self.avg_score,
            "threshold": self.threshold,
            "top_5": [
                {"obligor": s.obligor_name, "ticker": s.ticker, "f_score": s.f_score}
                for s in sorted(self.scores, key=lambda x: x.f_score, reverse=True)[:5]
            ],
        }
