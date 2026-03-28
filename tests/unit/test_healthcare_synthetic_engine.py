from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from synth.healthcare_engine import (
    EnginePaths,
    benchmark_project,
    build_healthcare_synthetic_engine,
    export_plotting_tables,
)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _build_fixture_dirs(tmp_path: Path) -> EnginePaths:
    corpus_dir = tmp_path / "corpus"
    analysis_dir = tmp_path / "analysis"
    db_path = tmp_path / "healthcare_corpus.db"

    _write_text(
        corpus_dir / "healthcare_financial_benchmarks.json",
        json.dumps(
            {
                "metadata": {"title": "fixture-healthcare-benchmarks"},
                "cross_sector_benchmark_summary": {
                    "dscr_by_rating": {
                        "aa": {"benchmark": 1.35},
                        "a": {"benchmark": 1.20},
                        "bbb": {"benchmark": 1.10},
                    },
                    "days_cash_by_rating": {
                        "aa": {"benchmark": 80},
                        "a": {"benchmark": 60},
                        "bbb": {"benchmark": 45},
                    },
                    "debt_to_cap_by_rating": {
                        "aa": {"benchmark": "42.5%"},
                        "a": {"benchmark": "55%"},
                        "bbb": {"benchmark": "67.5%"},
                    },
                },
                "hospital_revenue_bonds": {
                    "a_a": {
                        "benchmarks": {
                            "operating_margin": {"benchmark": "4%"},
                        }
                    }
                },
            }
        ),
    )
    _write_text(
        corpus_dir / "healthcare_credit_drivers.json",
        json.dumps({"metadata": {"title": "fixture-healthcare-credit-drivers"}}),
    )

    _write_text(
        analysis_dir / "pareto_paths.txt",
        "file_a.pdf\nfile_b.pdf\nfile_c.pdf\n",
    )
    _write_text(
        analysis_dir / "pareto_batch_log.txt",
        (
            "Pareto 4% batch: 3 PDFs queued (AI enrichment ON)\n"
            "PARETO BATCH COMPLETE: 3 succeeded, 0 failed out of 3\n"
            "By module:\n"
            "  official_statement: 1 succeeded, 0 failed\n"
            "  rating_action: 1 succeeded, 0 failed\n"
            "  financial_report: 1 succeeded, 0 failed\n"
        ),
    )
    _write_text(
        analysis_dir / "cchci_obligor_profile.json",
        json.dumps(
            {
                "financials": {
                    "fy2023": {
                        "total_revenue": 1000000,
                        "operating_income": 35000,
                        "total_assets": 500000,
                        "total_liabilities": 250000,
                    },
                    "ratios": {
                        "operating_margin_fy2023": 0.035,
                        "leverage_fy2023": 1.2,
                    },
                }
            }
        ),
    )

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE financial_reports (
            completeness_score REAL,
            fiscal_year INTEGER,
            total_revenue REAL,
            operating_income REAL,
            total_debt_outstanding REAL,
            total_equity REAL,
            total_liabilities REAL,
            total_assets REAL,
            debt_service_coverage_ratio REAL,
            days_cash_on_hand REAL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE rating_actions (
            agency TEXT,
            action_type TEXT,
            new_rating TEXT,
            new_outlook TEXT,
            sector TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE security_packages (
            pledge_type TEXT,
            lien_position TEXT,
            min_coverage_ratio REAL,
            dsrf_type TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE documents (
            id TEXT,
            primary_classification TEXT
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE risk_factors (
            category TEXT,
            severity_implied TEXT,
            mitigation_described INTEGER,
            document_id TEXT
        )
        """
    )

    cur.executemany(
        """
        INSERT INTO financial_reports VALUES (?,?,?,?,?,?,?,?,?,?)
        """,
        [
            (1.0, 2024, 2000000, 70000, 800000, 900000, 1100000, 2000000, 1.34, 85.0),
            (1.0, 2025, 2200000, 88000, 820000, 920000, 1200000, 2100000, 1.38, 90.0),
            (0.9, 2025, 1800000, 54000, 760000, 840000, 1050000, 1850000, 1.25, 72.0),
        ],
    )
    cur.executemany(
        """
        INSERT INTO rating_actions VALUES (?,?,?,?,?)
        """,
        [
            ("moodys", "affirm", "A2", "stable", "healthcare"),
            ("fitch", "upgrade", "A", "positive", "healthcare"),
        ],
    )
    cur.executemany(
        """
        INSERT INTO security_packages VALUES (?,?,?,?)
        """,
        [
            ("gross_revenue", "first", 1.10, "fixed_amount"),
            ("specific_revenue", "pari_passu", 1.15, "fixed_amount"),
        ],
    )
    cur.executemany(
        """
        INSERT INTO documents VALUES (?,?)
        """,
        [
            ("doc-1", "REVENUE_HEALTHCARE"),
            ("doc-2", "CONDUIT_501C3"),
        ],
    )
    cur.executemany(
        """
        INSERT INTO risk_factors VALUES (?,?,?,?)
        """,
        [
            ("regulatory", "material", 1, "doc-1"),
            ("financial", "significant", 0, "doc-1"),
            ("market_demand", "material", 1, "doc-2"),
        ],
    )

    conn.commit()
    conn.close()

    return EnginePaths(
        corpus_dir=corpus_dir,
        corpus_db_path=db_path,
        pareto_analysis_dir=analysis_dir,
    )


def _drop_generated_at(payload: dict) -> dict:
    out = json.loads(json.dumps(payload))
    out["metadata"].pop("generated_at_utc", None)
    return out


def test_build_healthcare_synthetic_engine_is_deterministic(tmp_path: Path) -> None:
    paths = _build_fixture_dirs(tmp_path)

    payload1 = build_healthcare_synthetic_engine(paths=paths, start_year=2020, end_year=2028, seed=11)
    payload2 = build_healthcare_synthetic_engine(paths=paths, start_year=2020, end_year=2028, seed=11)

    assert _drop_generated_at(payload1) == _drop_generated_at(payload2)
    assert payload1["benchmark_indices"][0]["index_id"] == "munipal.healthcare.composite"
    assert len(payload1["synthetic_track_records"]) == 12
    assert len(payload1["chart_packets"]) >= 3


def test_export_plotting_tables_writes_expected_files(tmp_path: Path) -> None:
    paths = _build_fixture_dirs(tmp_path)
    payload = build_healthcare_synthetic_engine(paths=paths, start_year=2022, end_year=2026, seed=7)

    output_dir = tmp_path / "exports"
    files = export_plotting_tables(payload, output_dir)
    names = {path.name for path in files}

    assert "benchmark_index_series.csv" in names
    assert "synthetic_track_records.csv" in names
    assert (output_dir / "benchmark_index_series.csv").exists()
    assert (output_dir / "synthetic_track_records.csv").exists()


def test_benchmark_project_positions_against_latest_benchmark() -> None:
    base_series = [
        {"year": 2024, "composite_index": 62.0},
        {"year": 2025, "composite_index": 63.0},
    ]

    project_input = {
        "project_id": "h1",
        "metrics": {
            "dscr": 1.55,
            "operating_margin_pct": 0.07,
            "debt_to_capitalization": 0.40,
            "days_cash_on_hand": 110.0,
            "structural_index": 76.0,
            "risk_mitigation_index": 74.0,
        },
    }
    result = benchmark_project(project_input=project_input, benchmark_base_series=base_series)
    assert result["benchmark_position"] == "above"
