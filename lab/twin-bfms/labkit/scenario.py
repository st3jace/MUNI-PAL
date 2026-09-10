"""Scenario loader / validator for `lab/twin-bfms` (BUILD-SPEC 3; stdlib only).

A scenario is a BONDI deal-v0 object plus one top-level `lab` block. Variants carry
`derived_from` + `knob_delta` and are materialised over the base file that sits beside
them. Validation is by hand (jsonschema is not installed):

- deal-v0 `required` keys and the `deal_id` pattern are read LIVE from BONDI's
  `deal-v0.json` (env `BONDI_ROOT`, default the OneDrive path); if the file is absent or
  dehydrated the built-in list is used and the fact is recorded, never a hard fail (M2);
- `mode` must be `synthetic` (calibration is rejected structurally);
- every party / label name must be a fictional-name-table value and blocklist-clean;
- every date is an ISO literal or null -- nothing here computes a date;
- constraint statuses are BONDI spelling (`pass|fail|unknown|n/a`), event statuses are
  BONDI event statuses, station and event names come from the transcribed emission
  format (`fixtures/bondi-reference/format.json`) plus the two lab extension names.
"""

from __future__ import annotations

import copy
import json
import os
import re
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from typing import Any

from labkit import law
from labkit import names as names_mod
from labkit.provenance import sha256_bytes, sha256_file

REPO_ROOT: Path = law.LAB_ROOT.parents[1]
SCENARIOS_DIR: Path = law.LAB_ROOT / "scenarios"
DEMO_SCENARIO_PATH: Path = REPO_ROOT / "fulfillment" / "demo" / "scenario" / "syn-hsg-2025.synthetic.json"
BONDI_FORMAT_PATH: Path = law.LAB_ROOT / "fixtures" / "bondi-reference" / "format.json"

BONDI_ROOT_ENV = "BONDI_ROOT"
DEFAULT_BONDI_ROOT = (
    "/mnt/c/Users/st3ja/OneDrive/Documents/MEGA/PROJECTS/INNOVATION FACTORY/"
    "APPLIED RESEARCH/bondi-bfms"
)
DEAL_V0_REL = "synth-issuance/schema/deal-v0.json"
BUILTIN_REQUIRED: tuple[str, ...] = (
    "deal_id", "mode", "jurisdiction", "stations", "parties", "instrument", "constraints",
)
BUILTIN_ID_PATTERN = "^SYN-"
DEAL_V0_ABSENT = "absent; built-in list used"

LAB_REQUIRED_KEYS: tuple[str, ...] = (
    "lab_version", "sector", "subsector", "sector_playbook_key", "archetype_id", "asof",
    "deal_status", "knobs", "intake_facts", "intake_docs", "review_plan", "expected_report",
)
#: Keys whose values must be ISO literals or null wherever they appear.
DATE_KEYS: frozenset[str] = frozenset(
    {"date", "dated", "closing", "final_maturity", "cda_executed", "posted", "filed", "due",
     "asof", "check_date"}
)
_DATE_SHAPE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SEGMENT = re.compile(r"^([^\[\]]+)(?:\[([^\[\]]+)\])?$")


class ScenarioError(ValueError):
    """The scenario breaks a lab law; every problem is listed in the message."""


# --------------------------------------------------------------------------------------
# deal-v0 contract (read live, never pinned under lab/ -- COS question 3)
# --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class DealV0Contract:
    required: tuple[str, ...]
    id_pattern: str
    source: str  # "live" | DEAL_V0_ABSENT
    path: str
    sha256: str | None


def bondi_root() -> Path:
    return Path(os.environ.get(BONDI_ROOT_ENV, DEFAULT_BONDI_ROOT))


def deal_v0_contract() -> DealV0Contract:
    """`required` + `deal_id.pattern` from BONDI's live deal-v0.json, else the built-ins."""
    path = bondi_root() / DEAL_V0_REL
    try:
        raw = path.read_bytes()
        doc = json.loads(raw.decode("utf-8"))
        required = tuple(str(k) for k in doc["required"])
        pattern = str(doc["properties"]["deal_id"]["pattern"])
    except (OSError, ValueError, KeyError, TypeError):
        return DealV0Contract(BUILTIN_REQUIRED, BUILTIN_ID_PATTERN, DEAL_V0_ABSENT, str(path), None)
    return DealV0Contract(required, pattern, "live", str(path), sha256_bytes(raw))


