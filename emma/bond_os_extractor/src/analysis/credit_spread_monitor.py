"""Credit Spread Monitor & All-In Cost of Capital Comparison Tool.

Combines:
  1. Live AAA MMD base curve (from yield_curve_fetcher)
  2. Sector-specific credit spreads derived from the EMMA corpus
  3. Issuer fee structures (IDA Sierra Vista defaults, PFA, generic HFA)
  4. All-in TIC calculation with structural adjustments

Produces a borrower-ready cost-of-capital grid and comparable deals table
that can be shared with prospective borrowers and used to benchmark
alternative issuance channels.
"""
from __future__ import annotations

import json
import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.engine import Engine

from ..config import get_settings
from .data_loader import (
    get_emma_ratings,
    get_emma_trades,
    load_emma_bond_data,
    load_os_records,
)
from .spread_table import DEFAULT_MUNI_SPREADS, get_spread_bps
from .yield_curve_fetcher import (
    TENORS,
    fetch_aaa_curve,
    get_yield_curves,
    interpolate_yield,
)

logger = logging.getLogger("bond_os_extractor.analysis.credit_spread_monitor")


# ---------------------------------------------------------------------------
# Issuer Fee Structures
# ---------------------------------------------------------------------------

@dataclass
class IssuerFeeSchedule:
    """Fee schedule for a bond issuer/conduit."""
    name: str
    display_name: str
    annual_fee_bps: float         # basis points per annum on outstanding
    annual_fee_min_usd: float     # minimum annual fee
    upfront_fee_bps: float        # one-time issuance fee (bps of par)
    upfront_fee_flat_usd: float   # flat issuance fee component
    out_of_state_surcharge_bps: float  # additional bps for out-of-state
    notes: list[str] = field(default_factory=list)

    def annual_fee_pct(self, outstanding: float) -> float:
        """Annual fee as a percentage of outstanding, respecting minimum."""
        fee_from_bps = outstanding * (self.annual_fee_bps / 10000.0)
        effective = max(fee_from_bps, self.annual_fee_min_usd)
        return (effective / outstanding * 100.0) if outstanding > 0 else 0.0

    def upfront_fee_pct(self, par_amount: float) -> float:
        """Upfront fee as a percentage of par."""
        fee = par_amount * (self.upfront_fee_bps / 10000.0) + self.upfront_fee_flat_usd
        return (fee / par_amount * 100.0) if par_amount > 0 else 0.0

    def all_in_fee_bps(
        self,
        par_amount: float,
        maturity_years: float = 30.0,
        out_of_state: bool = False,
    ) -> float:
        """Estimate total fee drag in bps annualized over life of bonds.

        Converts upfront fee to annualized equivalent and adds to annual fee.
        """
        annual = max(
            self.annual_fee_bps,
            (self.annual_fee_min_usd / par_amount * 10000.0) if par_amount > 0 else 0,
        )
        if out_of_state:
            annual += self.out_of_state_surcharge_bps

        # Amortize upfront over maturity (simple, conservative)
        upfront_annualized = (
            self.upfront_fee_bps + (
                self.upfront_fee_flat_usd / par_amount * 10000.0
                if par_amount > 0 else 0
            )
        ) / maturity_years

        return round(annual + upfront_annualized, 2)


# Pre-built fee schedules
IDA_SIERRA_VISTA = IssuerFeeSchedule(
    name="ida_sierra_vista",
    display_name="IDA of the City of Sierra Vista",
    annual_fee_bps=7.0,
    annual_fee_min_usd=3000.0,
    upfront_fee_bps=0.0,        # President may approve lump-sum alternative
    upfront_fee_flat_usd=0.0,
    out_of_state_surcharge_bps=3.0,  # President's discretion
    notes=[
        "Annual fee: 7 bps on outstanding, $3,000 minimum",
        "President may approve one-time PV lump sum in lieu of annual fees",
        "Out-of-state surcharge at President's discretion",
        "Fee shall not impact tax-exempt status of bonds",
        "Authority retains right to adjust fees per resolution",
    ],
)

