"""Bond Readiness Self-Assessment — Phase C of the Sensing Component.

Qualification engine: prospects who engaged with the Phase A sector report
and Phase B benchmarking calculator complete a structured self-assessment
to gauge their bond readiness. The output is a scored readiness packet
with gap analysis and corpus-derived recommendations.

Scoring model:
  5 risk dimensions (20 pts each)          = 100 pts max
  Financial health (DSCR, coverage)        = bonus/penalty overlay
  Evidence completeness                    = transparency multiplier

Each dimension scores 0-20 based on:
  - Risk description provided? (+5)
  - Mitigants documented?      (+5)
  - Evidence items gathered?   (+2 each, up to +10)

The composite Readiness Score (0-100) maps to readiness tiers:
  85-100  Bond Ready        — proceed to market engagement
  65-84   Nearly Ready      — address material gaps first
  40-64   Developing        — significant preparation needed
  0-39    Early Stage       — foundational work required
"""
from __future__ import annotations

import json
import logging
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from sqlalchemy.engine import Engine

from ..config import get_settings
from .risk_benchmark import (
    PLAYBOOK_RISK_GUIDANCE,
    READINESS_PATH_CONFIG,
    ReadinessRiskBenchmark,
    build_risk_benchmarks,
    get_playbook_guidance,
    get_readiness_path_config,
    _metric_to_dict,
)

logger = logging.getLogger("bond_os_extractor.analysis.readiness_assessment")


# ---------------------------------------------------------------------------
# Readiness Tiers
# ---------------------------------------------------------------------------

READINESS_TIERS = [
    (85, "Bond Ready", "Proceed to market engagement with confidence."),
    (65, "Nearly Ready", "Address remaining material gaps before market engagement."),
    (40, "Developing", "Significant preparation needed across multiple dimensions."),
    (0, "Early Stage", "Foundational risk and financial work required."),
]


def _tier_for_score(score: float) -> tuple[str, str]:
    """Return (tier_name, tier_guidance) for a readiness score."""
    for threshold, name, guidance in READINESS_TIERS:
        if score >= threshold:
            return name, guidance
    return "Early Stage", READINESS_TIERS[-1][2]


# ---------------------------------------------------------------------------
# Questionnaire Definition
# ---------------------------------------------------------------------------

@dataclass
class QuestionnaireItem:
    """A single assessment question."""
    item_id: str
    dimension: str           # readiness path (e.g., "risk.technology")
    category: str            # "description" | "mitigants" | "evidence"
    question: str            # user-facing question text
    help_text: str = ""      # guidance / corpus context
    points: float = 0.0      # max points for this item
    evidence_key: str = ""   # maps to evidence item name


def build_questionnaire(
    sector: str | None = None,
) -> list[QuestionnaireItem]:
    """Build the full self-assessment questionnaire from config.

    For each of the 5 risk dimensions, generates:
      - 1 description question (5 pts)
      - 1 mitigants question (5 pts)
      - Up to 5 evidence questions (2 pts each, max 10 pts)
    Total: 20 pts per dimension, 100 pts max.

    Args:
        sector: Sector name (e.g., "waste", "healthcare"). When provided,
            returns sector-specific dimensions and guidance.
    """
    path_config = get_readiness_path_config(sector)
    playbook_guidance = get_playbook_guidance(sector)

    items: list[QuestionnaireItem] = []

    for path, config in path_config.items():
        playbook = playbook_guidance.get(path, {})
        display = config["display_name"]

        # Description question
        items.append(QuestionnaireItem(
            item_id=f"{path}.description",
            dimension=path,
            category="description",
            question=(
                f"Have you prepared a comprehensive {display.lower()} "
                f"assessment for your project?"
            ),
            help_text=playbook.get("guidance", ""),
            points=5.0,
        ))

        # Mitigants question
        items.append(QuestionnaireItem(
            item_id=f"{path}.mitigants",
            dimension=path,
            category="mitigants",
            question=(
                f"Have you documented specific mitigants for "
                f"{display.lower()}?"
            ),
            help_text=(
                f"Example mitigants: {playbook.get('example_mitigants', '')}"
            ),
            points=5.0,
        ))

        # Evidence questions (2 pts each, up to 5 items)
        for i, ev_item in enumerate(
            playbook.get("suggested_evidence", [])[:5]
        ):
            items.append(QuestionnaireItem(
                item_id=f"{path}.evidence.{i}",
                dimension=path,
                category="evidence",
                question=f"Do you have: {ev_item}?",
                help_text="",
                points=2.0,
                evidence_key=ev_item,
            ))

    return items