# --------------------------------------------------------------------------------------
# BONDI emission format (transcribed; the vocabulary the loader validates against)
# --------------------------------------------------------------------------------------


def bondi_format(path: Path | None = None) -> dict[str, Any]:
    fmt_path = Path(path) if path is not None else BONDI_FORMAT_PATH
    return json.loads(fmt_path.read_text(encoding="utf-8"))


def known_event_names(fmt: dict[str, Any]) -> frozenset[str]:
    out: set[str] = set()
    for row in fmt["station_events_core"]:
        out.add(row["event"])
    for rows in fmt["station_events_by_pole"].values():
        out.update(r["event"] for r in rows)
    for row in fmt["station_events_post"]:
        out.add(row["event"])
    return frozenset(out)


# --------------------------------------------------------------------------------------
# Dotted-path delta materialisation (`a.b[0].c`, `stations.6_x.events[<event name>].date`)
# --------------------------------------------------------------------------------------


def _split_path(dotted: str) -> list[tuple[str, str | None]]:
    parts: list[tuple[str, str | None]] = []
    for seg in dotted.split("."):
        m = _SEGMENT.match(seg)
        if not m:
            raise ScenarioError(f"bad knob_delta path segment {seg!r} in {dotted!r}")
        parts.append((m.group(1), m.group(2)))
    return parts


def _index_into(container: Any, selector: str, dotted: str) -> Any:
    if not isinstance(container, list):
        raise ScenarioError(f"{dotted}: [{selector}] applied to a non-list")
    if selector.isdigit():
        idx = int(selector)
        if idx >= len(container):
            raise ScenarioError(f"{dotted}: index {idx} out of range")
        return container[idx]
    for item in container:
        if isinstance(item, dict) and item.get("event") == selector:
            return item
    raise ScenarioError(f"{dotted}: no list element with event == {selector!r}")


def apply_delta(data: dict[str, Any], dotted: str, value: Any) -> None:
    """Set `value` at `dotted` in place; every intermediate key must already exist."""
    parts = _split_path(dotted)
    node: Any = data
    for key, selector in parts[:-1]:
        if not isinstance(node, dict) or key not in node:
            raise ScenarioError(f"{dotted}: key {key!r} does not exist on the base")
        node = node[key]
        if selector is not None:
            node = _index_into(node, selector, dotted)
    key, selector = parts[-1]
    if not isinstance(node, dict) or key not in node:
        raise ScenarioError(f"{dotted}: key {key!r} does not exist on the base")
    if selector is None:
        node[key] = copy.deepcopy(value)
    else:
        target = _index_into(node[key], selector, dotted)
        raise ScenarioError(f"{dotted}: cannot replace a whole list element ({type(target).__name__})")


def materialise(base: dict[str, Any], variant: dict[str, Any]) -> dict[str, Any]:
    """Base deep-copied, `knob_delta` applied, `deal_id`/`derived_from`/`knob_delta` set."""
    data = copy.deepcopy(base)
    delta = variant.get("knob_delta") or {}
    if not isinstance(delta, dict) or not delta:
        raise ScenarioError("a derived scenario needs a non-empty knob_delta")
    for dotted, value in delta.items():
        apply_delta(data, dotted, value)
    data["deal_id"] = variant["deal_id"]
    data["derived_from"] = variant["derived_from"]
    data["knob_delta"] = copy.deepcopy(delta)
    if variant.get("mode") is not None:
        data["mode"] = variant["mode"]
    return data


def diff_paths(
    a: Any, b: Any, *, ignore: tuple[str, ...] = ("deal_id", "derived_from", "knob_delta"),
) -> list[str]:
    """Dotted paths (events[<name>] form for event lists) where `a` and `b` differ."""
    out: list[str] = []

    def walk(x: Any, y: Any, prefix: str) -> None:
        if isinstance(x, dict) and isinstance(y, dict):
            for key in sorted(set(x) | set(y)):
                sub = f"{prefix}.{key}" if prefix else key
                if key not in x or key not in y:
                    out.append(sub)
                else:
                    walk(x[key], y[key], sub)
        elif isinstance(x, list) and isinstance(y, list):
            if len(x) != len(y):
                out.append(prefix)
                return
            for i, (xi, yi) in enumerate(zip(x, y, strict=True)):
                if isinstance(xi, dict) and "event" in xi:
                    walk(xi, yi, f"{prefix}[{xi['event']}]")
                else:
                    walk(xi, yi, f"{prefix}[{i}]")
        elif x != y or type(x) is not type(y):
            out.append(prefix)

    walk(a, b, "")
    return [p for p in out if p.split(".")[0].split("[")[0] not in ignore]