PFA_WISCONSIN = IssuerFeeSchedule(
    name="pfa_wisconsin",
    display_name="Public Finance Authority (WI)",
    annual_fee_bps=10.0,
    annual_fee_min_usd=5000.0,
    upfront_fee_bps=15.0,
    upfront_fee_flat_usd=2500.0,
    out_of_state_surcharge_bps=0.0,  # PFA is designed for out-of-state
    notes=[
        "National conduit issuer — no geographic restrictions",
        "Typical annual fee ~10 bps (varies by deal)",
        "One-time issuance fee ~15 bps + $2,500",
        "Fees negotiable on larger transactions",
    ],
)

GENERIC_LOCAL_HFA = IssuerFeeSchedule(
    name="generic_hfa",
    display_name="Local Health Facilities Authority",
    annual_fee_bps=8.0,
    annual_fee_min_usd=4000.0,
    upfront_fee_bps=10.0,
    upfront_fee_flat_usd=1500.0,
    out_of_state_surcharge_bps=0.0,  # Local HFAs typically can't issue out-of-state
    notes=[
        "Representative local HFA fee structure",
        "Actual fees vary by jurisdiction",
        "May offer local market advantages (investor familiarity)",
    ],
)

ISSUER_SCHEDULES: dict[str, IssuerFeeSchedule] = {
    "ida_sierra_vista": IDA_SIERRA_VISTA,
    "pfa_wisconsin": PFA_WISCONSIN,
    "generic_hfa": GENERIC_LOCAL_HFA,
}


# ---------------------------------------------------------------------------
# Structural cost adjustments
# ---------------------------------------------------------------------------

@dataclass
class StructuralCosts:
    """Additional structural costs layered into all-in TIC."""
    underwriter_spread_bps: float = 75.0   # typical muni underwriter spread
    counsel_costs_bps: float = 10.0        # bond/issuer counsel (annualized)
    trustee_fee_bps: float = 2.0           # trustee/paying agent
    rating_agency_bps: float = 3.0         # rating agency fees (annualized)
    insurance_bps: float = 0.0             # bond insurance premium if applicable
    dsrf_drag_bps: float = 5.0             # debt service reserve fund opportunity cost
    cap_interest_bps: float = 0.0          # capitalized interest (if applicable)

    @property
    def total_bps(self) -> float:
        return (
            self.underwriter_spread_bps
            + self.counsel_costs_bps
            + self.trustee_fee_bps
            + self.rating_agency_bps
            + self.insurance_bps
            + self.dsrf_drag_bps
            + self.cap_interest_bps
        )


DEFAULT_STRUCTURAL_COSTS = StructuralCosts()


# ---------------------------------------------------------------------------
# Corpus-derived spread analysis
# ---------------------------------------------------------------------------

def _build_issuer_rating_map(engine: Engine) -> dict[str, str]:
    """Build issuer-name → rating-bucket map from all corpus DB sources.

    Merges three data sources (in priority order):
      1. rating_actions table (most specific: agency + new_rating)
      2. ratings table (from OS extraction)
      3. deal_identities table (may have embedded rating info)

    Returns a lowercased-issuer-name → bucket mapping.
    """
    from sqlalchemy import text

    mapping: dict[str, str] = {}

    # Source 1: rating_actions — use most recent action per issuer
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT issuer_name, new_rating, action_date "
                "FROM rating_actions "
                "WHERE new_rating IS NOT NULL AND new_rating != '' "
                "ORDER BY action_date DESC"
            )).fetchall()
            for issuer_name, new_rating, _ in rows:
                if issuer_name:
                    key = issuer_name.strip().lower()
                    if key not in mapping:
                        mapping[key] = _normalize_to_bucket(new_rating)
    except Exception as exc:
        logger.debug("Could not read rating_actions: %s", exc)

    # Source 2: ratings table joined through documents → deal_identities
    try:
        with engine.connect() as conn:
            rows = conn.execute(text(
                "SELECT di.issuer_name, r.rating "
                "FROM ratings r "
                "JOIN documents d ON r.document_id = d.id "
                "JOIN deal_identities di ON di.source_file = d.source_file "
                "WHERE r.rating IS NOT NULL AND r.rating != ''"
            )).fetchall()
            for issuer_name, rating in rows:
                if issuer_name:
                    key = issuer_name.strip().lower()
                    if key not in mapping:
                        mapping[key] = _normalize_to_bucket(rating)
    except Exception as exc:
        logger.debug("Could not join ratings→deal_identities: %s", exc)

    logger.info("Built issuer→rating map with %d entries from corpus DB", len(mapping))
    return mapping


