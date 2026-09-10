"""Law constants for `lab/twin-bfms` (transcribed rulings; see `lab/twin-bfms/LAW.md`).

Everything a fence test, a generator or the runner needs to *cite* lives here as data.

Self-hit avoidance (critic must-fix M5): the strings that the fence tests grep for
(QUARANTINE.md rule-3 tokens, the old-pack source names, the label-claim phrases, the
citation-control phrase and the brief rule-10 firm names) are NEVER spelled in a lab `.py`
file. They are loaded at import from two data files:

    scenarios/names/blocklist.v1.txt          one phrase per line; `#` starts a comment.
                                              Whole-phrase name-collision list: the brief
                                              rule-10 firms, the twelve old-pack city names
                                              and the real-issuer phrases (BUILD-SPEC 3.3).
                                              Spells the phrases whole, so every scanner
                                              excludes it by exact relative path
                                              (`EXCLUDED_DATA_FILES`); it carries no rule-3
                                              token.
    scenarios/names/forbidden-tokens.v1.txt   sectioned; `#` starts a comment. Each line is a
                                              regex fragment whose last plain character is
                                              wrapped in a one-character class, so the file
                                              never spells a fenced token literally and the
                                              scanners cover it too. Sections:
                                                [rule3]     QUARANTINE.md rule-3 grep tokens
                                                [sources]   old-pack cities, the rescue
                                                            branch name, the OneDrive folder
                                                            name, the rescued module names and
                                                            the three `synth` import spellings
                                                            (BUILD-SPEC 6, no-forbidden-sources)
                                                [lab-words] the label-claim phrases
                                                            (DEC-009 section 9.8)
                                                [citation]  the citation-control phrase
                                                            (brief rule 12)

If a data file is absent the corresponding list is EMPTY and `DATA_FILES_PRESENT` says so;
the fence tests assert presence. Nothing here fails at import time.
"""

from __future__ import annotations

import re
from fnmatch import fnmatchcase
from pathlib import Path

# --------------------------------------------------------------------------------------
# Roots and data files
# --------------------------------------------------------------------------------------

LAB_ROOT: Path = Path(__file__).resolve().parents[1]  # lab/twin-bfms
NAMES_DIR: Path = LAB_ROOT / "scenarios" / "names"

BLOCKLIST_FILE_REL = "scenarios/names/blocklist.v1.txt"
FORBIDDEN_TOKENS_FILE_REL = "scenarios/names/forbidden-tokens.v1.txt"
NAME_TABLE_FILE_REL = "scenarios/names/fictional-names.v1.json"

#: The two fence data files (presence asserted by the fence tests).
DATA_FILES: tuple[str, ...] = (BLOCKLIST_FILE_REL, FORBIDDEN_TOKENS_FILE_REL)
#: Relative paths (from LAB_ROOT, forward slashes) that every scanner skips by exact match:
#: only the blocklist, which spells real names and old-pack city phrases whole. The
#: forbidden-token file is scanned like any other lab file (its fragments are obfuscated).
EXCLUDED_DATA_FILES: tuple[str, ...] = (BLOCKLIST_FILE_REL,)

# --------------------------------------------------------------------------------------
# Legend (verbatim muni-twin/QUARANTINE.md lines 66-67 joined on one line)
# --------------------------------------------------------------------------------------

LEGEND_SOURCE = r"C:\Users\st3ja\muni-twin\QUARANTINE.md:66-67"
LEGEND = (
    "SYNTHETIC RESEARCH ARTIFACT — MUNI-TWIN — NOT LEGAL ADVICE — NOT PREPARED BY AN ATTORNEY — "
    "NOT AN OFFER OF SECURITIES. Fictional names collision-checked against real firms."
)
#: Long markdown files repeat the legend every N lines ("every page").
LEGEND_EVERY_N_LINES = 60

LABEL_NOTICE = "twin-bfms is a label, not a claim (DEC-009 §9.8)."

# --------------------------------------------------------------------------------------
# Four-valued honesty
# --------------------------------------------------------------------------------------

FOUR_VALUES: tuple[str, ...] = ("pass", "fail", "unknown", "not_applicable")
#: Worst-first ranking used to fold sub-assertions into a stage status.
STATUS_RANK: dict[str, int] = {"fail": 3, "unknown": 2, "pass": 1, "not_applicable": 0}

