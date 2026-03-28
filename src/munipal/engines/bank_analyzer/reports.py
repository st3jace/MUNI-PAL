"""Bank Analyzer report generation — produces Markdown reports from scoring results."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from .models import BankScorecard, DealMatchResult

logger = logging.getLogger("bank_analyzer.reports")

DEFAULT_REPORT_DIR = Path("reports/bank_analyzer")


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")


def _assets_str(val: float) -> str:
    if val >= 1e12:
        return f"${val / 1e12:.1f}T"
    if val >= 1e9:
        return f"${val / 1e9:.1f}B"
    if val >= 1e6:
        return f"${val / 1e6:.0f}M"
    return f"${val:,.0f}"


# ---------------------------------------------------------------------------
# Full Scoreboard Report
# ---------------------------------------------------------------------------

def generate_scoreboard_report(
    scorecards: list[BankScorecard],
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Generate full scoreboard report (MD + JSON)."""
    out = _ensure_dir(output_dir or DEFAULT_REPORT_DIR)
    ts = _ts()

    # --- Markdown ---
    lines = [
        f"# Bank Analyzer Scoreboard",
        f"",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Banks Scored:** {len(scorecards)}",
        f"",
    ]

    # PCA distribution
    pca_dist: dict[str, int] = {}
    for sc in scorecards:
        pca_dist[sc.pca_category] = pca_dist.get(sc.pca_category, 0) + 1
    lines.append("## Capital Health (PCA Distribution)")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|------:|")
    for cat, cnt in sorted(pca_dist.items(), key=lambda x: -x[1]):
        lines.append(f"| {cat.replace('_', ' ').title()} | {cnt} |")
    lines.append("")

    # Tier distribution
    tier_dist: dict[str, int] = {}
    for sc in scorecards:
        tier_dist[sc.asset_tier] = tier_dist.get(sc.asset_tier, 0) + 1
    lines.append("## Asset Size Distribution")
    lines.append("")
    lines.append("| Tier | Count |")
    lines.append("|------|------:|")
    for tier, cnt in sorted(tier_dist.items(), key=lambda x: -x[1]):
        lines.append(f"| {tier.replace('_', ' ').title()} | {cnt} |")
    lines.append("")

    # Top 25 composite
    lines.append("## Top 25 Banks by Composite Score")
    lines.append("")
    lines.append("| Rank | Bank | State | Assets | PCA | CRE | CE | DP | GF | Composite |")
    lines.append("|-----:|------|-------|-------:|-----|----:|---:|---:|---:|----------:|")
    for sc in scorecards[:25]:
        pca_short = sc.pca_category.split("_")[0].title()
        lines.append(
            f"| {sc.ranking} | {sc.bank_name[:35]} | {sc.state or ''} | "
            f"{_assets_str(sc.total_assets)} | {pca_short} | "
            f"{sc.cre_distress.score:.0f} | {sc.credit_enhancement.score:.0f} | "
            f"{sc.direct_purchase.score:.0f} | {sc.green_finance.score:.0f} | "
            f"**{sc.composite_score:.1f}** |"
        )
    lines.append("")

    # CRE Distress top 15
    cre_sorted = sorted(scorecards, key=lambda s: -s.cre_distress.score)
    cre_distressed = [s for s in cre_sorted if s.cre_distress.score >= 15]
    lines.append("## CRE Distress Analysis — Workout Advisory Targets")
    lines.append("")
    lines.append(f"Banks with distress score >= 15: **{len(cre_distressed)}**")
    lines.append("")
    if cre_distressed:
        lines.append("| Bank | State | Assets | Score | Opportunity | CRE NPL | CRE Conc | REO | Distressed Segments |")
        lines.append("|------|-------|-------:|------:|-------------|--------:|---------:|----:|---------------------|")
        for sc in cre_distressed[:20]:
            cre = sc.cre_distress
            reo_str = _assets_str(cre.total_reo) if cre.total_reo > 0 else "-"
            segs = ", ".join(s.replace("_", " ") for s in cre.distress_segments) or "-"
            lines.append(
                f"| {sc.bank_name[:30]} | {sc.state or ''} | {_assets_str(sc.total_assets)} | "
                f"**{cre.score:.0f}** | {cre.opportunity_type.replace('_', ' ')} | "
                f"{cre.cre_npl_ratio:.2%} | {cre.cre_concentration_pct:.1f}% | "
                f"{reo_str} | {segs} |"
            )
        lines.append("")

    # Credit Enhancement top 15
    ce_sorted = sorted(scorecards, key=lambda s: -s.credit_enhancement.score)
    lines.append("## Credit Enhancement Capacity — Top Providers")
    lines.append("")
    lines.append("| Bank | State | Assets | Score | PCA | Excess Cap | Types | Max Est |")
    lines.append("|------|-------|-------:|------:|-----|----------:|-------|--------:|")
    for sc in ce_sorted[:15]:
        ce = sc.credit_enhancement
        types = ", ".join(ce.enhancement_types) or "-"
        max_est = _assets_str(ce.max_enhancement_estimate) if ce.max_enhancement_estimate > 0 else "-"
        lines.append(
            f"| {sc.bank_name[:30]} | {sc.state or ''} | {_assets_str(sc.total_assets)} | "
            f"**{ce.score:.0f}** | {ce.pca_category.split('_')[0].title()} | "
            f"{ce.excess_capital_pct:.1f}% | {types} | {max_est} |"
        )
    lines.append("")

    # Direct Purchase top 15
    dp_sorted = sorted(scorecards, key=lambda s: -s.direct_purchase.score)
    lines.append("## Direct Purchase Appetite — Top Bond Buyers")
    lines.append("")
    lines.append("| Bank | State | Assets | Score | BQ Eligible | Tax Position | Signals |")
    lines.append("|------|-------|-------:|------:|:-----------:|:------------:|---------|")
    for sc in dp_sorted[:15]:
        dp = sc.direct_purchase
        bq = "Yes" if dp.bank_qualified_eligible else "No"
        sigs = "; ".join(dp.municipal_appetite_signals[:2]) or "-"
        lines.append(
            f"| {sc.bank_name[:30]} | {sc.state or ''} | {_assets_str(sc.total_assets)} | "
            f"**{dp.score:.0f}** | {bq} | {dp.tax_position_indicator or '-'} | {sigs} |"
        )
    lines.append("")

    # Green Finance
    gf_sorted = sorted(scorecards, key=lambda s: -s.green_finance.score)
    green_active = [s for s in gf_sorted if s.green_finance.score >= 40]
    lines.append("## Green Finance & Carbon Credit Capability")
    lines.append("")
    lines.append(f"Banks with green score >= 40: **{len(green_active)}**")
    lines.append("")
    if green_active:
        lines.append("| Bank | State | Assets | Score | ESG Level | Carbon Deals | Volume | Types |")
        lines.append("|------|-------|-------:|------:|-----------|:------------:|-------:|-------|")
        for sc in green_active[:15]:
            gf = sc.green_finance
            vol = _assets_str(gf.carbon_deal_volume) if gf.carbon_deal_volume > 0 else "-"
            types = ", ".join(gf.carbon_deal_types[:3]) or "-"
            carbon = "Yes" if gf.has_carbon_deals else "No"
            lines.append(
                f"| {sc.bank_name[:30]} | {sc.state or ''} | {_assets_str(sc.total_assets)} | "
                f"**{gf.score:.0f}** | {gf.esg_commitment_level} | {carbon} | {vol} | {types} |"
            )
    lines.append("")

    # Key findings
    lines.append("## Key Findings")
    lines.append("")
    lines.append(f"- **{len(scorecards)}** banks scored across 4 dimensions")
    lines.append(f"- **{pca_dist.get('well_capitalized', 0)}** well-capitalized ({pca_dist.get('well_capitalized', 0)/len(scorecards)*100:.0f}%)")
    lines.append(f"- **{len(cre_distressed)}** banks with elevated CRE distress (score >= 15)")
    lines.append(f"- **{len(green_active)}** banks with green finance capability (score >= 40)")
    top3 = scorecards[:3]
    lines.append(f"- Top composite: {', '.join(f'{s.bank_name} ({s.composite_score:.1f})' for s in top3)}")
    lines.append("")
    lines.append("---")
    lines.append(f"*Generated by Muni-Pal Bank Analyzer v0.1.0*")

    md_path = out / f"bank_scoreboard_{ts}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    json_path = out / f"bank_scoreboard_{ts}.json"
    json_data = [sc.model_dump(mode="json") for sc in scorecards]
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding="utf-8")

    logger.info("Scoreboard report: %s", md_path)
    return md_path, json_path


