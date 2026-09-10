#!/usr/bin/env python3
"""Drive one synthetic scenario through the full BFMS in-process (lab/twin-bfms).

    cd ~/Developer/MUNI-PAL && PYTHONPATH=src .venv/bin/python lab/twin-bfms/run_lab.py \\
        --scenario lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json [--out lab/twin-bfms/runs]

`--asof` is NOT accepted: the as-of date is the scenario's `lab.asof` literal.
`--write-golden` persists the status-only view of this run to
`expected/<deal_id>/run-report.expected.json` (derived, never typed; review before freezing).

Exit code: 0 iff the report verifies and no fence-class violation was recorded;
1 when the report does not verify; 2 on a fence-class violation. A golden delta is
reported in S18 and on stdout; it does not change the exit code (BUILD-SPEC 1).

WSL-native only. Never run against the UNC path. twin-bfms is a label, not a claim.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

PROGRAM_ROOT = Path(__file__).resolve().parent
if str(PROGRAM_ROOT) not in sys.path:
    sys.path.insert(0, str(PROGRAM_ROOT))

from labkit import GENERATOR_VERSION, LAB_VERSION, law  # noqa: E402
from labkit import report as report_mod  # noqa: E402
from labkit import scenario as scenario_mod  # noqa: E402
from labkit.types import Envelope  # noqa: E402

EXIT_OK = 0
EXIT_NOT_VERIFIED = 1
EXIT_FENCE = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    raw = list(sys.argv[1:] if argv is None else argv)
    if any(a == "--asof" or a.startswith("--asof=") for a in raw):
        print("REFUSED: --asof is not accepted; the as-of date is the scenario's lab.asof literal", file=sys.stderr)
        raise SystemExit(EXIT_FENCE)
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scenario", required=True, help="scenario json (deal-v0 + lab block)")
    parser.add_argument("--out", default=str(law.LAB_ROOT / "runs"), help="runs directory (default lab/twin-bfms/runs; gitignored)")
    parser.add_argument("--write-golden", action="store_true", help="write expected/<deal_id>/run-report.expected.json from this run")
    return parser.parse_args(raw)


async def drive(sc: scenario_mod.Scenario, run_dir: Path, run_id: str, commit: str, dirty: bool | str) -> tuple[Path, dict[str, object]]:
    from labkit import bfms_driver, harness

    pack_root = law.LAB_ROOT / "packs" / sc.deal_id
    if not (pack_root / law.PACK_MANIFEST_NAME).is_file():
        raise SystemExit(f"pack {pack_root} not found; generate it first (labkit/generate_pack.py --all)")
    async with harness.standalone(run_dir) as ctx:
        driver = bfms_driver.Driver(ctx, sc, pack_root, run_dir, run_id)
        out = await driver.run_all()
        expected = report_mod.load_expected(report_mod.expected_path(sc.deal_id))
        header = {
            "run_id": run_id,
            "scenario_id": sc.deal_id,
            "scenario_sha256": sc.sha256,
            "derived_from": sc.derived_from,
            "seed": sc.seed,
            "asof": sc.asof,
            "generator_version": GENERATOR_VERSION,
            "lab_version": LAB_VERSION,
            "repo_commit": commit,
            "repo_dirty": dirty,
            "python": out.python,
            "pins": out.pins,
            "fulfillment_tree_sha256_before": out.fulfillment_tree_before,
            "fulfillment_tree_sha256_after": out.fulfillment_tree_after,
            "environment": out.environment,
        }
        report = report_mod.build(
            header=header,
            stages=out.stages,
            conformance_table=out.conformance_rows,
            deal_workflow_mirror=out.deal_workflow_mirror,
            register_summary=out.register_summary,
            review=out.review,
            vocabulary_divergence=out.vocabulary_divergence,
            bfms_emitted_language=out.bfms_emitted_language,
            findings_touched=out.findings_touched,
            lab_statements=out.lab_statements,
            forbidden_scan=out.forbidden_scan,
            expected=expected,
            fence_class_violation=out.fence_class_violation,
            seal_stage=driver.seal_stage(out.forbidden_scan),
        )
        json_path, _md_path = report_mod.write(report, run_dir)
        summary: dict[str, object] = {
            "fence_class_violation": out.fence_class_violation or sum(out.forbidden_scan.values()) > 0,
            "forbidden_scan": out.forbidden_scan,
            "stages": {s.id: s.status for s in report.stages},
            "counts": report.counts,
            "register_status_counts": (report.register_summary or {}).get("status_counts", {}),
            "smoke": report.pilot_gates.pilot_smoke_test_green,
            "golden_diff": report.golden_diff,
            "extraction_mode": out.environment.get("extraction_mode"),
            "sensing_corpus_available": out.environment.get("sensing_corpus_available"),
        }
        return json_path, summary


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    from labkit.bfms_driver import repo_commit, repo_dirty, run_id_for

    sc = scenario_mod.load(args.scenario)
    commit = repo_commit()
    dirty = repo_dirty()
    run_id = run_id_for(sc, commit)
    run_dir = Path(args.out) / run_id
    json_path, summary = asyncio.run(drive(sc, run_dir, run_id, commit, dirty))
    verified = report_mod.verify(json_path)
    summary["verified"] = verified
    summary["report"] = str(json_path)
    if args.write_golden:
        view = report_mod.golden_view(report_mod.load(json_path))
        golden = report_mod.write_golden(view, report_mod.expected_path(sc.deal_id), Envelope(scenario_id=sc.deal_id, seed=sc.seed))
        summary["golden_written"] = str(golden)
    print(json.dumps(summary, indent=2, sort_keys=True, default=str))
    if summary["fence_class_violation"]:
        return EXIT_FENCE
    if not verified:
        return EXIT_NOT_VERIFIED
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
