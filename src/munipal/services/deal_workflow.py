"""Issuer-side deal workflow punchlist mirror for BFMS.

This module models the optional deal-execution accountability layer that sits
beside readiness and handoff. It mirrors counsel-derived punchlists and document
state for issuer/operator visibility; it does not approve issuance, size bonds,
set pricing, or replace counsel/advisor judgment.
"""
from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Any, Literal

from pydantic import Field

from munipal.core.schemas.base import BaseSchema
from munipal.services.pilot_onboarding import PilotOnboardingWorkflow

DealPhase = Literal[
    "engagement",
    "diligence",
    "drafting",
    "marketing",
    "pricing",
    "pre-closing",
    "closing",
    "post-closing",
    "closed",
]
PartyRole = Literal[
    "Conduit Issuer",
    "Bond Counsel",
    "Issuer Counsel",
    "Borrower Counsel",
    "Underwriter",
    "Underwriter Counsel",
    "Financial Advisor",
    "Municipal Advisor",
    "Trustee",
    "Trustee Counsel",
    "Title Company",
    "Borrower",
    "Borrower Operator",
    "Rating Agency",
    "Auditor",
    "Other",
]
DocumentState = Literal[
    "not_started",
    "in_progress",
    "initial_draft",
    "rev_1",
    "rev_2",
    "rev_3",
    "proof",
    "final_proof",
    "for_sign_off",
    "executed",
    "filed",
    "n_a",
]
TimelineStatus = Literal["planned", "current", "completed", "blocked", "missed"]


