from __future__ import annotations

import csv
import json
import random
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

def _load_json(path: Path) -> dict[str, Any]:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}

def _write_csv(path: Path, rows: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = sorted({key for row in rows for key in row.keys()})
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path

def _load_project_input(path: Path | None) -> dict[str, Any] | None:
    if path is None or not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class EnginePaths:
    corpus_dir: Path
    corpus_db_path: Path | None = None
    pareto_analysis_dir: Path | None = None

def default_engine_paths() -> EnginePaths:
    return EnginePaths(
        corpus_dir=REPO_ROOT / "research" / "healthcare",
        corpus_db_path=REPO_ROOT / "research" / "healthcare" / "healthcare_corpus.db",
        pareto_analysis_dir=REPO_ROOT / "reports" / "healthcare",
    )

def load_project_input(path: Path | None) -> dict[str, Any] | None:
    return _load_project_input(path)

def _db_financial_count(path: Path | None) -> int:
    if path is None or not path.exists():
        return 0
    import sqlite3
    conn=sqlite3.connect(path)
    try:
        cur=conn.cursor(); cur.execute("select count(*) from financial_reports"); return int(cur.fetchone()[0])
    except sqlite3.Error:
        return 0
    finally:
        conn.close()

def build_healthcare_synthetic_engine(*, paths: EnginePaths, start_year: int, end_year: int, seed: int, project_input: dict[str, Any] | None = None) -> dict[str, Any]:
    rng=random.Random(seed)
    benchmarks=_load_json(paths.corpus_dir / "healthcare_financial_benchmarks.json")
    credit_drivers=_load_json(paths.corpus_dir / "healthcare_credit_drivers.json")
    count=_db_financial_count(paths.corpus_db_path)
    years=list(range(start_year, end_year + 1))
    aa=benchmarks.get("cross_sector_benchmark_summary", {}).get("dscr_by_rating", {}).get("aa", {}).get("benchmark", 1.3)
    series=[]
    for idx, year in enumerate(years):
        composite=round(57 + idx*0.7 + float(aa)*4 + count*0.4 + rng.uniform(-0.12, 0.12), 3)
        series.append({"year": year, "composite_index": composite})
    records=[]
    for i in range(12):
        records.append({"record_id": f"healthcare-track-{i+1:02d}", "year": years[i % len(years)], "days_cash_on_hand": 65 + i*3, "dscr": round(float(aa) + (i % 3)*0.03, 3)})
    payload={
        "metadata": {"sector": "healthcare", "generated_at_utc": datetime.now(UTC).isoformat(), "seed": seed},
        "source_corpus": {"benchmarks": benchmarks, "credit_drivers": credit_drivers},
        "benchmark_indices": [{"index_id": "munipal.healthcare.composite", "series": series}],
        "synthetic_track_records": records,
        "chart_packets": [{"chart_id": "composite", "rows": series}, {"chart_id": "track_records", "rows": records}, {"chart_id": "corpus_coverage", "rows": [{"financial_report_count": count}]}],
    }
    if project_input:
        payload["project_benchmark"] = benchmark_project(project_input=project_input, benchmark_base_series=series)
    return payload

def benchmark_project(*, project_input: dict[str, Any], benchmark_base_series: list[dict[str, Any]]) -> dict[str, Any]:
    metrics=project_input.get("metrics", {})
    latest=float(benchmark_base_series[-1]["composite_index"]) if benchmark_base_series else 0.0
    project_score=round(float(metrics.get("dscr", 1.0))*18 + float(metrics.get("operating_margin_pct", 0))*90 + (1-float(metrics.get("debt_to_capitalization", 0.6)))*20 + float(metrics.get("days_cash_on_hand", 0))*0.08 + float(metrics.get("structural_index", 0))*0.25 + float(metrics.get("risk_mitigation_index", 0))*0.25, 3)
    return {"project_id": project_input.get("project_id"), "project_score": project_score, "benchmark_score": latest, "benchmark_position": "above" if project_score >= latest else "below"}

def export_plotting_tables(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    return [_write_csv(output_dir / "benchmark_index_series.csv", payload["benchmark_indices"][0]["series"]), _write_csv(output_dir / "synthetic_track_records.csv", payload["synthetic_track_records"])]