# ---------------------------------------------------------------------------
# Assessment Input and Scoring
# ---------------------------------------------------------------------------

@dataclass
class AssessmentResponse:
    """A prospect's responses to the self-assessment."""
    project_name: str = "Project"
    # Risk dimension responses: "risk.technology.description" -> True/False
    responses: dict[str, bool] = field(default_factory=dict)
    # Financial inputs (optional)
    dscr: float | None = None
    revenue: float | None = None
    coverage_ratio: float | None = None
    # Deal parameters (optional, from Phase B)
    deal_size: float | None = None
    state: str | None = None
    expected_rating: str | None = None


@dataclass
class DimensionScore:
    """Scored result for one risk dimension."""
    dimension: str = ""
    display_name: str = ""
    score: float = 0.0           # 0-20
    max_score: float = 20.0
    pct: float = 0.0             # 0-100%
    description_answered: bool = False
    mitigants_answered: bool = False
    evidence_count: int = 0
    evidence_total: int = 0
    evidence_items_present: list[str] = field(default_factory=list)
    evidence_items_missing: list[str] = field(default_factory=list)
    # Corpus context
    corpus_mitigation_rate: float = 0.0
    corpus_n_issuances: int = 0
    corpus_n_risk_factors: int = 0
    # Gap assessment
    gap_severity: str = ""       # "critical" | "material" | "acceptable"
    gap_narrative: str = ""
    recommendations: list[str] = field(default_factory=list)


@dataclass
class FinancialAssessment:
    """Financial health assessment against corpus benchmarks."""
    dscr_score: str = ""         # "strong" | "adequate" | "weak" | "not_provided"
    dscr_narrative: str = ""
    coverage_score: str = ""
    coverage_narrative: str = ""
    revenue_score: str = ""
    revenue_narrative: str = ""
    financial_flags: list[str] = field(default_factory=list)
    adjustment_points: float = 0.0  # bonus/penalty (-10 to +10)


@dataclass
class ReadinessResult:
    """Complete readiness assessment result."""
    project_name: str = ""
    generated_at: str = ""
    sector: str = ""

    # Composite score
    raw_score: float = 0.0       # 0-100
    adjusted_score: float = 0.0  # after financial adjustment
    readiness_tier: str = ""
    tier_guidance: str = ""

    # Per-dimension breakdown
    dimension_scores: list[DimensionScore] = field(default_factory=list)
    financial_assessment: FinancialAssessment = field(
        default_factory=FinancialAssessment
    )

    # Summary statistics
    dimensions_addressed: int = 0    # both desc + mitigants
    dimensions_partial: int = 0      # only one of desc/mitigants
    dimensions_missing: int = 0      # neither
    total_evidence_present: int = 0
    total_evidence_possible: int = 0
    evidence_completeness_pct: float = 0.0

    # Priority actions (top gaps to close)
    priority_actions: list[str] = field(default_factory=list)

    # Corpus context
    corpus_summary: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Scoring Engine
# ---------------------------------------------------------------------------