CLIENT_GATE_REASON = "internal lab; no client"
#: The two client gates can never be anything but not_applicable in the lab (brief rule 4).
PILOT_GATE_STATUS: dict[str, str] = {
    "registered_ma_confirmed": "not_applicable",
    "engagement_scope_signed": "not_applicable",
}
SMOKE_GATE_MEANING = (
    "pilot_smoke_test_green = pass means this synthetic run matched its reviewed expectations "
    "in-process; it is not a statement about any client, deal, or advisor"
)
PILOT_GATE_DEFINITION_REF = "src/munipal/services/pilot_onboarding.py::_PRE_PILOT_GATES"
PILOT_GATE_DISPLAY_NAME_FINDING = "F7"

#: Lab-scripted reviewer seat -- NOT a person, NOT a Bond Strategist. UUID4-shaped.
REVIEWER_ID = "00000000-0000-4000-8000-000000000001"
REVIEWER_LABEL = "lab-scripted-reviewer — NOT a human, NOT a Bond Strategist"

# --------------------------------------------------------------------------------------
# Stage / report vocabulary
# --------------------------------------------------------------------------------------

EXPECTED_STAGE_IDS: tuple[str, ...] = tuple(f"S{i:02d}" for i in range(19))
REPORT_SCHEMA_VERSION = "lab-run-report/1"
#: Keys the report `pins` block must carry (M1: the BONDI pin is the format.json hash).
PIN_KEYS: tuple[str, ...] = (
    "run_py_sha256",
    "build_fixtures_sha256",
    "pack_manifest_sha256",
    "bondi_format_json_sha256",
)
BFMS_EXCERPT_MAX_CHARS = 120

# --------------------------------------------------------------------------------------
# BONDI emission format (consumed, never vendored) and register vocabulary
# --------------------------------------------------------------------------------------

BONDI_STATIONS: tuple[str, ...] = (
    "1_facility",
    "2_conduit",
    "3_issuance",
    "4_structure",
    "5_buyers",
    "6_borrower_prep",
)
EVENT_LOG_HEADER: tuple[str, ...] = ("date", "station", "event", "actor_role", "status", "reason")
HOLD_STATUSES: tuple[str, ...] = ("on_hold", "suspended", "re_vintaged", "carried_forward")
BONDI_EVENT_STATUSES: tuple[str, ...] = ("fired", "skipped", "unknown", *HOLD_STATUSES)
#: Constraint vocabulary is BONDI spelling; the report renders `n/a` as `not_applicable`.
CONSTRAINT_STATUSES: tuple[str, ...] = ("pass", "fail", "unknown", "n/a")
LAB_EXTENSION_EVENTS: frozenset[str] = frozenset({"afs_posted_fy*", "listed_or_material:*"})
#: The sellable Obligation Register's four status codes (fulfillment/demo/run.py STATUSES).
REGISTER_STATUSES: tuple[str, ...] = ("filed", "not filed", "evidence missing", "not testable")

