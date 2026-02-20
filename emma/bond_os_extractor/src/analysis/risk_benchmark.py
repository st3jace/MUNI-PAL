"""EMMA Corpus Risk Benchmarking for Readiness Assessment.

Bridges the gap between EMMA-extracted bond corpus data and the Muni-Pal
readiness assessment framework. Aggregates risk factors, rating agency
perspectives, and financial metrics from actual municipal bond issuances
into benchmarks that contextualize a project's risk profile.

The EMMA corpus contains risk intelligence from real issuances:
  - Risk factor disclosures from Official Statements (severity + mitigation)
  - Rating agency factors (strengths, challenges, key factors)
  - Security package structures (pledge types, coverage ratios)
  - Financial reports (DSCR, revenue, debt service)

This module maps EMMA's 21 granular risk categories into the 5 readiness
risk paths used by the Muni-Pal scoring system:
  risk.technology, risk.construction, risk.market,
  risk.regulatory, risk.feedstock

Each benchmark includes contextual narratives explaining how it was derived
from the corpus, what the typical issuance looks like, and where rating
agencies focus their attention.
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
from .data_loader import (
    load_credit_enhancements,
    load_financial_reports,
    load_rationale_summaries,
    load_rating_action_factors,
    load_risk_factors,
    load_security_packages,
)

logger = logging.getLogger("bond_os_extractor.analysis.risk_benchmark")


# ---------------------------------------------------------------------------
# Category Mapping: EMMA 21 categories -> 5 readiness risk paths
# ---------------------------------------------------------------------------

CATEGORY_TO_READINESS: dict[str, str] = {
    # risk.technology — core technology and systems risk
    "technology": "risk.technology",
    "cybersecurity": "risk.technology",

    # risk.construction — physical build-out and execution risk
    "construction": "risk.construction",
    "labor": "risk.construction",
    "force_majeure": "risk.construction",
    "insurance": "risk.construction",

    # risk.market — demand, pricing, counterparty, and financial risk
    "market_demand": "risk.market",
    "offtake_counterparty": "risk.market",
    "competition": "risk.market",
    "financial": "risk.market",
    "interest_rate": "risk.market",
    "litigation": "risk.market",

    # risk.regulatory — government, environmental, and compliance risk
    "regulatory": "risk.regulatory",
    "environmental": "risk.regulatory",
    "tax_law": "risk.regulatory",
    "political": "risk.regulatory",
    "permitting": "risk.regulatory",
    "climate": "risk.regulatory",
    "pandemic": "risk.regulatory",

    # risk.feedstock — supply chain and operational management risk
    "feedstock_supply": "risk.feedstock",
    "management": "risk.feedstock",
}

# Rating action factor keywords that signal relevance to each readiness path.
# Used to classify rating_action_factors (which have free-text, not categories)
# into readiness paths.
_RATING_FACTOR_KEYWORDS: dict[str, list[str]] = {
    "risk.technology": [
        "technology", "system", "equipment", "process", "innovation",
        "operational efficiency", "automation", "cyber", "digital",
    ],
    "risk.construction": [
        "construction", "capital project", "build", "expansion",
        "labor", "workforce", "force majeure", "weather", "insurance",
        "capex", "capital expenditure",
    ],
    "risk.market": [
        "market", "demand", "competition", "competitive", "pricing",
        "revenue", "volume", "customer", "contract", "offtake",
        "interest rate", "financial", "debt", "leverage", "litigation",
        "counterparty",
    ],
    "risk.regulatory": [
        "regulat", "environmental", "compliance", "permit", "epa",
        "legislation", "tax", "political", "government", "climate",
        "emission", "zoning", "pandemic",
    ],
    "risk.feedstock": [
        "feedstock", "supply", "fuel", "waste", "collection",
        "landfill", "transfer station", "management", "operational",
        "route", "logistics",
    ],
}


# ---------------------------------------------------------------------------
# Readiness Path Benchmark Configuration — narrative templates
# ---------------------------------------------------------------------------

READINESS_PATH_CONFIG: dict[str, dict[str, Any]] = {
    "risk.technology": {
        "display_name": "Technology Risk",
        "methodology": (
            "Technology risk benchmarks are derived from {n_factors} risk factor "
            "disclosures across {n_issuances} municipal bond issuances in the EMMA "
            "corpus. The severity distribution ({pct_material:.0f}% material, "
            "{pct_significant:.0f}% significant, {pct_boilerplate:.0f}% boilerplate) "
            "reflects how issuers characterize technology risks in official statements. "
            "Rating agency perspectives are drawn from {n_rating_factors} rating "
            "action factors where agencies cited technology-related considerations."
        ),
        "benchmark_standard": (
            "Well-positioned issuers in the waste/environmental sector typically "
            "demonstrate: (1) proven technology at commercial scale with 2+ years "
            "of operating history, (2) explicit risk mitigation in {pct_mitigated:.0f}% "
            "of disclosures, and (3) OEM warranties and performance insurance. "
            "Rating agencies cite technology as a credit strength when backed by "
            "established operations ({n_strengths} instances in corpus) but flag it "
            "as a challenge for first-of-kind or unproven processes ({n_challenges} "
            "instances)."
        ),
        "emma_categories": ["technology", "cybersecurity"],
    },
    "risk.construction": {
        "display_name": "Construction Risk",
        "methodology": (
            "Construction risk benchmarks are derived from {n_factors} risk factor "
            "disclosures across {n_issuances} issuances. These cover physical "
            "build-out risks including schedule, budget, labor, force majeure, and "
            "insurance. The severity profile ({pct_material:.0f}% material, "
            "{pct_significant:.0f}% significant) reflects the capital-intensive "
            "nature of waste management infrastructure. Rating agencies assessed "
            "construction-related factors {n_rating_factors} times across the corpus."
        ),
        "benchmark_standard": (
            "The corpus benchmark for construction risk reflects issuers with: "
            "(1) experienced EPC contractors with fixed-price contracts, "
            "(2) mitigation described in {pct_mitigated:.0f}% of disclosures "
            "(performance bonds, liquidated damages, contingency reserves), "
            "(3) construction timelines of 18-36 months typical for sector. "
            "Rating agencies treat construction risk as a credit challenge "
            "{n_challenges} times, typically citing cost overruns and schedule delays. "
            "Strengths cited {n_strengths} times include established contractor "
            "relationships and track records."
        ),
        "emma_categories": ["construction", "labor", "force_majeure", "insurance"],
    },
    "risk.market": {
        "display_name": "Market & Revenue Risk",
        "methodology": (
            "Market risk benchmarks aggregate {n_factors} risk factor disclosures "
            "across {n_issuances} issuances, spanning demand uncertainty, pricing "
            "volatility, counterparty credit, competition, and interest rate "
            "exposure. This is typically the most frequently disclosed risk "
            "category in municipal waste/environmental bonds. {n_rating_factors} "
            "rating action factors addressed market-related considerations, making "
            "it the category with the most rating agency attention."
        ),
        "benchmark_standard": (
            "Well-positioned issuers demonstrate: (1) long-term contracted revenue "
            "streams (5-20 year municipal service agreements), (2) diversified "
            "customer bases reducing single-counterparty exposure, (3) mitigation "
            "described in {pct_mitigated:.0f}% of market risk disclosures. "
            "Rating agencies cite market position as a strength {n_strengths} times "
            "(typically referencing established franchise territories and contract "
            "renewals) but flag revenue concentration and commodity price exposure "
            "as challenges {n_challenges} times."
        ),
        "emma_categories": [
            "market_demand", "offtake_counterparty", "competition",
            "financial", "interest_rate", "litigation",
        ],
    },
    "risk.regulatory": {
        "display_name": "Regulatory & Environmental Risk",
        "methodology": (
            "Regulatory risk benchmarks draw from {n_factors} disclosures across "
            "{n_issuances} issuances, the broadest category in the EMMA corpus. "
            "This reflects the heavily regulated nature of waste management, "
            "encompassing environmental compliance, permitting, tax law, political "
            "risk, and climate policy. The severity distribution ({pct_material:.0f}% "
            "material, {pct_significant:.0f}% significant) indicates that regulatory "
            "risks are taken seriously by issuers. {n_rating_factors} rating agency "
            "factors referenced regulatory considerations."
        ),
        "benchmark_standard": (
            "The corpus standard shows: (1) regulatory risk is nearly universal "
            "in waste sector issuances with {pct_mitigated:.0f}% describing specific "
            "mitigants (compliance monitoring, legal opinions, regulatory relationships), "
            "(2) permitting is typically the longest-lead risk factor addressed early "
            "in the issuance timeline, (3) rating agencies cite regulatory environment "
            "as a strength {n_strengths} times (favorable franchise agreements, "
            "essential service designation) and a challenge {n_challenges} times "
            "(changing environmental regulations, litigation exposure)."
        ),
        "emma_categories": [
            "regulatory", "environmental", "tax_law",
            "political", "permitting", "climate", "pandemic",
        ],
    },
    "risk.feedstock": {
        "display_name": "Feedstock & Supply Risk",
        "methodology": (
            "Feedstock risk benchmarks are derived from {n_factors} disclosures "
            "across {n_issuances} issuances. In the waste management sector, "
            "feedstock risk primarily concerns waste volume availability, collection "
            "route economics, and the operational management of supply logistics. "
            "{n_rating_factors} rating agency factors addressed supply chain and "
            "operational management considerations."
        ),
        "benchmark_standard": (
            "Corpus issuers typically secure feedstock through: (1) long-term "
            "municipal waste collection contracts (franchise agreements), "
            "(2) diversified waste streams from multiple jurisdictions, "
            "(3) explicit mitigation in {pct_mitigated:.0f}% of disclosures. "
            "Rating agencies cite operational scale and diversified waste streams "
            "as strengths {n_strengths} times. Feedstock availability is flagged "
            "as a challenge {n_challenges} times, particularly for facilities "
            "dependent on a single waste source or with limited geographic reach."
        ),
        "emma_categories": ["feedstock_supply", "management"],
    },
}


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class RiskCategoryStats:
    """Statistics for one EMMA risk category within a readiness path."""
    category: str
    count: int = 0
    severity_distribution: dict[str, int] = field(default_factory=dict)
    mitigation_rate: float = 0.0
    sample_titles: list[str] = field(default_factory=list)


@dataclass
class MetricDistribution:
    """Statistical distribution of a numeric metric across the corpus."""
    metric_name: str
    n_observations: int = 0
    mean: float = 0.0
    median: float = 0.0
    p25: float = 0.0
    p75: float = 0.0
    min_val: float = 0.0
    max_val: float = 0.0


@dataclass
class ReadinessRiskBenchmark:
    """Benchmark for one readiness risk path (e.g., risk.technology)."""
    readiness_path: str
    display_name: str

    # EMMA corpus statistics
    n_risk_factors: int = 0
    n_issuances: int = 0
    severity_distribution: dict[str, int] = field(default_factory=dict)
    mitigation_rate: float = 0.0
    sample_titles: list[str] = field(default_factory=list)

    # Rating agency perspective
    n_rating_factors: int = 0
    strength_count: int = 0
    challenge_count: int = 0
    key_factor_count: int = 0
    sample_strengths: list[str] = field(default_factory=list)
    sample_challenges: list[str] = field(default_factory=list)

    # Contextual narratives (filled from templates)
    methodology_narrative: str = ""
    benchmark_standard: str = ""

    # Category breakdown
    category_stats: list[RiskCategoryStats] = field(default_factory=list)


@dataclass
class FinancialBenchmarks:
    """Corpus-wide financial metric benchmarks."""
    dscr: MetricDistribution | None = None
    coverage_ratio: MetricDistribution | None = None
    revenue: MetricDistribution | None = None
    pledge_type_distribution: dict[str, int] = field(default_factory=dict)
    lien_position_distribution: dict[str, int] = field(default_factory=dict)


@dataclass
class RiskBenchmarkReport:
    """Complete benchmark report."""
    generated_at: str = ""
    corpus_summary: dict[str, Any] = field(default_factory=dict)
    benchmarks: dict[str, ReadinessRiskBenchmark] = field(default_factory=dict)
    financial_benchmarks: FinancialBenchmarks = field(
        default_factory=FinancialBenchmarks
    )


@dataclass
class DimensionComparison:
    """Comparison for one readiness risk path."""
    readiness_path: str = ""
    display_name: str = ""
    project_status: str = ""      # "missing" | "partial" | "addressed"
    corpus_benchmark: str = ""    # narrative summary of corpus standard
    gap_assessment: str = ""      # narrative of how project compares
    severity: str = ""            # "critical" | "material" | "acceptable"
    recommendation: str = ""


@dataclass
class ProjectComparison:
    """Comparison of a project against corpus benchmarks."""
    project_name: str = ""
    generated_at: str = ""
    overall_risk_position: str = ""  # "below_corpus" | "at_corpus" | "above_corpus"
    dimension_comparisons: list[DimensionComparison] = field(default_factory=list)
    financial_comparison: dict[str, Any] = field(default_factory=dict)
    priority_actions: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Implementation Guide Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CorpusRiskEvidence:
    """How corpus issuers addressed a specific risk dimension."""
    readiness_path: str = ""
    display_name: str = ""
    n_risk_factors: int = 0
    n_issuances: int = 0
    severity_distribution: dict[str, int] = field(default_factory=dict)
    mitigation_rate: float = 0.0
    risk_factor_titles: list[str] = field(default_factory=list)


@dataclass
class StructuralProtection:
    """Structural protections observed in the corpus."""
    pledge_types: dict[str, int] = field(default_factory=dict)
    coverage_ratios: MetricDistribution | None = None
    dsrf_types: dict[str, int] = field(default_factory=dict)
    pledged_revenue_descriptions: list[str] = field(default_factory=list)
    credit_enhancements: list[dict[str, str]] = field(default_factory=list)
    lien_positions: dict[str, int] = field(default_factory=dict)


@dataclass
class ImplementationAction:
    """A single recommended implementation action."""
    action_id: int = 0
    priority: str = "medium"      # "critical" | "high" | "medium"
    dimension: str = ""           # readiness path
    action: str = ""              # what to do
    rationale: str = ""           # why (corpus evidence or playbook guidance)
    example_language: str = ""    # concrete mitigant example from playbook
    evidence_to_gather: str = ""  # documents/data needed


@dataclass
class DimensionGuide:
    """Complete implementation guide for one risk dimension."""
    readiness_path: str = ""
    display_name: str = ""
    # Section 1: How corpus issuers addressed this risk
    corpus_evidence: CorpusRiskEvidence = field(default_factory=CorpusRiskEvidence)
    # Section 2: Rating agency perspective by issuer
    agency_strengths_by_issuer: dict[str, list[str]] = field(default_factory=dict)
    agency_challenges_by_issuer: dict[str, list[str]] = field(default_factory=dict)
    rationale_excerpts: list[str] = field(default_factory=list)
    # Section 3: Structural protections
    structural_protections: StructuralProtection = field(
        default_factory=StructuralProtection
    )
    # Section 4: Implementation recommendations
    recommendations: list[ImplementationAction] = field(default_factory=list)
    # Section 5: Playbook guidance + examples
    playbook_guidance: str = ""
    playbook_example_description: str = ""
    playbook_example_mitigants: str = ""
    suggested_evidence: list[str] = field(default_factory=list)


@dataclass
class FinancialImplementation:
    """Financial implementation targets from corpus benchmarks."""
    dscr_target: str = ""
    dscr_corpus_context: str = ""
    coverage_ratio_target: str = ""
    recommended_pledge_type: str = ""
    recommended_dsrf: str = ""
    financial_actions: list[ImplementationAction] = field(default_factory=list)


@dataclass
class ImplementationGuide:
    """Complete Risk Mitigation Implementation Guide."""
    project_name: str = ""
    generated_at: str = ""
    executive_summary: str = ""
    overall_risk_posture: str = ""
    critical_gap_count: int = 0
    material_gap_count: int = 0
    dimension_guides: dict[str, DimensionGuide] = field(default_factory=dict)
    financial_implementation: FinancialImplementation = field(
        default_factory=FinancialImplementation
    )
    priority_sequence: list[ImplementationAction] = field(default_factory=list)
    corpus_summary: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Playbook Risk Guidance (from SCHEMA_PATH_METADATA, not imported to avoid
# cross-package dependency with src/munipal)
# ---------------------------------------------------------------------------

PLAYBOOK_RISK_GUIDANCE: dict[str, dict[str, Any]] = {
    "risk.technology": {
        "guidance": (
            "Assess technology risk including commercial readiness, "
            "performance track record, and execution uncertainties. "
            "Describe the technology's commercial maturity, any "
            "pilot/demonstration results, and key execution risks."
        ),
        "example_description": (
            "The Ultimate Conversion System technology has been demonstrated "
            "at pilot scale (10 TPD) over 24 months. Commercial scale-up to "
            "100 TPD introduces execution risk typical of first-of-kind "
            "deployments."
        ),
        "example_mitigants": (
            "5-year performance warranty from OEM; $10M performance bond; "
            "Technology Performance Insurance covering throughput shortfalls "
            "up to 20%."
        ),
        "suggested_evidence": [
            "Independent engineer report on technology readiness",
            "OEM performance warranty (5+ years)",
            "Performance bond ($10M+ from rated surety)",
            "Technology Performance Insurance policy",
            "Pilot/demonstration operating data (24+ months)",
        ],
        "concrete_mitigants": [
            "Performance warranty from OEM (minimum 5 years)",
            "Performance bond ($10M+ from rated surety)",
            "Technology Performance Insurance (throughput shortfall coverage)",
            "Independent engineer's technology assessment report",
        ],
    },
    "risk.construction": {
        "guidance": (
            "Assess construction risks including schedule, budget, contractor "
            "experience, and force majeure exposure. Describe construction "
            "timeline risks, contractor qualifications, and potential cost "
            "overrun scenarios."
        ),
        "example_description": (
            "24-month construction period with EPC contractor experienced in "
            "similar facilities. Primary risks: permitting delays (3-6 month "
            "impact), supply chain disruptions, weather-related delays."
        ),
        "example_mitigants": (
            "EPC fixed-price contract with $5M performance bond; Liquidated "
            "damages of $50K/day for delays beyond 30 days; 15% construction "
            "contingency reserve."
        ),
        "suggested_evidence": [
            "EPC contract (fixed-price, lump-sum preferred)",
            "Construction performance bond (100% of contract value)",
            "Liquidated damages schedule",
            "Construction contingency budget (15%+ of hard costs)",
            "Independent engineer construction monitoring plan",
        ],
        "concrete_mitigants": [
            "EPC fixed-price contract with experienced contractor",
            "Construction performance bond (100% of contract value)",
            "Liquidated damages ($50K/day for schedule delays)",
            "15% contingency reserve funded at closing",
            "Monthly independent engineer construction monitoring",
        ],
    },
    "risk.market": {
        "guidance": (
            "Assess market and offtake risks including commodity price "
            "volatility, counterparty credit, and demand uncertainty. "
            "Describe commodity pricing risks, offtake counterparty credit "
            "quality, and market demand factors."
        ),
        "example_description": (
            "Renewable diesel pricing indexed to OPIS diesel; Biochar market "
            "emerging with limited price history; Offtake counterparty is "
            "investment-grade fuel distributor."
        ),
        "example_mitigants": (
            "7-year renewable diesel offtake with floor price at 85% of OPIS "
            "index; Biochar offtake LOI with industrial buyer; Revenue "
            "diversification across 3 product streams."
        ),
        "suggested_evidence": [
            "Long-term offtake agreement (7+ years)",
            "Price floor mechanism (85%+ of reference index)",
            "Counterparty credit assessment (investment-grade or LC-backed)",
            "Revenue diversification analysis (3+ product streams)",
            "Market study from independent consultant",
        ],
        "concrete_mitigants": [
            "7-year offtake agreement with price floor (85% of index)",
            "Multiple counterparties (no single buyer >40% of revenue)",
            "Revenue diversification across 3+ product streams",
            "Counterparty credit requirements (investment-grade or LC-backed)",
        ],
    },
    "risk.regulatory": {
        "guidance": (
            "Assess regulatory risks including permit conditions, "
            "environmental compliance, and policy changes. Describe key "
            "regulatory exposures: permit conditions, compliance "
            "requirements, policy change scenarios."
        ),
        "example_description": (
            "Facility subject to air quality permits with emission limits. "
            "Changes to LCFS program could affect renewable fuel pricing. "
            "No federal solid waste regulatory changes anticipated."
        ),
        "example_mitigants": (
            "Continuous emissions monitoring system (CEMS) installed; Bond "
            "counsel opinion on tax-exempt eligibility; Quarterly regulatory "
            "compliance reporting to trustee."
        ),
        "suggested_evidence": [
            "Permit status summary (all required permits)",
            "Bond counsel tax opinion (unqualified)",
            "Environmental compliance plan",
            "Regulatory change impact analysis",
            "CEMS or equivalent monitoring system specification",
        ],
        "concrete_mitigants": [
            "CEMS (Continuous Emissions Monitoring System)",
            "Bond counsel tax opinion (unqualified)",
            "Quarterly compliance reporting to trustee",
            "Regulatory change contingency plan",
            "Environmental insurance coverage",
        ],
    },
    "risk.feedstock": {
        "guidance": (
            "Assess feedstock supply risks including availability, quality "
            "variability, supplier concentration, and pricing mechanisms. "
            "Describe feedstock availability risks, quality variability, "
            "supplier concentration, and pricing mechanisms."
        ),
        "example_description": (
            "Forest biomass supply dependent on timber harvest activity and "
            "fire prevention budgets. Multiple suppliers within 50-mile "
            "radius. Quality varies by season and source."
        ),
        "example_mitigants": (
            "10-year supply agreement with primary supplier; Secondary "
            "agreements covering 40% of capacity; 30-day feedstock storage "
            "on-site; Technology accepts alternative biomass types."
        ),
        "suggested_evidence": [
            "Primary supply agreement (10+ years)",
            "Secondary/backup supply agreements (40%+ of capacity)",
            "Feedstock availability study",
            "On-site storage capacity (30+ days)",
            "Technology feedstock flexibility documentation",
        ],
        "concrete_mitigants": [
            "10-year supply agreement with primary supplier",
            "Secondary agreements covering 40% of capacity",
            "30-day on-site feedstock storage",
            "Technology flexibility for alternative feedstock types",
            "Feedstock quality specifications in supply contracts",
        ],
    },
}


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _compute_distribution(
    values: list[float],
    name: str,
) -> MetricDistribution | None:
    """Compute statistical distribution for a numeric metric."""
    clean = [v for v in values if v is not None and v > 0]
    if len(clean) < 2:
        return None
    clean.sort()
    n = len(clean)
    return MetricDistribution(
        metric_name=name,
        n_observations=n,
        mean=round(statistics.mean(clean), 4),
        median=round(statistics.median(clean), 4),
        p25=round(clean[max(0, n // 4 - 1)], 4),
        p75=round(clean[min(n - 1, 3 * n // 4)], 4),
        min_val=round(clean[0], 4),
        max_val=round(clean[-1], 4),
    )


def _classify_rating_factor(text: str) -> str | None:
    """Classify a rating action factor's free text into a readiness path.

    Uses keyword matching against the factor text. Returns the best-matching
    readiness path, or None if no strong match.
    """
    text_lower = text.lower()
    best_path = None
    best_score = 0

    for path, keywords in _RATING_FACTOR_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > best_score:
            best_score = score
            best_path = path

    return best_path if best_score >= 1 else None


def _severity_pcts(dist: dict[str, int]) -> tuple[float, float, float]:
    """Compute severity percentages from distribution dict."""
    total = sum(dist.values()) or 1
    return (
        (dist.get("boilerplate", 0) / total) * 100,
        (dist.get("material", 0) / total) * 100,
        (dist.get("significant", 0) / total) * 100,
    )


# ---------------------------------------------------------------------------
# Benchmark builders
# ---------------------------------------------------------------------------

def _build_readiness_benchmark(
    readiness_path: str,
    config: dict[str, Any],
    risk_factors: list[dict],
    rating_factors: list[dict],
) -> ReadinessRiskBenchmark:
    """Build benchmark for one readiness risk path from corpus data."""

    emma_categories = config["emma_categories"]

    # Filter risk factors for this readiness path
    path_factors = [
        rf for rf in risk_factors
        if rf.get("category") in emma_categories
    ]

    # Aggregate severity distribution
    severity_dist: dict[str, int] = {"boilerplate": 0, "material": 0, "significant": 0}
    mitigated_count = 0
    titles: list[str] = []
    doc_ids: set[str] = set()

    for rf in path_factors:
        sev = (rf.get("severity_implied") or "boilerplate").lower()
        if sev in severity_dist:
            severity_dist[sev] += 1
        else:
            severity_dist["boilerplate"] += 1

        if rf.get("mitigation_described"):
            mitigated_count += 1

        doc_ids.add(rf.get("document_id", ""))
        title = rf.get("title", "")
        if title and len(titles) < 8:
            titles.append(title)

    n_factors = len(path_factors)
    mitigation_rate = mitigated_count / max(n_factors, 1)
    n_issuances = len(doc_ids - {""})

    # Per-category stats
    cat_stats = []
    for cat in emma_categories:
        cat_factors = [rf for rf in path_factors if rf.get("category") == cat]
        if not cat_factors:
            continue
        cat_sev: dict[str, int] = {"boilerplate": 0, "material": 0, "significant": 0}
        cat_mit = 0
        cat_titles: list[str] = []
        for rf in cat_factors:
            sev = (rf.get("severity_implied") or "boilerplate").lower()
            cat_sev[sev] = cat_sev.get(sev, 0) + 1
            if rf.get("mitigation_described"):
                cat_mit += 1
            t = rf.get("title", "")
            if t and len(cat_titles) < 5:
                cat_titles.append(t)
        cat_stats.append(RiskCategoryStats(
            category=cat,
            count=len(cat_factors),
            severity_distribution=cat_sev,
            mitigation_rate=cat_mit / max(len(cat_factors), 1),
            sample_titles=cat_titles,
        ))

    # Classify rating action factors into this readiness path
    path_rating_factors = [
        rf for rf in rating_factors
        if _classify_rating_factor(rf.get("text", "")) == readiness_path
    ]

    strengths = [
        rf for rf in path_rating_factors
        if rf.get("factor_type") == "strength"
    ]
    challenges = [
        rf for rf in path_rating_factors
        if rf.get("factor_type") == "challenge"
    ]
    key_factors = [
        rf for rf in path_rating_factors
        if rf.get("factor_type") == "key_factor"
    ]

    sample_strengths = [s.get("text", "")[:200] for s in strengths[:5]]
    sample_challenges = [c.get("text", "")[:200] for c in challenges[:5]]

    # Fill narrative templates
    pct_bp, pct_mat, pct_sig = _severity_pcts(severity_dist)
    template_vars = {
        "n_factors": n_factors,
        "n_issuances": n_issuances,
        "pct_boilerplate": pct_bp,
        "pct_material": pct_mat,
        "pct_significant": pct_sig,
        "pct_mitigated": mitigation_rate * 100,
        "n_rating_factors": len(path_rating_factors),
        "n_strengths": len(strengths),
        "n_challenges": len(challenges),
        "pct_challenge": (
            len(challenges) / max(len(path_rating_factors), 1) * 100
        ),
    }

    methodology = config.get("methodology", "")
    benchmark_std = config.get("benchmark_standard", "")
    try:
        methodology = methodology.format(**template_vars)
    except (KeyError, ValueError):
        pass
    try:
        benchmark_std = benchmark_std.format(**template_vars)
    except (KeyError, ValueError):
        pass

    return ReadinessRiskBenchmark(
        readiness_path=readiness_path,
        display_name=config["display_name"],
        n_risk_factors=n_factors,
        n_issuances=n_issuances,
        severity_distribution=severity_dist,
        mitigation_rate=round(mitigation_rate, 4),
        sample_titles=titles,
        n_rating_factors=len(path_rating_factors),
        strength_count=len(strengths),
        challenge_count=len(challenges),
        key_factor_count=len(key_factors),
        sample_strengths=sample_strengths,
        sample_challenges=sample_challenges,
        methodology_narrative=methodology,
        benchmark_standard=benchmark_std,
        category_stats=cat_stats,
    )


def _build_financial_benchmarks(
    financial_reports: list[dict],
    security_packages: list[dict],
) -> FinancialBenchmarks:
    """Build financial metric distributions from the corpus."""

    # DSCR distribution
    dscr_vals = [
        r["debt_service_coverage_ratio"]
        for r in financial_reports
        if r.get("debt_service_coverage_ratio")
    ]
    dscr_dist = _compute_distribution(dscr_vals, "debt_service_coverage_ratio")

    # Coverage ratio from security packages
    cov_vals = [
        sp["min_coverage_ratio"]
        for sp in security_packages
        if sp.get("min_coverage_ratio")
    ]
    cov_dist = _compute_distribution(cov_vals, "min_coverage_ratio")

    # Revenue distribution
    rev_vals = [
        r["total_revenue"]
        for r in financial_reports
        if r.get("total_revenue")
    ]
    rev_dist = _compute_distribution(rev_vals, "total_revenue")

    # Pledge type distribution
    pledge_dist: dict[str, int] = {}
    for sp in security_packages:
        pt = sp.get("pledge_type") or "unknown"
        pt = pt.strip().lower()
        pledge_dist[pt] = pledge_dist.get(pt, 0) + 1

    # Lien position distribution
    lien_dist: dict[str, int] = {}
    for sp in security_packages:
        lp = sp.get("lien_position") or "unknown"
        lp = lp.strip().lower()
        lien_dist[lp] = lien_dist.get(lp, 0) + 1

    return FinancialBenchmarks(
        dscr=dscr_dist,
        coverage_ratio=cov_dist,
        revenue=rev_dist,
        pledge_type_distribution=pledge_dist,
        lien_position_distribution=lien_dist,
    )


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

def build_risk_benchmarks(engine: Engine) -> RiskBenchmarkReport:
    """Build corpus-wide risk benchmarks from EMMA data.

    This is the primary entry point. Loads all risk-relevant data from the
    EMMA corpus database, aggregates it into per-readiness-path benchmarks,
    and produces contextual narratives explaining how each benchmark was
    derived.

    The benchmarks serve as the reference point for comparing individual
    project risk profiles against the broader municipal bond market.
    """
    # Load all data
    risk_factors = load_risk_factors(engine)
    rating_factors = load_rating_action_factors(engine)
    security_packages = load_security_packages(engine)
    financial_reports = load_financial_reports(engine)

    logger.info(
        "Building risk benchmarks from %d risk factors, %d rating factors, "
        "%d security packages, %d financial reports",
        len(risk_factors), len(rating_factors),
        len(security_packages), len(financial_reports),
    )

    # Build per-path benchmarks
    benchmarks: dict[str, ReadinessRiskBenchmark] = {}
    for path, config in READINESS_PATH_CONFIG.items():
        benchmarks[path] = _build_readiness_benchmark(
            path, config, risk_factors, rating_factors,
        )

    # Build financial benchmarks
    fin_benchmarks = _build_financial_benchmarks(financial_reports, security_packages)

    # Corpus summary
    all_doc_ids = {rf.get("document_id", "") for rf in risk_factors} - {""}
    corpus_summary = {
        "n_official_statements": len(all_doc_ids),
        "n_risk_factors": len(risk_factors),
        "n_rating_actions_with_factors": len(
            {rf.get("rating_action_id") for rf in rating_factors} - {"", None}
        ),
        "n_rating_factors": len(rating_factors),
        "n_security_packages": len(security_packages),
        "n_financial_reports": len(financial_reports),
        "risk_categories_observed": len(
            {rf.get("category") for rf in risk_factors if rf.get("category")}
        ),
        "sector": "waste management / environmental services",
    }

    report = RiskBenchmarkReport(
        generated_at=datetime.now().isoformat(),
        corpus_summary=corpus_summary,
        benchmarks=benchmarks,
        financial_benchmarks=fin_benchmarks,
    )

    logger.info(
        "Risk benchmarks built: %d readiness paths, %d total risk factors mapped",
        len(benchmarks),
        sum(b.n_risk_factors for b in benchmarks.values()),
    )
    return report


def compare_project_to_benchmarks(
    report: RiskBenchmarkReport,
    project_facts: dict[str, str | None],
    project_financials: dict[str, float | None],
    project_name: str = "Project",
) -> ProjectComparison:
    """Compare a project's risk profile against corpus benchmarks.

    Args:
        report: The corpus benchmark report from build_risk_benchmarks()
        project_facts: Dict mapping readiness schema paths to their values.
            Keys like "risk.technology.description", "risk.technology.mitigants", etc.
            None or empty string means the fact is missing.
        project_financials: Dict with numeric project metrics:
            "dscr", "revenue", "coverage_ratio", "maturity_years", etc.
        project_name: Display name for the project.

    Returns:
        ProjectComparison with per-dimension assessments and priority actions.
    """
    comparison = ProjectComparison(
        project_name=project_name,
        generated_at=datetime.now().isoformat(),
    )

    critical_count = 0
    material_count = 0
    acceptable_count = 0

    for path, benchmark in report.benchmarks.items():
        desc_key = f"{path}.description"
        mit_key = f"{path}.mitigants"

        has_description = bool(project_facts.get(desc_key))
        has_mitigants = bool(project_facts.get(mit_key))

        # Determine project status
        if has_description and has_mitigants:
            status = "addressed"
        elif has_description or has_mitigants:
            status = "partial"
        else:
            status = "missing"

        # Build corpus benchmark narrative
        corpus_narrative = (
            f"The EMMA corpus contains {benchmark.n_risk_factors} "
            f"{benchmark.display_name.lower()} disclosures across "
            f"{benchmark.n_issuances} issuances. "
            f"Mitigation is described in {benchmark.mitigation_rate * 100:.0f}% "
            f"of cases. Rating agencies cited this area as a strength "
            f"{benchmark.strength_count} times and a challenge "
            f"{benchmark.challenge_count} times."
        )

        # Use lowercase display name for narratives (e.g., "technology risk")
        dn = benchmark.display_name.lower()

        # Assess gap severity
        if status == "missing":
            # Missing risk disclosure is critical if the corpus shows it's
            # commonly disclosed (many issuances address it)
            if benchmark.n_issuances >= 5:
                severity = "critical"
                gap_text = (
                    f"{project_name} has not provided a {dn} assessment. "
                    f"This is a significant gap: {benchmark.n_issuances} of the "
                    f"corpus issuances include explicit {dn} disclosures. "
                    f"Rating agencies expect this information."
                )
                rec = (
                    f"Provide comprehensive {dn} description and mitigants. "
                    f"Reference corpus patterns for appropriate scope and specificity."
                )
            else:
                severity = "material"
                gap_text = (
                    f"{project_name} has not addressed {dn}. While less commonly "
                    f"disclosed in the corpus ({benchmark.n_issuances} issuances), "
                    f"this should be evaluated for relevance to the project."
                )
                rec = (
                    f"Assess whether {dn} is material to this project "
                    f"and provide disclosure if so."
                )
        elif status == "partial":
            severity = "material"
            missing_part = "mitigants" if has_description else "description"
            gap_text = (
                f"{project_name} has partially addressed {dn} but is "
                f"missing {missing_part}. The corpus shows "
                f"{benchmark.mitigation_rate * 100:.0f}% of issuers describe "
                f"both the risk and its mitigants."
            )
            rec = (
                f"Complete the {dn} disclosure by adding {missing_part}."
            )
        else:
            severity = "acceptable"
            gap_text = (
                f"{project_name} has addressed {dn} with both description "
                f"and mitigants, consistent with corpus practices."
            )
            rec = (
                f"Review against corpus benchmark standard for completeness: "
                f"{benchmark.benchmark_standard[:150]}..."
                if len(benchmark.benchmark_standard) > 150
                else f"Review against corpus benchmark standard: {benchmark.benchmark_standard}"
            )

        if severity == "critical":
            critical_count += 1
        elif severity == "material":
            material_count += 1
        else:
            acceptable_count += 1

        comparison.dimension_comparisons.append(DimensionComparison(
            readiness_path=path,
            display_name=benchmark.display_name,
            project_status=status,
            corpus_benchmark=corpus_narrative,
            gap_assessment=gap_text,
            severity=severity,
            recommendation=rec,
        ))

    # Financial comparison
    fin_comp: dict[str, Any] = {}
    dscr = project_financials.get("dscr")
    if dscr is not None and report.financial_benchmarks.dscr:
        corpus_dscr = report.financial_benchmarks.dscr
        if dscr < corpus_dscr.p25:
            position = "below_25th_percentile"
        elif dscr < corpus_dscr.median:
            position = "below_median"
        elif dscr < corpus_dscr.p75:
            position = "above_median"
        else:
            position = "above_75th_percentile"
        fin_comp["dscr"] = {
            "project_value": dscr,
            "corpus_median": corpus_dscr.median,
            "corpus_p25": corpus_dscr.p25,
            "corpus_p75": corpus_dscr.p75,
            "position": position,
            "assessment": (
                f"Project DSCR of {dscr:.2f}x is {position.replace('_', ' ')} "
                f"relative to the corpus (median {corpus_dscr.median:.2f}x, "
                f"p25-p75: {corpus_dscr.p25:.2f}x-{corpus_dscr.p75:.2f}x)."
            ),
        }

    revenue = project_financials.get("revenue")
    if revenue is not None and report.financial_benchmarks.revenue:
        corpus_rev = report.financial_benchmarks.revenue
        fin_comp["revenue"] = {
            "project_value": revenue,
            "corpus_median": corpus_rev.median,
            "corpus_p25": corpus_rev.p25,
            "corpus_p75": corpus_rev.p75,
            "assessment": (
                f"Project revenue of ${revenue:,.0f} relative to corpus "
                f"median ${corpus_rev.median:,.0f}."
            ),
        }

    coverage = project_financials.get("coverage_ratio")
    if coverage is not None and report.financial_benchmarks.coverage_ratio:
        corpus_cov = report.financial_benchmarks.coverage_ratio
        fin_comp["coverage_ratio"] = {
            "project_value": coverage,
            "corpus_median": corpus_cov.median,
            "corpus_p25": corpus_cov.p25,
            "corpus_p75": corpus_cov.p75,
        }

    comparison.financial_comparison = fin_comp

    # Overall position
    if critical_count >= 2:
        comparison.overall_risk_position = "below_corpus"
    elif critical_count >= 1 or material_count >= 3:
        comparison.overall_risk_position = "below_corpus"
    elif material_count >= 1:
        comparison.overall_risk_position = "at_corpus"
    else:
        comparison.overall_risk_position = "above_corpus"

    # Priority actions
    actions = []
    for dc in sorted(
        comparison.dimension_comparisons,
        key=lambda x: {"critical": 0, "material": 1, "acceptable": 2}.get(
            x.severity, 3
        ),
    ):
        if dc.severity in ("critical", "material"):
            actions.append(f"[{dc.severity.upper()}] {dc.recommendation}")
    if dscr is not None and report.financial_benchmarks.dscr:
        if dscr < report.financial_benchmarks.dscr.p25:
            actions.append(
                f"[CRITICAL] DSCR {dscr:.2f}x is below corpus 25th percentile "
                f"({report.financial_benchmarks.dscr.p25:.2f}x). "
                f"Strengthen debt service coverage before market engagement."
            )
        elif dscr < report.financial_benchmarks.dscr.median:
            actions.append(
                f"[MATERIAL] DSCR {dscr:.2f}x is below corpus median "
                f"({report.financial_benchmarks.dscr.median:.2f}x). "
                f"Consider structural enhancements to improve coverage."
            )
    comparison.priority_actions = actions[:8]

    return comparison


# ---------------------------------------------------------------------------
# Implementation Guide Builder
# ---------------------------------------------------------------------------

def _group_factors_by_issuer(
    rating_factors: list[dict[str, Any]],
    readiness_path: str,
) -> tuple[dict[str, list[str]], dict[str, list[str]]]:
    """Group rating agency factors by issuer for a readiness path.

    Returns (strengths_by_issuer, challenges_by_issuer) dicts.
    """
    strengths: dict[str, list[str]] = {}
    challenges: dict[str, list[str]] = {}

    for rf in rating_factors:
        text = rf.get("text", "")
        if not text:
            continue
        classified = _classify_rating_factor(text)
        if classified != readiness_path:
            continue

        issuer = rf.get("issuer_name") or "Unknown Issuer"
        agency = rf.get("agency", "")
        key = f"{issuer} ({agency})" if agency else issuer
        factor_type = rf.get("factor_type", "")

        if factor_type == "strength":
            strengths.setdefault(key, []).append(text)
        elif factor_type == "challenge":
            challenges.setdefault(key, []).append(text)

    return strengths, challenges


def _filter_rationales_for_path(
    rationales: list[dict[str, Any]],
    readiness_path: str,
) -> list[str]:
    """Filter rationale summaries relevant to a readiness path.

    Uses keyword matching to find rationale text that discusses
    topics relevant to the given readiness path.
    """
    keywords = _RATING_FACTOR_KEYWORDS.get(readiness_path, [])
    if not keywords:
        return []

    excerpts = []
    for rat in rationales:
        summary = rat.get("rationale_summary", "")
        if not summary:
            continue
        summary_lower = summary.lower()
        # Require at least 2 keyword hits for relevance
        hits = sum(1 for kw in keywords if kw in summary_lower)
        if hits >= 2:
            issuer = rat.get("issuer_name", "Unknown")
            agency = rat.get("agency", "")
            action = rat.get("action_type", "")
            prefix = f"{issuer} ({agency}, {action})" if agency else issuer
            # Truncate long summaries
            text = summary[:500] + "..." if len(summary) > 500 else summary
            excerpts.append(f"{prefix}: {text}")
    return excerpts[:5]


def _build_structural_protections(
    security_packages: list[dict[str, Any]],
    credit_enhancements: list[dict[str, Any]],
) -> StructuralProtection:
    """Build aggregate structural protection summary from corpus."""
    prot = StructuralProtection()

    # Pledge types
    for sp in security_packages:
        pt = sp.get("pledge_type") or "Unknown"
        prot.pledge_types[pt] = prot.pledge_types.get(pt, 0) + 1

    # Lien positions
    for sp in security_packages:
        lp = sp.get("lien_position") or "Unknown"
        prot.lien_positions[lp] = prot.lien_positions.get(lp, 0) + 1

    # Coverage ratios
    ratios = [
        sp["min_coverage_ratio"]
        for sp in security_packages
        if sp.get("min_coverage_ratio") and sp["min_coverage_ratio"] > 0
    ]
    prot.coverage_ratios = _compute_distribution(ratios, "min_coverage_ratio")

    # DSRF types
    for sp in security_packages:
        dt = sp.get("dsrf_type") or "Unknown"
        if dt and dt != "Unknown":
            prot.dsrf_types[dt] = prot.dsrf_types.get(dt, 0) + 1

    # Pledged revenue descriptions (unique, non-empty)
    seen = set()
    for sp in security_packages:
        desc = sp.get("pledged_revenues_description") or ""
        desc = desc.strip()
        if desc and desc not in seen:
            seen.add(desc)
            prot.pledged_revenue_descriptions.append(desc)
    # Cap at 10 for readability
    prot.pledged_revenue_descriptions = prot.pledged_revenue_descriptions[:10]

    # Credit enhancements
    for ce in credit_enhancements:
        prot.credit_enhancements.append({
            "type": ce.get("credit_enhancement_type", ""),
            "enhancer": ce.get("credit_enhancer_name", ""),
            "issuer": ce.get("issuer_name", ""),
        })
    prot.credit_enhancements = prot.credit_enhancements[:10]

    return prot


def _build_dimension_recommendations(
    readiness_path: str,
    comparison: DimensionComparison,
    playbook: dict[str, Any],
    benchmark: ReadinessRiskBenchmark,
    action_counter: list[int],
) -> list[ImplementationAction]:
    """Build implementation actions for one dimension.

    action_counter is a mutable [int] to track sequential action IDs.
    """
    actions = []
    dn = benchmark.display_name.lower()
    status = comparison.project_status
    severity = comparison.severity

    if status == "missing":
        # Need both description and mitigants
        action_counter[0] += 1
        actions.append(ImplementationAction(
            action_id=action_counter[0],
            priority="critical" if severity == "critical" else "high",
            dimension=readiness_path,
            action=f"Prepare comprehensive {dn} description",
            rationale=(
                f"The corpus shows {benchmark.n_issuances} issuances with "
                f"explicit {dn} disclosures. This is expected by rating "
                f"agencies and investors."
            ),
            example_language=playbook.get("example_description", ""),
            evidence_to_gather="; ".join(playbook.get("suggested_evidence", [])[:3]),
        ))
        action_counter[0] += 1
        actions.append(ImplementationAction(
            action_id=action_counter[0],
            priority="critical" if severity == "critical" else "high",
            dimension=readiness_path,
            action=f"Document {dn} mitigants",
            rationale=(
                f"{benchmark.mitigation_rate * 100:.0f}% of corpus issuers "
                f"describe specific mitigants for {dn}. "
                f"Rating agencies cited this area as a challenge "
                f"{benchmark.challenge_count} times."
            ),
            example_language=playbook.get("example_mitigants", ""),
            evidence_to_gather="; ".join(playbook.get("suggested_evidence", [])[3:]),
        ))

    elif status == "partial":
        # Determine what's missing
        action_counter[0] += 1
        actions.append(ImplementationAction(
            action_id=action_counter[0],
            priority="high",
            dimension=readiness_path,
            action=f"Complete {dn} disclosure by adding mitigants",
            rationale=(
                f"Corpus shows {benchmark.mitigation_rate * 100:.0f}% of "
                f"issuers describe both the risk and its mitigants. "
                f"Rating agencies evaluate mitigation quality when "
                f"assessing creditworthiness."
            ),
            example_language=playbook.get("example_mitigants", ""),
            evidence_to_gather="; ".join(playbook.get("suggested_evidence", [])[:3]),
        ))

    else:
        # Addressed — provide enhancement recommendation
        action_counter[0] += 1
        actions.append(ImplementationAction(
            action_id=action_counter[0],
            priority="medium",
            dimension=readiness_path,
            action=f"Review {dn} disclosure against corpus benchmark",
            rationale=(
                f"Disclosure is present. Review against corpus patterns: "
                f"{benchmark.n_risk_factors} risk factors across "
                f"{benchmark.n_issuances} issuances set the standard."
            ),
            example_language="",
            evidence_to_gather="",
        ))

    # Add concrete mitigant actions from playbook
    for mitigant in playbook.get("concrete_mitigants", [])[:2]:
        action_counter[0] += 1
        actions.append(ImplementationAction(
            action_id=action_counter[0],
            priority="high" if status in ("missing", "partial") else "medium",
            dimension=readiness_path,
            action=f"Secure: {mitigant}",
            rationale=(
                f"Corpus best practice for {dn}. Rating agencies cited "
                f"strengths {benchmark.strength_count} times and challenges "
                f"{benchmark.challenge_count} times in this area."
            ),
            example_language=mitigant,
            evidence_to_gather="",
        ))

    return actions


def build_implementation_guide(
    engine: Engine,
    project_facts: dict[str, str | None],
    project_financials: dict[str, float | None],
    project_name: str = "Project",
) -> ImplementationGuide:
    """Build a comprehensive Risk Mitigation Implementation Guide.

    Combines corpus evidence, rating agency perspectives, structural
    protections, and playbook guidance into actionable recommendations
    tailored to the target project's gaps.

    Args:
        engine: SQLAlchemy engine for the bond corpus database.
        project_facts: Dict mapping readiness paths to values.
        project_financials: Dict with numeric project metrics.
        project_name: Display name for the project.

    Returns:
        ImplementationGuide with per-dimension guides and priority sequence.
    """
    # 1. Build benchmarks and comparison using existing functions
    report = build_risk_benchmarks(engine)
    comparison = compare_project_to_benchmarks(
        report, project_facts, project_financials, project_name,
    )

    # 2. Load additional data
    rating_factors = load_rating_action_factors(engine)
    rationales = load_rationale_summaries(engine)
    security_packages = load_security_packages(engine)
    credit_enhancements = load_credit_enhancements(engine)

    # 3. Build structural protections (corpus-wide)
    structural = _build_structural_protections(security_packages, credit_enhancements)

    # 4. Build per-dimension guides
    dim_guides: dict[str, DimensionGuide] = {}
    action_counter = [0]  # mutable counter for sequential action IDs
    all_actions: list[ImplementationAction] = []

    # Map comparisons by path for lookup
    comp_by_path = {
        dc.readiness_path: dc for dc in comparison.dimension_comparisons
    }

    for path in READINESS_PATH_CONFIG:
        benchmark = report.benchmarks.get(path)
        dim_comp = comp_by_path.get(path)
        playbook = PLAYBOOK_RISK_GUIDANCE.get(path, {})

        if not benchmark or not dim_comp:
            continue

        # Section 1: Corpus evidence
        evidence = CorpusRiskEvidence(
            readiness_path=path,
            display_name=benchmark.display_name,
            n_risk_factors=benchmark.n_risk_factors,
            n_issuances=benchmark.n_issuances,
            severity_distribution=benchmark.severity_distribution,
            mitigation_rate=benchmark.mitigation_rate,
            risk_factor_titles=benchmark.sample_titles[:10],
        )

        # Section 2: Rating agency by issuer
        strengths_by_issuer, challenges_by_issuer = _group_factors_by_issuer(
            rating_factors, path,
        )
        rationale_excerpts = _filter_rationales_for_path(rationales, path)

        # Section 4: Recommendations
        recommendations = _build_dimension_recommendations(
            path, dim_comp, playbook, benchmark, action_counter,
        )
        all_actions.extend(recommendations)

        guide = DimensionGuide(
            readiness_path=path,
            display_name=benchmark.display_name,
            corpus_evidence=evidence,
            agency_strengths_by_issuer=strengths_by_issuer,
            agency_challenges_by_issuer=challenges_by_issuer,
            rationale_excerpts=rationale_excerpts,
            structural_protections=structural,
            recommendations=recommendations,
            playbook_guidance=playbook.get("guidance", ""),
            playbook_example_description=playbook.get("example_description", ""),
            playbook_example_mitigants=playbook.get("example_mitigants", ""),
            suggested_evidence=playbook.get("suggested_evidence", []),
        )
        dim_guides[path] = guide

    # 5. Financial implementation
    fin_impl = _build_financial_implementation(
        report, comparison, project_financials, action_counter,
    )
    all_actions.extend(fin_impl.financial_actions)

    # 6. Priority sequence — sort by priority, cap at 15
    priority_order = {"critical": 0, "high": 1, "medium": 2}
    sorted_actions = sorted(
        all_actions,
        key=lambda a: (priority_order.get(a.priority, 3), a.action_id),
    )
    priority_seq = sorted_actions[:15]
    # Re-number
    for i, act in enumerate(priority_seq, 1):
        act.action_id = i

    # 7. Executive summary
    critical_count = sum(
        1 for dc in comparison.dimension_comparisons if dc.severity == "critical"
    )
    material_count = sum(
        1 for dc in comparison.dimension_comparisons if dc.severity == "material"
    )
    missing_count = sum(
        1 for dc in comparison.dimension_comparisons if dc.project_status == "missing"
    )
    partial_count = sum(
        1 for dc in comparison.dimension_comparisons
        if dc.project_status == "partial"
    )
    addressed_count = sum(
        1 for dc in comparison.dimension_comparisons
        if dc.project_status == "addressed"
    )

    position_label = comparison.overall_risk_position.replace("_", " ").upper()
    summary = (
        f"{project_name} has been evaluated against risk benchmarks derived from "
        f"the EMMA municipal bond corpus (waste management / environmental services "
        f"sector). The project's overall risk position is {position_label}, "
        f"with {missing_count} dimension(s) missing disclosures, "
        f"{partial_count} partially addressed, and "
        f"{addressed_count} fully addressed. "
    )
    if critical_count > 0:
        summary += (
            f"There are {critical_count} critical gap(s) that must be resolved "
            f"before market engagement. "
        )
    if material_count > 0:
        summary += (
            f"{material_count} material gap(s) require attention to strengthen "
            f"the project's risk profile to corpus standards. "
        )
    summary += (
        f"This guide provides {len(priority_seq)} prioritized implementation "
        f"actions based on corpus evidence and industry best practices."
    )

    return ImplementationGuide(
        project_name=project_name,
        generated_at=datetime.now(tz=None).isoformat(),
        executive_summary=summary,
        overall_risk_posture=comparison.overall_risk_position,
        critical_gap_count=critical_count,
        material_gap_count=material_count,
        dimension_guides=dim_guides,
        financial_implementation=fin_impl,
        priority_sequence=priority_seq,
        corpus_summary=report.corpus_summary,
    )


def _build_financial_implementation(
    report: RiskBenchmarkReport,
    comparison: ProjectComparison,
    project_financials: dict[str, float | None],
    action_counter: list[int],
) -> FinancialImplementation:
    """Build financial implementation targets from corpus benchmarks."""
    fin = FinancialImplementation()
    fb = report.financial_benchmarks

    # DSCR target
    if fb.dscr:
        fin.dscr_corpus_context = (
            f"Corpus DSCR: median {fb.dscr.median:.2f}x, "
            f"p25-p75: {fb.dscr.p25:.2f}x-{fb.dscr.p75:.2f}x "
            f"({fb.dscr.n_observations} observations)."
        )
        dscr = project_financials.get("dscr")
        if dscr is not None:
            if dscr < fb.dscr.p25:
                fin.dscr_target = f"Target minimum {fb.dscr.median:.2f}x (corpus median)"
                action_counter[0] += 1
                fin.financial_actions.append(ImplementationAction(
                    action_id=action_counter[0],
                    priority="critical",
                    dimension="financial",
                    action=(
                        f"Improve DSCR from {dscr:.2f}x to at least "
                        f"{fb.dscr.median:.2f}x (corpus median)"
                    ),
                    rationale=(
                        f"Project DSCR of {dscr:.2f}x is below the corpus "
                        f"25th percentile ({fb.dscr.p25:.2f}x). This level "
                        f"may not meet minimum rate covenant requirements."
                    ),
                    example_language=(
                        "Consider: higher initial rates, additional pledged "
                        "revenues, capitalized interest during ramp-up, or "
                        "debt restructuring to reduce annual service."
                    ),
                    evidence_to_gather="Pro forma financial model; rate study",
                ))
            elif dscr < fb.dscr.median:
                fin.dscr_target = f"Target {fb.dscr.p75:.2f}x (corpus 75th percentile)"
                action_counter[0] += 1
                fin.financial_actions.append(ImplementationAction(
                    action_id=action_counter[0],
                    priority="high",
                    dimension="financial",
                    action=(
                        f"Strengthen DSCR from {dscr:.2f}x toward "
                        f"{fb.dscr.p75:.2f}x (corpus 75th percentile)"
                    ),
                    rationale=(
                        f"Project DSCR of {dscr:.2f}x is below corpus median "
                        f"({fb.dscr.median:.2f}x). Improving coverage "
                        f"strengthens credit profile."
                    ),
                    example_language=(
                        "Consider: revenue enhancement, additional security, "
                        "or structural protections (DSRF, rate covenant)."
                    ),
                    evidence_to_gather="Updated financial projections",
                ))
            else:
                fin.dscr_target = "At or above corpus median"
        else:
            fin.dscr_target = f"Target minimum {fb.dscr.median:.2f}x (corpus median)"

    # Coverage ratio target
    if fb.coverage_ratio:
        fin.coverage_ratio_target = (
            f"Minimum {fb.coverage_ratio.median:.2f}x rate covenant "
            f"(corpus median)"
        )
        fin.coverage_corpus_context = (
            f"Corpus coverage ratios: median {fb.coverage_ratio.median:.2f}x, "
            f"p25-p75: {fb.coverage_ratio.p25:.2f}x-{fb.coverage_ratio.p75:.2f}x."
        )

    # Recommended pledge type (most common in corpus)
    if fb.pledge_type_distribution:
        most_common = max(
            fb.pledge_type_distribution,
            key=fb.pledge_type_distribution.get,  # type: ignore[arg-type]
        )
        fin.recommended_pledge_type = (
            f"{most_common} (most common in corpus: "
            f"{fb.pledge_type_distribution[most_common]} of "
            f"{sum(fb.pledge_type_distribution.values())} issuances)"
        )

    # Recommended DSRF
    if fb.lien_position_distribution:
        fin.recommended_dsrf = (
            "Establish a debt service reserve fund (DSRF) sized at "
            "maximum annual debt service, consistent with corpus norms."
        )

    return fin


# ---------------------------------------------------------------------------
# Export functions
# ---------------------------------------------------------------------------

def _metric_to_dict(m: MetricDistribution | None) -> dict | None:
    """Convert MetricDistribution to serializable dict."""
    if m is None:
        return None
    return {
        "metric_name": m.metric_name,
        "n_observations": m.n_observations,
        "mean": m.mean,
        "median": m.median,
        "p25": m.p25,
        "p75": m.p75,
        "min": m.min_val,
        "max": m.max_val,
    }


def export_risk_benchmark(
    report: RiskBenchmarkReport,
    output_path: Path | None = None,
) -> Path:
    """Export benchmark report to JSON."""
    if output_path is None:
        output_path = (
            get_settings().data_dir / "analysis" / "risk_benchmark_report.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "analysis": "EMMA Corpus Risk Benchmarks for Readiness Assessment",
        "generated_at": report.generated_at,
        "corpus_summary": report.corpus_summary,
        "benchmarks": {},
        "financial_benchmarks": {
            "dscr": _metric_to_dict(report.financial_benchmarks.dscr),
            "coverage_ratio": _metric_to_dict(
                report.financial_benchmarks.coverage_ratio
            ),
            "revenue": _metric_to_dict(report.financial_benchmarks.revenue),
            "pledge_type_distribution": (
                report.financial_benchmarks.pledge_type_distribution
            ),
            "lien_position_distribution": (
                report.financial_benchmarks.lien_position_distribution
            ),
        },
    }

    for path, bm in report.benchmarks.items():
        data["benchmarks"][path] = {
            "display_name": bm.display_name,
            "n_risk_factors": bm.n_risk_factors,
            "n_issuances": bm.n_issuances,
            "severity_distribution": bm.severity_distribution,
            "mitigation_rate": bm.mitigation_rate,
            "sample_titles": bm.sample_titles,
            "methodology_narrative": bm.methodology_narrative,
            "benchmark_standard": bm.benchmark_standard,
            "rating_agency_perspective": {
                "n_factors": bm.n_rating_factors,
                "strengths": bm.strength_count,
                "challenges": bm.challenge_count,
                "key_factors": bm.key_factor_count,
                "sample_strengths": bm.sample_strengths,
                "sample_challenges": bm.sample_challenges,
            },
            "category_breakdown": [
                {
                    "category": cs.category,
                    "count": cs.count,
                    "severity_distribution": cs.severity_distribution,
                    "mitigation_rate": round(cs.mitigation_rate, 4),
                    "sample_titles": cs.sample_titles,
                }
                for cs in bm.category_stats
            ],
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported risk benchmark report to %s", output_path)
    return output_path


def export_project_comparison(
    comparison: ProjectComparison,
    output_path: Path | None = None,
) -> Path:
    """Export project comparison to JSON."""
    if output_path is None:
        output_path = (
            get_settings().data_dir / "analysis" / "risk_comparison_report.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "analysis": "Project Risk Comparison vs EMMA Corpus Benchmarks",
        "project_name": comparison.project_name,
        "generated_at": comparison.generated_at,
        "overall_risk_position": comparison.overall_risk_position,
        "dimension_comparisons": [
            {
                "readiness_path": dc.readiness_path,
                "display_name": dc.display_name,
                "project_status": dc.project_status,
                "severity": dc.severity,
                "corpus_benchmark": dc.corpus_benchmark,
                "gap_assessment": dc.gap_assessment,
                "recommendation": dc.recommendation,
            }
            for dc in comparison.dimension_comparisons
        ],
        "financial_comparison": comparison.financial_comparison,
        "priority_actions": comparison.priority_actions,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported project comparison to %s", output_path)
    return output_path


def _action_to_dict(a: ImplementationAction) -> dict:
    """Convert ImplementationAction to serializable dict."""
    return {
        "action_id": a.action_id,
        "priority": a.priority,
        "dimension": a.dimension,
        "action": a.action,
        "rationale": a.rationale,
        "example_language": a.example_language,
        "evidence_to_gather": a.evidence_to_gather,
    }


def export_implementation_guide(
    guide: ImplementationGuide,
    output_path: Path | None = None,
) -> Path:
    """Export implementation guide to JSON."""
    if output_path is None:
        output_path = (
            get_settings().data_dir
            / "analysis"
            / "risk_implementation_guide.json"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    data: dict[str, Any] = {
        "analysis": "Risk Mitigation Implementation Guide",
        "project_name": guide.project_name,
        "generated_at": guide.generated_at,
        "executive_summary": guide.executive_summary,
        "overall_risk_posture": guide.overall_risk_posture,
        "critical_gap_count": guide.critical_gap_count,
        "material_gap_count": guide.material_gap_count,
        "corpus_summary": guide.corpus_summary,
        "dimension_guides": {},
        "financial_implementation": {
            "dscr_target": guide.financial_implementation.dscr_target,
            "dscr_corpus_context": guide.financial_implementation.dscr_corpus_context,
            "coverage_ratio_target": guide.financial_implementation.coverage_ratio_target,
            "recommended_pledge_type": guide.financial_implementation.recommended_pledge_type,
            "recommended_dsrf": guide.financial_implementation.recommended_dsrf,
            "financial_actions": [
                _action_to_dict(a)
                for a in guide.financial_implementation.financial_actions
            ],
        },
        "priority_sequence": [
            _action_to_dict(a) for a in guide.priority_sequence
        ],
    }

    for path, dg in guide.dimension_guides.items():
        data["dimension_guides"][path] = {
            "readiness_path": dg.readiness_path,
            "display_name": dg.display_name,
            "corpus_evidence": {
                "n_risk_factors": dg.corpus_evidence.n_risk_factors,
                "n_issuances": dg.corpus_evidence.n_issuances,
                "severity_distribution": dg.corpus_evidence.severity_distribution,
                "mitigation_rate": dg.corpus_evidence.mitigation_rate,
                "risk_factor_titles": dg.corpus_evidence.risk_factor_titles,
            },
            "agency_strengths_by_issuer": dg.agency_strengths_by_issuer,
            "agency_challenges_by_issuer": dg.agency_challenges_by_issuer,
            "rationale_excerpts": dg.rationale_excerpts,
            "structural_protections": {
                "pledge_types": dg.structural_protections.pledge_types,
                "coverage_ratios": _metric_to_dict(
                    dg.structural_protections.coverage_ratios
                ),
                "dsrf_types": dg.structural_protections.dsrf_types,
                "pledged_revenue_descriptions": (
                    dg.structural_protections.pledged_revenue_descriptions
                ),
                "credit_enhancements": (
                    dg.structural_protections.credit_enhancements
                ),
                "lien_positions": dg.structural_protections.lien_positions,
            },
            "recommendations": [
                _action_to_dict(a) for a in dg.recommendations
            ],
            "playbook_guidance": dg.playbook_guidance,
            "playbook_example_description": dg.playbook_example_description,
            "playbook_example_mitigants": dg.playbook_example_mitigants,
            "suggested_evidence": dg.suggested_evidence,
        }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

    logger.info("Exported implementation guide to %s", output_path)
    return output_path


def export_implementation_guide_markdown(
    guide: ImplementationGuide,
    output_path: Path | None = None,
) -> Path:
    """Export implementation guide as Markdown report."""
    if output_path is None:
        output_path = (
            get_settings().data_dir
            / "analysis"
            / "risk_implementation_guide.md"
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    _a = lines.append  # shorthand

    _a(f"# Risk Mitigation Implementation Guide: {guide.project_name}")
    _a("")
    _a(f"**Generated:** {guide.generated_at[:10]}")
    _a(f"**Project:** {guide.project_name}")
    pos = guide.overall_risk_posture.replace("_", " ").upper()
    _a(f"**Overall Risk Posture:** {pos}")
    _a("")
    _a("---")
    _a("")
    _a("## Executive Summary")
    _a("")
    _a(guide.executive_summary)
    _a("")
    _a(f"| Metric | Count |")
    _a(f"|--------|------:|")
    _a(f"| Critical Gaps | {guide.critical_gap_count} |")
    _a(f"| Material Gaps | {guide.material_gap_count} |")
    _a(f"| Implementation Actions | {len(guide.priority_sequence)} |")
    _a("")
    _a("---")

    # Dimension guides
    for idx, (path, dg) in enumerate(guide.dimension_guides.items(), 1):
        _a("")
        _a(f"## {idx}. {dg.display_name} (`{path}`)")
        _a("")

        # Section 1: Corpus evidence
        ev = dg.corpus_evidence
        _a(f"### How Corpus Issuers Addressed {dg.display_name}")
        _a("")
        _a(f"The EMMA corpus contains **{ev.n_risk_factors} risk factor "
           f"disclosures** across **{ev.n_issuances} issuances** for "
           f"{dg.display_name.lower()}.")
        _a("")
        sev = ev.severity_distribution
        total_sev = sum(sev.values()) or 1
        _a("| Severity | Count | Percentage |")
        _a("|----------|------:|-----------:|")
        for level in ("material", "significant", "boilerplate"):
            cnt = sev.get(level, 0)
            pct = cnt / total_sev * 100
            _a(f"| {level.title()} | {cnt} | {pct:.0f}% |")
        _a("")
        _a(f"**Mitigation rate:** {ev.mitigation_rate * 100:.0f}% of "
           f"disclosures describe specific mitigants.")
        _a("")
        if ev.risk_factor_titles:
            _a("**Risk factor titles observed in corpus:**")
            for title in ev.risk_factor_titles:
                _a(f"- {title}")
            _a("")

        # Section 2: Rating agency perspective
        if dg.agency_strengths_by_issuer or dg.agency_challenges_by_issuer:
            _a(f"### Rating Agency Perspective")
            _a("")

            all_issuers = set(dg.agency_strengths_by_issuer) | set(
                dg.agency_challenges_by_issuer
            )
            for issuer in sorted(all_issuers):
                _a(f"**{issuer}:**")
                s_list = dg.agency_strengths_by_issuer.get(issuer, [])
                c_list = dg.agency_challenges_by_issuer.get(issuer, [])
                if s_list:
                    _a("")
                    _a("*Strengths:*")
                    for s in s_list[:5]:
                        _a(f"- {s}")
                if c_list:
                    _a("")
                    _a("*Challenges:*")
                    for c in c_list[:5]:
                        _a(f"- {c}")
                _a("")

        if dg.rationale_excerpts:
            _a("**Rating Agency Rationale Excerpts:**")
            _a("")
            for excerpt in dg.rationale_excerpts:
                _a(f"> {excerpt}")
                _a("")

        # Section 3: Structural protections (only for first dimension
        # to avoid repetition, or selectively)
        if idx == 1:
            sp = dg.structural_protections
            _a("### Structural Protections Observed in Corpus")
            _a("")
            if sp.pledge_types:
                _a("**Pledge Type Distribution:**")
                _a("")
                _a("| Pledge Type | Count |")
                _a("|-------------|------:|")
                for pt, cnt in sorted(
                    sp.pledge_types.items(), key=lambda x: -x[1]
                ):
                    _a(f"| {pt} | {cnt} |")
                _a("")
            if sp.coverage_ratios:
                cr = sp.coverage_ratios
                _a(
                    f"**Coverage Ratios:** median {cr.median:.2f}x "
                    f"(p25-p75: {cr.p25:.2f}x-{cr.p75:.2f}x, "
                    f"n={cr.n_observations})"
                )
                _a("")
            if sp.lien_positions:
                _a("**Lien Positions:**")
                _a("")
                _a("| Position | Count |")
                _a("|----------|------:|")
                for lp, cnt in sorted(
                    sp.lien_positions.items(), key=lambda x: -x[1]
                ):
                    _a(f"| {lp} | {cnt} |")
                _a("")
            if sp.pledged_revenue_descriptions:
                _a("**Sample Pledged Revenue Descriptions:**")
                _a("")
                for desc in sp.pledged_revenue_descriptions[:5]:
                    _a(f"> {desc}")
                    _a("")
            if sp.credit_enhancements:
                _a("**Credit Enhancements:**")
                _a("")
                for ce in sp.credit_enhancements[:5]:
                    _a(
                        f"- {ce.get('type', '')} "
                        f"({ce.get('issuer', '')})"
                    )
                _a("")

        # Section 4: Recommendations
        _a(f"### Implementation Recommendations for {guide.project_name}")
        _a("")
        for rec in dg.recommendations:
            marker = rec.priority.upper()
            _a(f"**{rec.action_id}. [{marker}] {rec.action}**")
            _a("")
            _a(f"*Rationale:* {rec.rationale}")
            if rec.example_language:
                _a("")
                _a(f"*Example:* \"{rec.example_language}\"")
            if rec.evidence_to_gather:
                _a("")
                _a(f"*Evidence needed:* {rec.evidence_to_gather}")
            _a("")

        # Section 5: Playbook guidance
        _a(f"### Example Mitigant Language")
        _a("")
        _a(f"**Guidance:** {dg.playbook_guidance}")
        _a("")
        if dg.playbook_example_description:
            _a(f"**Example Risk Description:**")
            _a(f"> {dg.playbook_example_description}")
            _a("")
        if dg.playbook_example_mitigants:
            _a(f"**Example Mitigants:**")
            _a(f"> {dg.playbook_example_mitigants}")
            _a("")
        if dg.suggested_evidence:
            _a(f"### Evidence to Gather")
            _a("")
            for ev_item in dg.suggested_evidence:
                _a(f"- {ev_item}")
            _a("")

        _a("---")

    # Financial implementation
    _a("")
    _a("## Financial Implementation")
    _a("")
    fi = guide.financial_implementation
    if fi.dscr_target:
        _a(f"### DSCR Target")
        _a("")
        _a(f"**Target:** {fi.dscr_target}")
        _a("")
        if fi.dscr_corpus_context:
            _a(f"**Corpus Context:** {fi.dscr_corpus_context}")
            _a("")
    if fi.coverage_ratio_target:
        _a(f"### Coverage Ratio")
        _a("")
        _a(f"**Target:** {fi.coverage_ratio_target}")
        _a("")
        if fi.coverage_corpus_context:
            _a(f"**Corpus Context:** {fi.coverage_corpus_context}")
            _a("")
    if fi.recommended_pledge_type:
        _a(f"### Recommended Pledge Type")
        _a("")
        _a(f"{fi.recommended_pledge_type}")
        _a("")
    if fi.recommended_dsrf:
        _a(f"### Debt Service Reserve Fund")
        _a("")
        _a(f"{fi.recommended_dsrf}")
        _a("")
    if fi.financial_actions:
        _a("### Financial Actions")
        _a("")
        for fa in fi.financial_actions:
            marker = fa.priority.upper()
            _a(f"**[{marker}] {fa.action}**")
            _a("")
            _a(f"*Rationale:* {fa.rationale}")
            if fa.example_language:
                _a(f"")
                _a(f"*Approach:* {fa.example_language}")
            _a("")

    # Priority sequence
    _a("---")
    _a("")
    _a("## Priority Implementation Sequence")
    _a("")
    _a("| # | Priority | Dimension | Action |")
    _a("|---|----------|-----------|--------|")
    for act in guide.priority_sequence:
        dim_label = act.dimension.replace("risk.", "").replace(".", " ").title()
        if act.dimension == "financial":
            dim_label = "Financial"
        _a(f"| {act.action_id} | {act.priority.upper()} | {dim_label} | {act.action} |")
    _a("")
    _a("---")
    _a("")
    _a("*Report generated by Muni-Pal EMMA Risk Benchmarking Module*")
    _a("*Data source: MSRB EMMA municipal bond corpus "
       "(waste management / environmental services sector)*")
    _a("")

    content = "\n".join(lines)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info("Exported implementation guide markdown to %s", output_path)
    return output_path