def score_assessment(
    engine: Engine,
    response: AssessmentResponse,
    sector: str | None = None,
) -> ReadinessResult:
    """Score a prospect's self-assessment against corpus benchmarks.

    Loads corpus risk benchmarks, scores each dimension, applies
    financial adjustments, and produces a composite readiness score.

    Args:
        engine: SQLAlchemy engine for the corpus database.
        response: The prospect's self-assessment responses.
        sector: Sector name (e.g., "waste", "healthcare"). Uses
            sector-specific dimensions and benchmarks when provided.
    """
    settings = get_settings()
    if sector is None:
        sector = settings.sector

    path_config = get_readiness_path_config(sector)
    playbook_guidance = get_playbook_guidance(sector)

    report = build_risk_benchmarks(engine, sector=sector)

    questionnaire = build_questionnaire(sector=sector)
    # Group questions by dimension
    dim_items: dict[str, list[QuestionnaireItem]] = {}
    for item in questionnaire:
        dim_items.setdefault(item.dimension, []).append(item)

    result = ReadinessResult(
        project_name=response.project_name,
        generated_at=datetime.now().isoformat(),
        sector=sector,
        corpus_summary=report.corpus_summary,
    )

    total_raw = 0.0
    total_evidence_present = 0
    total_evidence_possible = 0

    for path, config in path_config.items():
        benchmark = report.benchmarks.get(path)
        playbook = playbook_guidance.get(path, {})
        items = dim_items.get(path, [])

        dim = DimensionScore(
            dimension=path,
            display_name=config["display_name"],
        )

        # Score description (5 pts)
        desc_key = f"{path}.description"
        dim.description_answered = response.responses.get(desc_key, False)
        dim_score = 5.0 if dim.description_answered else 0.0

        # Score mitigants (5 pts)
        mit_key = f"{path}.mitigants"
        dim.mitigants_answered = response.responses.get(mit_key, False)
        dim_score += 5.0 if dim.mitigants_answered else 0.0

        # Score evidence items (2 pts each, max 10 pts)
        evidence_items = [i for i in items if i.category == "evidence"]
        dim.evidence_total = len(evidence_items)
        total_evidence_possible += dim.evidence_total

        for ev_item in evidence_items:
            answered = response.responses.get(ev_item.item_id, False)
            if answered:
                dim_score += ev_item.points
                dim.evidence_count += 1
                dim.evidence_items_present.append(ev_item.evidence_key)
                total_evidence_present += 1
            else:
                dim.evidence_items_missing.append(ev_item.evidence_key)

        dim.score = dim_score
        dim.pct = (dim_score / dim.max_score) * 100 if dim.max_score else 0

        # Corpus context
        if benchmark:
            dim.corpus_mitigation_rate = benchmark.mitigation_rate
            dim.corpus_n_issuances = benchmark.n_issuances
            dim.corpus_n_risk_factors = benchmark.n_risk_factors

        # Gap assessment
        if dim.description_answered and dim.mitigants_answered:
            result.dimensions_addressed += 1
            if dim.evidence_count >= dim.evidence_total * 0.6:
                dim.gap_severity = "acceptable"
                dim.gap_narrative = (
                    f"{config['display_name']} is well-addressed with both "
                    f"description and mitigants, plus {dim.evidence_count}/"
                    f"{dim.evidence_total} evidence items."
                )
            else:
                dim.gap_severity = "acceptable"
                dim.gap_narrative = (
                    f"{config['display_name']} description and mitigants "
                    f"provided. Strengthen with additional evidence items "
                    f"({dim.evidence_count}/{dim.evidence_total} gathered)."
                )
        elif dim.description_answered or dim.mitigants_answered:
            result.dimensions_partial += 1
            dim.gap_severity = "material"
            missing = "mitigants" if dim.description_answered else "description"
            dim.gap_narrative = (
                f"{config['display_name']} is partially addressed — "
                f"missing {missing}. Corpus shows "
                f"{benchmark.mitigation_rate * 100:.0f}% of issuers "
                f"provide both."
                if benchmark else
                f"{config['display_name']} is partially addressed — "
                f"missing {missing}."
            )
        else:
            result.dimensions_missing += 1
            if benchmark and benchmark.n_issuances >= 5:
                dim.gap_severity = "critical"
                dim.gap_narrative = (
                    f"{config['display_name']} has not been addressed. "
                    f"This is a significant gap: {benchmark.n_issuances} "
                    f"corpus issuances include explicit disclosures."
                )
            else:
                dim.gap_severity = "material"
                dim.gap_narrative = (
                    f"{config['display_name']} has not been addressed. "
                    f"Evaluate whether this risk is material to your project."
                )

        # Recommendations
        if not dim.description_answered:
            dim.recommendations.append(
                f"Prepare comprehensive {config['display_name'].lower()} "
                f"description."
            )
        if not dim.mitigants_answered:
            mitigants_example = playbook.get("example_mitigants", "")
            dim.recommendations.append(
                f"Document specific mitigants for "
                f"{config['display_name'].lower()}."
                + (f" Example: {mitigants_example[:100]}" if mitigants_example else "")
            )
        for missing_ev in dim.evidence_items_missing[:3]:
            dim.recommendations.append(f"Gather: {missing_ev}")

        total_raw += dim_score
        result.dimension_scores.append(dim)

    result.raw_score = total_raw
    result.total_evidence_present = total_evidence_present
    result.total_evidence_possible = total_evidence_possible
    result.evidence_completeness_pct = (
        (total_evidence_present / total_evidence_possible * 100)
        if total_evidence_possible > 0 else 0
    )

    # Financial assessment
    fin = _assess_financials(response, report)
    result.financial_assessment = fin
    result.adjusted_score = max(0, min(100, total_raw + fin.adjustment_points))

    # Readiness tier
    tier_name, tier_guidance = _tier_for_score(result.adjusted_score)
    result.readiness_tier = tier_name
    result.tier_guidance = tier_guidance

    # Priority actions (sorted by gap severity)
    priority_actions: list[str] = []
    for dim in sorted(
        result.dimension_scores,
        key=lambda d: {"critical": 0, "material": 1, "acceptable": 2}.get(
            d.gap_severity, 3
        ),
    ):
        if dim.gap_severity in ("critical", "material"):
            for rec in dim.recommendations[:2]:
                priority_actions.append(
                    f"[{dim.gap_severity.upper()}] {rec}"
                )
    for flag in fin.financial_flags:
        priority_actions.append(f"[FINANCIAL] {flag}")
    result.priority_actions = priority_actions[:10]

    logger.info(
        "Assessment scored: %s — %.0f/100 (adjusted %.0f), tier=%s, "
        "%d addressed, %d partial, %d missing",
        response.project_name, total_raw, result.adjusted_score,
        tier_name, result.dimensions_addressed,
        result.dimensions_partial, result.dimensions_missing,
    )

    return result