DEMO_DEAL_ID = "SYN-HSG-AZ-2025"
LAB_DEAL_ID_RE = re.compile(r"^SYN-[A-Z]{2,4}-[A-Z]{2}-\d{4}-LAB\d{2}$")
SYN_ID_RE = re.compile(r"^SYN-")
SYN_ARTIFACT_ID_RE = re.compile(r"^SYN-ART-[0-9a-f]{8}$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_lab_extension_event(event: str) -> bool:
    """True when `event` is one of the lab's own extension rows (not a BONDI station event)."""
    return any(fnmatchcase(event, pattern) for pattern in LAB_EXTENSION_EVENTS)


# --------------------------------------------------------------------------------------
# File-system law
# --------------------------------------------------------------------------------------

#: Directory names the root .gitignore swallows; no directory under lab/ may carry one.
IGNORED_DIR_NAMES: frozenset[str] = frozenset(
    {"data", "artifacts", "uploads", "reports", "research", "synth", "files", "pdfs", "logs"}
)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset({".md", ".txt", ".csv", ".json"})
CSV_SIDECAR_SUFFIX = ".provenance.json"
PACK_MANIFEST_NAME = "PACK-MANIFEST.json"

# --------------------------------------------------------------------------------------
# The MSRB platform token (DEC-008): allowed exactly once per pack, inside the CDA quote.
# The regex is assembled so this file never carries the bare word.
# --------------------------------------------------------------------------------------

EMMA_WORD: re.Pattern[str] = re.compile(r"\b" + "EM" + "MA" + r"\b")
#: (pack-relative file, section heading that must precede the line, allowed count).
EMMA_ALLOWLIST: frozenset[tuple[str, str, int]] = frozenset(
    {("closing-documents/03-continuing-disclosure-agreement.md", "## Section 4", 1)}
)

# --------------------------------------------------------------------------------------
# Out-of-bounds modules (assembled, never literal -- M5)
# --------------------------------------------------------------------------------------

ENGINES_MODULE = "munipal." + "engines"
OUT_OF_BOUNDS_MODULES: tuple[str, ...] = (
    ENGINES_MODULE,
    ENGINES_MODULE + ".credit_analyzer.deal_" + "structuring",
    ENGINES_MODULE + ".credit_analyzer.bond_" + "sizing",
)

# --------------------------------------------------------------------------------------
# Naming law: CUSIP-like tokens
# --------------------------------------------------------------------------------------

#: Nine-character CUSIP-shaped token within 40 chars of the word CUSIP (either order).
CUSIP_NEAR_WORD_RE = re.compile(
    r"CUSIP.{0,40}?\b\d{5}[A-Z0-9]{4}\b|\b\d{5}[A-Z0-9]{4}\b.{0,40}?CUSIP"
)
#: Strict nine-character upper-alnum token; applied to scenarios/ and packs/ only.
CUSIP_LIKE_STRICT_RE = re.compile(r"\b[0-9A-Z]{6}[A-Z0-9]{3}\b")
CUSIP_LIKE: tuple[re.Pattern[str], ...] = (CUSIP_NEAR_WORD_RE, CUSIP_LIKE_STRICT_RE)

# --------------------------------------------------------------------------------------
# Citation control (brief rule 12): cite a path, never a person's approval.
# --------------------------------------------------------------------------------------

BRIEF_SHA256 = "f031201cc35a3651da7b45f67e485c0995ab9f04f066e6274d258ef9fa621cb4"
BRIEF_CITATION = f"COS working paper 2026-09-10 (scratchpad, sha256 {BRIEF_SHA256})"
RESET_PLAN_PATH = r"C:\Users\st3ja\braintrust\workspace\cos\2026-09-10-RESET-plain-plan.md"
#: A governance/README/LAW file must carry at least one of these strings.
ACCEPTED_CITATIONS: tuple[str, ...] = (BRIEF_CITATION, RESET_PLAN_PATH, "LAB-BRIEF.md")

# --------------------------------------------------------------------------------------
# Blocklist minimum (brief rule 10 + real-issuer phrases + the twelve old-pack city names).
# No real name is spelled in this .py: the set is the phrase list loaded from
# blocklist.v1.txt by `reload()`; the brief's minimum list is asserted only in
# tests/unit/test_lab_names.py (where the negative cases already spell real names).
# --------------------------------------------------------------------------------------

#: Populated by `reload()`; empty when the data file is absent (`DATA_FILES_PRESENT`).
BLOCKLIST_MIN: tuple[str, ...] = ()

# --------------------------------------------------------------------------------------
# Forbidden lab words (brief rule 4). Built-ins are safe to spell; the label-claim phrases
# come from the data file. Patterns are matched case-insensitively.
# "approve" is a review verb on facts; "approved fact(s)" is therefore allowed.
# --------------------------------------------------------------------------------------

_BUILTIN_LAB_WORD_PATTERNS: tuple[str, ...] = (
    r"\bcompliant\b",
    r"\bapproved\b(?![ _-]facts?\b)",
    r"\brecommend\w*\b",
)

# --------------------------------------------------------------------------------------
# Data-file loading
# --------------------------------------------------------------------------------------

_NEVER_MATCH = re.compile(r"(?!x)x")

#: Populated by `reload()`.
DATA_FILES_PRESENT: dict[str, bool] = {}
BLOCKLIST_PHRASES: tuple[str, ...] = ()
FORBIDDEN_TOKEN_PATTERNS: tuple[str, ...] = ()
FORBIDDEN_TOKENS: re.Pattern[str] = _NEVER_MATCH
FORBIDDEN_SOURCES: tuple[str, ...] = ()
FORBIDDEN_SOURCES_RE: re.Pattern[str] = _NEVER_MATCH
FORBIDDEN_LAB_WORDS: tuple[str, ...] = _BUILTIN_LAB_WORD_PATTERNS
FORBIDDEN_LAB_WORDS_RE: re.Pattern[str] = _NEVER_MATCH
CITATION_FORBIDDEN: tuple[str, ...] = ()
CITATION_FORBIDDEN_RE: re.Pattern[str] = _NEVER_MATCH


def read_phrase_lines(path: Path) -> list[str]:
    """Non-empty, non-comment lines of a flat phrase file (UTF-8, stripped)."""
    if not path.is_file():
        return []
    out: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line and not line.startswith("#"):
            out.append(line)
    return out


def read_sectioned_lines(path: Path) -> dict[str, list[str]]:
    """Lines of a `[section]` file, keyed by section name; lines before a header go to ''."""
    sections: dict[str, list[str]] = {}
    current = ""
    for line in read_phrase_lines(path):
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1].strip().lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _alternation(fragments: tuple[str, ...], flags: int = 0) -> re.Pattern[str]:
    if not fragments:
        return _NEVER_MATCH
    return re.compile("|".join(f"(?:{f})" for f in fragments), flags)


