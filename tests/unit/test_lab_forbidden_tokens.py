"""Fence: provenance tokens, the MSRB platform token, forbidden sources, computed dates,
label-not-claim and citation control (BUILD-SPEC section 6, rows 4-8).

Every forbidden string is loaded from the two data files that `labkit.law` reads at
import (critic M5); this file spells none of them. The scanners skip only the blocklist
data file (`law.EXCLUDED_DATA_FILES`, whole real names), `runs/` (gitignored, local-disk
only) and `__pycache__`; the forbidden-token file is scanned like any other lab file
because its fragments never spell a token literally (one-character no-op classes).
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from tests import lab_support

REPO = lab_support.REPO_ROOT
LAB = lab_support.LAB_ROOT
_SKIP_PARTS = frozenset({"__pycache__", "runs"})
_ISO_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
_DATE_CALLS = ("timedelta(", "relativedelta", "form_8038_due", "date.today(")
_NOW_CALL = "datetime.now("
_CDA_FILE = "closing-documents/03-continuing-disclosure-agreement.md"
_GOVERNANCE_DOCS = (
    "README.md",
    "LAW.md",
    "governance/FINDINGS.md",
    "governance/PRFAQ-lite.md",
    "governance/decision-request.md",
)


def _law():
    return lab_support.import_labkit().law


def _lab_files(root: Path = LAB.parent) -> list[Path]:
    """Every file under `lab/` (both levels) minus the excluded data files, runs/, caches."""
    law = _law()
    out: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if _SKIP_PARTS & set(path.relative_to(root).parts):
            continue
        if path.is_relative_to(LAB) and path.relative_to(LAB).as_posix() in law.EXCLUDED_DATA_FILES:
            continue
        out.append(path)
    return out


def _scan_targets() -> list[Path]:
    files = _lab_files()
    files.append(REPO / "tests" / "lab_support.py")
    files += sorted((REPO / "tests").rglob("test_lab_*.py"))
    return files


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _rel(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def _rel_lab(path: Path) -> str:
    """Path relative to the top-level `lab/` folder (e.g. `twin-bfms/labkit/law.py`)."""
    return path.relative_to(LAB.parent).as_posix()


def test_lab_quarantine_rule3_grep() -> None:
    law = _law()
    assert law.DATA_FILES_PRESENT.get(law.FORBIDDEN_TOKENS_FILE_REL), "rule-3 token data file absent"
    assert len(law.FORBIDDEN_TOKEN_PATTERNS) >= 4, "rule-3 token list is empty; the fence would be vacuous"
    hits = []
    for path in _scan_targets():
        for token in law.forbidden_token_hits(_text(path)):
            hits.append(f"{_rel(path)}: {token!r}")
    assert hits == [], f"QUARANTINE.md rule-3 token(s) present: {hits}"
    # MUNI-PAL carries no pre-commit hook (verified .git/hooks 2026-09-10); this test IS the grep.
    assert (LAB / law.FORBIDDEN_TOKENS_FILE_REL) in _scan_targets(), "the token data file must be scanned too"


def test_lab_forbidden_token_probe_fires() -> None:
    """A planted token (built at run time from each fragment, never spelled here) must hit:
    the obfuscated fragments still match real occurrences, and the data file itself is clean."""
    law = _law()
    for section, patterns, hits_fn in (
        ("rule3", law.FORBIDDEN_TOKEN_PATTERNS, law.forbidden_token_hits),
        ("sources", law.FORBIDDEN_SOURCES, lambda text: law.FORBIDDEN_SOURCES_RE.findall(text)),
        ("citation", law.CITATION_FORBIDDEN, lambda text: law.CITATION_FORBIDDEN_RE.findall(text)),
    ):
        assert patterns, f"[{section}] is empty"
        for fragment in patterns:
            assert "[" in fragment, f"[{section}] fragment {fragment!r} is not obfuscated (spells its token literally)"
            planted = law.deobfuscate_fragment(fragment)
            assert planted != fragment
            assert hits_fn(f"see {planted} here"), f"[{section}] probe {planted!r} did not fire"
            assert not hits_fn(fragment), f"[{section}] fragment {fragment!r} hits itself"
    claim_patterns = [re.compile(p, re.IGNORECASE) for p in law.read_sectioned_lines(LAB / law.FORBIDDEN_TOKENS_FILE_REL).get("lab-words", [])]
    assert claim_patterns
    for pattern in claim_patterns:
        assert "[" in pattern.pattern
        assert not pattern.search(pattern.pattern), f"label-claim fragment {pattern.pattern!r} hits itself"
    assert any(p.search("this artifact is a process twin of the deal") for p in claim_patterns)
    assert any(p.search("a digital twin of the process") for p in claim_patterns)
    assert law.CITATION_FORBIDDEN_RE.search("Stephen " + "approved it")


def test_lab_emma_only_in_cda_quote_pinned() -> None:
    law = _law()
    allowlist = {rel: (heading, count) for rel, heading, count in law.EMMA_ALLOWLIST}
    assert _CDA_FILE in allowlist
    packs = sorted(p for p in (LAB / "packs").iterdir() if p.is_dir())
    assert packs, "no committed packs"
    hits = []
    for path in _lab_files():
        text = _text(path)
        n = len(law.EMMA_WORD.findall(text))
        if n == 0:
            continue
        rel = _rel_lab(path)
        pack_rel = "/".join(rel.split("/")[3:]) if rel.startswith("twin-bfms/packs/") else rel
        if pack_rel not in allowlist:
            hits.append(f"{rel}: {n} occurrence(s) outside the allowlist")
            continue
        heading, allowed = allowlist[pack_rel]
        lines = text.split("\n")
        start = next((i for i, line in enumerate(lines) if line.startswith(heading)), None)
        if start is None:
            hits.append(f"{rel}: heading {heading!r} missing")
            continue
        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
        inside = sum(len(law.EMMA_WORD.findall(line)) for line in lines[start + 1 : end])
        if n != allowed or inside != allowed:
            hits.append(f"{rel}: {n} total / {inside} under {heading!r}; pinned {allowed}")
    assert hits == [], hits
    for pack in packs:
        cda = pack / _CDA_FILE
        assert cda.is_file(), f"{pack.name}: CDA excerpt missing"
        assert len(law.EMMA_WORD.findall(_text(cda))) == 1, f"{pack.name}: platform token count != 1"
        approved = pack / "post-close" / "approved-inputs.csv"
        assert not law.EMMA_WORD.search(_text(approved)), f"{pack.name}: approved-inputs.csv carries the token"
        for vault_file in sorted((pack / "post-close" / "vault").glob("*.txt")):
            assert not law.EMMA_WORD.search(_text(vault_file)), f"{pack.name}: {vault_file.name} carries the token"


def test_lab_no_forbidden_sources() -> None:
    law = _law()
    assert len(law.FORBIDDEN_SOURCES) >= 20, "forbidden-source list is empty; the fence would be vacuous"
    hits = []
    allowlisted = 0
    for path in _lab_files():
        rel = _rel_lab(path)
        for lineno, line in enumerate(_text(path).split("\n"), start=1):
            if not law.FORBIDDEN_SOURCES_RE.search(line):
                continue
            if rel == "twin-bfms/governance/FINDINGS.md" and "pilot_onboarding.py" in line and "F7" in line and allowlisted == 0:
                allowlisted += 1  # the one line that names F7 by path (display_name rename request)
                continue
            hits.append(f"{rel}:{lineno}")
    assert hits == [], f"forbidden source token(s): {hits}"


def _scenario_dates(deal_id: str) -> set[str]:
    lab_support.import_labkit()
    from labkit import scenario as scenario_mod

    data = scenario_mod.load(LAB / "scenarios" / f"{deal_id}.synthetic.json").data
    found: set[str] = set()

    def walk(node: object) -> None:
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, str):
            found.update(_ISO_DATE.findall(node))

    walk(data)
    return found


def test_lab_no_computed_dates() -> None:
    problems = []
    for path in _lab_files():
        if path.suffix != ".py":
            continue
        rel = _rel_lab(path)
        text = _text(path)
        for marker in _DATE_CALLS:
            if marker in text:
                problems.append(f"{rel}: {marker!r}")
        if _NOW_CALL in text and rel != "twin-bfms/labkit/report.py":
            problems.append(f"{rel}: {_NOW_CALL!r} only labkit/report.py may read the clock")
    assert problems == [], problems

    packs = sorted(p for p in (LAB / "packs").iterdir() if p.is_dir())
    assert packs
    for pack in packs:
        literals = _scenario_dates(pack.name)
        with (pack / "bondi" / "event_log.csv").open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        assert rows, f"{pack.name}: empty event log"
        for row in rows:
            if row["date"]:
                assert row["date"] in literals, f"{pack.name}: {row['event']} date {row['date']} is not a scenario literal"
            else:
                assert row["status"] != "fired", f"{pack.name}: {row['event']} fired without a date"


def test_lab_label_not_claim_and_citation_control() -> None:
    law = _law()
    sections = law.read_sectioned_lines(LAB / law.FORBIDDEN_TOKENS_FILE_REL)
    claim_patterns = [re.compile(p, re.IGNORECASE) for p in sections.get("lab-words", [])]
    assert claim_patterns, "label-claim phrase list is empty"
    assert law.CITATION_FORBIDDEN, "citation-control phrase list is empty"
    hits = []
    for path in _lab_files():
        rel = _rel_lab(path)
        for lineno, line in enumerate(_text(path).split("\n"), start=1):
            if any(p.search(line) for p in claim_patterns):
                hits.append(f"{rel}:{lineno}: label-claim phrase")
            if law.CITATION_FORBIDDEN_RE.search(line):
                hits.append(f"{rel}:{lineno}: citation-control phrase")
    assert hits == [], hits

    docs = [LAB.parent / "README.md"] + [LAB / rel for rel in _GOVERNANCE_DOCS]
    missing = [d.relative_to(REPO).as_posix() for d in docs if not d.is_file()]
    assert missing == [], f"governance/README/LAW files not written yet (docs lane): {missing}"
    problems = []
    for doc in docs:
        text = _text(doc)
        if "label, not a claim" not in text:
            problems.append(f"{_rel(doc)}: lacks the 'label, not a claim' line")
        if not any(cite in text for cite in law.ACCEPTED_CITATIONS):
            problems.append(f"{_rel(doc)}: cites neither the COS working paper nor the RESET plan path")
    assert problems == [], problems


def test_lab_forbidden_token_data_files_present() -> None:
    """The two data files exist, are the ones `law` loaded, and carry every section."""
    law = _law()
    assert set(law.EXCLUDED_DATA_FILES) == {law.BLOCKLIST_FILE_REL}, "only the blocklist may be excluded from the scanners"
    for rel in law.DATA_FILES:
        assert (LAB / rel).is_file(), f"{rel} missing"
        assert law.DATA_FILES_PRESENT.get(rel) is True
    drafts = LAB / "scenarios" / "names" / Path(law.FORBIDDEN_TOKENS_FILE_REL).name
    sections = law.read_sectioned_lines(drafts)
    assert set(sections) >= {"rule3", "sources", "lab-words", "citation"}
    manifest = json.loads((LAB / "packs" / "_pins.json").read_text(encoding="utf-8"))
    assert "bondi_format_json_sha256" in manifest