def _assess_financials(
    response: AssessmentResponse,
    report,
) -> FinancialAssessment:
    """Assess financial health against corpus benchmarks."""
    fin = FinancialAssessment()
    fb = report.financial_benchmarks
    adjustment = 0.0

    # DSCR assessment
    if response.dscr is not None and fb.dscr:
        if response.dscr >= fb.dscr.p75:
            fin.dscr_score = "strong"
            fin.dscr_narrative = (
                f"DSCR of {response.dscr:.2f}x is above the corpus 75th "
                f"percentile ({fb.dscr.p75:.2f}x). Strong debt service coverage."
            )
            adjustment += 5.0
        elif response.dscr >= fb.dscr.median:
            fin.dscr_score = "adequate"
            fin.dscr_narrative = (
                f"DSCR of {response.dscr:.2f}x is above the corpus median "
                f"({fb.dscr.median:.2f}x). Adequate coverage."
            )
            adjustment += 2.0
        elif response.dscr >= fb.dscr.p25:
            fin.dscr_score = "weak"
            fin.dscr_narrative = (
                f"DSCR of {response.dscr:.2f}x is below the corpus median "
                f"({fb.dscr.median:.2f}x) but above the 25th percentile "
                f"({fb.dscr.p25:.2f}x). Consider strengthening coverage."
            )
            adjustment -= 3.0
            fin.financial_flags.append(
                f"DSCR ({response.dscr:.2f}x) below corpus median "
                f"({fb.dscr.median:.2f}x) — strengthen debt service coverage."
            )
        else:
            fin.dscr_score = "weak"
            fin.dscr_narrative = (
                f"DSCR of {response.dscr:.2f}x is below the corpus 25th "
                f"percentile ({fb.dscr.p25:.2f}x). Significant improvement needed."
            )
            adjustment -= 7.0
            fin.financial_flags.append(
                f"DSCR ({response.dscr:.2f}x) below corpus 25th percentile "
                f"({fb.dscr.p25:.2f}x) — critical coverage deficiency."
            )
    else:
        fin.dscr_score = "not_provided"
        fin.dscr_narrative = (
            "DSCR not provided. This is a key metric for bond readiness."
        )
        if fb.dscr:
            fin.dscr_narrative += (
                f" Corpus median: {fb.dscr.median:.2f}x "
                f"(p25-p75: {fb.dscr.p25:.2f}x-{fb.dscr.p75:.2f}x)."
            )

    # Coverage ratio assessment
    if response.coverage_ratio is not None and fb.coverage_ratio:
        if response.coverage_ratio >= fb.coverage_ratio.median:
            fin.coverage_score = "adequate"
            fin.coverage_narrative = (
                f"Coverage ratio of {response.coverage_ratio:.2f}x meets "
                f"or exceeds the corpus median ({fb.coverage_ratio.median:.2f}x)."
            )
            adjustment += 2.0
        else:
            fin.coverage_score = "weak"
            fin.coverage_narrative = (
                f"Coverage ratio of {response.coverage_ratio:.2f}x is below "
                f"the corpus median ({fb.coverage_ratio.median:.2f}x)."
            )
            adjustment -= 3.0
            fin.financial_flags.append(
                f"Coverage ratio ({response.coverage_ratio:.2f}x) below "
                f"corpus median ({fb.coverage_ratio.median:.2f}x)."
            )
    else:
        fin.coverage_score = "not_provided"
        fin.coverage_narrative = "Coverage ratio not provided."

    # Revenue assessment
    if response.revenue is not None and fb.revenue:
        if response.revenue >= fb.revenue.median:
            fin.revenue_score = "strong"
            fin.revenue_narrative = (
                f"Revenue of ${response.revenue:,.0f} is at or above "
                f"the corpus median (${fb.revenue.median:,.0f})."
            )
        elif response.revenue >= fb.revenue.p25:
            fin.revenue_score = "adequate"
            fin.revenue_narrative = (
                f"Revenue of ${response.revenue:,.0f} is between the "
                f"25th percentile (${fb.revenue.p25:,.0f}) and median "
                f"(${fb.revenue.median:,.0f})."
            )
        else:
            fin.revenue_score = "weak"
            fin.revenue_narrative = (
                f"Revenue of ${response.revenue:,.0f} is below the corpus "
                f"25th percentile (${fb.revenue.p25:,.0f})."
            )
    else:
        fin.revenue_score = "not_provided"
        fin.revenue_narrative = "Revenue not provided."

    # Clamp adjustment
    fin.adjustment_points = max(-10.0, min(10.0, adjustment))

    return fin


