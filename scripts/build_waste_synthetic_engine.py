"""
Build synthetic waste benchmark indices and track records from local corpus files.

Usage:
    python scripts/build_waste_synthetic_engine.py
    python scripts/build_waste_synthetic_engine.py --project-input synth/project_input.example.json
    python scripts/build_waste_synthetic_engine.py --start-year 2007 --end-year 2035 --seed 17
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from synth.waste_engine import (  # noqa: E402
    EnginePaths,
    build_waste_synthetic_engine,
    default_engine_paths,
    export_plotting_tables,
    load_project_input,
)


def _repo_root() -> Path:
    return REPO_ROOT


def _timestamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build waste synthetic benchmark engine payload and plotting tables."
    )
    parser.add_argument(
        "--corpus-dir",
        type=Path,
        default=None,
        help="Directory containing waste_financial_benchmarks.json and waste_credit_drivers.json.",
    )
    parser.add_argument(
        "--sub-agent-dir",
        type=Path,
        default=None,
        help="Directory containing SA6 CSV extracts (wte_financial_data.csv, etc.).",
    )
    parser.add_argument(
        "--project-input",
        type=Path,
        default=None,
        help="Optional project input JSON to benchmark against generated indices.",
    )
    parser.add_argument("--start-year", type=int, default=2007, help="Synthetic series start year.")
    parser.add_argument("--end-year", type=int, default=2035, help="Synthetic series end year.")
    parser.add_argument("--seed", type=int, default=17, help="Random seed for deterministic output.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory. Defaults to synth/output/<timestamp>/ under repo.",
    )
    args = parser.parse_args()

    defaults = default_engine_paths()
    paths = EnginePaths(
        corpus_dir=args.corpus_dir or defaults.corpus_dir,
        sub_agent_dir=args.sub_agent_dir if args.sub_agent_dir is not None else defaults.sub_agent_dir,
    )

    project_input = load_project_input(args.project_input)

    if args.output_dir is not None:
        output_dir = args.output_dir
    else:
        output_dir = _repo_root() / "synth" / "output" / _timestamp()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = build_waste_synthetic_engine(
        paths=paths,
        start_year=args.start_year,
        end_year=args.end_year,
        seed=args.seed,
        project_input=project_input,
    )
    payload_path = output_dir / "waste_synthetic_engine_payload.json"
    payload_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    csv_paths = export_plotting_tables(payload, output_dir)
    print(f"[waste-synth-engine] payload={payload_path}")
    for csv_path in csv_paths:
        print(f"[waste-synth-engine] table={csv_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
