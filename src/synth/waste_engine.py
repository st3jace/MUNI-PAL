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
    sub_agent_dir: Path

def default_engine_paths() -> EnginePaths:
    return EnginePaths(
        corpus_dir=REPO_ROOT / "research" / "waste",
        sub_agent_dir=REPO_ROOT / "workplan_files" / "sub_agent_outputs",
    )

def load_project_input(path: Path | None) -> dict[str, Any] | None:
    return _load_project_input(path)

def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

def build_waste_synthetic_engine(*, paths: EnginePaths, start_year: int, end_year: int, seed: int, project_input: dict[str, Any] | None = None) -> dict[str, Any]:
    rng = random.Random(seed)
    financial_rows = _read_csv(paths.sub_agent_dir / "wte_financial_data.csv")
    risk_rows = _read_csv(paths.sub_agent_dir / "wte_risk_factors.csv")
    years = list(range(start_year, end_year + 1))
    base_dscr = sum(float(r.get("debt_service_coverage_ratio") or 1.2) for r in financial_rows) / max(len(financial_rows), 1)
    base_margin = sum((float(r.get("operating_income") or 0) / max(float(r.get("total_revenue") or 1), 1)) for r in financial_rows) / max(len(financial_rows), 1)
    series=[]
    for idx, year in enumerate(years):
        composite = round(55 + idx * 0.65 + (base_dscr - 1.0) * 10 + base_margin * 20 + rng.uniform(-0.15, 0.15), 3)
        series.append({"year": year, "composite_index": composite})
    records=[]
    for i in range(12):
        year = years[i % len(years)]
        records.append({"record_id": f"waste-track-{i+1:02d}", "year": year, "dscr": round(base_dscr + (i % 4) * 0.02, 3), "risk_factor_count": len(risk_rows)})
    payload={
        "metadata": {"sector": "waste", "generated_at_utc": datetime.now(UTC).isoformat(), "seed": seed},
        "source_corpus": {"benchmarks": _load_json(paths.corpus_dir / "waste_financial_benchmarks.json"), "credit_drivers": _load_json(paths.corpus_dir / "waste_credit_drivers.json")},
        "benchmark_indices": [{"index_id": "munipal.waste.composite", "series": series}],
        "synthetic_track_records": records,
        "chart_packets": [{"chart_id": "composite", "rows": series}, {"chart_id": "track_records", "rows": records}, {"chart_id": "risk_factors", "rows": risk_rows}],
    }
    if project_input:
        payload["project_benchmark"] = benchmark_project(project_input=project_input, benchmark_base_series=series)
    return payload

def benchmark_project(*, project_input: dict[str, Any], benchmark_base_series: list[dict[str, Any]]) -> dict[str, Any]:
    metrics=project_input.get("metrics", {})
    latest=float(benchmark_base_series[-1]["composite_index"]) if benchmark_base_series else 0.0
    project_score=round(float(metrics.get("dscr", 1.0))*20 + float(metrics.get("operating_margin_pct", 0))*80 + float(metrics.get("structural_index", 0))*0.35 + float(metrics.get("risk_mitigation_index", 0))*0.35, 3)
    return {"project_id": project_input.get("project_id"), "project_score": project_score, "benchmark_score": latest, "benchmark_position": "above" if project_score >= latest else "below"}

def export_plotting_tables(payload: dict[str, Any], output_dir: Path) -> list[Path]:
    series=payload["benchmark_indices"][0]["series"]
    records=payload["synthetic_track_records"]
    return [_write_csv(output_dir / "benchmark_index_series.csv", series), _write_csv(output_dir / "synthetic_track_records.csv", records)]
