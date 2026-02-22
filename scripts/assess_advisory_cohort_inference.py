"""
Assess advisory cohort inference behavior used by external package generation.

Usage:
    python scripts/assess_advisory_cohort_inference.py
    python scripts/assess_advisory_cohort_inference.py --output-dir reports/phase10_postlaunch
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from munipal.services.advisory_package_service import ExternalPackageService

TARGET_SECTORS = ("healthcare", "waste_to_energy")
TARGET_DEAL_TYPES = ("revenue", "conduit", "private_activity")


@dataclass
class _FactStub:
    value: Any


@dataclass
class _ProjectStub:
    name: str | None = None
    description: str | None = None
    issuer_name: str | None = None
    project_location: str | None = None
    target_bond_amount: float | None = None


@dataclass
class _Scenario:
    name: str
    expected: dict[str, Any]
    facts: dict[str, Any]
    project: _ProjectStub | None
    source_artifacts: list[str]


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


def _default_healthcare_profile_path() -> Path:
    return (
        _repo_root()
        / "emma"
        / "bond_os_extractor"
        / "data"
        / "healthcare"
        / "analysis"
        / "cchci_obligor_profile.json"
    )


def _default_waste_guide_path() -> Path:
    return (
        _repo_root()
        / "emma"
        / "bond_os_extractor"
        / "data"
        / "waste"
        / "analysis"
        / "risk_implementation_guide.json"
    )


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _safe_percent(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 2)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _as_fact_map(raw: dict[str, Any]) -> dict[str, _FactStub]:
    return {key: _FactStub(value=value) for key, value in raw.items()}


def _build_scenarios(
    *,
    healthcare_profile: dict[str, Any],
    waste_guide: dict[str, Any],
    healthcare_profile_path: Path,
    waste_guide_path: Path,
) -> list[_Scenario]:
    obligor = healthcare_profile.get("obligor", {})
    ida_loan = healthcare_profile.get("ida_loan", {})
    healthcare_desc = " ".join(
        part
        for part in (
            str(ida_loan.get("description", "")).strip(),
            str(obligor.get("sub_sector", "")).strip(),
            "community health clinic patient care expansion",
        )
        if part
    ).strip()

    waste_project_name = str(waste_guide.get("project_name", "GSI Caldor UCS")).strip()
    waste_sector = str(waste_guide.get("corpus_summary", {}).get("sector", "")).strip()

    return [
        _Scenario(
            name="healthcare_conduit_extractor_profile",
            expected={
                "sector": "healthcare",
                "deal_type": "conduit",
                "issuer_size_band": "small",
                "sample_size": 24,
                "recency_window": "5y",
            },
            facts={
                "project.canonicaldescription": healthcare_desc,
                "parties.issuer.name": str(ida_loan.get("lender", "")).strip(),
                "parties.borrower.name": str(ida_loan.get("borrower", "")).strip(),
                "cab.originalprincipial": ida_loan.get("principal", 250000),
            },
            project=None,
            source_artifacts=[healthcare_profile_path.as_posix()],
        ),
        _Scenario(
            name="healthcare_revenue_project_metadata",
            expected={
                "sector": "healthcare",
                "deal_type": "revenue",
                "issuer_size_band": "mid",
                "sample_size": 30,
                "recency_window": "5y",
            },
            facts={
                "project.canonicaldescription": "Regional hospital modernization and patient care capacity expansion.",
                "parties.issuer.name": "",
                "parties.borrower.name": "",
            },
            project=_ProjectStub(
                name="Regional Hospital Revenue Bonds",
                description="Healthcare infrastructure expansion project.",
                issuer_name="Cochise County Public Health Department",
                project_location="AZ",
                target_bond_amount=120_000_000,
            ),
            source_artifacts=[healthcare_profile_path.as_posix()],
        ),
        _Scenario(
            name="healthcare_private_activity_501c3",
            expected={
                "sector": "healthcare",
                "deal_type": "private_activity",
                "issuer_size_band": "mid",
                "sample_size": 24,
                "recency_window": "5y",
            },
            facts={
                "project.canonicaldescription": (
                    "Private activity bond financing for 501(c)(3) hospital system expansion."
                ),
                "parties.issuer.name": "Industrial Development Authority of Cochise County",
                "parties.borrower.name": "Nonprofit Hospital System",
                "cab.originalprincipial": 90_000_000,
            },
            project=None,
            source_artifacts=[healthcare_profile_path.as_posix()],
        ),
        _Scenario(
            name="waste_revenue_feedstock",
            expected={
                "sector": "waste_to_energy",
                "deal_type": "revenue",
                "issuer_size_band": "mid",
                "sample_size": 50,
                "recency_window": "5y",
            },
            facts={
                "project.canonicaldescription": (
                    f"{waste_project_name} revenue-backed facility with feedstock supply contracts."
                ),
                "feedstock.type": "forest biomass",
                "parties.issuer.name": "City of Caldor Solid Waste Utility",
                "cab.originalprincipial": 140_000_000,
            },
            project=_ProjectStub(
                name=waste_project_name or "GSI Caldor UCS",
                description=waste_sector or "waste management environmental services",
                issuer_name="City of Caldor Solid Waste Utility",
                project_location="CA",
                target_bond_amount=140_000_000,
            ),
            source_artifacts=[waste_guide_path.as_posix()],
        ),
        _Scenario(
            name="waste_conduit_ida_structure",
            expected={
                "sector": "waste_to_energy",
                "deal_type": "conduit",
                "issuer_size_band": "small",
                "sample_size": 35,
                "recency_window": "5y",
            },
            facts={
                "project.canonicaldescription": "Conduit bond financing for biomass conversion with feedstock agreements.",
                "feedstock.type": "forest biomass",
                "parties.issuer.name": "Industrial Development Authority of Caldor County",
                "parties.borrower.name": "Caldor Waste Energy LLC",
                "cab.originalprincipial": 45_000_000,
            },
            project=None,
            source_artifacts=[waste_guide_path.as_posix()],
        ),
        _Scenario(
            name="waste_private_activity_industrial_development",
            expected={
                "sector": "waste_to_energy",
                "deal_type": "private_activity",
                "issuer_size_band": "mid",
                "sample_size": 30,
                "recency_window": "5y",
            },
            facts={
                "project.canonicaldescription": (
                    "Industrial development bond private activity financing for waste-to-energy expansion."
                ),
                "feedstock.type": "forest biomass",
                "parties.issuer.name": "Caldor County Industrial Development Board",
                "parties.borrower.name": "Caldor Bioenergy LLC",
                "cab.originalprincipial": 85_000_000,
            },
            project=None,
            source_artifacts=[waste_guide_path.as_posix()],
        ),
    ]


def _target_matrix_template() -> dict[str, dict[str, int]]:
    return {
        sector: dict.fromkeys(TARGET_DEAL_TYPES, 0)
        for sector in TARGET_SECTORS
    }


def _write_markdown(path: Path, payload: dict[str, Any]) -> None:
    summary = payload["summary"]
    recommendation = payload["recommendation"]
    lines = [
        "# Advisory Cohort Inference Assessment",
        "",
        f"- Generated (UTC): `{payload['generated_at_utc']}`",
        f"- Recommendation: `{recommendation['status']}`",
        "",
        "## Summary",
        "",
        f"- Scenarios evaluated: `{summary['scenarios_evaluated']}`",
        f"- Scenarios passed: `{summary['scenarios_passed']}`",
        f"- Scenarios failed: `{summary['scenarios_failed']}`",
        f"- Match rate: `{summary['match_rate_pct']}%`",
        f"- Target combos covered: `{summary['covered_target_combo_count']}/{summary['target_combo_count']}`",
        "",
        "## Scenario Results",
        "",
        "| Scenario | Expected Sector | Expected Deal Type | Inferred Sector | Inferred Deal Type | Status |",
        "|---|---|---|---|---|---|",
    ]

    for scenario in payload["scenarios"]:
        inferred = scenario["inferred"]
        expected = scenario["expected"]
        status = "pass" if scenario["status"] == "pass" else "fail"
        lines.append(
            f"| {scenario['name']} | {expected['sector']} | {expected['deal_type']} | "
            f"{inferred.get('sector', '<missing>')} | {inferred.get('deal_type', '<missing>')} | {status} |"
        )

    lines.extend(
        [
            "",
            "## Coverage Matrix (Expected Profiles)",
            "",
            "| Sector | Revenue | Conduit | Private Activity |",
            "|---|---:|---:|---:|",
        ]
    )
    for sector, row in payload["expected_coverage_matrix"].items():
        lines.append(
            f"| {sector} | {row['revenue']} | {row['conduit']} | {row['private_activity']} |"
        )

    lines.extend(["", "## Recommendation Notes", ""])
    if recommendation["reasons"]:
        for reason in recommendation["reasons"]:
            lines.append(f"- {reason}")
    else:
        lines.append("- No blocking issues detected.")

    if payload["source_artifacts"]["missing"]:
        lines.extend(["", "## Missing Source Artifacts", ""])
        for item in payload["source_artifacts"]["missing"]:
            lines.append(f"- `{item}`")

    path.write_text("\n".join(lines), encoding="utf-8")


def assess_advisory_cohort_inference(
    *,
    output_dir: Path,
    healthcare_profile_path: Path,
    waste_guide_path: Path,
) -> AssessmentResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    reasons: list[str] = []

    healthcare_profile: dict[str, Any] = {}
    waste_guide: dict[str, Any] = {}
    missing_artifacts: list[str] = []
    for path, dest in (
        (healthcare_profile_path, "healthcare"),
        (waste_guide_path, "waste"),
    ):
        if not path.exists():
            missing_artifacts.append(path.as_posix())
            reasons.append(f"Source artifact missing: {path.as_posix()}.")
            continue
        try:
            loaded = _load_json(path)
        except Exception as exc:  # noqa: BLE001
            reasons.append(f"Unable to parse source artifact {path.as_posix()}: {exc}.")
            loaded = {}
        if dest == "healthcare":
            healthcare_profile = loaded
        else:
            waste_guide = loaded

    scenarios = _build_scenarios(
        healthcare_profile=healthcare_profile,
        waste_guide=waste_guide,
        healthcare_profile_path=healthcare_profile_path,
        waste_guide_path=waste_guide_path,
    )
    service = ExternalPackageService(session=None)  # type: ignore[arg-type]

    expected_coverage = _target_matrix_template()
    inferred_coverage = _target_matrix_template()
    scenario_rows: list[dict[str, Any]] = []

    pass_count = 0
    for scenario in scenarios:
        fact_map = _as_fact_map(scenario.facts)
        inferred = service._infer_risk_benchmark_cohort_values(  # noqa: SLF001
            project=scenario.project,
            facts=fact_map,
        )

        expected_sector = str(scenario.expected["sector"])
        expected_deal_type = str(scenario.expected["deal_type"])
        if expected_sector in expected_coverage and expected_deal_type in expected_coverage[expected_sector]:
            expected_coverage[expected_sector][expected_deal_type] += 1

        inferred_sector = str(inferred.get("sector", ""))
        inferred_deal = str(inferred.get("deal_type", ""))
        if inferred_sector in inferred_coverage and inferred_deal in inferred_coverage[inferred_sector]:
            inferred_coverage[inferred_sector][inferred_deal] += 1

        checks = {
            key: inferred.get(key) == expected_value
            for key, expected_value in scenario.expected.items()
        }
        status = "pass" if all(checks.values()) else "fail"
        if status == "pass":
            pass_count += 1
        else:
            mismatch_keys = [key for key, ok in checks.items() if not ok]
            reasons.append(
                f"{scenario.name}: inferred cohort mismatch for {', '.join(mismatch_keys)}."
            )

        scenario_rows.append(
            {
                "name": scenario.name,
                "expected": scenario.expected,
                "inferred": inferred,
                "checks": checks,
                "status": status,
                "source_artifacts": scenario.source_artifacts,
            }
        )

    target_combo_count = len(TARGET_SECTORS) * len(TARGET_DEAL_TYPES)
    covered_target_combo_count = sum(
        1
        for sector in TARGET_SECTORS
        for deal_type in TARGET_DEAL_TYPES
        if expected_coverage[sector][deal_type] > 0
    )
    if covered_target_combo_count < target_combo_count:
        reasons.append(
            f"Target combo coverage incomplete: {covered_target_combo_count}/{target_combo_count}."
        )

    scenario_count = len(scenarios)
    fail_count = max(0, scenario_count - pass_count)
    recommendation = "go" if fail_count == 0 and not missing_artifacts else "no-go"

    payload: dict[str, Any] = {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "target_profiles": {
            "sectors": list(TARGET_SECTORS),
            "deal_types": list(TARGET_DEAL_TYPES),
        },
        "source_artifacts": {
            "healthcare_profile": healthcare_profile_path.as_posix(),
            "waste_implementation_guide": waste_guide_path.as_posix(),
            "missing": missing_artifacts,
        },
        "summary": {
            "scenarios_evaluated": scenario_count,
            "scenarios_passed": pass_count,
            "scenarios_failed": fail_count,
            "match_rate_pct": _safe_percent(pass_count, scenario_count),
            "target_combo_count": target_combo_count,
            "covered_target_combo_count": covered_target_combo_count,
        },
        "expected_coverage_matrix": expected_coverage,
        "inferred_coverage_matrix": inferred_coverage,
        "scenarios": scenario_rows,
        "recommendation": {
            "status": recommendation,
            "reasons": reasons,
        },
    }

    stamp = _timestamp()
    report_json_path = output_dir / f"advisory_cohort_inference_{stamp}.json"
    report_md_path = output_dir / f"advisory_cohort_inference_{stamp}.md"
    report_json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_markdown(report_md_path, payload)

    return AssessmentResult(
        report_json_path=report_json_path,
        report_md_path=report_md_path,
        recommendation=recommendation,
        reasons=reasons,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess advisory package cohort inference behavior across target profiles."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_default_output_dir(),
        help="Output directory for advisory cohort inference artifacts.",
    )
    parser.add_argument(
        "--healthcare-profile-path",
        type=Path,
        default=_default_healthcare_profile_path(),
        help="Path to healthcare obligor profile JSON source.",
    )
    parser.add_argument(
        "--waste-guide-path",
        type=Path,
        default=_default_waste_guide_path(),
        help="Path to waste implementation guide JSON source.",
    )
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    result = assess_advisory_cohort_inference(
        output_dir=args.output_dir.resolve(),
        healthcare_profile_path=args.healthcare_profile_path.resolve(),
        waste_guide_path=args.waste_guide_path.resolve(),
    )
    print(f"[advisory-cohort-inference] recommendation={result.recommendation}")
    print(f"[advisory-cohort-inference] markdown={result.report_md_path.as_posix()}")
    print(f"[advisory-cohort-inference] json={result.report_json_path.as_posix()}")
    if result.reasons:
        print("[advisory-cohort-inference] notes:")
        for reason in result.reasons:
            print(f"- {reason}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