# --------------------------------------------------------------------------------------
# Validation
# --------------------------------------------------------------------------------------


def _walk_dates(node: Any, prefix: str, problems: list[str]) -> None:
    if isinstance(node, dict):
        for key, value in node.items():
            sub = f"{prefix}.{key}" if prefix else str(key)
            if key in DATE_KEYS:
                if value is None:
                    continue
                if not isinstance(value, str) or not _DATE_SHAPE.match(value):
                    problems.append(f"{sub}: must be an ISO literal YYYY-MM-DD or null, got {value!r}")
                    continue
                try:
                    _date.fromisoformat(value)
                except ValueError:
                    problems.append(f"{sub}: not a real calendar date: {value!r}")
            else:
                _walk_dates(value, sub, problems)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _walk_dates(item, f"{prefix}[{i}]", problems)
    elif isinstance(node, str) and _DATE_SHAPE.match(node):
        try:
            _date.fromisoformat(node)
        except ValueError:
            problems.append(f"{prefix}: date-shaped literal is not a real date: {node!r}")


def _check_name(value: Any, where: str, problems: list[str], *, allow_null: bool = False) -> None:
    if value is None:
        if not allow_null:
            problems.append(f"{where}: name is null")
        return
    if not isinstance(value, str):
        problems.append(f"{where}: name must be a string")
        return
    try:
        names_mod.require_tabled(value)
    except (names_mod.NameNotTabled, names_mod.NameCollision) as exc:
        problems.append(f"{where}: {exc}")


