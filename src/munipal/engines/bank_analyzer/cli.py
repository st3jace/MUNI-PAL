"""Bank Analyzer CLI — standalone command-line interface.

Usage:
    python -m munipal.engines.bank_analyzer.cli score --data-dir PATH
    python -m munipal.engines.bank_analyzer.cli match --deal-type green_bond --deal-size 50000000
    python -m munipal.engines.bank_analyzer.cli distress --top 20
    python -m munipal.engines.bank_analyzer.cli detail "JPMORGAN CHASE"
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

logger = logging.getLogger("bank_analyzer")


def _default_data_dir() -> Path:
    """Default TOUCAN data directory."""
    return Path(r"C:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\TOUCAN")


@click.group()
@click.option("--log-level", default="WARNING", help="Log level")
def cli(log_level: str) -> None:
    """Bank Analyzer — score and match banks to municipal bond opportunities."""
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.WARNING))


@cli.command()
@click.option("--data-dir", type=click.Path(exists=True), default=None,
              help="Directory containing bank_search CSV files")
@click.option("--top", "-n", default=25, help="Show top N banks")
@click.option("--sort-by", type=click.Choice(["composite", "cre", "enhancement", "purchase", "green"]),
              default="composite", help="Sort dimension")
@click.option("--output", "-o", type=click.Path(), default=None, help="Export JSON path")
def score(data_dir: str | None, top: int, sort_by: str, output: str | None) -> None:
    """Score all banks across 4 dimensions and rank."""
    from .ingest import load_all_banks
    from .scoring import score_all_banks

    dd = Path(data_dir) if data_dir else _default_data_dir()
    banks = load_all_banks(dd)
    if not banks:
        click.echo("No bank data found. Provide --data-dir with bank_search CSV files.")
        sys.exit(1)

    scorecards = score_all_banks(banks)

    # Sort by selected dimension
    sort_keys = {
        "composite": lambda s: -s.composite_score,
        "cre": lambda s: -s.cre_distress.score,
        "enhancement": lambda s: -s.credit_enhancement.score,
        "purchase": lambda s: -s.direct_purchase.score,
        "green": lambda s: -s.green_finance.score,
    }
    scorecards.sort(key=sort_keys[sort_by])

    click.echo(f"\n{'=' * 110}")
    click.echo(f"  BANK ANALYZER: {len(scorecards)} Banks Scored")
    click.echo(f"  Sorted by: {sort_by.upper()}")
    click.echo(f"{'=' * 110}")

    click.echo(f"\n{'#':>3} {'Bank':<40} {'Assets':>12} {'PCA':<12} "
               f"{'CRE':>5} {'CE':>5} {'DP':>5} {'GF':>5} {'Comp':>6}")
    click.echo("-" * 110)

    for sc in scorecards[:top]:
        assets_str = f"${sc.total_assets / 1e9:.0f}B" if sc.total_assets >= 1e9 else f"${sc.total_assets / 1e6:.0f}M"
        pca_short = {
            "well_capitalized": "Well",
            "adequately_capitalized": "Adequate",
            "undercapitalized": "Under",
            "significantly_undercapitalized": "Sig Under",
            "critically_undercapitalized": "Critical",
        }.get(sc.pca_category, "?")

        click.echo(
            f"{sc.ranking:>3} {sc.bank_name[:39]:<40} {assets_str:>12} {pca_short:<12} "
            f"{sc.cre_distress.score:>5.1f} {sc.credit_enhancement.score:>5.1f} "
            f"{sc.direct_purchase.score:>5.1f} {sc.green_finance.score:>5.1f} "
            f"{sc.composite_score:>6.1f}"
        )

    # Summary stats
    click.echo(f"\n{'=' * 110}")
    pca_dist = {}
    for sc in scorecards:
        pca_dist[sc.pca_category] = pca_dist.get(sc.pca_category, 0) + 1
    click.echo(f"  PCA Distribution: {dict(pca_dist)}")

    tier_dist = {}
    for sc in scorecards:
        tier_dist[sc.asset_tier] = tier_dist.get(sc.asset_tier, 0) + 1
    click.echo(f"  Asset Tiers: {dict(tier_dist)}")

    distressed = [sc for sc in scorecards if sc.cre_distress.score >= 30]
    click.echo(f"  CRE Distressed (score >= 30): {len(distressed)} banks")

    green_leaders = [sc for sc in scorecards if sc.green_finance.esg_commitment_level in ("leader", "active")]
    click.echo(f"  Green Finance Leaders/Active: {len(green_leaders)} banks")

    if output:
        out_path = Path(output)
        data = [sc.model_dump(mode="json") for sc in scorecards]
        out_path.write_text(json.dumps(data, indent=2, default=str))
        click.echo(f"\n  Exported: {out_path}")

    # Generate reports
    from .reports import generate_scoreboard_report
    md_path, json_path = generate_scoreboard_report(scorecards)
    click.echo(f"\n  Report: {md_path}")
    click.echo(f"  Data:   {json_path}")

    click.echo("")


@cli.command()
@click.option("--data-dir", type=click.Path(exists=True), default=None)
@click.option("--top", "-n", default=10, help="Show top N distressed")
def distress(data_dir: str | None, top: int) -> None:
    """Show banks with highest CRE distress — workout advisory opportunities."""
    from .ingest import load_all_banks
    from .scoring import score_all_banks

    dd = Path(data_dir) if data_dir else _default_data_dir()
    banks = load_all_banks(dd)
    scorecards = score_all_banks(banks)
    scorecards.sort(key=lambda s: -s.cre_distress.score)

    click.echo(f"\n{'=' * 100}")
    click.echo("  CRE DISTRESS ANALYSIS — Workout Advisory Opportunities")
    click.echo(f"{'=' * 100}")

    for sc in scorecards[:top]:
        cre = sc.cre_distress
        if cre.score <= 0:
            continue
        assets_str = f"${sc.total_assets / 1e9:.0f}B" if sc.total_assets >= 1e9 else f"${sc.total_assets / 1e6:.0f}M"
        click.echo(f"\n  {sc.bank_name} ({sc.state}, {assets_str})")
        click.echo(f"    Distress Score: {cre.score:.1f}/100  |  Opportunity: {cre.opportunity_type}")
        click.echo(f"    CRE NPL Ratio: {cre.cre_npl_ratio:.2%}  |  CRE Concentration: {cre.cre_concentration_pct:.1f}%")
        if cre.total_reo > 0:
            click.echo(f"    Total REO: ${cre.total_reo / 1e6:.1f}M  |  REO/Assets: {cre.reo_to_assets_pct:.2f}%")
        if cre.distress_segments:
            click.echo(f"    Distressed Segments: {', '.join(cre.distress_segments)}")
        click.echo(f"    Non-Owner CRE NPL: {cre.commercial_non_owner_npl:.2%}  |  "
                   f"Multifamily NPL: {cre.multifamily_npl:.2%}  |  "
                   f"Construction NPL: {cre.construction_npl:.2%}")

    # Generate report
    from .reports import generate_distress_report
    md_path, json_path = generate_distress_report(scorecards)
    click.echo(f"\n  Report: {md_path}")
    click.echo(f"  Data:   {json_path}")

    click.echo("")


@cli.command()
@click.option("--data-dir", type=click.Path(exists=True), default=None)
@click.option("--deal-type", required=True,
              type=click.Choice(["revenue_bond", "go_bond", "conduit", "private_placement",
                                 "credit_enhancement", "green_bond", "project_finance"]))
@click.option("--deal-size", required=True, type=float, help="Deal size in USD")
@click.option("--state", default=None, help="Issuer state (2-letter)")
@click.option("--sector", default=None, help="Sector (waste, healthcare, energy)")
@click.option("--needs-enhancement", is_flag=True)
@click.option("--enhancement-type", type=click.Choice(["loc", "sbpa", "bond_insurance"]), default=None)
@click.option("--green", is_flag=True, help="Green bond")
@click.option("--carbon", is_flag=True, help="Carbon credit deal")
@click.option("--bank-qualified", is_flag=True, help="Bank-qualified (<$10M)")
@click.option("--top", "-n", default=15)
def match(
    data_dir: str | None, deal_type: str, deal_size: float,
    state: str | None, sector: str | None,
    needs_enhancement: bool, enhancement_type: str | None,
    green: bool, carbon: bool, bank_qualified: bool, top: int,
) -> None:
    """Match banks to a specific deal profile."""
    from .ingest import load_all_banks
    from .matching import match_banks_to_deal
    from .models import DealMatchRequest
    from .scoring import score_all_banks

    dd = Path(data_dir) if data_dir else _default_data_dir()
    banks = load_all_banks(dd)
    scorecards = score_all_banks(banks)

    deal = DealMatchRequest(
        deal_type=deal_type,
        deal_size=deal_size,
        state=state.upper() if state else None,
        sector=sector,
        needs_credit_enhancement=needs_enhancement,
        enhancement_type=enhancement_type,
        is_green=green,
        is_carbon_credit=carbon,
        bank_qualified=bank_qualified,
    )

    result = match_banks_to_deal(scorecards, deal, top_n=top)

    size_str = f"${deal_size / 1e6:.0f}M"
    click.echo(f"\n{'=' * 100}")
    click.echo(f"  BANK-DEAL MATCHING: {deal_type.upper()} | {size_str}")
    if state:
        click.echo(f"  State: {state.upper()}", nl=False)
    if green:
        click.echo(f"  | GREEN", nl=False)
    if carbon:
        click.echo(f"  | CARBON CREDIT", nl=False)
    if needs_enhancement:
        click.echo(f"  | Enhancement: {enhancement_type or 'any'}", nl=False)
    click.echo(f"\n  Banks screened: {result.total_banks_screened}")
    click.echo(f"{'=' * 100}")

    if not result.matches:
        click.echo("\n  No matching banks found for this deal profile.\n")
        return

    for i, m in enumerate(result.matches, 1):
        assets_str = f"${m.total_assets / 1e9:.0f}B" if m.total_assets >= 1e9 else f"${m.total_assets / 1e6:.0f}M"
        click.echo(f"\n  {i}. {m.bank_name} ({m.state}, {assets_str})")
        click.echo(f"     Match Score: {m.match_score:.1f}  |  Role: {m.recommended_role}")
        for reason in m.match_reasons:
            click.echo(f"     + {reason}")
        for concern in m.concerns:
            click.echo(f"     ! {concern}")

    # Generate report
    from .reports import generate_match_report
    md_path, json_path = generate_match_report(result)
    click.echo(f"\n  Report: {md_path}")
    click.echo(f"  Data:   {json_path}")

    click.echo("")


@cli.command()
@click.argument("bank_name")
@click.option("--data-dir", type=click.Path(exists=True), default=None)
def detail(bank_name: str, data_dir: str | None) -> None:
    """Show detailed scorecard for a specific bank."""
    from .ingest import load_all_banks
    from .scoring import score_bank

    dd = Path(data_dir) if data_dir else _default_data_dir()
    banks = load_all_banks(dd)

    # Find bank by name (case-insensitive substring match)
    target = None
    for b in banks:
        if bank_name.upper() in b.bank_name.upper():
            target = b
            break

    if not target:
        click.echo(f"Bank not found: '{bank_name}'")
        click.echo(f"Available banks ({len(banks)}):")
        for b in banks[:20]:
            click.echo(f"  {b.bank_name}")
        sys.exit(1)

    sc = score_bank(target)

    assets_str = f"${sc.total_assets / 1e9:.1f}B" if sc.total_assets >= 1e9 else f"${sc.total_assets / 1e6:.0f}M"
    click.echo(f"\n{'=' * 80}")
    click.echo(f"  {sc.bank_name}")
    click.echo(f"  {target.city}, {target.state} {target.postal_code}  |  {assets_str}  |  PCA: {sc.pca_category}")
    click.echo(f"  RSSD: {sc.id_rssd}  |  FDIC: {target.fdic_cert}  |  {target.website or ''}")
    click.echo(f"{'=' * 80}")

    # Capital ratios
    click.echo(f"\n  CAPITAL RATIOS")
    click.echo(f"  {'Risk-Based Capital:':>25} {(target.risk_based_capital_ratio or 0)*100:.2f}%")
    click.echo(f"  {'Tier 1 RBC:':>25} {(target.tier1_rbc_ratio or 0)*100:.2f}%")
    click.echo(f"  {'Tier 1 Leverage:':>25} {(target.tier1_leverage_ratio or 0)*100:.2f}%")

    # CRE Distress
    cre = sc.cre_distress
    click.echo(f"\n  CRE DISTRESS: {cre.score:.1f}/100  ({cre.opportunity_type})")
    click.echo(f"    CRE NPL: {cre.cre_npl_ratio:.2%}  |  Concentration: {cre.cre_concentration_pct:.1f}%")
    if cre.distress_segments:
        click.echo(f"    Distressed: {', '.join(cre.distress_segments)}")

    # Credit Enhancement
    ce = sc.credit_enhancement
    click.echo(f"\n  CREDIT ENHANCEMENT: {ce.score:.1f}/100")
    click.echo(f"    Excess capital: {ce.excess_capital_pct:.1f}%  |  Types: {', '.join(ce.enhancement_types) or 'none'}")
    if ce.max_enhancement_estimate > 0:
        click.echo(f"    Max enhancement (est): ${ce.max_enhancement_estimate / 1e6:.0f}M")

    # Direct Purchase
    dp = sc.direct_purchase
    click.echo(f"\n  DIRECT PURCHASE: {dp.score:.1f}/100")
    click.echo(f"    BQ eligible: {dp.bank_qualified_eligible}  |  Tax position: {dp.tax_position_indicator}")
    for sig in dp.municipal_appetite_signals:
        click.echo(f"    + {sig}")

    # Green Finance
    gf = sc.green_finance
    click.echo(f"\n  GREEN FINANCE: {gf.score:.1f}/100  ({gf.esg_commitment_level})")
    if gf.has_carbon_deals:
        click.echo(f"    Carbon deals: ${gf.carbon_deal_volume / 1e6:.0f}M  |  Types: {', '.join(gf.carbon_deal_types)}")

    # Loan portfolio summary
    click.echo(f"\n  LOAN PORTFOLIO")
    for seg in target.all_segments():
        if seg.portfolio_balance > 0:
            bal_str = f"${seg.portfolio_balance / 1e9:.1f}B" if seg.portfolio_balance >= 1e9 else f"${seg.portfolio_balance / 1e6:.0f}M"
            npl_str = f"{seg.npl_ratio:.2f}%" if seg.npl_ratio else "0.00%"
            click.echo(f"    {seg.segment_name:<30} {bal_str:>10}  NPL: {npl_str}")

    click.echo(f"\n  COMPOSITE SCORE: {sc.composite_score:.1f}/100")
    click.echo("")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