# ---------------------------------------------------------------------------
# Export — JSON
# ---------------------------------------------------------------------------

def export_json(
    result: ReadinessResult,
    output_path: Path | None = None,
) -> Path:
    """Export readiness assessment to JSON."""
    if output_path is None:
        output_path = (
            get_settings().data_dir / "analysis" / "readiness_assessment.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "analysis": "Bond Readiness Self-Assessment",
        "project_name": result.project_name,
        "generated_at": result.generated_at,
        "sector": result.sector,
        "readiness_score": {
            "raw": round(result.raw_score, 1),
            "adjusted": round(result.adjusted_score, 1),
            "max": 100,
            "tier": result.readiness_tier,
            "tier_guidance": result.tier_guidance,
        },
        "summary": {
            "dimensions_addressed": result.dimensions_addressed,
            "dimensions_partial": result.dimensions_partial,
            "dimensions_missing": result.dimensions_missing,
            "evidence_present": result.total_evidence_present,
            "evidence_possible": result.total_evidence_possible,
            "evidence_completeness_pct": round(
                result.evidence_completeness_pct, 1
            ),
        },
        "dimension_scores": [],
        "financial_assessment": {
            "dscr": {
                "score": result.financial_assessment.dscr_score,
                "narrative": result.financial_assessment.dscr_narrative,
            },
            "coverage_ratio": {
                "score": result.financial_assessment.coverage_score,
                "narrative": result.financial_assessment.coverage_narrative,
            },
            "revenue": {
                "score": result.financial_assessment.revenue_score,
                "narrative": result.financial_assessment.revenue_narrative,
            },
            "adjustment_points": result.financial_assessment.adjustment_points,
            "flags": result.financial_assessment.financial_flags,
        },
        "priority_actions": result.priority_actions,
        "corpus_summary": result.corpus_summary,
    }

    for dim in result.dimension_scores:
        data["dimension_scores"].append({
            "dimension": dim.dimension,
            "display_name": dim.display_name,
            "score": round(dim.score, 1),
            "max_score": dim.max_score,
            "pct": round(dim.pct, 1),
            "description_provided": dim.description_answered,
            "mitigants_provided": dim.mitigants_answered,
            "evidence_count": dim.evidence_count,
            "evidence_total": dim.evidence_total,
            "evidence_present": dim.evidence_items_present,
            "evidence_missing": dim.evidence_items_missing,
            "corpus_context": {
                "mitigation_rate": dim.corpus_mitigation_rate,
                "n_issuances": dim.corpus_n_issuances,
                "n_risk_factors": dim.corpus_n_risk_factors,
            },
            "gap_severity": dim.gap_severity,
            "gap_narrative": dim.gap_narrative,
            "recommendations": dim.recommendations,
        })

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported readiness assessment to %s", output_path)
    return output_path


