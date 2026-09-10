"""`bondi/event_log.csv` -> DealWorkflow conformance (BUILD-SPEC 5, row S14; critic M10).

One `ConformanceRow` per log row. A DocumentState / phase / open item advances ONLY on a
`fired`, dated event whose evidence is in the pack (or was observed by an earlier stage);
`validate_deal_workflow` runs after every event. Dates are copied from the log row
(scenario literals), never computed.

Mapping (spec S14):

| event               | BFMS object                                    | evidence                          |
|---------------------|------------------------------------------------|-----------------------------------|
| issuer_engagement   | phase engagement -> completed                   | S03 project created               |
| prelim_resolution   | open item issuer-initial-closing-checklist -> in_progress | governance.inducement approved fact |
| application_filed   | phase diligence -> current                      | S05 uploads                       |
| indemnity_accepted  | (none)                                         | not_applicable                    |
| tefra_notice/hearing| (log unknown)                                  | unknown                           |
| afa_confirm         | open item afa-confirm APPENDED, blocked (M10)   | unknown (second board not carried)|
| final_resolution    | open item issuer-initial-closing-checklist -> completed | bond_counsel.inducement_resolution approved fact |
| scale_locked        | (mirror only, no number)                       | not_applicable                    |
| indenture_executed  | document trust-indenture -> executed            | closing-documents/01              |
| g17_letter          | (none)                                         | not_applicable                    |
| lom_posted          | document limited-offering-memorandum            | not carried -> unknown            |
| investment_letters  | document investor-letters                       | not carried -> unknown            |
| closing             | phase closing -> completed, deal.closing_date; post-closing stays planned | instrument.closing literal |
| g32_os_filed        | document limited-offering-memorandum (filed)    | not carried -> unknown            |
| cda_executed        | document continuing-disclosure-agreement -> executed | closing-documents/03 + S13 signed |
| 8038_filed          | document tax-documents                          | form not carried -> unknown       |
| afs_posted_fy*      | phase post-closing planned -> current (the ONLY event that moves it) | post-close/vault/afs-FY<fy>.txt |
| listed_or_material:*| (no BFMS object)                               | not_applicable                    |

Hold statuses (`deal_status` in law.HOLD_STATUSES) leave closing / post-closing planned.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from typing import Any

from labkit import law
from labkit.types import ConformanceRow

LAB_REPLAY_SYSTEM = "lab_replay"
AFA_OPEN_ITEM_ID = "afa-confirm"
CHECKLIST_OPEN_ITEM_ID = "issuer-initial-closing-checklist"

NO_OBJECT_EVENTS: dict[str, str] = {
    "indemnity_accepted": "no BFMS object for a conduit indemnity acceptance",
    "g17_letter": "no BFMS object for an underwriter G-17 letter",
    "scale_locked": "mirror only; the workflow carries no number",
}
NOT_CARRIED_DOCUMENTS: dict[str, tuple[str, str]] = {
    "lom_posted": ("limited-offering-memorandum", "limited offering memorandum not carried by the pack"),
    "investment_letters": ("investor-letters", "investor letters not carried by the pack"),
    "g32_os_filed": ("limited-offering-memorandum", "G-32 filing not carried by the pack (no document)"),
    "8038_filed": ("tax-documents", "Form 8038 not carried by the pack (scenario date only)"),
}


@dataclass
class Evidence:
    """What earlier stages and the pack can vouch for."""

    project_created: bool = False
    uploads_done: bool = False
    approved_paths: frozenset[str] = frozenset()
    pack_files: frozenset[str] = frozenset()  # pack-relative posix paths
    cda_signed_in_bfms: bool = False
    closing_literal: str | None = None
    deal_status: str = "closed"


@dataclass
class ReplayResult:
    rows: list[ConformanceRow]
    workflow: Any
    counts: dict[str, int] = field(default_factory=dict)
    validation_errors: list[str] = field(default_factory=list)

    def mirror(self) -> dict[str, Any]:
        wf = self.workflow
        return {
            "deal_phase": wf.deal.phase,
            "closing_date": wf.deal.closing_date.isoformat() if wf.deal.closing_date else None,
            "phase_timeline": [
                {
                    "phase": t.phase,
                    "status": t.status,
                    "completed_date": t.completed_date.isoformat() if t.completed_date else None,
                }
                for t in wf.phase_timeline
            ],
            "document_states": wf.document_state_matrix(),
            "open_items": [
                {
                    "id": i.id,
                    "status": i.status.value if hasattr(i.status, "value") else str(i.status),
                    "completed_date": i.completed_date.isoformat() if i.completed_date else None,
                    "source": i.source.system,
                }
                for i in wf.open_items
            ],
        }


def read_event_log(path: Path) -> list[dict[str, str]]:
    with Path(path).open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    header = list(rows[0].keys()) if rows else []
    if rows and tuple(header) != law.EVENT_LOG_HEADER:
        raise ValueError(f"event_log header {header} != {law.EVENT_LOG_HEADER}")
    return rows


def _timeline(workflow: Any, phase: str) -> Any:
    for entry in workflow.phase_timeline:
        if entry.phase == phase:
            return entry
    return None


def _document(workflow: Any, doc_id: str) -> Any:
    for doc in workflow.documents:
        if doc.id == doc_id:
            return doc
    return None


def _open_item(workflow: Any, item_id: str) -> Any:
    return workflow.open_items_by_id.get(item_id)


def _phase_state(workflow: Any, phase: str) -> str:
    entry = _timeline(workflow, phase)
    return entry.status if entry is not None else "absent"


def _advance_document(doc: Any, state: str, when: _date) -> None:
    states = tuple(dict.fromkeys(doc.states_completed + (state,)))
    doc.current_state = state
    doc.states_completed = states
    doc.last_updated = when


def _complete_phase(workflow: Any, phase: str, when: _date, *, next_phase: str | None = None) -> None:
    entry = _timeline(workflow, phase)
    if entry is not None:
        entry.status = "completed"
        entry.completed_date = when
    if next_phase is not None:
        nxt = _timeline(workflow, next_phase)
        if nxt is not None and nxt.status == "planned":
            nxt.status = "current"
        workflow.deal.phase = next_phase


def apply(log_rows: list[dict[str, str]], workflow: Any, evidence: Evidence) -> ReplayResult:
    """Replay every log row against `workflow` (mutated in place) and return the rows."""
    from munipal.services.deal_workflow import (
        DealWorkflowValidationError,
        OpenItem,
        OpenItemStatus,
        SourceBreadcrumb,
        validate_deal_workflow,
    )

    rows: list[ConformanceRow] = []
    on_hold = evidence.deal_status in law.HOLD_STATUSES
    conduit_issuer = workflow.deal.conduit_issuer

    for log in log_rows:
        event = log["event"]
        station = log["station"]
        log_status = log["status"]
        date_literal = log["date"] or None
        when = _date.fromisoformat(date_literal) if date_literal else None
        fired = log_status == "fired" and when is not None

        bfms_object = "(none)"
        expected_state = "unchanged"
        observed_state = "unchanged"
        evidence_ref: str | None = None
        status = "unknown"
        reason = ""

        try:
            if event in NO_OBJECT_EVENTS:
                status, reason = "not_applicable", NO_OBJECT_EVENTS[event]
            elif event.startswith("listed_or_material:"):
                status, reason = "not_applicable", "no BFMS post-close object for a listed-event notice"
            elif on_hold and (event in ("closing", "g32_os_filed", "cda_executed", "8038_filed") or law.is_lab_extension_event(event)):
                status, reason = "unknown", f"deal_status={evidence.deal_status}; close not invented"
            elif log_status != "fired" and event == "afa_confirm":
                bfms_object = f"OpenItem {AFA_OPEN_ITEM_ID} (appended by lab replay, M10)"
                expected_state = "blocked"
                if _open_item(workflow, AFA_OPEN_ITEM_ID) is None:
                    workflow.open_items.append(
                        OpenItem(
                            id=AFA_OPEN_ITEM_ID,
                            owner=conduit_issuer,
                            description="Second-board (AFA) confirmation is not carried by the scenario; item blocked until a human supplies it.",
                            status=OpenItemStatus.BLOCKED,
                            blocks_closing=False,
                            first_seen=None,
                            source=SourceBreadcrumb(system=LAB_REPLAY_SYSTEM),
                            human_confirmation_required=True,
                        )
                    )
                item = _open_item(workflow, AFA_OPEN_ITEM_ID)
                observed_state = item.status.value if hasattr(item.status, "value") else str(item.status)
                status, reason = "unknown", f"log status {log_status}: second board not carried; open item appended blocked, human confirmation required"
            elif log_status != "fired":
                status, reason = "unknown", f"log status {log_status}: {log.get('reason') or 'not carried by scenario'}"
            elif not fired:
                status, reason = "unknown", "fired row without a scenario-literal date"
            elif event == "issuer_engagement":
                bfms_object = "PhaseTimeline engagement"
                expected_state = "completed"
                if evidence.project_created:
                    _complete_phase(workflow, "engagement", when)
                    evidence_ref = "S03 project created"
                    observed_state = _phase_state(workflow, "engagement")
                    status = "pass" if observed_state == expected_state else "fail"
                else:
                    observed_state = _phase_state(workflow, "engagement")
                    status, reason = "unknown", "S03 did not create the project; phase left as is"
            elif event == "prelim_resolution":
                bfms_object = f"OpenItem {CHECKLIST_OPEN_ITEM_ID}"
                expected_state = "in_progress"
                item = _open_item(workflow, CHECKLIST_OPEN_ITEM_ID)
                if item is None:
                    status, reason = "fail", "seed open item missing from the workflow"
                elif "governance.inducement" in evidence.approved_paths:
                    item.status = OpenItemStatus.IN_PROGRESS
                    item.last_updated = when
                    item.first_seen = item.first_seen or when
                    evidence_ref = "approved fact governance.inducement"
                    observed_state = item.status.value
                    status = "pass"
                else:
                    observed_state = item.status.value
                    status, reason = "unknown", "governance.inducement has no approved fact; item left as is"
            elif event == "application_filed":
                bfms_object = "PhaseTimeline diligence"
                expected_state = "current"
                if evidence.uploads_done:
                    entry = _timeline(workflow, "diligence")
                    if entry is not None and entry.status == "planned":
                        entry.status = "current"
                    workflow.deal.phase = "diligence"
                    evidence_ref = "S05 uploads"
                    observed_state = _phase_state(workflow, "diligence")
                    status = "pass" if observed_state == expected_state else "fail"
                else:
                    observed_state = _phase_state(workflow, "diligence")
                    status, reason = "unknown", "S05 uploaded nothing; phase left as is"
            elif event == "final_resolution":
                bfms_object = f"OpenItem {CHECKLIST_OPEN_ITEM_ID}"
                expected_state = "completed"
                item = _open_item(workflow, CHECKLIST_OPEN_ITEM_ID)
                if item is None:
                    status, reason = "fail", "seed open item missing from the workflow"
                elif "bond_counsel.inducement_resolution" in evidence.approved_paths:
                    item.status = OpenItemStatus.COMPLETED
                    item.completed_date = when
                    item.last_updated = when
                    evidence_ref = "approved fact bond_counsel.inducement_resolution"
                    observed_state = item.status.value
                    status = "pass"
                else:
                    observed_state = item.status.value
                    status, reason = "unknown", "bond_counsel.inducement_resolution has no approved fact; item left as is"
            elif event == "indenture_executed":
                bfms_object = "DealDocument trust-indenture"
                expected_state = "executed"
                doc = _document(workflow, "trust-indenture")
                ref = "closing-documents/01-indenture-excerpt.md"
                if doc is None:
                    status, reason = "fail", "trust-indenture missing from the workflow documents"
                elif ref in evidence.pack_files:
                    _advance_document(doc, "executed", when)
                    evidence_ref = ref
                    observed_state = doc.current_state
                    status = "pass"
                else:
                    observed_state = doc.current_state
                    status, reason = "unknown", f"{ref} not in the pack; state unchanged"
            elif event in NOT_CARRIED_DOCUMENTS:
                doc_id, why = NOT_CARRIED_DOCUMENTS[event]
                bfms_object = f"DealDocument {doc_id}"
                doc = _document(workflow, doc_id)
                observed_state = doc.current_state if doc is not None else "absent"
                status, reason = "unknown", why
            elif event == "closing":
                bfms_object = "PhaseTimeline closing + DealMetadata.closing_date"
                expected_state = "completed"
                if evidence.closing_literal == date_literal:
                    for phase in ("drafting", "marketing", "pricing", "pre-closing"):
                        entry = _timeline(workflow, phase)
                        if entry is not None and entry.status == "current":
                            entry.status = "completed"
                    # closing completes its own phase only; post-closing stays `planned`
                    # until the afs_posted_fy* row (the one event with post-close evidence)
                    _complete_phase(workflow, "closing", when)
                    workflow.deal.phase = "closing"
                    workflow.deal.closing_date = when
                    evidence_ref = "instrument.closing literal"
                    observed_state = _phase_state(workflow, "closing")
                    status = "pass" if observed_state == expected_state else "fail"
                else:
                    observed_state = _phase_state(workflow, "closing")
                    status, reason = "unknown", "closing row date differs from instrument.closing; not applied"
            elif event == "cda_executed":
                bfms_object = "DealDocument continuing-disclosure-agreement"
                expected_state = "executed"
                doc = _document(workflow, "continuing-disclosure-agreement")
                ref = "closing-documents/03-continuing-disclosure-agreement.md"
                if doc is None:
                    status, reason = "fail", "continuing-disclosure-agreement missing from the workflow documents"
                elif ref in evidence.pack_files and evidence.cda_signed_in_bfms:
                    _advance_document(doc, "executed", when)
                    evidence_ref = f"{ref} + S13 signed"
                    observed_state = doc.current_state
                    status = "pass"
                else:
                    observed_state = doc.current_state
                    missing = [] if ref in evidence.pack_files else [ref]
                    if not evidence.cda_signed_in_bfms:
                        missing.append("S13 signed")
                    status, reason = "unknown", "evidence incomplete: " + ", ".join(missing)
            elif law.is_lab_extension_event(event) and event.startswith("afs_posted_fy"):
                fy = event[len("afs_posted_fy"):]
                bfms_object = "PhaseTimeline post-closing"
                expected_state = "current"
                ref = f"post-close/vault/afs-FY{fy}.txt"
                if ref in evidence.pack_files:
                    entry = _timeline(workflow, "post-closing")
                    before = _phase_state(workflow, "post-closing")
                    if entry is not None and entry.status == "planned":
                        entry.status = "current"
                    workflow.deal.phase = "post-closing"
                    evidence_ref = ref
                    observed_state = _phase_state(workflow, "post-closing")
                    # pass means THIS row moved the phase: it was still planned before it
                    status = "pass" if observed_state == expected_state and before == "planned" else "fail"
                    if status == "fail":
                        reason = f"post-closing was {before!r} before this row; the afs row must be the one that moves it"
                else:
                    observed_state = _phase_state(workflow, "post-closing")
                    status, reason = "unknown", f"{ref} not in the pack; phase left as is"
            else:
                status, reason = "unknown", "no conformance mapping for this event"

            validate_deal_workflow(workflow)
        except DealWorkflowValidationError as exc:
            status, reason = "fail", f"workflow validation failed after {event}: {exc}"
        except ValueError as exc:
            status, reason = "fail", f"replay error at {event}: {exc}"

        if status in ("unknown", "not_applicable") and not reason:
            reason = "not carried by scenario"
        rows.append(
            ConformanceRow(
                event=event,
                station=station,
                log_status=log_status,
                date=date_literal,
                bfms_object=bfms_object,
                expected_state=expected_state,
                observed_state=observed_state,
                evidence_ref=evidence_ref,
                status=status,  # type: ignore[arg-type]
                reason=reason,
            )
        )

    counts = dict.fromkeys(law.FOUR_VALUES, 0)
    for row in rows:
        counts[row.status] += 1
    return ReplayResult(rows=rows, workflow=workflow, counts=counts)


__all__ = [
    "AFA_OPEN_ITEM_ID",
    "CHECKLIST_OPEN_ITEM_ID",
    "LAB_REPLAY_SYSTEM",
    "NOT_CARRIED_DOCUMENTS",
    "NO_OBJECT_EVENTS",
    "Evidence",
    "ReplayResult",
    "apply",
    "read_event_log",
]
