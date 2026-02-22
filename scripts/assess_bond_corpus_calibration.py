"""
Assess bond corpus calibration readiness across sectors and bond types.

Usage:
    python scripts/assess_bond_corpus_calibration.py
    python scripts/assess_bond_corpus_calibration.py --sectors waste healthcare --output-dir reports/phase10_postlaunch
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

RISK_DIMENSIONS = (
    "risk.technology",
    "risk.construction",
    "risk.market",
    "risk.regulatory",
    "risk.feedstock",
)

DEFAULT_RISK_CATEGORY_TO_DIMENSION: dict[str, str] = {
    "technology": "risk.technology",
    "cybersecurity": "risk.technology",
    "construction": "risk.construction",
    "labor": "risk.construction",
    "force_majeure": "risk.construction",
    "insurance": "risk.construction",
    "market_demand": "risk.market",
    "competition": "risk.market",
    "financial": "risk.market",
    "interest_rate": "risk.market",
    "litigation": "risk.market",
    "regulatory": "risk.regulatory",
    "environmental": "risk.regulatory",
    "tax_law": "risk.regulatory",
    "political": "risk.regulatory",
    "permitting": "risk.regulatory",
    "climate": "risk.regulatory",
    "feedstock_supply": "risk.feedstock",
    "management": "risk.feedstock",
}

BOND_COHORTS = ("revenue", "conduit", "private_activity")

SECTOR_CATEGORY_OVERRIDES: dict[str, dict[str, str]] = {
    # Avoid routing healthcare management factors into waste-specific feedstock mapping.
    "healthcare": {
        "management": "risk.market",
    },
}


@dataclass
class AssessmentResult:
    report_json_path: Path
    report_md_path: Path
    recommendation: str
    reasons: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_output_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _default_sector_db_map() -> dict[str, Path]:
    root = _repo_root() / "emma" / "bond_os_extractor" / "data"
    return {
        "waste": root / "waste" / "corpus.db",
        "healthcare": root / "healthcare" / "corpus.db",
    }


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _safe_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


def _sample_reliability_score(*, exposure_count: int) -> float:
    if exposure_count >= 50:
        return 1.0
    if exposure_count >= 20:
        return 0.75
    return 0.4


def _normalize_bond_cohort(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if not raw:
        return "unknown"
    if "conduit" in raw:
        return "conduit"
    if "private_activity" in raw or "industrial_development" in raw:
        return "private_activity"
    if "revenue" in raw:
        return "revenue"
    return "other"


def _truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "y", "mitigated", "described"}


def _dimension_for_category(*, category: str, sector: str) -> str | None:
    category_key = category.strip().lower()
    if not category_key:
        return None
    sector_key = sector.strip().lower()
    if sector_key in SECTOR_CATEGORY_OVERRIDES:
        override = SECTOR_CATEGORY_OVERRIDES[sector_key]
        if category_key in override:
            return override[category_key]
    return DEFAULT_RISK_CATEGORY_TO_DIMENSION.get(category_key)


def _open_sqlite(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _table_count(conn: sqlite3.Connection, table: str) -> int:
    cur = conn.execute(f"SELECT COUNT(*) AS count FROM {table}")
    return int(cur.fetchone()["count"])


def _distinct_counts_by_col(
    conn: sqlite3.Connection,
    *,
    table: str,
    col: str,
) -> dict[str, int]:
    rows = conn.execute(
        f"""
        SELECT COALESCE({col}, '<null>') AS key, COUNT(*) AS count
        FROM {table}
        GROUP BY key
        ORDER BY count DESC
        """
    ).fetchall()
    return {str(row["key"]): int(row["count"]) for row in rows}


def _sector_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {
        "documents": _table_count(conn, "documents"),
        "deal_structures": _table_count(conn, "deal_structures"),
        "deal_identities": _table_count(conn, "deal_identities"),
        "risk_factors": _table_count(conn, "risk_factors"),
        "security_packages": _table_count(conn, "security_packages"),
        "financial_reports": _table_count(conn, "financial_reports"),
        "rating_actions": _table_count(conn, "rating_actions"),
    }

    bond_type_counts_raw = _distinct_counts_by_col(
        conn,
        table="deal_structures",
        col="bond_type",
    )
    bond_cohort_counts: dict[str, int] = {}
    for bond_type, count in bond_type_counts_raw.items():
        cohort = _normalize_bond_cohort(bond_type if bond_type != "<null>" else None)
        bond_cohort_counts[cohort] = bond_cohort_counts.get(cohort, 0) + int(count)

    class_primary_counts = _distinct_counts_by_col(
        conn,
        table="classifications",
        col="primary_type",
    )
    issuer_type_counts = _distinct_counts_by_col(
        conn,
        table="deal_identities",
        col="issuer_type",
    )

    return {
        "counts": counts,
        "bond_type_counts": bond_type_counts_raw,
        "bond_cohort_counts": bond_cohort_counts,
        "classification_primary_counts": class_primary_counts,
        "issuer_type_counts": issuer_type_counts,
    }


def _dimension_rollup(
    conn: sqlite3.Connection,
    *,
    sector: str,
    bond_cohort_filter: str | None,
) -> dict[str, dict[str, Any]]:
    where_clause = ""
    params: tuple[Any, ...] = ()
    if bond_cohort_filter:
        if bond_cohort_filter == "revenue":
            where_clause = "WHERE lower(COALESCE(ds.bond_type, '')) LIKE ?"
            params = ("%revenue%",)
        elif bond_cohort_filter == "conduit":
            where_clause = "WHERE lower(COALESCE(ds.bond_type, '')) LIKE ?"
            params = ("%conduit%",)
        elif bond_cohort_filter == "private_activity":
            where_clause = (
                "WHERE lower(COALESCE(ds.bond_type, '')) LIKE ? "
                "OR lower(COALESCE(ds.bond_type, '')) LIKE ?"
            )
            params = ("%private_activity%", "%industrial_development%")

    rows = conn.execute(
        f"""
        SELECT
            rf.category AS category,
            rf.document_id AS document_id,
            rf.mitigation_described AS mitigation_described
        FROM risk_factors rf
        LEFT JOIN deal_structures ds ON ds.document_id = rf.document_id
        {where_clause}
        """,
        params,
    ).fetchall()

    rollup: dict[str, dict[str, Any]] = {
        dim: {
            "exposure_count": 0,
            "mitigant_count": 0,
            "distinct_documents": set(),
            "unmapped_category_count": 0,
        }
        for dim in RISK_DIMENSIONS
    }
    unmapped_total = 0

    for row in rows:
        category = str(row["category"] or "").strip().lower()
        dimension = _dimension_for_category(category=category, sector=sector)
        if not dimension:
            unmapped_total += 1
            continue

        slot = rollup[dimension]
        slot["exposure_count"] += 1
        if _truthy_flag(row["mitigation_described"]):
            slot["mitigant_count"] += 1
        document_id = str(row["document_id"] or "").strip()
        if document_id:
            slot["distinct_documents"].add(document_id)

    output: dict[str, dict[str, Any]] = {}
    for dimension, values in rollup.items():
        distinct_documents = len(values["distinct_documents"])
        exposure_count = int(values["exposure_count"])
        mitigant_count = int(values["mitigant_count"])
        uncovered_exposure_count = max(0, exposure_count - mitigant_count)
        mitigation_coverage_ratio = _safe_ratio(mitigant_count, exposure_count)
        conflict_rate_proxy = _safe_ratio(uncovered_exposure_count, exposure_count)
        sample_reliability_score = _sample_reliability_score(exposure_count=exposure_count)
        dimension_posture_score = round(
            (int(exposure_count > 0 and mitigant_count > 0) * 0.40)
            + (mitigation_coverage_ratio * 0.35)
            + (sample_reliability_score * 0.25),
            4,
        )
        output[dimension] = {
            "exposure_count": exposure_count,
            "mitigant_count": mitigant_count,
            "uncovered_exposure_count": uncovered_exposure_count,
            "mitigation_coverage_ratio": mitigation_coverage_ratio,
            "conflict_rate_proxy": conflict_rate_proxy,
            "dimension_posture_score_proxy": dimension_posture_score,
            "distinct_documents": distinct_documents,
            "pair_complete": int(exposure_count > 0 and mitigant_count > 0),
            "meets_cdr1_medium": int(exposure_count >= 20),
            "meets_cdr1_high": int(exposure_count >= 50),
            "meets_cdr4_source_diversity": int(distinct_documents >= 2),
        }

    posture_scores = [float(output[dim]["dimension_posture_score_proxy"]) for dim in RISK_DIMENSIONS]
    conflict_rates = [float(output[dim]["conflict_rate_proxy"]) for dim in RISK_DIMENSIONS]
    output["_meta"] = {
        "rows_considered": len(rows),
        "unmapped_category_count": unmapped_total,
        "overall_posture_score_proxy": round(sum(posture_scores) / len(posture_scores), 4),
        "conflict_rate_proxy_avg": round(sum(conflict_rates) / len(conflict_rates), 4),
        "conflict_rate_proxy_max": round(max(conflict_rates), 4),
    }
    return output


def _cohort_dimension_assessment(
    conn: sqlite3.Connection,
    *,
    sector: str,
) -> dict[str, Any]:
    cohorts = {
        "all": _dimension_rollup(conn, sector=sector, bond_cohort_filter=None),
    }
    for cohort in BOND_COHORTS:
        cohorts[cohort] = _dimension_rollup(conn, sector=sector, bond_cohort_filter=cohort)

    cdr3_status: dict[str, dict[str, Any]] = {}
    for cohort_name, rollup in cohorts.items():
        pair_complete_count = sum(rollup[dim]["pair_complete"] for dim in RISK_DIMENSIONS)
        medium_count = sum(rollup[dim]["meets_cdr1_medium"] for dim in RISK_DIMENSIONS)
        cdr3_status[cohort_name] = {
            "dimensions_with_pair_complete": pair_complete_count,
            "dimensions_at_medium_plus": medium_count,
            "meets_cdr3_minimum_dimensions": int(pair_complete_count == 5),
            "meets_cdr3_full_mode_dimensions": int(medium_count == 5),
        }

    return {
        "dimension_rollup": cohorts,
        "cdr3_status": cdr3_status,
    }


def _recency_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = conn.execute(
        """
        SELECT extraction_timestamp
        FROM documents
        WHERE extraction_timestamp IS NOT NULL
        """
    ).fetchall()
    now = datetime.now(UTC)
    ages_days: list[int] = []
    parse_errors = 0
    for row in rows:
        raw = str(row["extraction_timestamp"] or "").strip()
        if not raw:
            continue
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            age_days = max(0, int((now - parsed.astimezone(UTC)).days))
            ages_days.append(age_days)
        except Exception:  # noqa: BLE001
            parse_errors += 1

    total = len(ages_days)
    stale_180 = sum(1 for age in ages_days if age > 180)
    stale_365 = sum(1 for age in ages_days if age > 365)
    return {
        "timestamp_rows": len(rows),
        "parsed_rows": total,
        "parse_errors": parse_errors,
        "stale_ratio_180_pct": _safe_percent(stale_180, total),
        "stale_ratio_365_pct": _safe_percent(stale_365, total),
    }


def _assess_sector(*, sector: str, db_path: Path) -> dict[str, Any]:
    if not db_path.exists():
        return {
            "sector": sector,
            "db_path": str(db_path),
            "status": "missing_db",
            "reason": "Corpus database file not found.",
        }

    with _open_sqlite(db_path) as conn:
        summary = _sector_summary(conn)
        cohort_assessment = _cohort_dimension_assessment(conn, sector=sector)
        recency = _recency_summary(conn)

    return {
        "sector": sector,
        "db_path": str(db_path),
        "status": "ok",
        "summary": summary,
        "cohort_assessment": cohort_assessment,
        "recency": recency,
    }


def _recommendation(payload: dict[str, Any]) -> tuple[str, list[str]]:
    reasons: list[str] = []
    sectors = payload["sectors"]

    for sector_name, sector_data in sectors.items():
        if sector_data.get("status") != "ok":
            reasons.append(f"{sector_name}: corpus DB missing or unreadable.")
            continue

        all_cdr3 = sector_data["cohort_assessment"]["cdr3_status"]["all"]
        if not all_cdr3["meets_cdr3_minimum_dimensions"]:
            reasons.append(
                f"{sector_name}: CDR-3 minimum not met in all-cohort rollup "
                f"({all_cdr3['dimensions_with_pair_complete']}/5 dimensions pair-complete)."
            )

        revenue_cohort_rows = sector_data["cohort_assessment"]["dimension_rollup"]["revenue"]["_meta"][
            "rows_considered"
        ]
        if revenue_cohort_rows == 0:
            reasons.append(f"{sector_name}: no revenue-cohort risk factor rows available for calibration.")

        recency = sector_data["recency"]
        if recency["parsed_rows"] == 0:
            reasons.append(f"{sector_name}: no parseable extraction timestamps for recency checks.")

    return ("go" if not reasons else "no-go"), reasons


def _write_markdown_report(*, report_path: Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Bond Corpus Calibration Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Recommendation: `{payload['recommendation']['status']}`",
        "",
        "## Sector Summary",
        "",
        "| Sector | Documents | Risk Factors | Security Packages | Financial Reports | Rating Actions |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for sector_name, sector_data in payload["sectors"].items():
        if sector_data.get("status") != "ok":
            lines.append(f"| {sector_name} | - | - | - | - | - |")
            continue
        counts = sector_data["summary"]["counts"]
        lines.append(
            f"| {sector_name} | {counts['documents']} | {counts['risk_factors']} | "
            f"{counts['security_packages']} | {counts['financial_reports']} | {counts['rating_actions']} |"
        )

    lines.extend(["", "## CDR-3 Rollup (All Cohorts)", "", "| Sector | Pair-Complete Dims | MEDIUM+ Dims | Meets CDR-3 Min | Meets Full-Mode |", "|---|---:|---:|---:|---:|"])
    for sector_name, sector_data in payload["sectors"].items():
        if sector_data.get("status") != "ok":
            lines.append(f"| {sector_name} | 0 | 0 | 0 | 0 |")
            continue
        cdr3 = sector_data["cohort_assessment"]["cdr3_status"]["all"]
        lines.append(
            f"| {sector_name} | {cdr3['dimensions_with_pair_complete']} | "
            f"{cdr3['dimensions_at_medium_plus']} | {cdr3['meets_cdr3_minimum_dimensions']} | "
            f"{cdr3['meets_cdr3_full_mode_dimensions']} |"
        )

    lines.extend(
        [
            "",
            "## CDR-5 Proxy Baseline (All Cohorts)",
            "",
            "| Sector | Posture Score Proxy | Conflict Proxy Avg | Conflict Proxy Max |",
            "|---|---:|---:|---:|",
        ]
    )
    for sector_name, sector_data in payload["sectors"].items():
        if sector_data.get("status") != "ok":
            lines.append(f"| {sector_name} | - | - | - |")
            continue
        meta = sector_data["cohort_assessment"]["dimension_rollup"]["all"]["_meta"]
        lines.append(
            f"| {sector_name} | {meta.get('overall_posture_score_proxy', 0.0)} | "
            f"{meta.get('conflict_rate_proxy_avg', 0.0)} | {meta.get('conflict_rate_proxy_max', 0.0)} |"
        )

    lines.extend(["", "## Revenue / Conduit / Private Activity Coverage", ""])
    for sector_name, sector_data in payload["sectors"].items():
        lines.append(f"### {sector_name}")
        if sector_data.get("status") != "ok":
            lines.append("- Corpus DB missing; no cohort coverage available.")
            lines.append("")
            continue
        cohort_counts = sector_data["summary"]["bond_cohort_counts"]
        lines.append(
            f"- Revenue rows: `{cohort_counts.get('revenue', 0)}`"
        )
        lines.append(
            f"- Conduit rows: `{cohort_counts.get('conduit', 0)}`"
        )
        lines.append(
            f"- Private activity rows: `{cohort_counts.get('private_activity', 0)}`"
        )
        lines.append(
            f"- Other/unknown rows: `{cohort_counts.get('other', 0) + cohort_counts.get('unknown', 0)}`"
        )
        recency = sector_data["recency"]
        lines.append(
            f"- Recency stale >180d: `{recency['stale_ratio_180_pct']}%`; stale >365d: `{recency['stale_ratio_365_pct']}%`"
        )
        lines.append("")

    lines.extend(["## Recommendation Notes", ""])
    reasons = payload["recommendation"]["reasons"]
    if reasons:
        for reason in reasons:
            lines.append(f"- {reason}")
    else:
        lines.append("- No blocking issues detected by automated calibration checks.")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def assess_bond_corpus_calibration(
    *,
    sectors: list[str],
    output_dir: Path,
) -> AssessmentResult:
    sector_db_map = _default_sector_db_map()
    output_dir.mkdir(parents=True, exist_ok=True)

    sector_payload: dict[str, Any] = {}
    for sector in sectors:
        db_path = sector_db_map.get(sector)
        if db_path is None:
            sector_payload[sector] = {
                "sector": sector,
                "status": "unsupported_sector",
                "reason": "No default corpus DB mapping for sector.",
            }
            continue
        sector_payload[sector] = _assess_sector(sector=sector, db_path=db_path)

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "sectors": sector_payload,
    }
    recommendation, reasons = _recommendation(payload)
    payload["recommendation"] = {
        "status": recommendation,
        "reasons": reasons,
    }

    stamp = _timestamp()
    report_json_path = output_dir / f"bond_corpus_calibration_{stamp}.json"
    report_md_path = output_dir / f"bond_corpus_calibration_{stamp}.md"
    report_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown_report(report_path=report_md_path, payload=payload)

    return AssessmentResult(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        recommendation=recommendation,
        reasons=reasons,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Assess bond corpus calibration readiness across sectors."
    )
    parser.add_argument(
        "--sectors",
        nargs="+",
        default=["waste", "healthcare"],
        help="Sectors to assess (default: waste healthcare).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Output report directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = assess_bond_corpus_calibration(
        sectors=args.sectors,
        output_dir=args.output_dir,
    )
    print(f"[bond-corpus-calibration] recommendation={result.recommendation}")
    print(f"[bond-corpus-calibration] markdown={result.report_md_path.as_posix()}")
    print(f"[bond-corpus-calibration] json={result.report_json_path.as_posix()}")
    if result.reasons:
        print("[bond-corpus-calibration] reasons:")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