# ---------------------------------------------------------------------------
# Export — Markdown
# ---------------------------------------------------------------------------

def export_markdown(
    result: ReadinessResult,
    output_path: Path | None = None,
) -> Path:
    """Export readiness assessment as Markdown report."""
    if output_path is None:
        output_path = (
            get_settings().data_dir / "analysis" / "readiness_assessment.md"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    _a = lines.append

    _a(f"# Bond Readiness Self-Assessment: {result.project_name}")
    _a("")
    _a(f"**Generated:** {result.generated_at[:10]}")
    _a(f"**Sector:** {result.sector}")
    _a("")

    # Score banner
    _a("---")
    _a("")
    _a("## Readiness Score")
    _a("")
    _a(f"| Metric | Value |")
    _a(f"|--------|------:|")
    _a(f"| **Readiness Score** | **{result.adjusted_score:.0f} / 100** |")
    _a(f"| Readiness Tier | {result.readiness_tier} |")
    _a(f"| Raw Score (risk dimensions) | {result.raw_score:.0f} / 100 |")
    adj = result.financial_assessment.adjustment_points
    adj_str = f"+{adj:.0f}" if adj >= 0 else f"{adj:.0f}"
    _a(f"| Financial Adjustment | {adj_str} |")
    _a("")
    _a(f"> **{result.readiness_tier}**: {result.tier_guidance}")
    _a("")

    # Summary
    _a("## Assessment Summary")
    _a("")
    _a(f"| Status | Dimensions |")
    _a(f"|--------|----------:|")
    _a(f"| Fully Addressed | {result.dimensions_addressed} |")
    _a(f"| Partially Addressed | {result.dimensions_partial} |")
    _a(f"| Not Addressed | {result.dimensions_missing} |")
    _a(f"| Evidence Completeness | "
       f"{result.total_evidence_present}/{result.total_evidence_possible} "
       f"({result.evidence_completeness_pct:.0f}%) |")
    _a("")

    # Score breakdown chart (text-based)
    _a("## Dimension Scores")
    _a("")
    _a(f"| Dimension | Score | % | Status | Gap |")
    _a(f"|-----------|------:|----:|--------|-----|")
    for dim in result.dimension_scores:
        status = "Addressed" if dim.description_answered and dim.mitigants_answered \
            else "Partial" if dim.description_answered or dim.mitigants_answered \
            else "Missing"
        _a(f"| {dim.display_name} | {dim.score:.0f}/{dim.max_score:.0f} | "
           f"{dim.pct:.0f}% | {status} | {dim.gap_severity} |")
    _a("")

    # Detailed dimension breakdown
    _a("---")
    _a("")
    for i, dim in enumerate(result.dimension_scores, 1):
        _a(f"### {i}. {dim.display_name}")
        _a("")
        _a(f"**Score: {dim.score:.0f} / {dim.max_score:.0f} ({dim.pct:.0f}%)**")
        _a("")

        # Checklist
        desc_mark = "x" if dim.description_answered else " "
        mit_mark = "x" if dim.mitigants_answered else " "
        _a(f"- [{desc_mark}] Risk description provided (+5 pts)")
        _a(f"- [{mit_mark}] Mitigants documented (+5 pts)")
        _a(f"- Evidence items: {dim.evidence_count}/{dim.evidence_total} "
           f"(+{dim.evidence_count * 2} pts)")
        if dim.evidence_items_present:
            for ev in dim.evidence_items_present:
                _a(f"  - [x] {ev}")
        if dim.evidence_items_missing:
            for ev in dim.evidence_items_missing:
                _a(f"  - [ ] {ev}")
        _a("")

        # Corpus context
        _a(f"**Corpus Context:** {dim.corpus_n_risk_factors} risk factors "
           f"across {dim.corpus_n_issuances} issuances | "
           f"Mitigation rate: {dim.corpus_mitigation_rate * 100:.0f}%")
        _a("")

        # Gap assessment
        sev_label = dim.gap_severity.upper() if dim.gap_severity != "acceptable" else "OK"
        _a(f"**Gap Assessment [{sev_label}]:** {dim.gap_narrative}")
        _a("")

        if dim.recommendations:
            _a("**Recommendations:**")
            for rec in dim.recommendations:
                _a(f"1. {rec}")
            _a("")
        _a("")

    # Financial assessment
    _a("---")
    _a("")
    _a("## Financial Assessment")
    _a("")
    fin = result.financial_assessment
    _a(f"| Metric | Rating | Detail |")
    _a(f"|--------|--------|--------|")
    _a(f"| DSCR | {fin.dscr_score} | {fin.dscr_narrative} |")
    _a(f"| Coverage Ratio | {fin.coverage_score} | {fin.coverage_narrative} |")
    _a(f"| Revenue | {fin.revenue_score} | {fin.revenue_narrative} |")
    _a("")
    if fin.financial_flags:
        _a("**Financial Flags:**")
        for flag in fin.financial_flags:
            _a(f"- {flag}")
        _a("")

    # Priority actions
    if result.priority_actions:
        _a("---")
        _a("")
        _a("## Priority Actions")
        _a("")
        for i, action in enumerate(result.priority_actions, 1):
            _a(f"{i}. {action}")
        _a("")

    # Footer
    _a("---")
    _a("")
    _a("*Report generated by Muni-Pal Bond Readiness Assessment*")
    _a(f"*Benchmarked against EMMA municipal bond corpus "
       f"({result.sector} sector)*")
    _a("")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Exported readiness assessment markdown to %s", output_path)
    return output_path