def validate(data: dict[str, Any], contract: DealV0Contract | None = None) -> None:
    """Raise `ScenarioError` listing every problem; return None when clean."""
    contract = contract or deal_v0_contract()
    problems: list[str] = []

    for key in contract.required:
        if key not in data:
            problems.append(f"deal-v0 required key missing: {key}")
    deal_id = data.get("deal_id")
    if not isinstance(deal_id, str) or not re.match(contract.id_pattern, deal_id):
        problems.append(f"deal_id must match {contract.id_pattern!r}: {deal_id!r}")
    elif not law.LAB_DEAL_ID_RE.match(deal_id):
        problems.append(f"lab deal ids look like SYN-HSG-AZ-2025-LAB01: {deal_id!r}")
    if deal_id == law.DEMO_DEAL_ID:
        problems.append(f"deal_id must never equal the demo id {law.DEMO_DEAL_ID}")
    if data.get("mode") != "synthetic":
        problems.append(f"mode must be 'synthetic' (calibration rejected structurally): {data.get('mode')!r}")
    if not isinstance(data.get("seed"), int) or isinstance(data.get("seed"), bool):
        problems.append("seed must be an integer")

    if data.get("deal_status") is not None and data["deal_status"] not in ("closed", *law.HOLD_STATUSES):
        problems.append(f"deal_status {data['deal_status']!r} not in closed|{law.HOLD_STATUSES}")

    # parties + labels: every name from the table, blocklist-clean
    parties = data.get("parties")
    if not isinstance(parties, list) or not parties:
        problems.append("parties must be a non-empty list")
        parties = []
    roles: list[str] = []
    for i, party in enumerate(parties):
        if not isinstance(party, dict) or "role" not in party:
            problems.append(f"parties[{i}]: needs a role")
            continue
        roles.append(str(party["role"]))
        _check_name(party.get("name"), f"parties[{i}] ({party['role']})", problems,
                    allow_null=party.get("status") == "unrated")
    if roles.count("municipal_advisor") and roles.count("underwriter"):
        ma = next(p["name"] for p in parties if p.get("role") == "municipal_advisor")
        uw = next(p["name"] for p in parties if p.get("role") == "underwriter")
        if ma == uw:
            problems.append("municipal_advisor and underwriter share a name (G-23 separation)")
    op = data.get("obligated_person")
    if isinstance(op, dict):
        _check_name(op.get("name"), "obligated_person", problems)
        if op.get("city") is not None:
            _check_name(op.get("city"), "obligated_person.city", problems)
    disclosure = data.get("disclosure")
    if isinstance(disclosure, dict) and disclosure.get("dissemination_agent") is not None:
        _check_name(disclosure["dissemination_agent"], "disclosure.dissemination_agent", problems)
        for j, afs in enumerate(disclosure.get("afs") or []):
            if not isinstance(afs, dict) or not isinstance(afs.get("fy"), int):
                problems.append(f"disclosure.afs[{j}]: needs an integer fy")
            elif afs.get("status") is not None and afs["status"] not in law.BONDI_EVENT_STATUSES:
                problems.append(f"disclosure.afs[{j}]: status {afs['status']!r} not a BONDI event status")
        for j, me in enumerate(disclosure.get("material_events") or []):
            if not isinstance(me, dict) or not me.get("type"):
                problems.append(f"disclosure.material_events[{j}]: needs a type")

    # stations
    stations = data.get("stations")
    if not isinstance(stations, dict):
        problems.append("stations must be a dict keyed 1_facility .. 6_borrower_prep")
        stations = {}
    unknown_stations = sorted(set(stations) - set(law.BONDI_STATIONS))
    if unknown_stations:
        problems.append(f"unknown station keys {unknown_stations}")
    try:
        fmt = bondi_format()
        event_names = known_event_names(fmt)
    except (OSError, ValueError, KeyError):
        fmt = None
        event_names = frozenset()
        problems.append(f"{law.LAB_ROOT.name}/fixtures/bondi-reference/format.json unreadable")
    seen_events: set[str] = set()
    for station, block in stations.items():
        if not isinstance(block, dict):
            problems.append(f"stations.{station}: must be a dict")
            continue
        for label_key in ("issuer", "borrower"):
            if block.get(label_key) is not None:
                _check_name(block[label_key], f"stations.{station}.{label_key}", problems)
        for k, ev in enumerate(block.get("events") or []):
            where = f"stations.{station}.events[{k}]"
            if not isinstance(ev, dict):
                problems.append(f"{where}: must be a dict")
                continue
            name = ev.get("event")
            if not isinstance(name, str) or not name:
                problems.append(f"{where}: event name missing")
                continue
            if name in seen_events:
                problems.append(f"{where}: duplicate event name {name!r}")
            seen_events.add(name)
            if fmt is not None and name not in event_names and not law.is_lab_extension_event(name):
                problems.append(f"{where}: event {name!r} is not a BONDI station event nor a lab extension")
            if ev.get("status") not in law.BONDI_EVENT_STATUSES:
                problems.append(f"{where}: status {ev.get('status')!r} not in {law.BONDI_EVENT_STATUSES}")
            if not ev.get("actor_role"):
                problems.append(f"{where}: actor_role missing")
            if "date" not in ev:
                problems.append(f"{where}: date key missing (use null when not carried)")
            if ev.get("status") == "fired" and ev.get("date") is None:
                problems.append(f"{where}: a fired event needs a scenario-literal date")
            if ev.get("status") != "fired" and ev.get("date") is not None:
                problems.append(f"{where}: only fired events carry a date")
    closing_station = stations.get("3_issuance", {}).get("closing") if isinstance(stations.get("3_issuance"), dict) else None
    instrument = data.get("instrument")
    if isinstance(instrument, dict) and closing_station is not None and instrument.get("closing") != closing_station:
        problems.append("instrument.closing and stations.3_issuance.closing disagree")

    # constraints
    constraints = data.get("constraints")
    if not isinstance(constraints, list):
        problems.append("constraints must be a list")
        constraints = []
    for k, c in enumerate(constraints):
        if not isinstance(c, dict) or not c.get("id"):
            problems.append(f"constraints[{k}]: needs an id")
        elif c.get("status") not in law.CONSTRAINT_STATUSES:
            problems.append(f"constraints[{k}] ({c['id']}): status {c.get('status')!r} not in {law.CONSTRAINT_STATUSES}")

    # dates everywhere
    _walk_dates(data, "", problems)

    # lab block
    lab = data.get("lab")
    if not isinstance(lab, dict):
        problems.append("lab block missing")
    else:
        for key in LAB_REQUIRED_KEYS:
            if key not in lab:
                problems.append(f"lab.{key} missing")
        if lab.get("deal_status") is not None and lab["deal_status"] not in ("closed", *law.HOLD_STATUSES):
            problems.append(f"lab.deal_status {lab['deal_status']!r} not in closed|{law.HOLD_STATUSES}")
        facts = lab.get("intake_facts")
        docs = lab.get("intake_docs")
        if not isinstance(facts, dict) or not facts:
            problems.append("lab.intake_facts must be a non-empty dict")
            facts = {}
        for path, value in facts.items():
            if not isinstance(value, str) or not value.strip():
                problems.append(f"lab.intake_facts[{path}]: every value is a non-empty string (compared as string)")
        if not isinstance(docs, dict) or not docs:
            problems.append("lab.intake_docs must be a non-empty dict")
            docs = {}
        placed: dict[str, str] = {}
        for artifact_key, paths in docs.items():
            if paths is None:
                continue  # dropped by knob; the paths stay in intake_facts as unknowns
            if not isinstance(paths, list) or not paths:
                problems.append(f"lab.intake_docs[{artifact_key}]: list of paths or null")
                continue
            for p in paths:
                if p not in facts:
                    problems.append(f"lab.intake_docs[{artifact_key}]: {p} has no intake_facts value")
                if p in placed:
                    problems.append(f"{p} appears in two intake docs ({placed[p]}, {artifact_key})")
                placed[p] = artifact_key
        knobs = lab.get("knobs")
        if not isinstance(knobs, dict):
            problems.append("lab.knobs must be a dict")
        else:
            dropped = knobs.get("drop_required_artifact")
            if dropped is not None and docs.get(dropped, "missing") is not None:
                problems.append(f"knobs.drop_required_artifact={dropped!r} but lab.intake_docs.{dropped} is not null")
            for key, val in docs.items():
                if val is None and dropped != key:
                    problems.append(f"lab.intake_docs.{key} is null but no knob names it")
            if knobs.get("deal_status") is not None and knobs["deal_status"] != lab.get("deal_status"):
                problems.append("lab.knobs.deal_status and lab.deal_status disagree")
        plan = lab.get("review_plan")
        if not isinstance(plan, dict):
            problems.append("lab.review_plan must be a dict")
        else:
            if plan.get("reviewer_id") != law.REVIEWER_ID:
                problems.append(f"lab.review_plan.reviewer_id must be law.REVIEWER_ID ({law.REVIEWER_ID})")
            for p in plan.get("reject") or []:
                if p not in facts:
                    problems.append(f"lab.review_plan.reject names unknown path {p}")
    if problems:
        raise ScenarioError(f"{deal_id}: " + "; ".join(problems))