class OpenItemStatus(StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    CIRCULATED_FOR_SIGNATURE = "circulated_for_signature"
    AWAITING_RESPONSE = "awaiting_response"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    N_A = "n_a"


_OPEN_ITEM_ACTIVE = {
    OpenItemStatus.PENDING,
    OpenItemStatus.IN_PROGRESS,
    OpenItemStatus.CIRCULATED_FOR_SIGNATURE,
    OpenItemStatus.AWAITING_RESPONSE,
    OpenItemStatus.BLOCKED,
}


class DealWorkflowValidationError(ValueError):
    """Raised when a deal workflow is incomplete or unsafe."""


class SourceBreadcrumb(BaseSchema):
    """Audit source for a mirrored counsel-derived item."""

    system: str = Field(default="manual", min_length=1)
    message_id: str | None = None
    source_author: str | None = None
    audit_date: date | None = None
    excerpt_ref: str | None = None


class DealMetadata(BaseSchema):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    year: int = Field(..., ge=2000)
    conduit_issuer: str = Field(..., min_length=1)
    borrower: str = Field(..., min_length=1)
    type: str = Field(default="Other", min_length=1)
    series_label: str | None = None
    sector: str | None = None
    par_amount_usd: float | None = None
    underwriter: str | None = None
    bond_counsel: str | None = None
    issuer_counsel: str | None = None
    borrower_counsel: str | None = None
    trustee: str | None = None
    title_company: str | None = None
    financial_advisor: str | None = None
    pricing_date: date | None = None
    closing_date: date | None = None
    phase: DealPhase = "engagement"
    notes: str = ""


class WorkingGroupParty(BaseSchema):
    counterparty: str = Field(..., min_length=1)
    role: PartyRole
    lead: str = ""
    lead_email: str | None = None
    team: tuple[str, ...] = Field(default_factory=tuple)
    is_owner_bucket: bool = True
    is_self: bool = False


class DealDocument(BaseSchema):
    id: str = Field(..., min_length=1)
    name: str = Field(..., min_length=1)
    abbreviation: str | None = None
    owner: str = ""
    current_state: DocumentState = "not_started"
    states_completed: tuple[DocumentState, ...] = Field(default_factory=tuple)
    category: str = Field(default="closing", min_length=1)
    required: bool = True
    last_updated: date | None = None


class OpenItem(BaseSchema):
    id: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    status: OpenItemStatus = OpenItemStatus.PENDING
    owner_individual: str | None = None
    blocks_closing: bool = False
    first_seen: date | None = None
    last_updated: date | None = None
    completed_date: date | None = None
    source: SourceBreadcrumb = Field(default_factory=SourceBreadcrumb)
    related_documents: tuple[str, ...] = Field(default_factory=tuple)
    related_readiness_gaps: tuple[str, ...] = Field(default_factory=tuple)
    related_handoff_outputs: tuple[str, ...] = Field(default_factory=tuple)
    human_confirmation_required: bool = True

    @property
    def is_active(self) -> bool:
        return self.status in _OPEN_ITEM_ACTIVE


class ForwardCommitment(BaseSchema):
    id: str = Field(..., min_length=1)
    owner: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    due_date: date | None = None
    source: SourceBreadcrumb = Field(default_factory=SourceBreadcrumb)


class PhaseTimelineEntry(BaseSchema):
    phase: DealPhase
    target_date: date | None = None
    completed_date: date | None = None
    status: TimelineStatus = "planned"
    notes: str = ""


class SnapshotDiff(BaseSchema):
    snapshot_id: str = Field(..., min_length=1)
    captured_at: date
    source: SourceBreadcrumb = Field(default_factory=SourceBreadcrumb)
    added_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    updated_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    closed_item_ids: tuple[str, ...] = Field(default_factory=tuple)
    document_state_changes: tuple[str, ...] = Field(default_factory=tuple)


class DealWorkflowMetadata(BaseSchema):
    source_system: str = "bfms"
    primary_counsel_email_pattern: str | None = None
    human_confirmation_required: bool = True
    liability_boundary: str = "mirror_only"
    liability_disclaimers: tuple[str, ...] = ("no_approval_no_sizing_no_pricing_advice",)
    deal_workflow_tracking_enabled: bool = False
    pilot_workflow_id: str | None = None
    measurement_hooks: tuple[str, ...] = Field(default_factory=tuple)


class DealWorkflow(BaseSchema):
    deal: DealMetadata
    working_group: list[WorkingGroupParty] = Field(..., min_length=1)
    documents: list[DealDocument] = Field(..., min_length=1)
    open_items: list[OpenItem] = Field(default_factory=list)
    forward_commitments: list[ForwardCommitment] = Field(default_factory=list)
    phase_timeline: list[PhaseTimelineEntry] = Field(..., min_length=1)
    snapshots: list[SnapshotDiff] = Field(default_factory=list)
    metadata: DealWorkflowMetadata = Field(default_factory=DealWorkflowMetadata)

    @property
    def self_owner_counterparties(self) -> tuple[str, ...]:
        return tuple(party.counterparty for party in self.working_group if party.is_self)

    def issuer_first_open_items(self) -> list[OpenItem]:
        self_owners = set(self.self_owner_counterparties)
        return sorted(self.open_items, key=lambda item: (item.owner not in self_owners, item.blocks_closing is False, item.id))

    def blocking_open_items(self) -> list[OpenItem]:
        return [item for item in self.issuer_first_open_items() if item.blocks_closing and item.is_active]

    def document_state_matrix(self) -> dict[str, str]:
        return {document.id: document.current_state for document in self.documents}

    @property
    def open_items_by_id(self) -> dict[str, OpenItem]:
        return {item.id: item for item in self.open_items}


def _slug(value: str) -> str:
    safe = "".join(ch.lower() if ch.isalnum() else "-" for ch in value)
    return "-".join(part for part in safe.split("-") if part)


def validate_deal_workflow(workflow: DealWorkflow | dict[str, Any]) -> DealWorkflow:
    if not isinstance(workflow, DealWorkflow):
        workflow = DealWorkflow.model_validate(workflow)

    if workflow.metadata.liability_boundary not in {"mirror_only", "mirror-only"}:
        raise DealWorkflowValidationError("deal workflow liability boundary must be mirror-only; it cannot imply approval")

    owners = {party.counterparty for party in workflow.working_group}
    if not workflow.self_owner_counterparties:
        raise DealWorkflowValidationError("deal workflow must include a self/issuer/operator owner bucket")

    document_ids = {document.id for document in workflow.documents}
    seen_documents: set[str] = set()
    for document in workflow.documents:
        if document.id in seen_documents:
            raise DealWorkflowValidationError(f"duplicate document id: {document.id}")
        seen_documents.add(document.id)
        if document.owner and document.owner not in owners:
            raise DealWorkflowValidationError(f"document {document.id} references unknown owner: {document.owner}")

    seen_items: set[str] = set()
    for item in workflow.open_items:
        if item.id in seen_items:
            raise DealWorkflowValidationError(f"duplicate open item id: {item.id}")
        seen_items.add(item.id)
        if item.owner not in owners:
            raise DealWorkflowValidationError(f"open item {item.id} references unknown owner: {item.owner}")
        for document_id in item.related_documents:
            if document_id not in document_ids:
                raise DealWorkflowValidationError(f"open item {item.id} references unknown document: {document_id}")
        if item.status == OpenItemStatus.COMPLETED and item.completed_date is None:
            raise DealWorkflowValidationError(f"completed open item {item.id} must include completed_date")

    for commitment in workflow.forward_commitments:
        if commitment.owner not in owners:
            raise DealWorkflowValidationError(f"commitment {commitment.id} references unknown owner: {commitment.owner}")

    return workflow


_STANDARD_DOCUMENTS: tuple[tuple[str, str, str], ...] = (
    ("plom", "Preliminary Limited Offering Memorandum", "disclosure"),
    ("limited-offering-memorandum", "Limited Offering Memorandum", "disclosure"),
    ("bond-purchase-agreement", "Bond Purchase Agreement", "underwriting"),
    ("continuing-disclosure-agreement", "Continuing Disclosure Agreement", "underwriting"),
    ("loan-agreement", "Loan Agreement", "core_financing"),
    ("trust-indenture", "Trust Indenture", "core_financing"),
    ("tax-documents", "Tax Documents", "tax"),
    ("investor-letters", "Investor Letters", "underwriting"),
    ("closing-memo", "Closing Memo", "closing"),
    ("signature-pages", "Signature Pages", "closing"),
)


def _party(counterparty: str, role: PartyRole, *, is_self: bool = False, lead_email: str | None = None) -> WorkingGroupParty:
    return WorkingGroupParty(counterparty=counterparty or role, role=role, lead_email=lead_email, is_owner_bucket=True, is_self=is_self)


def build_deal_workflow_from_seed(
    *,
    deal_id: str,
    name: str,
    year: int,
    borrower: str,
    conduit_issuer: str,
    sector: str,
    series_label: str | None = None,
    par_amount_usd: float | None = None,
    bond_counsel: str = "Bond Counsel",
    issuer_counsel: str = "Issuer Counsel",
    borrower_counsel: str = "Borrower Counsel",
    municipal_advisor: str = "Municipal Advisor",
    underwriter: str = "Underwriter",
    trustee: str = "Trustee",
    title_company: str = "Title Company",
    target_closing_date: date | None = None,
    closing_date: date | None = None,
    pricing_date: date | None = None,
    primary_counsel_email_pattern: str | None = None,
    additional_document_templates: tuple[str, ...] = (),
) -> DealWorkflow:
    closing = target_closing_date or closing_date
    deal = DealMetadata(
        id=deal_id,
        name=name,
        year=year,
        conduit_issuer=conduit_issuer,
        borrower=borrower,
        type={"healthcare": "Healthcare Facilities", "housing": "Multifamily Housing", "waste": "Water/Wastewater"}.get(sector, "Other"),
        series_label=series_label or f"Series {year}",
        sector=sector,
        par_amount_usd=par_amount_usd,
        underwriter=underwriter,
        bond_counsel=bond_counsel,
        issuer_counsel=issuer_counsel,
        borrower_counsel=borrower_counsel,
        trustee=trustee,
        title_company=title_company,
        financial_advisor=municipal_advisor,
        pricing_date=pricing_date,
        closing_date=closing,
        phase="engagement",
    )
    parties = [
        _party(conduit_issuer, "Conduit Issuer", is_self=True),
        _party(bond_counsel, "Bond Counsel"),
        _party(issuer_counsel, "Issuer Counsel"),
        _party(borrower_counsel, "Borrower Counsel"),
        _party(municipal_advisor, "Financial Advisor"),
        _party(underwriter, "Underwriter"),
        _party(trustee, "Trustee"),
        _party(title_company, "Title Company"),
        _party(borrower, "Borrower"),
    ]
    documents = [DealDocument(id=doc_id, name=doc_name, category=category, owner=bond_counsel) for doc_id, doc_name, category in _STANDARD_DOCUMENTS]
    for doc_id in additional_document_templates:
        documents.append(DealDocument(id=doc_id, name=doc_id.replace("-", " ").title(), category="sector_playbook", owner=borrower))

    open_items = [OpenItem(id="issuer-initial-closing-checklist", owner=conduit_issuer, description="Review issuer-owned closing checklist items and confirm accountable owner for each open counsel request.", blocks_closing=False, related_documents=("closing-memo",), source=SourceBreadcrumb(system="bfms_seed"))]
    timeline = [
        PhaseTimelineEntry(phase="engagement", status="current"),
        PhaseTimelineEntry(phase="diligence"),
        PhaseTimelineEntry(phase="drafting"),
        PhaseTimelineEntry(phase="marketing"),
        PhaseTimelineEntry(phase="pricing", target_date=pricing_date),
        PhaseTimelineEntry(phase="pre-closing", target_date=closing),
        PhaseTimelineEntry(phase="closing", target_date=closing),
        PhaseTimelineEntry(phase="post-closing"),
    ]
    metadata = DealWorkflowMetadata(primary_counsel_email_pattern=primary_counsel_email_pattern, liability_disclaimers=("no_approval_no_sizing_no_pricing_advice", "mirror_requires_human_confirmation"))
    return validate_deal_workflow(DealWorkflow(deal=deal, working_group=parties, documents=documents, open_items=open_items, phase_timeline=timeline, metadata=metadata))


def initialize_deal_workflow_from_pilot(
    pilot: PilotOnboardingWorkflow,
    *,
    deal_id: str,
    borrower: str,
    conduit_issuer: str,
    advisor: str,
    reviewer: str,
    target_closing_date: date | None = None,
    readiness_gap_refs: tuple[str, ...] = (),
    handoff_output_refs: tuple[str, ...] = (),
) -> DealWorkflow:
    playbook = pilot.playbook
    workflow = build_deal_workflow_from_seed(deal_id=deal_id, name=borrower, year=(target_closing_date or date.today()).year, borrower=borrower, conduit_issuer=conduit_issuer, sector=playbook.metadata.sector, municipal_advisor=advisor, target_closing_date=target_closing_date, additional_document_templates=tuple(artifact.artifact_key for artifact in playbook.required_artifacts if artifact.requirement_level == "required")[:4])
    workflow.working_group.append(_party(reviewer, "Other"))
    for gap_ref in readiness_gap_refs:
        workflow.open_items.append(OpenItem(id=f"readiness-gap-{_slug(gap_ref)}", owner=conduit_issuer, description=f"Resolve or assign BFMS readiness gap before advisor handoff: {gap_ref}", status=OpenItemStatus.PENDING, related_readiness_gaps=(gap_ref,), related_handoff_outputs=handoff_output_refs, source=SourceBreadcrumb(system="pilot_onboarding", message_id=pilot.workflow_id), human_confirmation_required=True))
    workflow.metadata.deal_workflow_tracking_enabled = True
    workflow.metadata.pilot_workflow_id = pilot.workflow_id
    workflow.metadata.measurement_hooks = ("pilot_workflow_snapshots", "operator_owned_items", "blocker_counts", "milestone_dates", "closing_progress")
    workflow.metadata.liability_disclaimers = tuple(sorted(set(workflow.metadata.liability_disclaimers + ("no_approval_no_sizing_no_pricing_advice",))))
    return validate_deal_workflow(workflow)


class RollupItem(BaseSchema):
    deal_id: str
    deal_name: str
    item_id: str
    owner: str
    description: str
    status: OpenItemStatus
    blocks_closing: bool
    last_updated: date | None = None


class UpcomingClosing(BaseSchema):
    deal_id: str
    deal_name: str
    closing_date: date
    days_to_closing: int


class DealWorkflowRollup(BaseSchema):
    human_confirmation_required: bool
    active_deal_count: int
    blocking_item_count: int
    self_owned_open_items: list[RollupItem]
    stale_items: list[RollupItem]
    upcoming_closings: list[UpcomingClosing]


def _rollup_item(workflow: DealWorkflow, item: OpenItem) -> RollupItem:
    return RollupItem(deal_id=workflow.deal.id, deal_name=workflow.deal.name, item_id=item.id, owner=item.owner, description=item.description, status=item.status, blocks_closing=item.blocks_closing, last_updated=item.last_updated)


def build_deal_workflow_rollup(workflows: list[DealWorkflow], *, as_of: date | None = None, stale_after_days: int = 14) -> DealWorkflowRollup:
    as_of = as_of or date.today()
    valid = [validate_deal_workflow(workflow) for workflow in workflows]
    self_owned: list[RollupItem] = []
    stale: list[RollupItem] = []
    blocking_count = 0
    upcoming: list[UpcomingClosing] = []
    for workflow in valid:
        self_owners = set(workflow.self_owner_counterparties)
        for item in workflow.issuer_first_open_items():
            if item.blocks_closing and item.is_active:
                blocking_count += 1
            if item.is_active and item.owner in self_owners:
                rollup = _rollup_item(workflow, item)
                self_owned.append(rollup)
                if item.last_updated and (as_of - item.last_updated).days > stale_after_days:
                    stale.append(rollup)
        if workflow.deal.closing_date and workflow.deal.phase != "closed":
            upcoming.append(UpcomingClosing(deal_id=workflow.deal.id, deal_name=workflow.deal.name, closing_date=workflow.deal.closing_date, days_to_closing=(workflow.deal.closing_date - as_of).days))
    upcoming.sort(key=lambda closing: closing.closing_date)
    return DealWorkflowRollup(human_confirmation_required=True, active_deal_count=len([workflow for workflow in valid if workflow.deal.phase != "closed"]), blocking_item_count=blocking_count, self_owned_open_items=self_owned, stale_items=stale, upcoming_closings=upcoming)


class ParsedCounselItem(BaseSchema):
    """Open-item line conservatively extracted from a counsel punchlist email."""

    description: str = Field(..., min_length=1)
    inferred_owner: str = Field(..., min_length=1)
    status_verb: str = Field(..., min_length=1)
    status: OpenItemStatus
    owner_individual: str | None = None
    audit_breadcrumb: SourceBreadcrumb = Field(default_factory=SourceBreadcrumb)


class ParsedDocumentSignal(BaseSchema):
    document_id: str
    next_state: DocumentState
    action: str
    confidence: float = Field(..., ge=0, le=1)
    source: SourceBreadcrumb = Field(default_factory=SourceBreadcrumb)


class ParsedCounselPunchlistEmail(BaseSchema):
    source: SourceBreadcrumb
    open_items: list[ParsedCounselItem] = Field(default_factory=list)
    forward_commitments: list[ForwardCommitment] = Field(default_factory=list)
    document_signals: list[ParsedDocumentSignal] = Field(default_factory=list)
    private_body_redacted: bool = True


class CounselRefreshDiff(SnapshotDiff):
    refreshed_workflow: DealWorkflow


def _normalized_owner(owner: str) -> str:
    owner = owner.strip().strip(":")
    lowered = owner.lower().replace("/", " ")
    aliases = {
        "authority": "SVIDA",
        "svida": "SVIDA",
        "svida authority": "SVIDA",
        "issuer": "SVIDA",
        "trustee": "UMB Bank",
        "umb": "UMB Bank",
        "umb bank": "UMB Bank",
        "bond counsel": "Ice Miller",
        "ice miller": "Ice Miller",
        "borrower counsel": "Borrower Counsel",
    }
    for key, value in aliases.items():
        if lowered == key or lowered.startswith(f"{key} "):
            return value
    if "authority" in lowered and "svida" in lowered:
        return "SVIDA"
    return owner.replace(" Open Items", "").strip()


def _canonical_status(verb: str) -> OpenItemStatus:
    normalized = verb.lower().replace("_", " ").replace("-", " ").strip(" .")
    if any(token in normalized for token in ("received", "complete", "completed", "done", "resolved", "closed")):
        return OpenItemStatus.COMPLETED
    if "circulated" in normalized and "signature" in normalized:
        return OpenItemStatus.CIRCULATED_FOR_SIGNATURE
    if "await" in normalized or "waiting" in normalized or "response" in normalized:
        return OpenItemStatus.AWAITING_RESPONSE
    if "block" in normalized or "hold" in normalized:
        return OpenItemStatus.BLOCKED
    if "progress" in normalized or "working" in normalized or "draft" in normalized:
        return OpenItemStatus.IN_PROGRESS
    return OpenItemStatus.PENDING


def _extract_owner_individual(text: str) -> tuple[str, str | None]:
    stripped = text.strip()
    if stripped.endswith(")") and "(" in stripped:
        body, individual = stripped.rsplit("(", 1)
        return body.strip(" -"), individual[:-1].strip() or None
    return stripped, None


def _split_description_status(text: str) -> tuple[str, str]:
    import re

    parts = re.split(r"\s+-\s+", text.strip(), maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    lowered = text.lower()
    for marker in (" is blocked", " is outstanding", " is pending", " is received", " is complete", " is completed"):
        if marker in lowered:
            idx = lowered.rfind(marker)
            return text[:idx].strip(), marker.replace(" is ", "").strip()
    return text.strip(), "pending"


def _source(system: str, message_id: str | None, source_author: str | None, audit_date: date | None, excerpt_ref: str | None = None) -> SourceBreadcrumb:
    return SourceBreadcrumb(system=system, message_id=message_id, source_author=source_author, audit_date=audit_date, excerpt_ref=excerpt_ref)


def _parse_document_signals(subject: str, breadcrumb: SourceBreadcrumb) -> list[ParsedDocumentSignal]:
    subject_l = subject.lower()
    document_id: str | None = None
    if "closing memo" in subject_l or "closing memorandum" in subject_l:
        document_id = "closing-memo"
    elif "lom" in subject_l or "limited offering memorandum" in subject_l:
        document_id = "limited-offering-memorandum"
    elif "bpa" in subject_l or "bond purchase agreement" in subject_l:
        document_id = "bond-purchase-agreement"
    if not document_id:
        return []
    signals: list[tuple[str, DocumentState, float]] = [
        ("filed", "filed", 0.9),
        ("executed", "executed", 0.85),
        ("sign off", "for_sign_off", 0.8),
        ("sign-off", "for_sign_off", 0.8),
        ("proof", "proof", 0.75),
        ("rev 3", "rev_3", 0.72),
        ("rev 2", "rev_2", 0.7),
        ("rev 1", "rev_1", 0.68),
        ("draft", "initial_draft", 0.65),
    ]
    found: list[ParsedDocumentSignal] = []
    for action, state, confidence in signals:
        if action in subject_l:
            found.append(ParsedDocumentSignal(document_id=document_id, next_state=state, action=action, confidence=confidence, source=breadcrumb))
            break
    return found


def parse_counsel_punchlist_email(*, subject: str, body: str, source_author: str | None, audit_date: date | None, message_id: str | None = None) -> ParsedCounselPunchlistEmail:
    import re

    breadcrumb = _source("counsel_email", message_id, source_author, audit_date)
    items: list[ParsedCounselItem] = []
    commitments: list[ForwardCommitment] = []
    current_owner: str | None = None
    in_commitments = False
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        line_l = line.lower()
        if "expect to complete" in line_l or "in preparation for closing" in line_l or "forward-looking" in line_l:
            in_commitments = True
            current_owner = None
            continue
        header = re.match(r"^([A-Za-z0-9&/ .-]+?)\s+Open Items:?$", line, flags=re.I)
        if header:
            current_owner = _normalized_owner(header.group(1))
            in_commitments = False
            continue
        if not line.startswith(("-", "*", "•")):
            continue
        content = line.lstrip("-*• ").strip()
        if in_commitments:
            commitments.append(ForwardCommitment(id=f"counsel-commitment-{_slug(content)}", owner="Counsel", description=content, source=breadcrumb))
            continue
        owner = current_owner
        inline = re.match(r"^([A-Za-z0-9&/ .-]+?):\s+(.+)$", content)
        if inline:
            owner = _normalized_owner(inline.group(1))
            content = inline.group(2).strip()
        if not owner:
            owner = "Counsel"
        content, individual = _extract_owner_individual(content)
        description, status_verb = _split_description_status(content)
        items.append(
            ParsedCounselItem(
                description=description,
                inferred_owner=owner,
                status_verb=status_verb.lower().strip(),
                status=_canonical_status(status_verb),
                owner_individual=individual,
                audit_breadcrumb=breadcrumb,
            )
        )
    return ParsedCounselPunchlistEmail(source=breadcrumb, open_items=items, forward_commitments=commitments, document_signals=_parse_document_signals(subject, breadcrumb), private_body_redacted=True)


def _item_key(owner: str, description: str) -> str:
    return f"{_slug(owner)}::{_slug(description)}"


def _owner_in_workflow(workflow: DealWorkflow, parsed_owner: str) -> str:
    owners = {party.counterparty for party in workflow.working_group}
    if parsed_owner in owners:
        return parsed_owner
    normalized = _normalized_owner(parsed_owner)
    if normalized in owners:
        return normalized
    for party in workflow.working_group:
        if parsed_owner.lower() in party.role.lower() or party.role.lower() in parsed_owner.lower():
            return party.counterparty
    return parsed_owner


def _latest_or_same_author(existing: OpenItem, parsed: ParsedCounselPunchlistEmail) -> bool:
    if existing.source.source_author != parsed.source.source_author:
        return False
    if existing.source.audit_date and parsed.source.audit_date and parsed.source.audit_date < existing.source.audit_date:
        return False
    return True


def apply_counsel_refresh(workflow: DealWorkflow, parsed: ParsedCounselPunchlistEmail) -> CounselRefreshDiff:
    added: list[str] = []
    updated: list[str] = []
    closed: list[str] = []
    document_changes: list[str] = []
    parsed_keys: set[str] = set()
    existing_by_key = {_item_key(item.owner, item.description): item for item in workflow.open_items}

    for parsed_item in parsed.open_items:
        owner = _owner_in_workflow(workflow, parsed_item.inferred_owner)
        key = _item_key(owner, parsed_item.description)
        parsed_keys.add(key)
        existing = existing_by_key.get(key)
        if existing:
            changed = False
            if existing.status != parsed_item.status:
                existing.status = parsed_item.status
                changed = True
            if parsed_item.status == OpenItemStatus.COMPLETED and existing.completed_date is None:
                existing.completed_date = parsed.source.audit_date
                changed = True
            existing.owner_individual = parsed_item.owner_individual or existing.owner_individual
            existing.last_updated = parsed.source.audit_date or existing.last_updated
            existing.source = parsed.source
            existing.human_confirmation_required = True
            if changed:
                updated.append(existing.id)
            continue
        new_id = f"counsel-{_slug(owner)}-{_slug(parsed_item.description)}"
        workflow.open_items.append(
            OpenItem(
                id=new_id,
                owner=owner,
                description=parsed_item.description,
                status=parsed_item.status,
                owner_individual=parsed_item.owner_individual,
                blocks_closing=parsed_item.status != OpenItemStatus.COMPLETED,
                first_seen=parsed.source.audit_date,
                last_updated=parsed.source.audit_date,
                completed_date=parsed.source.audit_date if parsed_item.status == OpenItemStatus.COMPLETED else None,
                source=parsed.source,
                human_confirmation_required=True,
            )
        )
        added.append(new_id)

    for item in workflow.open_items:
        key = _item_key(item.owner, item.description)
        if key not in parsed_keys and item.is_active and _latest_or_same_author(item, parsed):
            item.status = OpenItemStatus.COMPLETED
            item.completed_date = parsed.source.audit_date
            item.last_updated = parsed.source.audit_date
            item.source = parsed.source
            item.human_confirmation_required = True
            closed.append(item.id)

    documents = {document.id: document for document in workflow.documents}
    for signal in parsed.document_signals:
        document = documents.get(signal.document_id)
        if document and signal.confidence >= 0.7 and document.current_state != signal.next_state:
            states = tuple(dict.fromkeys(document.states_completed + (signal.next_state,)))
            document.current_state = signal.next_state
            document.states_completed = states
            document.last_updated = parsed.source.audit_date
            document_changes.append(f"{document.id}:{signal.next_state}")

    for commitment in parsed.forward_commitments:
        owner = workflow.deal.bond_counsel or "Counsel"
        if owner not in {party.counterparty for party in workflow.working_group}:
            owner = workflow.working_group[0].counterparty
        workflow.forward_commitments.append(commitment.model_copy(update={"owner": owner}))

    snapshot = SnapshotDiff(
        snapshot_id=f"counsel-refresh-{parsed.source.message_id or parsed.source.audit_date or len(workflow.snapshots)+1}",
        captured_at=parsed.source.audit_date or date.today(),
        source=parsed.source,
        added_item_ids=tuple(added),
        updated_item_ids=tuple(updated),
        closed_item_ids=tuple(closed),
        document_state_changes=tuple(document_changes),
    )
    workflow.snapshots.append(snapshot)
    refreshed = validate_deal_workflow(workflow)
    return CounselRefreshDiff(
        snapshot_id=snapshot.snapshot_id,
        captured_at=snapshot.captured_at,
        source=snapshot.source,
        added_item_ids=snapshot.added_item_ids,
        updated_item_ids=snapshot.updated_item_ids,
        closed_item_ids=snapshot.closed_item_ids,
        document_state_changes=snapshot.document_state_changes,
        refreshed_workflow=refreshed,
    )
