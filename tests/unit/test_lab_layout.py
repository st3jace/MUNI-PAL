"""Fence: folder layout, local gitignore, registry drafts and governance docs
(BUILD-SPEC 1, 6 row 23; brief rules 8 and 11; critic M17 registry keys).
"""

from __future__ import annotations

import json
import re
import subprocess

from tests import lab_support

LAB = lab_support.LAB_ROOT
REPO = lab_support.REPO_ROOT
_CORE_KEYS = ("id", "type", "ts", "author", "domain", "prediction", "p", "kill", "verifier", "consequence", "review_by", "status")
_V11_KEYS = (
    "experiment_id", "lifecycle", "gate", "evidence_level", "owner", "evaluator", "baselines",
    "primary_metric", "guardrails", "trial_cohort", "source_health", "risk_tier", "budget", "prfaq",
)
_DRAFT_TS = "<SET-AT-FILING>"
# A line is either a DRAFT (ts placeholder, a value says DRAFT) or FILED (ISO-8601 UTC ts,
# a value says FILED). Filing happened 2026-09-10 on Stephen's ruling "1. A  2. A"; the
# canonical record is INDUSTRIALIZATION/experiments/registry.jsonl (PIT law: never edited).
_ISO_TS = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _draft_line(name: str) -> dict:
    path = LAB / "governance" / name
    assert path.is_file(), f"{name} not written yet (docs lane)"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 1, f"{name}: one JSON line expected, got {len(lines)}"
    return json.loads(lines[0])


def _check_registry_line(name: str, entry: dict, *, id_: str, type_: str, statement_key: str, v11: tuple[str, ...]) -> None:
    """PATTERN.md:34-58 (v1.1): core keys always; `v11` names the v1.1 keys this line must carry."""
    missing = [k for k in (*_CORE_KEYS, statement_key, *v11) if k not in entry]
    assert missing == [], f"{name}: missing registry keys {missing}"
    assert entry["id"] == id_ and entry["type"] == type_
    filed = entry["ts"] != _DRAFT_TS
    if filed:
        assert _ISO_TS.match(entry["ts"]), f"{name}: a filed line carries an ISO-8601 UTC ts, got {entry['ts']!r}"
        assert any(isinstance(v, str) and "FILED" in v for v in entry.values()), f"{name}: filed line must say FILED"
    else:
        assert any(isinstance(v, str) and "DRAFT" in v for v in entry.values()), f"{name}: no value says DRAFT"
    assert entry["status"] == "open"
    assert 0.0 <= float(entry["p"]) <= 1.0
    if "experiment_id" in entry:
        assert entry["experiment_id"] == id_
    if "evaluator" in entry:
        assert entry["evaluator"] != entry["author"], f"{name}: evaluator must not be the builder"
        assert entry["evaluator"] != entry.get("owner"), f"{name}: evaluator must not be the owner"
        assert "VAIA" not in entry["evaluator"] and "COS" not in entry["evaluator"], f"{name}: the builder cannot evaluate"
    if "baselines" in entry:
        assert isinstance(entry["baselines"], list) and isinstance(entry["guardrails"], list)


def test_lab_layout_gitignore_governance() -> None:
    labkit = lab_support.import_labkit()
    law = labkit.law
    assert LAB == law.LAB_ROOT
    ignore = (LAB / ".gitignore").read_text(encoding="utf-8")
    assert "runs/" in ignore and "**/_storage/" in ignore
    assert (LAB / "runs" / ".gitkeep").is_file()
    assert not list(LAB.rglob("registry.jsonl")), "the registry is never copied under lab/ (PIT law)"
    ignored_dirs = [p.relative_to(LAB).as_posix() for p in LAB.rglob("*") if p.is_dir() and p.name in law.IGNORED_DIR_NAMES]
    assert ignored_dirs == [], f"directories swallowed by the root .gitignore: {ignored_dirs}"

    probe = [
        "lab/twin-bfms/runs/x",
        "lab/twin-bfms/runs/r1/run-report.json",
        "lab/twin-bfms/packs/_pins.json",
        "lab/twin-bfms/packs/SYN-HSG-AZ-2025-LAB01/PACK-MANIFEST.json",
        "lab/twin-bfms/expected/SYN-HSG-AZ-2025-LAB01/run-report.expected.json",
        "lab/twin-bfms/scenarios/SYN-HSG-AZ-2025-LAB01.synthetic.json",
        "lab/twin-bfms/fixtures/bondi-reference/format.json",
    ]
    proc = subprocess.run(["git", "check-ignore", *probe], cwd=REPO, capture_output=True, text=True, check=False)
    assert proc.returncode in (0, 1), proc.stderr
    ignored = set(proc.stdout.split())
    assert ignored == {probe[0], probe[1]}, f"git check-ignore: {sorted(ignored)}"

    exp = _draft_line("EXP-012.draft.jsonl")
    dec = _draft_line("DEC-010.draft.jsonl")
    _check_registry_line("EXP-012.draft.jsonl", exp, id_="EXP-012", type_="experiment", statement_key="hypothesis", v11=_V11_KEYS)
    # M17: DEC-010 is a decision line -- core keys plus the prfaq pointer (rule 11); an
    # evaluator, if named, must not be the builder.
    _check_registry_line("DEC-010.draft.jsonl", dec, id_="DEC-010", type_="decision", statement_key="decision", v11=("prfaq",))
    for entry in (exp, dec):
        # Filed lines follow the registry convention (`prfaq/<file>` relative to
        # INDUSTRIALIZATION/experiments, cf. EXP-011) and name the canonical lab file after it.
        assert "lab/twin-bfms/governance/PRFAQ-lite.md" in str(entry["prfaq"]), f"{entry['id']}: prfaq must point at the lab PRFAQ-lite"
    assert exp["evidence_level"] == "E0" and exp["gate"] == "G0" and exp["lifecycle"] == "experimental"
    assert (LAB / "governance" / "PRFAQ-lite.md").is_file()
    for entry in (exp, dec):
        assert not law.CITATION_FORBIDDEN_RE.search(json.dumps(entry))

    prfaq = (LAB / "governance" / "PRFAQ-lite.md").read_text(encoding="utf-8")
    for phrase in ("Municipal bonds", "2 Advertise", "DEMAND", "OUT-002"):
        assert phrase in prfaq, f"PRFAQ-lite.md lacks {phrase!r}"

    pulls = (LAB / "docs" / "CONSUMER-PULLS.md").read_text(encoding="utf-8")
    rows = [line for line in pulls.splitlines() if line.startswith("|") and not line.startswith("|--") and not set(line) <= set("|-: ")]
    assert rows, "CONSUMER-PULLS.md has no table"
    body_rows = rows[1:]
    assert len(body_rows) == 4, f"CONSUMER-PULLS.md must carry four consumer rows, found {len(body_rows)}"
    assert all("not yet pulled" in row for row in body_rows)

    for rel in ("README.md", "LAW.md", "docs/STAGE-MAP.md", "docs/WALKTHROUGH.md", "governance/FINDINGS.md", "governance/decision-request.md"):
        assert (LAB / rel).is_file(), f"{rel} not written yet (docs lane)"
    assert (LAB.parent / "README.md").is_file()
    top_readme = (LAB.parent / "README.md").read_text(encoding="utf-8")
    assert "P1" in top_readme and "DEC-010" in top_readme, "lab/README.md must carry the DEC-010 gate sentence"
    law_md = (LAB / "LAW.md").read_text(encoding="utf-8")
    assert "runs/" in law_md and "OneDrive" in law_md, "LAW.md must carry the runs/ retention rule"
