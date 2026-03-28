"""Run combined Credit Analysis + Bank Match for a project."""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from munipal.engines.bank_analyzer.ingest import load_all_banks
from munipal.engines.bank_analyzer.scoring import score_all_banks
from munipal.engines.bank_analyzer.matching import match_banks_to_deal
from munipal.engines.bank_analyzer.models import DealMatchRequest
from munipal.engines.bank_analyzer.reports import generate_match_report
from munipal.engines.credit_analyzer.five_cs import assess_five_cs
from munipal.engines.credit_analyzer.bond_sizing import size_bond
from munipal.engines.credit_analyzer.financial_model import build_financial_model
from munipal.engines.credit_analyzer.deal_structuring import structure_deal
from munipal.engines.credit_analyzer.standard_model import integrate_standard_model
from munipal.engines.credit_analyzer.models import CreditAnalysisResult, ProjectInputs
from munipal.engines.credit_analyzer.reports import generate_full_analysis_report

TOUCAN_DIR = Path(r"C:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\TOUCAN")
REPORT_DIR = Path("reports/combined")


def run(project_file: str) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    # Load inputs
    project = ProjectInputs(**json.loads(Path(project_file).read_text(encoding="utf-8")))
    banks = load_all_banks(TOUCAN_DIR)
    scorecards = score_all_banks(banks)

    # --- Credit Analysis Pipeline ---
    five_cs = assess_five_cs(project)
    sizing = size_bond(project)
    fin_model = build_financial_model(project, sizing)
    deal_struct = structure_deal(project, five_cs, sizing)

    opinion = "investment_grade"
    if five_cs.composite_score < 70 or sizing.min_dscr < 1.25:
        opinion = "crossover" if five_cs.composite_score >= 55 else "not_rated_adequate"

    result = CreditAnalysisResult(
        project_name=project.project_name,
        analysis_timestamp=datetime.now(timezone.utc),
        five_cs=five_cs,
        bond_sizing=sizing,
        financial_model=fin_model,
        deal_structure=deal_struct,
        credit_opinion=opinion,
    )
    result = integrate_standard_model(result, project)

    # --- Bank Matching ---
    deal_req = DealMatchRequest(
        deal_type="project_finance",
        deal_size=sizing.recommended_par,
        state=project.state,
        sector=project.sector,
        needs_credit_enhancement=deal_struct.credit_enhancement_recommended,
        enhancement_type=deal_struct.enhancement_type,
        is_green=project.is_green,
        is_carbon_credit=False,
        bank_qualified=False,
    )
    match_result = match_banks_to_deal(scorecards, deal_req, top_n=10)

    # --- Console Output ---
    print("=" * 90)
    print(f"  COMBINED DEAL ANALYSIS + BANK MATCH: {project.project_name}")
    print("=" * 90)

    print(f"\n  CREDIT ANALYSIS")
    print(f"  " + "-" * 50)
    rec = five_cs.recommendation.replace("_", " ").title()
    print(f"  5 Cs:     {five_cs.composite_score:.1f}/100 ({five_cs.composite_grade}) -- {rec}")
    print(f"  Par:      ${sizing.recommended_par/1e6:.0f}M @ {sizing.coupon_rate:.2%}, {sizing.maturity_years:.0f}yr")
    print(f"  DSCR:     {sizing.min_dscr:.2f}x min / {sizing.avg_dscr:.2f}x avg")
    if result.projected_f_score is not None:
        print(f"  F_i:      {result.projected_f_score:.1f} ({result.corpus_cri_percentile:.0f}th percentile)")
    if result.projected_s_omega is not None:
        print(f"  S_Omega:  {result.projected_s_omega*100:.2f}%")
    print(f"  Opinion:  {result.credit_opinion.replace('_', ' ').upper()}")

    print(f"\n  DEAL STRUCTURE")
    print(f"  " + "-" * 50)
    print(f"  {deal_struct.maturity_type} | {deal_struct.bond_type} | {deal_struct.tax_status}")
    print(f"  Coverage: {deal_struct.covenants.minimum_coverage_ratio:.2f}x | "
          f"ABT: {deal_struct.covenants.additional_bonds_test_historical:.2f}x")
    if deal_struct.estimated_spread_bps:
        print(f"  Spread:   {deal_struct.estimated_spread_bps:.0f} bps over AAA MMD")
    enh = (f"Yes ({deal_struct.enhancement_type})"
           if deal_struct.credit_enhancement_recommended else "Not required")
    print(f"  Enhancement: {enh}")

    print(f"\n  MATCHED BANKS")
    print(f"  " + "-" * 50)
    print(f"  Screened: {match_result.total_banks_screened} | Matches: {len(match_result.matches)}")
    print()
    for i, m in enumerate(match_result.matches, 1):
        a = f"${m.total_assets/1e9:.0f}B" if m.total_assets >= 1e9 else f"${m.total_assets/1e6:.0f}M"
        role = (m.recommended_role or "").replace("_", " ").title()
        print(f"  {i:>2}. [{m.match_score:>5.1f}] {m.bank_name[:40]:<42} {a:>8}  {role}")
        for reason in m.match_reasons[:2]:
            print(f"              + {reason}")

    # --- Generate Reports ---
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    cr_md, cr_json = generate_full_analysis_report(result, REPORT_DIR)
    bm_md, bm_json = generate_match_report(match_result, REPORT_DIR)

    # Combined MD
    lines = [
        f"# Combined Deal Analysis + Bank Match",
        f"",
        f"**Project:** {project.project_name}",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"",
        f"## Credit Analysis Summary",
        f"",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| 5 Cs Score | {five_cs.composite_score:.1f}/100 ({five_cs.composite_grade}) |",
        f"| Recommendation | {rec} |",
        f"| Bond Par | ${sizing.recommended_par/1e6:.1f}M |",
        f"| Coupon | {sizing.coupon_rate:.2%} |",
        f"| Maturity | {sizing.maturity_years:.0f} years |",
        f"| Min DSCR | {sizing.min_dscr:.2f}x |",
    ]
    if result.projected_f_score is not None:
        lines.append(f"| F_i Score | {result.projected_f_score:.1f} ({result.corpus_cri_percentile:.0f}th pctile) |")
    if result.projected_s_omega is not None:
        lines.append(f"| S_Omega | {result.projected_s_omega*100:.2f}% |")
    lines.extend([
        f"| Credit Opinion | **{result.credit_opinion.replace('_', ' ').title()}** |",
        f"| Spread | {deal_struct.estimated_spread_bps:.0f} bps over AAA MMD |" if deal_struct.estimated_spread_bps else "",
        f"",
        f"## Deal Structure",
        f"",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Bond Type | {deal_struct.bond_type.replace('_', ' ').title()} |",
        f"| Maturity Type | {deal_struct.maturity_type.replace('_', ' ').title()} |",
        f"| Coverage Covenant | {deal_struct.covenants.minimum_coverage_ratio:.2f}x |",
        f"| ABT | {deal_struct.covenants.additional_bonds_test_historical:.2f}x hist / {deal_struct.covenants.additional_bonds_test_projected:.2f}x proj |",
        f"| DSRF | {deal_struct.covenants.dsrf_type} |",
        f"| Security | {deal_struct.security.pledge_type}, {deal_struct.security.lien_position} lien |",
        f"| Enhancement | {enh} |",
        f"",
        f"## Bank Matches",
        f"",
        f"Banks screened: {match_result.total_banks_screened} | "
        f"Deal: {deal_req.deal_type} ${deal_req.deal_size/1e6:.0f}M "
        f"{deal_req.state or ''} {'Green' if deal_req.is_green else ''}",
        f"",
        f"| Rank | Score | Bank | Assets | Role | Key Strengths |",
        f"|-----:|------:|------|-------:|------|---------------|",
    ])
    for i, m in enumerate(match_result.matches, 1):
        a = f"${m.total_assets/1e9:.0f}B" if m.total_assets >= 1e9 else f"${m.total_assets/1e6:.0f}M"
        role = (m.recommended_role or "").replace("_", " ").title()
        strengths = "; ".join(m.match_reasons[:2]) if m.match_reasons else "-"
        lines.append(f"| {i} | {m.match_score:.1f} | {m.bank_name[:35]} | {a} | {role} | {strengths} |")

    if result.executive_summary:
        lines.extend([
            f"",
            f"## Executive Summary",
            f"",
            result.executive_summary,
        ])

    lines.extend([
        f"",
        f"---",
        f"*Generated by Muni-Pal Engine 1 (Bank Analyzer) + Engine 2 (Credit Analyzer) v0.1.0*",
    ])

    combined_path = REPORT_DIR / f"combined_{ts}.md"
    combined_path.write_text("\n".join(lines), encoding="utf-8")

    # Combined JSON
    combined_json_path = REPORT_DIR / f"combined_{ts}.json"
    combined_data = {
        "project": project.model_dump(mode="json"),
        "credit_analysis": result.model_dump(mode="json"),
        "bank_matches": match_result.model_dump(mode="json"),
    }
    combined_json_path.write_text(json.dumps(combined_data, indent=2, default=str), encoding="utf-8")

    print(f"\n  REPORTS")
    print(f"  " + "-" * 50)
    print(f"  Credit:   {cr_md}")
    print(f"  Bank:     {bm_md}")
    print(f"  Combined: {combined_path}")
    print(f"  Data:     {combined_json_path}")
    print()


if __name__ == "__main__":
    project_file = sys.argv[1] if len(sys.argv) > 1 else "reports/credit_analyzer/sample_project.json"
    run(project_file)