# --------------------------------------------------------------------------------------
# Demo-core comparison (S01: base-core == demo-core; spec 2.13 / F10)
# --------------------------------------------------------------------------------------


def core_view(data: dict[str, Any]) -> dict[str, Any]:
    """The shared core: obligated_person, parties (minus bfms_party_role), instrument,
    disclosure scalars, seed and the constraints the demo carries."""
    parties = [
        {k: v for k, v in p.items() if k != "bfms_party_role"} for p in data.get("parties", [])
    ]
    disclosure = data.get("disclosure") or {}
    demo_constraint_ids = {"rule_15c2_12_applicability", "irc_142d_set_aside"}
    return {
        "obligated_person": data.get("obligated_person"),
        "parties": parties,
        "instrument": data.get("instrument"),
        "disclosure_scalars": {k: v for k, v in disclosure.items() if not isinstance(v, list | dict)},
        "seed": data.get("seed"),
        "demo_constraints": [c for c in data.get("constraints", []) if c.get("id") in demo_constraint_ids],
    }


def demo_core(path: Path | None = None) -> dict[str, Any]:
    demo = json.loads((Path(path) if path else DEMO_SCENARIO_PATH).read_text(encoding="utf-8"))
    return core_view(demo)


def base_core_vs_demo(data: dict[str, Any], demo_path: Path | None = None) -> list[str]:
    """Dotted paths where the scenario core differs from the demo core (empty == equal)."""
    return diff_paths(core_view(data), demo_core(demo_path), ignore=())


# --------------------------------------------------------------------------------------
# Loaded scenario
# --------------------------------------------------------------------------------------


