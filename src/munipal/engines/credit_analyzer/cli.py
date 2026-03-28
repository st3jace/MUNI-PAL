"""Credit Analyzer CLI — standalone command-line interface.

Usage:
    python -m munipal.engines.credit_analyzer.cli analyze --project project.json
    python -m munipal.engines.credit_analyzer.cli five-cs --project-name "GSI Caldor" --dscr 1.34 ...
    python -m munipal.engines.credit_analyzer.cli size --revenue 10000000 --expenses 7000000 ...
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

logger = logging.getLogger("credit_analyzer")


@click.group()
@click.option("--log-level", default="WARNING", help="Log level")
def cli(log_level: str) -> None:
    """Credit Analyzer — 5 Cs assessment, bond sizing, and deal structuring."""
    logging.basicConfig(level=getattr(logging, log_level.upper(), logging.WARNING))


@cli.command(name="five-cs")
@click.option("--project-name", "-p", required=True, help="Project name")
@click.option("--sector", default="waste", type=click.Choice(["waste", "healthcare", "energy", "water", "transportation", "housing", "other"]))
@click.option("--dscr", type=float, default=None, help="Historical DSCR")
@click.option("--revenue", type=float, default=None, help="Annual revenue (USD)")
@click.option("--expenses", type=float, default=None, help="Annual expenses (USD)")
@click.option("--margin", type=float, default=None, help="Operating margin (decimal)")
@click.option("--revenue-growth", type=float, default=None, help="Revenue growth rate (decimal)")
@click.option("--equity", type=float, default=None, help="Equity contribution (USD)")
@click.option("--equity-pct", type=float, default=None, help="Equity as % of project cost (decimal)")
@click.option("--leverage", type=float, default=None, help="Leverage ratio (debt/equity)")
@click.option("--current-ratio", type=float, default=None, help="Current ratio")
@click.option("--total-assets", type=float, default=None)
@click.option("--total-liabilities", type=float, default=None)
@click.option("--total-equity", type=float, default=None)
@click.option("--pledge-type", type=click.Choice(["gross_revenue", "net_revenue", "specific_revenue", "none"]), default=None)
@click.option("--lien", type=click.Choice(["first", "second", "pari_passu", "subordinate"]), default=None)
@click.option("--has-offtake", is_flag=True)
@click.option("--has-real-property", is_flag=True)
@click.option("--rating", type=str, default=None, help="Credit rating (e.g., A, BBB+)")
@click.option("--market-position", type=click.Choice(["dominant", "strong", "competitive", "weak"]), default=None)
@click.option("--sector-outlook", type=click.Choice(["growing", "stable", "declining", "distressed"]), default=None)
@click.option("--experience-years", type=float, default=None, help="Management experience (years)")
@click.option("--prior-projects", type=int, default=None, help="Prior projects completed")
@click.option("--green", is_flag=True, help="Green bond")
@click.option("--project-file", type=click.Path(exists=True), default=None, help="JSON project file (overrides flags)")
def five_cs_cmd(project_name: str, project_file: str | None, **kwargs) -> None:
    """Run 5 Cs credit assessment on a project."""
    from .five_cs import assess_five_cs
    from .models import ManagementProfile, ProjectInputs

    if project_file:
        data = json.loads(Path(project_file).read_text(encoding="utf-8"))
        project = ProjectInputs(**data)
    else:
        mgmt = ManagementProfile(
            team_experience_years=kwargs.get("experience_years"),
            prior_projects_completed=kwargs.get("prior_projects"),
        )
        project = ProjectInputs(
            project_name=project_name,
            sector=kwargs.get("sector", "waste"),
            management=mgmt,
            historical_revenue=kwargs.get("revenue"),
            historical_expenses=kwargs.get("expenses"),
            historical_dscr=kwargs.get("dscr"),
            operating_margin=kwargs.get("margin"),
            revenue_growth_rate=kwargs.get("revenue_growth"),
            total_assets=kwargs.get("total_assets"),
            total_liabilities=kwargs.get("total_liabilities"),
            total_equity=kwargs.get("total_equity"),
            equity_contribution=kwargs.get("equity"),
            equity_contribution_pct=kwargs.get("equity_pct"),
            leverage_ratio=kwargs.get("leverage"),
            current_ratio=kwargs.get("current_ratio"),
            pledge_type=kwargs.get("pledge_type"),
            lien_position=kwargs.get("lien"),
            has_offtake_agreements=kwargs.get("has_offtake", False),
            has_real_property=kwargs.get("has_real_property", False),
            credit_rating=kwargs.get("rating"),
            market_position=kwargs.get("market_position"),
            sector_outlook=kwargs.get("sector_outlook"),
            is_green=kwargs.get("green", False),
        )

    result = assess_five_cs(project)

    # Display
    click.echo(f"\n{'=' * 80}")
    click.echo(f"  5 Cs CREDIT ASSESSMENT: {result.project_name}")
    click.echo(f"{'=' * 80}")
    click.echo(f"\n  Composite Score: {result.composite_score:.1f}/100  |  "
               f"Grade: {result.composite_grade}  |  "
               f"Recommendation: {result.recommendation.replace('_', ' ').upper()}")

    for cs in [result.character, result.capacity, result.capital, result.collateral, result.conditions]:
        click.echo(f"\n{'-' * 80}")
        click.echo(f"  {cs.dimension} ({cs.weight:.0%} weight)  "
                   f"Score: {cs.score:.0f}/100  Grade: {cs.grade}  "
                   f"Weighted: {cs.weighted_score:.1f}")
        for f in cs.findings:
            click.echo(f"    + {f}")
        for r in cs.risks:
            click.echo(f"    ! {r}")
        for m in cs.mitigants:
            click.echo(f"    ~ {m}")

    if result.key_strengths:
        click.echo(f"\n{'=' * 80}")
        click.echo("  KEY STRENGTHS")
        for s in result.key_strengths:
            click.echo(f"    + {s}")

    if result.key_risks:
        click.echo(f"\n  KEY RISKS")
        for r in result.key_risks:
            click.echo(f"    ! {r}")

    if result.conditions_for_approval:
        click.echo(f"\n  CONDITIONS FOR APPROVAL")
        for i, c in enumerate(result.conditions_for_approval, 1):
            click.echo(f"    {i}. {c}")

    # Generate report
    from .reports import generate_five_cs_report
    md_path, json_path = generate_five_cs_report(result)
    click.echo(f"\n  Report: {md_path}")
    click.echo(f"  Data:   {json_path}")
    click.echo("")


@cli.command()
@click.option("--project-name", "-p", default="Project", help="Project name")
@click.option("--revenue", type=float, required=True, help="Annual gross revenue")
@click.option("--expenses", type=float, required=True, help="Annual operating expenses")
@click.option("--revenue-growth", type=float, default=0.02, help="Annual revenue growth rate")
@click.option("--maturity", type=float, default=30, help="Bond maturity (years)")
@click.option("--coupon", type=float, default=0.05, help="Coupon rate (decimal)")
@click.option("--target-dscr", type=float, default=1.25, help="Target minimum DSCR")
@click.option("--target-par", type=float, default=None, help="Desired par amount (USD)")
@click.option("--equity", type=float, default=None, help="Equity contribution (USD)")
@click.option("--project-cost", type=float, default=None, help="Total project cost (USD)")
@click.option("--project-file", type=click.Path(exists=True), default=None, help="JSON project file")
def size(
    project_name: str, revenue: float, expenses: float,
    revenue_growth: float, maturity: float, coupon: float,
    target_dscr: float, target_par: float | None,
    equity: float | None, project_cost: float | None,
    project_file: str | None,
) -> None:
    """Size a bond issue based on projected revenue and target DSCR."""
    from .bond_sizing import size_bond
    from .models import ProjectInputs

    if project_file:
        data = json.loads(Path(project_file).read_text(encoding="utf-8"))
        project = ProjectInputs(**data)
    else:
        project = ProjectInputs(
            project_name=project_name,
            historical_revenue=revenue,
            historical_expenses=expenses,
            revenue_growth_rate=revenue_growth,
            target_maturity_years=maturity,
            target_coupon_rate=coupon,
            target_par_amount=target_par,
            equity_contribution=equity,
            total_project_cost=project_cost,
        )

    result = size_bond(project, target_dscr=target_dscr, coupon_rate=coupon)

    click.echo(f"\n{'=' * 80}")
    click.echo(f"  BOND SIZING: {project_name}")
    click.echo(f"{'=' * 80}")

    if result.recommended_par <= 0:
        click.echo("\n  Cannot size bond:")
        for note in result.sizing_notes:
            click.echo(f"    ! {note}")
        click.echo("")
        return

    click.echo(f"\n  Max Par Capacity:    ${result.max_par_amount / 1e6:>10.1f}M")
    click.echo(f"  Recommended Par:     ${result.recommended_par / 1e6:>10.1f}M")
    click.echo(f"  Coupon Rate:         {result.coupon_rate:>10.2%}")
    click.echo(f"  Maturity:            {result.maturity_years:>10.0f} years")
    click.echo(f"  Annual Debt Service: ${result.annual_debt_service / 1e6:>10.2f}M")

    click.echo(f"\n{'-' * 80}")
    click.echo(f"  COVERAGE")
    click.echo(f"  Target DSCR:  {result.target_dscr:.2f}x")
    click.echo(f"  Min DSCR:     {result.min_dscr:.2f}x")
    click.echo(f"  Avg DSCR:     {result.avg_dscr:.2f}x")
    click.echo(f"  Cushion:      {result.dscr_cushion_pct:+.1f}%")

    click.echo(f"\n{'-' * 80}")
    click.echo(f"  SENSITIVITY")
    click.echo(f"  Par at 1.20x DSCR:  ${result.par_at_dscr_1_20 / 1e6:.1f}M")
    click.echo(f"  Par at 1.25x DSCR:  ${result.recommended_par / 1e6:.1f}M")
    click.echo(f"  Par at 1.30x DSCR:  ${result.par_at_dscr_1_30 / 1e6:.1f}M")
    click.echo(f"  Par at 1.40x DSCR:  ${result.par_at_dscr_1_40 / 1e6:.1f}M")
    click.echo(f"  Par at 1.50x DSCR:  ${result.par_at_dscr_1_50 / 1e6:.1f}M")

    click.echo(f"\n{'-' * 80}")
    click.echo(f"  SOURCES & USES")
    click.echo(f"  {'Sources':<30} {'Uses':<30}")
    click.echo(f"  {'Bond Proceeds':<25} ${result.recommended_par / 1e6:>8.1f}M  "
               f"{'Project Fund':<25} ${result.project_fund / 1e6:>8.1f}M")
    if equity:
        click.echo(f"  {'Equity':<25} ${equity / 1e6:>8.1f}M  ", nl=False)
    else:
        click.echo(f"  {'':<25} {'':>10}  ", nl=False)
    click.echo(f"{'DSRF':<25} ${result.debt_service_reserve / 1e6:>8.2f}M")
    click.echo(f"  {'':<25} {'':>10}  {'COI':<25} ${result.costs_of_issuance / 1e6:>8.2f}M")
    click.echo(f"  {'':<25} {'':>10}  {'UW Discount':<25} ${result.underwriter_discount / 1e6:>8.2f}M")

    if result.schedule:
        click.echo(f"\n{'-' * 80}")
        click.echo(f"  DEBT SERVICE SCHEDULE (first {len(result.schedule)} years)")
        click.echo(f"  {'Year':>6} {'Principal':>12} {'Interest':>12} {'Total DS':>12} {'Net Rev':>12} {'DSCR':>8}")
        click.echo(f"  {'-' * 66}")
        for yr in result.schedule:
            click.echo(
                f"  {yr.year:>6} ${yr.principal / 1e6:>10.2f}M ${yr.interest / 1e6:>10.2f}M "
                f"${yr.total / 1e6:>10.2f}M ${yr.net_revenue / 1e6:>10.2f}M {yr.dscr:>7.2f}x"
            )

    for note in result.sizing_notes:
        click.echo(f"\n  Note: {note}")

    # Generate report
    from .reports import generate_sizing_report
    md_path, json_path = generate_sizing_report(result, project_name)
    click.echo(f"\n  Report: {md_path}")
    click.echo(f"  Data:   {json_path}")
    click.echo("")


@cli.command()
@click.argument("project_file", type=click.Path(exists=True))
@click.option("--target-dscr", type=float, default=1.25)
def analyze(project_file: str, target_dscr: float) -> None:
    """Run full credit analysis pipeline from a JSON project file."""
    from datetime import datetime, timezone
    from .five_cs import assess_five_cs
    from .bond_sizing import size_bond
    from .financial_model import build_financial_model
    from .deal_structuring import structure_deal
    from .models import CreditAnalysisResult, ProjectInputs

    data = json.loads(Path(project_file).read_text(encoding="utf-8"))
    project = ProjectInputs(**data)

    click.echo(f"\nRunning full credit analysis for: {project.project_name}")
    click.echo("=" * 80)

    # 5 Cs
    click.echo("\n[1/5] 5 Cs Assessment...")
    five_cs = assess_five_cs(project)
    click.echo(f"  Composite: {five_cs.composite_score:.1f} ({five_cs.composite_grade}) — {five_cs.recommendation}")

    # Bond Sizing
    click.echo("[2/5] Bond Sizing...")
    sizing = size_bond(project, target_dscr=target_dscr)
    if sizing.recommended_par > 0:
        click.echo(f"  Recommended Par: ${sizing.recommended_par / 1e6:.1f}M at {sizing.min_dscr:.2f}x min DSCR")
    else:
        click.echo("  Insufficient data for sizing")

    # Financial Model
    click.echo("[3/5] 3-Statement Model...")
    fin_model = build_financial_model(project, sizing)
    if fin_model.cash_flows:
        min_dscr_model = min(cf.dscr for cf in fin_model.cash_flows)
        avg_dscr_model = sum(cf.dscr for cf in fin_model.cash_flows) / len(fin_model.cash_flows)
        click.echo(f"  {fin_model.projection_years}-year projection | Min DSCR: {min_dscr_model:.2f}x | Avg DSCR: {avg_dscr_model:.2f}x")

    # Deal Structuring
    click.echo("[4/5] Deal Structuring...")
    deal = structure_deal(project, five_cs, sizing)
    click.echo(f"  {deal.maturity_type} | {deal.covenants.minimum_coverage_ratio:.2f}x coverage | "
               f"Enhancement: {'Yes (' + deal.enhancement_type + ')' if deal.credit_enhancement_recommended else 'No'}")

    # Assemble result
    click.echo("[5/5] Assembling analysis...")
    result = CreditAnalysisResult(
        project_name=project.project_name,
        analysis_timestamp=datetime.now(timezone.utc),
        five_cs=five_cs,
        financial_model=fin_model,
        bond_sizing=sizing,
        deal_structure=deal,
    )

    # Credit opinion
    if five_cs.composite_score >= 70 and sizing.min_dscr >= 1.25:
        result.credit_opinion = "investment_grade"
    elif five_cs.composite_score >= 55:
        result.credit_opinion = "crossover"
    elif five_cs.composite_score >= 40:
        result.credit_opinion = "not_rated_adequate"
    else:
        result.credit_opinion = "not_rated_weak"

    # Standard Model integration (capstone)
    from .standard_model import integrate_standard_model
    result = integrate_standard_model(result, project)

    click.echo(f"  Credit Opinion: {result.credit_opinion.replace('_', ' ').upper()}")

    # Standard Model positioning
    if result.projected_f_score is not None:
        click.echo(f"\n{'-' * 80}")
        click.echo(f"  STANDARD MODEL POSITIONING")
        click.echo(f"{'-' * 80}")
        click.echo(f"  Fundamental Score (F_i): {result.projected_f_score:.1f}/100")
        if result.corpus_cri_percentile is not None:
            click.echo(f"  Corpus Percentile:       {result.corpus_cri_percentile:.0f}th (of EMMA waste sector)")
        if result.projected_s_omega is not None:
            click.echo(f"  Projected S_Omega:       {result.projected_s_omega:.4f} ({result.projected_s_omega*100:.2f}%)")
        if result.sic_efficiency is not None:
            click.echo(f"  SIC Efficiency:          {result.sic_efficiency:.4f}")

    # Executive summary
    if result.executive_summary:
        click.echo(f"\n{'-' * 80}")
        click.echo(f"  EXECUTIVE SUMMARY")
        click.echo(f"{'-' * 80}")
        # Word wrap
        import textwrap
        for line in textwrap.wrap(result.executive_summary, width=76):
            click.echo(f"  {line}")

    # Display deal structure summary
    click.echo(f"\n{'-' * 80}")
    click.echo(f"  DEAL STRUCTURE SUMMARY")
    click.echo(f"{'-' * 80}")
    click.echo(f"  Par: ${deal.par_amount / 1e6:.1f}M | Coupon: {deal.coupon_rate:.2%} | "
               f"Maturity: {deal.maturity_years:.0f}yr ({deal.maturity_type})")
    click.echo(f"  Coverage covenant: {deal.covenants.minimum_coverage_ratio:.2f}x | "
               f"ABT: {deal.covenants.additional_bonds_test_historical:.2f}x hist / "
               f"{deal.covenants.additional_bonds_test_projected:.2f}x proj")
    click.echo(f"  DSRF: {deal.covenants.dsrf_type} | O&M reserve: {deal.covenants.operating_reserve_months}mo")
    click.echo(f"  Security: {deal.security.pledge_type} | {deal.security.lien_position} lien")
    if deal.estimated_spread_bps:
        click.echo(f"  Estimated spread: {deal.estimated_spread_bps} bps over AAA MMD")
    if deal.comparable_deals:
        click.echo(f"  Comparables: {', '.join(deal.comparable_deals[:3])}")
    for note in deal.structuring_notes[:5]:
        click.echo(f"    - {note}")

    # Generate report
    from .reports import generate_full_analysis_report
    md_path, json_path = generate_full_analysis_report(result)
    click.echo(f"\n  Report: {md_path}")
    click.echo(f"  Data:   {json_path}")
    click.echo("")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