# ---------------------------------------------------------------------------
# Deal Match Report
# ---------------------------------------------------------------------------

def generate_match_report(
    result: DealMatchResult,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Generate deal match report (MD + JSON)."""
    out = _ensure_dir(output_dir or DEFAULT_REPORT_DIR)
    ts = _ts()
    deal = result.deal

    deal_size_str = _assets_str(deal.deal_size)
    deal_desc = f"{deal.deal_type.replace('_', ' ').title()} | {deal_size_str}"
    if deal.state:
        deal_desc += f" | {deal.state}"
    flags = []
    if deal.is_green:
        flags.append("Green")
    if deal.is_carbon_credit:
        flags.append("Carbon Credit")
    if deal.needs_credit_enhancement:
        flags.append(f"Enhancement: {deal.enhancement_type or 'any'}")
    if deal.bank_qualified:
        flags.append("Bank-Qualified")
    if flags:
        deal_desc += f" | {', '.join(flags)}"

    lines = [
        f"# Bank-Deal Match Report",
        f"",
        f"**Deal:** {deal_desc}",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Banks Screened:** {result.total_banks_screened}",
        f"**Matches Found:** {len(result.matches)}",
        f"",
        f"## Deal Parameters",
        f"",
        f"| Parameter | Value |",
        f"|-----------|-------|",
        f"| Deal Type | {deal.deal_type.replace('_', ' ').title()} |",
        f"| Deal Size | {deal_size_str} |",
        f"| State | {deal.state or 'Any'} |",
        f"| Sector | {deal.sector or 'Any'} |",
        f"| Green Bond | {'Yes' if deal.is_green else 'No'} |",
        f"| Carbon Credit | {'Yes' if deal.is_carbon_credit else 'No'} |",
        f"| Credit Enhancement | {'Yes' if deal.needs_credit_enhancement else 'No'} |",
        f"| Bank-Qualified | {'Yes' if deal.bank_qualified else 'No'} |",
        f"",
        f"## Matched Banks",
        f"",
    ]

    if not result.matches:
        lines.append("*No matching banks found for this deal profile.*")
    else:
        for i, m in enumerate(result.matches, 1):
            lines.append(f"### {i}. {m.bank_name}")
            lines.append(f"")
            lines.append(f"| | |")
            lines.append(f"|---|---|")
            lines.append(f"| **Match Score** | **{m.match_score:.1f}/100** |")
            lines.append(f"| State | {m.state or '-'} |")
            lines.append(f"| Total Assets | {_assets_str(m.total_assets)} |")
            lines.append(f"| Recommended Role | {(m.recommended_role or '').replace('_', ' ').title()} |")
            lines.append(f"")

            if m.match_reasons:
                lines.append("**Strengths:**")
                for reason in m.match_reasons:
                    lines.append(f"- {reason}")
                lines.append("")

            if m.concerns:
                lines.append("**Concerns:**")
                for concern in m.concerns:
                    lines.append(f"- {concern}")
                lines.append("")

    lines.append("---")
    lines.append(f"*Generated by Muni-Pal Bank Analyzer v0.1.0*")

    deal_type_slug = deal.deal_type.replace("_", "-")
    md_path = out / f"match_{deal_type_slug}_{ts}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    json_path = out / f"match_{deal_type_slug}_{ts}.json"
    json_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

    logger.info("Match report: %s", md_path)
    return md_path, json_path


# ---------------------------------------------------------------------------
# Distress Report
# ---------------------------------------------------------------------------

def generate_distress_report(
    scorecards: list[BankScorecard],
    threshold: float = 15.0,
    output_dir: Path | None = None,
) -> tuple[Path, Path]:
    """Generate CRE distress / workout advisory report (MD + JSON)."""
    out = _ensure_dir(output_dir or DEFAULT_REPORT_DIR)
    ts = _ts()

    distressed = sorted(
        [sc for sc in scorecards if sc.cre_distress.score >= threshold],
        key=lambda s: -s.cre_distress.score,
    )

    lines = [
        f"# CRE Distress Report — Workout Advisory Opportunities",
        f"",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"**Threshold:** Distress score >= {threshold}",
        f"**Banks Flagged:** {len(distressed)} of {len(scorecards)}",
        f"",
        f"## Summary",
        f"",
    ]

    # Group by opportunity type
    by_opp: dict[str, list] = {}
    for sc in distressed:
        opp = sc.cre_distress.opportunity_type
        by_opp.setdefault(opp, []).append(sc)

    for opp in ["workout_advisory", "credit_restructuring", "asset_acquisition"]:
        banks = by_opp.get(opp, [])
        if banks:
            lines.append(f"### {opp.replace('_', ' ').title()} ({len(banks)} banks)")
            lines.append(f"")

            for sc in banks:
                cre = sc.cre_distress
                lines.append(f"#### {sc.bank_name}")
                lines.append(f"")
                lines.append(f"- **Location:** {sc.state or '-'} | **Assets:** {_assets_str(sc.total_assets)}")
                lines.append(f"- **Distress Score:** {cre.score:.0f}/100")
                lines.append(f"- **CRE NPL Ratio:** {cre.cre_npl_ratio:.2%}")
                lines.append(f"- **CRE Concentration:** {cre.cre_concentration_pct:.1f}% of total assets")
                if cre.total_reo > 0:
                    lines.append(f"- **REO (Foreclosed Assets):** {_assets_str(cre.total_reo)} ({cre.reo_to_assets_pct:.2f}% of assets)")
                if cre.distress_segments:
                    lines.append(f"- **Distressed Segments:** {', '.join(s.replace('_', ' ').title() for s in cre.distress_segments)}")
                lines.append(f"- **Non-Owner CRE NPL:** {cre.commercial_non_owner_npl:.2%} | **Multifamily NPL:** {cre.multifamily_npl:.2%} | **Construction NPL:** {cre.construction_npl:.2%}")
                lines.append(f"")

    if not distressed:
        lines.append("*No banks above distress threshold.*")
        lines.append("")

    lines.append("---")
    lines.append(f"*Generated by Muni-Pal Bank Analyzer v0.1.0*")

    md_path = out / f"cre_distress_{ts}.md"
    md_path.write_text("\n".join(lines), encoding="utf-8")

    json_path = out / f"cre_distress_{ts}.json"
    json_data = [
        {
            "bank_name": sc.bank_name,
            "state": sc.state,
            "total_assets": sc.total_assets,
            **sc.cre_distress.model_dump(mode="json"),
        }
        for sc in distressed
    ]
    json_path.write_text(json.dumps(json_data, indent=2, default=str), encoding="utf-8")

    logger.info("Distress report: %s", md_path)
    return md_path, json_path