@dataclass
class Scenario:
    path: Path
    raw_bytes: bytes
    #: sha256 of `raw_bytes` for a base scenario; for a variant, of `raw_bytes` and the base
    #: file bytes together (a change to the base file changes the materialised run, so it
    #: must change the scenario hash and the run id).
    sha256: str
    data: dict[str, Any]
    contract: DealV0Contract
    derived_from: str | None = None
    knob_delta: dict[str, Any] = field(default_factory=dict)
    base_path: Path | None = None
    base_raw_bytes: bytes = b""

    @property
    def deal_id(self) -> str:
        return str(self.data["deal_id"])

    @property
    def seed(self) -> int:
        return int(self.data["seed"])

    @property
    def lab(self) -> dict[str, Any]:
        return self.data["lab"]

    @property
    def asof(self) -> str:
        return str(self.lab["asof"])

    @property
    def deal_status(self) -> str:
        return str(self.data.get("deal_status") or self.lab.get("deal_status") or "closed")

    @property
    def on_hold(self) -> bool:
        return self.deal_status in law.HOLD_STATUSES

    @property
    def closing(self) -> str | None:
        """The scenario's closing literal (never computed; None when not carried)."""
        value = (self.data.get("instrument") or {}).get("closing")
        return str(value) if value else None

    @property
    def intake_facts(self) -> dict[str, str]:
        return dict(self.lab["intake_facts"])

    @property
    def intake_docs(self) -> dict[str, list[str]]:
        """artifact_key -> paths, in scenario order, dropped artifacts omitted."""
        return {k: list(v) for k, v in self.lab["intake_docs"].items() if v is not None}

    @property
    def dropped_artifacts(self) -> list[str]:
        return [k for k, v in self.lab["intake_docs"].items() if v is None]

    @property
    def present_intake_paths(self) -> list[str]:
        return [p for paths in self.intake_docs.values() for p in paths]

    @property
    def dropped_intake_paths(self) -> list[str]:
        present = set(self.present_intake_paths)
        return [p for p in self.intake_facts if p not in present]

    @property
    def deal_v0_schema_note(self) -> str:
        return "live" if self.contract.source == "live" else DEAL_V0_ABSENT


def _read_json(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        doc = json.loads(raw.decode("utf-8"))
    except ValueError as exc:
        raise ScenarioError(f"{path}: not valid JSON ({exc})") from exc
    if not isinstance(doc, dict):
        raise ScenarioError(f"{path}: top level must be an object")
    return raw, doc


def load(path: Path | str, *, contract: DealV0Contract | None = None) -> Scenario:
    """Load, materialise (variants) and validate a scenario file."""
    path = Path(path)
    raw, doc = _read_json(path)
    contract = contract or deal_v0_contract()
    derived_from = doc.get("derived_from")
    base_path: Path | None = None
    base_raw = b""
    if derived_from is not None:
        if not isinstance(derived_from, str) or not law.SYN_ID_RE.match(derived_from):
            raise ScenarioError(f"{path}: derived_from must be a SYN- deal id")
        if "deal_id" not in doc:
            raise ScenarioError(f"{path}: a derived scenario needs its own deal_id")
        base_path = path.with_name(f"{derived_from}.synthetic.json")
        if not base_path.is_file():
            raise ScenarioError(f"{path}: base scenario {base_path.name} not found beside it")
        base_raw, base = _read_json(base_path)
        if base.get("derived_from") is not None:
            raise ScenarioError(f"{path}: base {base_path.name} is itself derived (one level only)")
        validate(base, contract)
        data = materialise(base, doc)
    else:
        data = copy.deepcopy(doc)
    validate(data, contract)
    return Scenario(
        path=path,
        raw_bytes=raw,
        sha256=sha256_bytes(raw + b"||base||" + base_raw) if derived_from is not None else sha256_bytes(raw),
        data=data,
        contract=contract,
        derived_from=derived_from,
        knob_delta=dict(doc.get("knob_delta") or {}),
        base_path=base_path,
        base_raw_bytes=base_raw,
    )


def load_base_of(scenario: Scenario) -> dict[str, Any] | None:
    """The validated base data of a derived scenario (None for a base scenario)."""
    if scenario.base_path is None:
        return None
    _, base = _read_json(scenario.base_path)
    return base


def scenario_file_sha256(path: Path | str) -> str:
    return sha256_file(Path(path))


__all__ = [
    "BONDI_FORMAT_PATH",
    "BONDI_ROOT_ENV",
    "BUILTIN_ID_PATTERN",
    "BUILTIN_REQUIRED",
    "DATE_KEYS",
    "DEAL_V0_ABSENT",
    "DEFAULT_BONDI_ROOT",
    "DEMO_SCENARIO_PATH",
    "LAB_REQUIRED_KEYS",
    "REPO_ROOT",
    "SCENARIOS_DIR",
    "DealV0Contract",
    "Scenario",
    "ScenarioError",
    "apply_delta",
    "base_core_vs_demo",
    "bondi_format",
    "bondi_root",
    "core_view",
    "deal_v0_contract",
    "demo_core",
    "diff_paths",
    "known_event_names",
    "load",
    "load_base_of",
    "materialise",
    "scenario_file_sha256",
    "validate",
]
