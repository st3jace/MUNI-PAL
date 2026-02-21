"""
Assess EMMA healthcare corpus readiness and write report artifacts.

Usage:
    python scripts/assess_healthcare_corpus_readiness.py
    python scripts/assess_healthcare_corpus_readiness.py --dataset-dir <path> --output-dir <path>
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REQUIRED_TOP_LEVEL_FIELDS = ("cusip", "crawl_metadata", "snapshot")
REQUIRED_SNAPSHOT_FIELDS = ("security_name", "principal_amount", "maturity_date", "state")
EXTRACTION_COMPONENTS = ("snapshot", "interest_rate", "trade_activity", "ratings", "disclosures")


@dataclass
class AssessmentResult:
    report_json_path: Path
    report_md_path: Path
    recommendation: str
    reasons: list[str]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _default_dataset_dir() -> Path:
    return _repo_root() / "emma" / "emma_crawler" / "output" / "healthcare" / "data"


def _default_output_dir() -> Path:
    return _repo_root() / "reports" / "phase10_postlaunch"


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _is_populated(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, dict, tuple, set)):
        return len(value) > 0
    return True


def _safe_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _write_markdown_report(
    *,
    report_path: Path,
    payload: dict[str, Any],
) -> None:
    summary = payload["summary"]
    recommendation = payload["recommendation"]

    lines = [
        "# Healthcare Corpus Readiness Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Dataset: `{payload['dataset_dir']}`",
        f"- Recommendation: `{recommendation['status']}`",
        "",
        "## Summary",
        "",
        f"- Files discovered: `{summary['files_discovered']}`",
        f"- Files parsed: `{summary['files_parsed']}`",
        f"- Parse errors: `{summary['parse_errors']}`",
        f"- Parse success rate: `{summary['parse_success_rate_pct']}%`",
        f"- Unique CUSIPs: `{summary['unique_cusips']}`",
        f"- Duplicate CUSIPs: `{summary['duplicate_cusips']}`",
        "",
        "## Field Coverage",
        "",
        "| Field | Coverage (%) | Present / Parsed |",
        "|---|---:|---:|",
    ]

    for field_name, stats in payload["coverage"]["top_level"].items():
        lines.append(
            f"| top_level.{field_name} | {stats['coverage_pct']} | {stats['present_count']} / {summary['files_parsed']} |"
        )
    for field_name, stats in payload["coverage"]["snapshot"].items():
        lines.append(
            f"| snapshot.{field_name} | {stats['coverage_pct']} | {stats['present_count']} / {summary['files_parsed']} |"
        )

    lines.extend(
        [
            "",
            "## Extraction Status Counts",
            "",
            "| Component | Success | Other | Missing |",
            "|---|---:|---:|---:|",
        ]
    )
    for component, counts in payload["extraction_status_counts"].items():
        success = counts.get("success", 0)
        other = sum(v for k, v in counts.items() if k not in {"success", "missing"})
        missing = counts.get("missing", 0)
        lines.append(f"| {component} | {success} | {other} | {missing} |")

    lines.extend(
        [
            "",
            "## Recommendation Notes",
            "",
        ]
    )
    if recommendation["reasons"]:
        for reason in recommendation["reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No blocking issues detected by automated readiness checks.")

    if payload["parse_error_samples"]:
        lines.extend(["", "## Parse Error Samples", ""])
        for entry in payload["parse_error_samples"]:
            lines.append(f"- `{entry['file']}`: {entry['error']}")

    report_path.write_text("\n".join(lines), encoding="utf-8")


def assess_healthcare_corpus(
    *,
    dataset_dir: Path,
    output_dir: Path,
    max_error_samples: int,
) -> AssessmentResult:
    output_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(dataset_dir.glob("*.json")) if dataset_dir.exists() else []
    parse_error_samples: list[dict[str, str]] = []

    top_level_present = Counter()
    snapshot_present = Counter()
    extraction_status_counts: dict[str, Counter[str]] = defaultdict(Counter)
    cusips: list[str] = []

    files_parsed = 0
    parse_errors = 0

    for file_path in files:
        try:
            content = json.loads(file_path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            parse_errors += 1
            if len(parse_error_samples) < max_error_samples:
                parse_error_samples.append({"file": file_path.name, "error": str(exc)})
            continue

        files_parsed += 1
        if _is_populated(content.get("cusip")):
            cusips.append(str(content["cusip"]).strip())

        for field in REQUIRED_TOP_LEVEL_FIELDS:
            if _is_populated(content.get(field)):
                top_level_present[field] += 1

        snapshot = content.get("snapshot")
        if isinstance(snapshot, dict):
            for field in REQUIRED_SNAPSHOT_FIELDS:
                if _is_populated(snapshot.get(field)):
                    snapshot_present[field] += 1

        crawl_metadata = content.get("crawl_metadata")
        status_map = (
            crawl_metadata.get("extraction_status")
            if isinstance(crawl_metadata, dict)
            else None
        )
        for component in EXTRACTION_COMPONENTS:
            if isinstance(status_map, dict) and _is_populated(status_map.get(component)):
                extraction_status_counts[component][str(status_map[component]).strip().lower()] += 1
            else:
                extraction_status_counts[component]["missing"] += 1

    files_discovered = len(files)
    unique_cusips = len(set(cusips))
    duplicate_cusips = max(0, len(cusips) - unique_cusips)
    parse_success_rate_pct = _safe_percent(files_parsed, files_discovered)

    top_level_coverage = {
        field: {
            "present_count": top_level_present[field],
            "coverage_pct": _safe_percent(top_level_present[field], files_parsed),
        }
        for field in REQUIRED_TOP_LEVEL_FIELDS
    }
    snapshot_coverage = {
        field: {
            "present_count": snapshot_present[field],
            "coverage_pct": _safe_percent(snapshot_present[field], files_parsed),
        }
        for field in REQUIRED_SNAPSHOT_FIELDS
    }

    reasons: list[str] = []
    if files_discovered == 0:
        reasons.append("No healthcare corpus files found in dataset directory.")
    if parse_success_rate_pct < 95.0:
        reasons.append(f"Parse success rate below threshold: {parse_success_rate_pct}% (<95%).")
    if snapshot_coverage["security_name"]["coverage_pct"] < 95.0:
        reasons.append("Snapshot security_name coverage below threshold (95%).")
    if snapshot_coverage["principal_amount"]["coverage_pct"] < 85.0:
        reasons.append("Snapshot principal_amount coverage below threshold (85%).")

    recommendation = "go" if not reasons else "no-go"

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "dataset_dir": str(dataset_dir),
        "summary": {
            "files_discovered": files_discovered,
            "files_parsed": files_parsed,
            "parse_errors": parse_errors,
            "parse_success_rate_pct": parse_success_rate_pct,
            "unique_cusips": unique_cusips,
            "duplicate_cusips": duplicate_cusips,
        },
        "coverage": {
            "top_level": top_level_coverage,
            "snapshot": snapshot_coverage,
        },
        "extraction_status_counts": {
            component: dict(extraction_status_counts[component]) for component in EXTRACTION_COMPONENTS
        },
        "recommendation": {
            "status": recommendation,
            "reasons": reasons,
        },
        "parse_error_samples": parse_error_samples,
    }

    stamp = _timestamp()
    report_json_path = output_dir / f"healthcare_readiness_{stamp}.json"
    report_md_path = output_dir / f"healthcare_readiness_{stamp}.md"
    report_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown_report(report_path=report_md_path, payload=payload)

    return AssessmentResult(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        recommendation=recommendation,
        reasons=reasons,
    )


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assess healthcare corpus readiness.")
    parser.add_argument(
        "--dataset-dir",
        type=Path,
        default=_default_dataset_dir(),
        help="Path to healthcare JSON corpus directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Path to output report directory.",
    )
    parser.add_argument(
        "--max-error-samples",
        type=int,
        default=20,
        help="Max parse error samples to include in report.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    result = assess_healthcare_corpus(
        dataset_dir=args.dataset_dir,
        output_dir=args.output_dir,
        max_error_samples=args.max_error_samples,
    )
    print(f"[healthcare-readiness] recommendation={result.recommendation}")
    print(
        "[healthcare-readiness] markdown="
        f"{result.report_md_path.as_posix()}"
    )
    print(
        "[healthcare-readiness] json="
        f"{result.report_json_path.as_posix()}"
    )
    if result.reasons:
        print("[healthcare-readiness] reasons:")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