def _compute_corpus_spreads(
    engine: Engine,
) -> dict[str, Any]:
    """Derive credit spreads from EMMA corpus trade and rating data.

    Uses three rating sources in priority order:
      1. EMMA crawler JSON ratings (direct from EMMA security page)
      2. Corpus DB rating_actions (from extracted rating action PDFs)
      3. Corpus DB ratings table (from Official Statement extraction)

    Returns sector-specific observed spreads by rating bucket,
    plus recent comparable deals.
    """
    from .yield_curve_fetcher import REFERENCE_AAA_CURVE

    settings = get_settings()
    bonds = load_emma_bond_data()

    # Build a fallback rating map from the corpus DB
    db_rating_map = _build_issuer_rating_map(engine)

    # Collect (rating_bucket, yield, par_amount, issuer, maturity, cusip) tuples
    observations: list[dict[str, Any]] = []
    rating_yields: dict[str, list[float]] = defaultdict(list)

    for bond in bonds:
        ratings = get_emma_ratings(bond)
        trades = get_emma_trades(bond)
        snapshot = bond.get("snapshot", {})
        issuer = snapshot.get("security_name", snapshot.get("issuer_name", "Unknown"))

        # Get best available rating — try EMMA data first, then corpus DB
        best_rating = None
        for r in ratings:
            rating_str = r.get("rating", "")
            if rating_str:
                best_rating = _normalize_to_bucket(rating_str)
                break

        if not best_rating:
            # Fuzzy match against corpus DB by issuer name
            issuer_lower = issuer.strip().lower()
            for db_issuer, db_bucket in db_rating_map.items():
                # Check if either name contains the other (handles
                # "City of X Solid Waste Rev" vs "City of X")
                if db_issuer in issuer_lower or issuer_lower in db_issuer:
                    best_rating = db_bucket
                    break
                # Also try matching on first 3 words (entity name)
                db_words = db_issuer.split()[:3]
                iss_words = issuer_lower.split()[:3]
                if len(db_words) >= 2 and db_words == iss_words:
                    best_rating = db_bucket
                    break

        # Validate rating bucket is a real rating, not a date or garbage
        valid_buckets = {"AAA", "AA", "A", "BBB", "BB", "B"}
        if not best_rating or best_rating not in valid_buckets:
            continue

        # Get most recent trade yield
        valid_trades = [
            t for t in trades
            if t.get("yield") and _parse_yield(t["yield"]) is not None
        ]
        if not valid_trades:
            continue

        # Sort by trade date descending
        valid_trades.sort(
            key=lambda t: t.get("trade_date", ""), reverse=True
        )
        latest = valid_trades[0]
        yld = _parse_yield(latest["yield"])
        if yld is None or yld <= 0 or yld > 15:
            continue

        par_str = snapshot.get("principal_amount", "0")
        par = _parse_amount(par_str)
        maturity = snapshot.get("maturity_date", "")

        # Estimate remaining tenor from maturity date
        tenor_years = _estimate_tenor(maturity)

        # Compute spread vs tenor-matched AAA reference curve
        aaa_at_tenor = interpolate_yield(REFERENCE_AAA_CURVE, tenor_years) if tenor_years else None
        spread_bps_vs_aaa = round((yld - aaa_at_tenor) * 100, 1) if aaa_at_tenor else None

        rating_yields[best_rating].append(yld)
        observations.append({
            "cusip": bond.get("cusip", ""),
            "issuer": issuer,
            "rating_bucket": best_rating,
            "yield": yld,
            "par_amount": par,
            "maturity_date": maturity,
            "trade_date": latest.get("trade_date", ""),
            "trade_type": latest.get("trade_type", ""),
            "tenor_years": tenor_years,
            "spread_vs_aaa_bps": spread_bps_vs_aaa,
        })

    # Compute median spread by rating bucket using tenor-adjusted spreads
    # Each observation's spread is already calculated vs its maturity-matched
    # AAA curve point, so median spread here is meaningful across mixed tenors
    rating_spreads: dict[str, list[float]] = defaultdict(list)
    for obs in observations:
        if obs.get("spread_vs_aaa_bps") is not None:
            rating_spreads[obs["rating_bucket"]].append(obs["spread_vs_aaa_bps"])

    spread_by_rating: dict[str, dict[str, Any]] = {}

    for bucket in ["AAA", "AA", "A", "BBB", "BB", "B"]:
        yields = rating_yields.get(bucket, [])
        if not yields:
            continue
        med = statistics.median(yields)
        spreads = rating_spreads.get(bucket, [])
        median_spread = round(statistics.median(spreads), 1) if spreads else None
        spread_by_rating[bucket] = {
            "n_observations": len(yields),
            "median_yield": round(med, 3),
            "min_yield": round(min(yields), 3),
            "max_yield": round(max(yields), 3),
            "spread_over_aaa_bps": median_spread,
        }

    # Recent comparable deals (last 20 by trade date)
    observations.sort(key=lambda o: o.get("trade_date", ""), reverse=True)
    recent_comps = observations[:20]

    return {
        "spread_by_rating": spread_by_rating,
        "n_total_observations": len(observations),
        "recent_comps": recent_comps,
        "aaa_reference_10yr": REFERENCE_AAA_CURVE.get(10, 3.85),
    }


