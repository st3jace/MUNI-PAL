"""Fence: the lab's `bondi/` emission matches the transcribed BONDI format (BUILD-SPEC 4.4, 6;
critic M1: format.json is compared against generate.py by ast when the OneDrive file is
present, else that half skips with a reason; generate.py is never executed or imported).
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from tests import lab_support

LAB = lab_support.LAB_ROOT
PACKS = LAB / "packs"
DEAL_IDS = ("SYN-HSG-AZ-2025-LAB01", "SYN-HSG-AZ-2025-LAB02", "SYN-HSG-AZ-2025-LAB03")
BONDI_FILES = ("deal.json", "event_log.csv", "constraint_report.json", "artifact_manifest.json")
_REFERENCE_KEYS = (
    "event_log_header",
    "stations",
    "sale_poles",
    "station_events_core",
    "station_events_by_pole",
    "station_events_post",
    "event_statuses",
    "constraint_statuses",
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        assert reader.fieldnames is not None
        return [dict(row, __header__=",".join(reader.fieldnames)) for row in rows]


def test_lab_bondi_emission_format() -> None:
    lab_support.import_labkit()
    from labkit import events, law, scenario

    fmt = scenario.bondi_format()
    assert list(fmt["event_log_header"]) == list(law.EVENT_LOG_HEADER)
    assert list(fmt["stations"]) == list(law.BONDI_STATIONS)
    assert set(fmt["event_statuses"]) == set(law.BONDI_EVENT_STATUSES)
    assert set(fmt["constraint_statuses"]) == set(law.CONSTRAINT_STATUSES)
    known = scenario.known_event_names(fmt)
    assert {"issuer_engagement", "closing", "cda_executed", "8038_filed", "g32_os_filed"} <= known

    for deal_id in DEAL_IDS:
        bondi = PACKS / deal_id / "bondi"
        names = sorted(p.name for p in bondi.iterdir())
        assert names == sorted([*BONDI_FILES, "event_log.csv" + law.CSV_SIDECAR_SUFFIX]), f"{deal_id}: {names}"
        assert tuple(events.BONDI_FILES) == BONDI_FILES
        rows = _rows(bondi / "event_log.csv")
        assert rows and rows[0]["__header__"] == ",".join(law.EVENT_LOG_HEADER)
        for row in rows:
            assert row["station"] in law.BONDI_STATIONS, row
            assert row["status"] in law.BONDI_EVENT_STATUSES, row
            assert row["event"] in known or law.is_lab_extension_event(row["event"]), row
            if row["status"] != "fired":
                assert row["date"] == "", f"{deal_id}: non-fired row carries a date {row}"
                assert row["reason"], f"{deal_id}: non-fired row lacks a reason {row}"
            else:
                assert law.ISO_DATE_RE.match(row["date"]), row
        dated = [r for r in rows if r["date"]]
        undated = [r for r in rows if not r["date"]]
        assert rows == dated + undated, f"{deal_id}: empty-date rows must come last"
        assert dated == sorted(dated, key=lambda r: (r["date"], r["event"]))
        assert undated == sorted(undated, key=lambda r: r["event"])
        assert len({r["event"] for r in rows}) == len(rows)

        report = json.loads((bondi / "constraint_report.json").read_text(encoding="utf-8"))["constraint_report"]
        sc = scenario.load(LAB / "scenarios" / f"{deal_id}.synthetic.json")
        assert [c["id"] for c in report] == [c["id"] for c in sc.data["constraints"]]
        assert {c["status"] for c in report} <= set(law.CONSTRAINT_STATUSES)
        deal = json.loads((bondi / "deal.json").read_text(encoding="utf-8"))
        assert deal["deal_id"] == deal_id and deal["mode"] == "synthetic"
        artifacts = json.loads((bondi / "artifact_manifest.json").read_text(encoding="utf-8"))["artifacts"]
        assert artifacts and all(law.SYN_ARTIFACT_ID_RE.match(a["id"]) for a in artifacts)
        assert all(a["id"] == events.artifact_id(sc.seed, a["path"]) for a in artifacts)
        assert len({a["id"] for a in artifacts}) == len(artifacts)

    lab02 = _rows(PACKS / DEAL_IDS[1] / "bondi" / "event_log.csv")
    afs = next(r for r in lab02 if r["event"] == "afs_posted_fy2025")
    assert afs["status"] == "unknown" and afs["date"] == ""


def test_lab_bondi_format_matches_generate_py() -> None:
    lab_support.import_labkit()
    from labkit import generate_pack, scenario

    generate_py = scenario.bondi_root() / generate_pack.BONDI_GENERATE_REL
    fmt_path = generate_pack.FORMAT_JSON_PATH
    fmt = json.loads(fmt_path.read_text(encoding="utf-8"))
    pins = json.loads((PACKS / "_pins.json").read_text(encoding="utf-8"))
    assert pins["bondi_format_json_sha256"] == hashlib.sha256(fmt_path.read_bytes()).hexdigest()
    try:
        source = generate_py.read_bytes()
    except OSError:
        pytest.skip("reference absent (generate.py not invoked / OneDrive dehydrated)")
    if not source:
        pytest.skip("reference absent (generate.py not invoked / OneDrive dehydrated)")
    transcribed = generate_pack.transcribe_bondi_format(generate_py)
    assert transcribed["source_sha256"] == fmt["source_sha256"], "generate.py changed since format.json was transcribed"
    for key in _REFERENCE_KEYS:
        assert transcribed[key] == fmt[key], f"format.json {key} drifted from generate.py"
    assert "def main" not in transcribed["method"]  # the transcription is by ast, not a run