def reload(names_dir: Path | None = None) -> None:
    """(Re)load the two data files; safe to call from tests with a temporary directory."""
    global BLOCKLIST_PHRASES, BLOCKLIST_MIN, FORBIDDEN_TOKEN_PATTERNS, FORBIDDEN_TOKENS
    global FORBIDDEN_SOURCES, FORBIDDEN_SOURCES_RE, FORBIDDEN_LAB_WORDS, FORBIDDEN_LAB_WORDS_RE
    global CITATION_FORBIDDEN, CITATION_FORBIDDEN_RE
    base = names_dir if names_dir is not None else NAMES_DIR
    blocklist_path = base / Path(BLOCKLIST_FILE_REL).name
    tokens_path = base / Path(FORBIDDEN_TOKENS_FILE_REL).name
    DATA_FILES_PRESENT.clear()
    DATA_FILES_PRESENT[BLOCKLIST_FILE_REL] = blocklist_path.is_file()
    DATA_FILES_PRESENT[FORBIDDEN_TOKENS_FILE_REL] = tokens_path.is_file()

    BLOCKLIST_PHRASES = tuple(read_phrase_lines(blocklist_path))
    BLOCKLIST_MIN = BLOCKLIST_PHRASES
    sections = read_sectioned_lines(tokens_path)
    FORBIDDEN_TOKEN_PATTERNS = tuple(sections.get("rule3", []))
    FORBIDDEN_TOKENS = _alternation(FORBIDDEN_TOKEN_PATTERNS)
    FORBIDDEN_SOURCES = tuple(sections.get("sources", []))
    FORBIDDEN_SOURCES_RE = _alternation(FORBIDDEN_SOURCES)
    FORBIDDEN_LAB_WORDS = (*_BUILTIN_LAB_WORD_PATTERNS, *sections.get("lab-words", []))
    FORBIDDEN_LAB_WORDS_RE = _alternation(FORBIDDEN_LAB_WORDS, re.IGNORECASE)
    CITATION_FORBIDDEN = tuple(sections.get("citation", []))
    CITATION_FORBIDDEN_RE = _alternation(CITATION_FORBIDDEN)


def deobfuscate_fragment(fragment: str) -> str:
    """The literal a data-file fragment stands for: unwrap every one-character class and
    unescape `\\.` (used by the fence tests to plant a token at run time without spelling it)."""
    return re.sub(r"\[(.)\]", r"\1", fragment).replace(r"\.", ".")


def forbidden_lab_word_hits(text: str) -> list[str]:
    """Every forbidden-word match in `text` (empty list == clean)."""
    return [m.group(0) for m in FORBIDDEN_LAB_WORDS_RE.finditer(text)]


def forbidden_token_hits(text: str) -> list[str]:
    """Every rule-3 token match in `text` (empty list == clean)."""
    return [m.group(0) for m in FORBIDDEN_TOKENS.finditer(text)]


def blocklist_hits(name: str, phrases: tuple[str, ...] | None = None) -> list[str]:
    """Whole-phrase, case-insensitive blocklist matches inside `name`."""
    pool = phrases if phrases is not None else BLOCKLIST_PHRASES
    hits: list[str] = []
    for phrase in pool:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(phrase) + r"(?![A-Za-z0-9])"
        if re.search(pattern, name, re.IGNORECASE):
            hits.append(phrase)
    return hits


reload()