def _normalize_to_bucket(rating: str) -> str:
    """Map a granular rating to its broad bucket (AAA, AA, A, BBB, BB, B)."""
    r = rating.strip()
    # Moody's to S&P mapping
    moodys_map = {
        "Aaa": "AAA", "Aa1": "AA", "Aa2": "AA", "Aa3": "AA",
        "A1": "A", "A2": "A", "A3": "A",
        "Baa1": "BBB", "Baa2": "BBB", "Baa3": "BBB",
        "Ba1": "BB", "Ba2": "BB", "Ba3": "BB",
        "B1": "B", "B2": "B", "B3": "B",
    }
    if r in moodys_map:
        return moodys_map[r]
    if r.startswith("AAA"):
        return "AAA"
    if r.startswith("AA"):
        return "AA"
    if r.startswith("BBB"):
        return "BBB"
    if r.startswith("BB"):
        return "BB"
    if r.startswith("B"):
        return "B"
    if r.startswith("A"):
        return "A"
    return r


def _parse_yield(val: Any) -> float | None:
    """Parse a yield value that may be string or numeric."""
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace("%", "").strip())
    except (ValueError, TypeError):
        return None


def _estimate_tenor(maturity_date: str) -> float | None:
    """Estimate remaining tenor in years from a maturity date string."""
    if not maturity_date:
        return None
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y"):
        try:
            mat = datetime.strptime(maturity_date.strip(), fmt)
            now = datetime.now()
            tenor = (mat - now).days / 365.25
            return round(max(tenor, 0.5), 1) if tenor > 0 else None
        except ValueError:
            continue
    return None


def _parse_amount(val: Any) -> float:
    """Parse a par amount string."""
    if val is None:
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    try:
        return float(str(val).replace(",", "").replace("$", "").strip())
    except (ValueError, TypeError):
        return 0.0


# ---------------------------------------------------------------------------
# Cost of Capital Grid
# ---------------------------------------------------------------------------

