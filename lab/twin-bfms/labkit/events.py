"""The lab's own BONDI-format emitter (BUILD-SPEC 4.4). Consumed format, never vendored.

Emits into `packs/<deal_id>/bondi/`:

- `deal.json`               the materialised scenario;
- `event_log.csv`           columns `date,station,event,actor_role,status,reason`, dated rows
                            first (by date, then event), empty-date rows last (by event);
- `constraint_report.json`  `{"constraint_report": [{id, status, cite?, note?}]}` copied from
                            the scenario -- the lab never recomputes a constraint;
- `artifact_manifest.json`  `{"artifacts": [{id, path, kind, sha256}]}` for every pack file.

Dates are copied from the scenario, never computed: a row for an event the scenario does not
date carries an empty date and status `unknown` (or `skipped` when the scenario says so).
Hold statuses (`deal_status` in law.HOLD_STATUSES) turn the close-side rows into empty-date
rows whose status is the hold value ("close not invented").

The station / event vocabulary is the transcription in `fixtures/bondi-reference/format.json`
(generate.py:42-82 of the BONDI working paper), plus the two lab extension names.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from labkit import law
from labkit.provenance import PackManifest, WrittenFile, sha256_text, write_csv, write_json
from labkit.types import Envelope

#: Rows a hold status suspends (BONDI rule: post_close set + the lab's afs rows).
POST_CLOSE_EVENTS: frozenset[str] = frozenset({"closing", "g32_os_filed", "cda_executed", "8038_filed"})
BONDI_DIR_NAME = "bondi"
BONDI_FILES: tuple[str, ...] = (
    "deal.json", "event_log.csv", "constraint_report.json", "artifact_manifest.json",
)


@dataclass(frozen=True)
class EventRow:
    date: str  # ISO literal copied from the scenario, or ""
    station: str
    event: str
    actor_role: str
    status: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {k: getattr(self, k) for k in law.EVENT_LOG_HEADER}


@dataclass
class Emission:
    deal: dict[str, Any]
    events: list[EventRow]
    constraint_report: list[dict[str, Any]]
    scenario_dates: frozenset[str] = field(default_factory=frozenset)

    def dated_rows(self) -> list[EventRow]:
        return [r for r in self.events if r.date]

    def undated_rows(self) -> list[EventRow]:
        return [r for r in self.events if not r.date]


def _reason_for(ev: dict[str, Any], party_roles: set[str]) -> str:
    if ev.get("reason"):
        return str(ev["reason"])
    status = ev.get("status")
    if status == "fired":
        return ""
    if status == "skipped":
        role = str(ev.get("actor_role", ""))
        if role not in party_roles:
            return f"party role {role} absent"
        return "skipped by scenario"
    if status == "unknown":
        return "not carried by scenario; not invented"
    return f"deal_status={status}; close not invented"


def _hold_row(row: EventRow, hold: str) -> EventRow:
    return EventRow(
        date="", station=row.station, event=row.event, actor_role=row.actor_role,
        status=hold, reason=f"deal_status={hold}; close not invented",
    )


def _sort_key(row: EventRow) -> tuple[bool, str, str]:
    # generate.py:232 -- dated rows first (date, event); empty-date rows last (event).
    return (row.date == "", row.date, row.event)


def emit(data: dict[str, Any]) -> Emission:
    """Build the event log, constraint report and deal payload from a materialised scenario."""
    lab = data.get("lab") or {}
    deal_status = str(data.get("deal_status") or lab.get("deal_status") or "closed")
    hold = deal_status if deal_status in law.HOLD_STATUSES else None
    party_roles = {str(p.get("role")) for p in data.get("parties", [])}
    scenario_dates: set[str] = set()
    rows: list[EventRow] = []
    seen: dict[str, EventRow] = {}

    for station in law.BONDI_STATIONS:
        block = (data.get("stations") or {}).get(station) or {}
        for ev in block.get("events") or []:
            date = ev.get("date")
            if date:
                scenario_dates.add(str(date))
            row = EventRow(
                date=str(date) if date else "",
                station=station,
                event=str(ev["event"]),
                actor_role=str(ev.get("actor_role", "")),
                status=str(ev.get("status", "unknown")),
                reason=_reason_for(ev, party_roles),
            )
            if hold and (row.event in POST_CLOSE_EVENTS or law.is_lab_extension_event(row.event)):
                row = _hold_row(row, hold)
            seen[row.event] = row
            rows.append(row)

    disclosure = data.get("disclosure") or {}
    for afs in disclosure.get("afs") or []:
        name = f"afs_posted_fy{afs['fy']}"
        posted = afs.get("posted")
        status = str(afs.get("status") or ("fired" if posted else "unknown"))
        if posted:
            scenario_dates.add(str(posted))
        row = EventRow(
            date=str(posted) if posted else "",
            station="6_borrower_prep",
            event=name,
            actor_role="obligated_person",
            status=status,
            reason=str(afs.get("file") or ("" if posted else "afs posting not carried by scenario")),
        )
        if hold:
            row = _hold_row(row, hold)
        if name in seen:
            prior = seen[name]
            if (prior.date, prior.status) != (row.date, row.status):
                raise ValueError(
                    f"{name}: stations row ({prior.date!r}, {prior.status!r}) disagrees with "
                    f"disclosure.afs ({row.date!r}, {row.status!r})"
                )
            continue
        seen[name] = row
        rows.append(row)
    for me in disclosure.get("material_events") or []:
        name = f"listed_or_material:{me['type']}"
        date = me.get("date")
        if date:
            scenario_dates.add(str(date))
        row = EventRow(
            date=str(date) if date else "",
            station="6_borrower_prep",
            event=name,
            actor_role="obligated_person",
            status="fired" if date else "unknown",
            reason=str(me.get("summary") or ("" if date else "event date not carried by scenario")),
        )
        if hold:
            row = _hold_row(row, hold)
        if name in seen:
            raise ValueError(f"duplicate material event {name}")
        seen[name] = row
        rows.append(row)

    rows.sort(key=_sort_key)
    for row in rows:
        if row.status not in law.BONDI_EVENT_STATUSES:
            raise ValueError(f"{row.event}: status {row.status!r} outside the BONDI vocabulary")
        if row.status != "fired" and row.date:
            raise ValueError(f"{row.event}: only fired rows carry a date")
        if row.date and row.date not in scenario_dates:
            raise ValueError(f"{row.event}: date {row.date} is not a scenario literal")

    report: list[dict[str, Any]] = []
    for c in data.get("constraints") or []:
        item = {"id": c["id"], "status": c["status"]}
        if c.get("cite"):
            item["cite"] = c["cite"]
        if c.get("note"):
            item["note"] = c["note"]
        report.append(item)

    return Emission(deal=data, events=rows, constraint_report=report, scenario_dates=frozenset(scenario_dates))


def artifact_id(seed: int, relpath: str) -> str:
    """`SYN-ART-<sha256(seed||relpath)[:8]>` (BUILD-SPEC 4.6)."""
    return "SYN-ART-" + sha256_text(f"{seed}||{relpath}")[:8]


def write(
    emission: Emission,
    pack_root: Path,
    envelope: Envelope,
    manifest: PackManifest,
) -> dict[str, WrittenFile]:
    """Write deal.json, event_log.csv (+sidecar) and constraint_report.json under bondi/."""
    bondi = Path(pack_root) / BONDI_DIR_NAME
    out: dict[str, WrittenFile] = {}
    env = envelope.model_copy(update={"created_from": [f"scenario:{envelope.scenario_id}"]})
    out["deal.json"] = write_json(bondi / "deal.json", emission.deal, env, manifest=manifest)
    main, sidecar = write_csv(
        bondi / "event_log.csv",
        list(law.EVENT_LOG_HEADER),
        [r.as_dict() for r in emission.events],
        env.model_copy(update={"created_from": [f"scenario:{envelope.scenario_id}#stations", f"scenario:{envelope.scenario_id}#disclosure"]}),
        manifest=manifest,
    )
    out["event_log.csv"] = main
    out["event_log.csv.provenance.json"] = sidecar
    out["constraint_report.json"] = write_json(
        bondi / "constraint_report.json",
        {"constraint_report": emission.constraint_report},
        env.model_copy(update={"created_from": [f"scenario:{envelope.scenario_id}#constraints"]}),
        manifest=manifest,
    )
    return out


def write_artifact_manifest(
    pack_root: Path,
    envelope: Envelope,
    manifest: PackManifest,
) -> WrittenFile:
    """`bondi/artifact_manifest.json`: every pack file written so far, with a SYN-ART id."""
    artifacts = [
        {
            "id": artifact_id(envelope.seed, entry["path"]),
            "path": entry["path"],
            "kind": entry["kind"],
            "sha256": entry["sha256"],
        }
        for entry in sorted(manifest.files, key=lambda e: e["path"])
    ]
    return write_json(
        Path(pack_root) / BONDI_DIR_NAME / "artifact_manifest.json",
        {"artifacts": artifacts},
        envelope.model_copy(update={"created_from": [law.PACK_MANIFEST_NAME + " (files written before it)"]}),
        manifest=manifest,
    )


__all__ = [
    "BONDI_DIR_NAME",
    "BONDI_FILES",
    "POST_CLOSE_EVENTS",
    "Emission",
    "EventRow",
    "artifact_id",
    "emit",
    "write",
    "write_artifact_manifest",
]
