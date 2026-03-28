from __future__ import annotations

import json
from pathlib import Path

from synth.waste_engine import (
    EnginePaths,
    benchmark_project,
    build_waste_synthetic_engine,
    export_plotting_tables,
)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_fixture_dirs(tmp_path: Path) -> EnginePaths:
    corpus_dir = tmp_path / "corpus"
    sub_dir = tmp_path / "sub_agent"

    _write_text(
        corpus_dir / "waste_financial_benchmarks.json",
        json.dumps({"metadata": {"title": "fixture-benchmarks"}}),
    )
    _write_text(
        corpus_dir / "waste_credit_drivers.json",
        json.dumps({"metadata": {"title": "fixture-credit-drivers"}}),
    )
    _write_text(
        sub_dir / "wte_financial_data.csv",
        (
            "issuer_name,fiscal_year,total_revenue,operating_income,debt_service_coverage_ratio,total_debt_outstanding\n"
            "A,2024,1000000,120000,1.34,900000\n"
            "A,2025,1050000,126000,1.36,905000\n"
            "B,2025,800000,64000,1.21,910000\n"
        ),
    )
    _write_text(
        sub_dir / "wte_deals_data.csv",
        (
            "document_id,pledge_type,credit_quality\n"
            "1,specific_revenue,INVESTMENT_GRADE_MID\n"
            "2,net_revenue,NON_RATED\n"
        ),
    )
    _write_text(
        sub_dir / "wte_risk_factors.csv",
        (
            "category,title,severity_implied,frequency\n"
            "market_demand,A,material,2\n"
            "feedstock_supply,B,significant,1\n"
        ),
    )
    return EnginePaths(corpus_dir=corpus_dir, sub_agent_dir=sub_dir)


def _drop_generated_at(payload: dict) -> dict:
    out = json.loads(json.dumps(payload))
    out["metadata"].pop("generated_at_utc", None)
    return out


def test_build_waste_synthetic_engine_is_deterministic(tmp_path: Path) -> None:
    paths = _build_fixture_dirs(tmp_path)

    payload1 = build_waste_synthetic_engine(paths=paths, start_year=2020, end_year=2028, seed=11)
    payload2 = build_waste_synthetic_engine(paths=paths, start_year=2020, end_year=2028, seed=11)

    assert _drop_generated_at(payload1) == _drop_generated_at(payload2)
    assert payload1["benchmark_indices"][0]["index_id"] == "munipal.waste.composite"
    assert len(payload1["synthetic_track_records"]) == 12
    assert len(payload1["chart_packets"]) >= 3


def test_export_plotting_tables_writes_expected_files(tmp_path: Path) -> None:
    paths = _build_fixture_dirs(tmp_path)
    payload = build_waste_synthetic_engine(paths=paths, start_year=2022, end_year=2026, seed=7)

    output_dir = tmp_path / "exports"
    files = export_plotting_tables(payload, output_dir)
    names = {path.name for path in files}

    assert "benchmark_index_series.csv" in names
    assert "synthetic_track_records.csv" in names
    assert (output_dir / "benchmark_index_series.csv").exists()
    assert (output_dir / "synthetic_track_records.csv").exists()


def test_benchmark_project_positions_against_latest_benchmark() -> None:
    base_series = [
        {"year": 2024, "composite_index": 60.0},
        {"year": 2025, "composite_index": 61.0},
    ]

    project_input = {
        "project_id": "p1",
        "metrics": {
            "dscr": 1.60,
            "operating_margin_pct": 0.20,
            "debt_to_revenue": 0.80,
            "structural_index": 75.0,
            "risk_mitigation_index": 75.0,
        },
    }
    result = benchmark_project(project_input=project_input, benchmark_base_series=base_series)
    assert result["benchmark_position"] == "above"