@dataclass
class CostOfCapitalRow:
    """One row in the cost-of-capital comparison grid."""
    rating: str
    tenor: int
    base_aaa_yield: float
    sector_spread_bps: float
    estimated_yield: float
    issuer_fee_bps: float
    structural_cost_bps: float
    all_in_tic: float
    corpus_observed_yield: float | None = None
    n_corpus_obs: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "rating": self.rating,
            "tenor": self.tenor,
            "base_aaa_yield": self.base_aaa_yield,
            "sector_spread_bps": self.sector_spread_bps,
            "estimated_yield": round(self.estimated_yield, 3),
            "issuer_fee_bps": self.issuer_fee_bps,
            "structural_cost_bps": self.structural_cost_bps,
            "all_in_tic": round(self.all_in_tic, 3),
            "corpus_observed_yield": self.corpus_observed_yield,
            "n_corpus_obs": self.n_corpus_obs,
        }


@dataclass
class IssuerComparison:
    """Side-by-side issuer cost comparison for a single rating/tenor."""
    rating: str
    tenor: int
    base_yield: float
    comparisons: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "rating": self.rating,
            "tenor": self.tenor,
            "base_yield": self.base_yield,
            "comparisons": self.comparisons,
        }


@dataclass
class CreditSpreadReport:
    """Complete credit spread monitor report."""
    sector: str
    generated_at: str
    aaa_curve_source: str
    aaa_curve_date: str

    # Yield curves by rating
    yield_curves: dict[str, dict[str, float]]

    # Cost of capital grid
    cost_grid: list[CostOfCapitalRow]

    # Issuer comparison
    issuer_comparisons: list[IssuerComparison]

    # Corpus-derived data
    corpus_spreads: dict[str, Any]
    recent_comps: list[dict[str, Any]]

    # Fee schedules
    fee_schedules: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "sector": self.sector,
            "generated_at": self.generated_at,
            "aaa_curve_source": self.aaa_curve_source,
            "aaa_curve_date": self.aaa_curve_date,
            "yield_curves": self.yield_curves,
            "cost_grid": [r.to_dict() for r in self.cost_grid],
            "issuer_comparisons": [c.to_dict() for c in self.issuer_comparisons],
            "corpus_spreads": self.corpus_spreads,
            "recent_comps": self.recent_comps,
            "fee_schedules": self.fee_schedules,
        }


# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_credit_spread_report(
    engine: Engine,
    par_amount: float = 50_000_000.0,
    out_of_state: bool = False,
    structural_costs: StructuralCosts | None = None,
    issuer_keys: list[str] | None = None,
) -> CreditSpreadReport:
    """Generate the full credit spread monitor report.

    Args:
        engine: SQLAlchemy engine for the sector corpus
        par_amount: Representative par amount for fee calculations
        out_of_state: Whether borrower is out-of-state (affects IDA fees)
        structural_costs: Override structural cost assumptions
        issuer_keys: Which issuers to compare (default: all three)

    Returns:
        CreditSpreadReport with all sections populated
    """
    costs = structural_costs or DEFAULT_STRUCTURAL_COSTS
    issuers = issuer_keys or list(ISSUER_SCHEDULES.keys())

    # 1. Fetch yield curves
    curve_data = get_yield_curves()
    yield_curves = curve_data["curves"]
    aaa_curve = {int(k): v for k, v in yield_curves["AAA"].items()}

    # 2. Compute corpus-derived spreads
    corpus = _compute_corpus_spreads(engine)

    # 3. Build cost-of-capital grid
    ratings_to_grid = ["AA", "A", "BBB", "BB"]
    tenors_to_grid = [10, 20, 30]
    primary_issuer = ISSUER_SCHEDULES.get(issuers[0], IDA_SIERRA_VISTA)

    cost_grid: list[CostOfCapitalRow] = []
    for rating in ratings_to_grid:
        spread_bps = DEFAULT_MUNI_SPREADS.get(rating, 0)

        # Override with corpus-observed spread if available
        corpus_rating = corpus["spread_by_rating"].get(rating, {})
        if corpus_rating.get("spread_over_aaa_bps") is not None:
            # Blend: 50% reference table, 50% corpus observed
            corpus_spread = corpus_rating["spread_over_aaa_bps"]
            spread_bps = (spread_bps + corpus_spread) / 2.0

        for tenor in tenors_to_grid:
            base_yield = aaa_curve.get(tenor)
            if base_yield is None:
                base_yield = interpolate_yield(aaa_curve, tenor) or 4.0

            estimated_yield = base_yield + spread_bps / 100.0
            issuer_bps = primary_issuer.all_in_fee_bps(
                par_amount, float(tenor), out_of_state
            )
            all_in = estimated_yield + (issuer_bps + costs.total_bps) / 100.0

            row = CostOfCapitalRow(
                rating=rating,
                tenor=tenor,
                base_aaa_yield=base_yield,
                sector_spread_bps=round(spread_bps, 1),
                estimated_yield=estimated_yield,
                issuer_fee_bps=issuer_bps,
                structural_cost_bps=round(costs.total_bps, 1),
                all_in_tic=all_in,
                corpus_observed_yield=corpus_rating.get("median_yield"),
                n_corpus_obs=corpus_rating.get("n_observations", 0),
            )
            cost_grid.append(row)

    # 4. Build issuer comparisons
    issuer_comparisons: list[IssuerComparison] = []
    for rating in ["A", "BBB"]:
        spread_bps = DEFAULT_MUNI_SPREADS.get(rating, 0)
        for tenor in [20, 30]:
            base_yield = aaa_curve.get(tenor, 4.0)
            est_yield = base_yield + spread_bps / 100.0

            comps: list[dict[str, Any]] = []
            for key in issuers:
                schedule = ISSUER_SCHEDULES.get(key)
                if not schedule:
                    continue
                fee_bps = schedule.all_in_fee_bps(
                    par_amount, float(tenor), out_of_state
                )
                tic = est_yield + (fee_bps + costs.total_bps) / 100.0
                comps.append({
                    "issuer": schedule.display_name,
                    "issuer_key": key,
                    "issuer_fee_bps": fee_bps,
                    "structural_cost_bps": round(costs.total_bps, 1),
                    "total_cost_bps": round(fee_bps + costs.total_bps, 1),
                    "all_in_tic": round(tic, 3),
                    "annual_fee_on_par": round(
                        par_amount * schedule.annual_fee_bps / 10000.0, 0
                    ),
                })
            issuer_comparisons.append(IssuerComparison(
                rating=rating,
                tenor=tenor,
                base_yield=round(est_yield, 3),
                comparisons=comps,
            ))

    # 5. Serialize fee schedules
    fee_info = []
    for key in issuers:
        s = ISSUER_SCHEDULES.get(key)
        if not s:
            continue
        fee_info.append({
            "key": s.name,
            "display_name": s.display_name,
            "annual_fee_bps": s.annual_fee_bps,
            "annual_fee_min_usd": s.annual_fee_min_usd,
            "upfront_fee_bps": s.upfront_fee_bps,
            "upfront_fee_flat_usd": s.upfront_fee_flat_usd,
            "out_of_state_surcharge_bps": s.out_of_state_surcharge_bps,
            "notes": s.notes,
            "example_annual_on_50m": round(
                max(50_000_000 * s.annual_fee_bps / 10000, s.annual_fee_min_usd), 0
            ),
        })

    return CreditSpreadReport(
        sector=get_settings().sector,
        generated_at=datetime.now(timezone.utc).isoformat(),
        aaa_curve_source=curve_data["aaa_source"],
        aaa_curve_date=curve_data["as_of"],
        yield_curves=yield_curves,
        cost_grid=cost_grid,
        issuer_comparisons=issuer_comparisons,
        corpus_spreads=corpus["spread_by_rating"],
        recent_comps=corpus["recent_comps"],
        fee_schedules=fee_info,
    )
