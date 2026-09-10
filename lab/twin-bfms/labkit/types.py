"""pydantic v2 contracts for `lab/twin-bfms`.

Four-valued honesty by construction: every status field is a `Literal`, `unknown` and
`not_applicable` must carry a reason, the two client pilot gates are
`Literal["not_applicable"]` (a pass cannot be constructed), and `RunReport.lab_statements`
rejects the forbidden lab words. No field ever holds a computed date.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date as _date
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from labkit import GENERATOR_VERSION, LAB_VERSION, law

StageStatus = Literal["pass", "fail", "unknown", "not_applicable"]
SmokeStatus = Literal["pass", "fail"]
NotApplicable = Literal["not_applicable"]
RegisterStatus = Literal["filed", "not filed", "evidence missing", "not testable"]

_STAGE_ID_RE = re.compile(r"^S\d{2}$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def worst_status(statuses: Iterable[str]) -> StageStatus:
    """Fold statuses worst-first: fail > unknown > pass; not_applicable only if all are."""
    vals = list(statuses)
    if not vals:
        return "unknown"
    return max(vals, key=lambda s: law.STATUS_RANK[s])  # type: ignore[return-value]


def _needs_reason(status: str, reason: str, where: str) -> None:
    if status in ("unknown", "not_applicable") and not reason.strip():
        raise ValueError(f"{where}: status {status!r} requires a non-empty reason")


def _iso_literal_or_none(value: str | None, where: str) -> str | None:
    if value is None:
        return None
    if not law.ISO_DATE_RE.match(value):
        raise ValueError(f"{where}: date must be an ISO literal YYYY-MM-DD or null, got {value!r}")
    _date.fromisoformat(value)  # rejects 2025-13-01 and friends; never computes anything
    return value


class LabModel(BaseModel):
    """Strict base: unknown keys are errors; aliases and names both populate."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True, str_strip_whitespace=False)


# --------------------------------------------------------------------------------------
# Stage results
# --------------------------------------------------------------------------------------


class SubAssertion(LabModel):
    key: str = Field(min_length=1)
    status: StageStatus
    observed: Any = None
    expected: Any = None
    reason: str = ""

    @model_validator(mode="after")
    def _reason_rule(self) -> SubAssertion:
        _needs_reason(self.status, self.reason, f"sub-assertion {self.key}")
        return self


class CallRecord(LabModel):
    method: str
    path: str
    status_code: int | None = None
    note: str = ""


class StageResult(LabModel):
    id: str
    station: str
    bfms_stage: str
    checklist_phase: str = ""
    deal_phase: str
    pilot_stage: str
    status: StageStatus
    assertion: str
    sub_assertions: list[SubAssertion] = Field(default_factory=list)
    observed: dict[str, Any] = Field(default_factory=dict)
    reason: str = ""
    evidence_refs: list[str] = Field(default_factory=list)
    calls: list[CallRecord] = Field(default_factory=list)

    @field_validator("id")
    @classmethod
    def _stage_id(cls, v: str) -> str:
        if not _STAGE_ID_RE.match(v):
            raise ValueError(f"stage id must look like S07, got {v!r}")
        return v

    @model_validator(mode="after")
    def _status_rules(self) -> StageResult:
        _needs_reason(self.status, self.reason, f"stage {self.id}")
        if self.sub_assertions:
            worst = worst_status(s.status for s in self.sub_assertions)
            if law.STATUS_RANK[self.status] < law.STATUS_RANK[worst]:
                raise ValueError(
                    f"stage {self.id}: status {self.status!r} is better than its worst "
                    f"sub-assertion {worst!r}; statuses are computed, never softened"
                )
        return self

    @classmethod
    def from_sub_assertions(cls, **fields: Any) -> StageResult:
        """Build a stage whose status is the worst of its sub-assertions (never passed in)."""
        if "status" in fields:
            raise ValueError("from_sub_assertions computes status; do not pass it")
        subs = [s if isinstance(s, SubAssertion) else SubAssertion(**s) for s in fields.pop("sub_assertions", [])]
        status = worst_status(s.status for s in subs) if subs else "unknown"
        reason = fields.pop("reason", "")
        if status in ("unknown", "not_applicable") and not reason:
            worst = next((s for s in subs if s.status == status), None)
            reason = worst.reason if worst is not None else "no sub-assertions recorded"
        return cls(status=status, sub_assertions=subs, reason=reason, **fields)


# --------------------------------------------------------------------------------------
# Conformance (event_log.csv row -> DealWorkflow object)
# --------------------------------------------------------------------------------------


class ConformanceRow(LabModel):
    event: str = Field(min_length=1)
    station: str
    log_status: str
    date: str | None = None
    bfms_object: str
    expected_state: str
    observed_state: str
    evidence_ref: str | None = None
    status: StageStatus
    reason: str = ""

    @field_validator("station")
    @classmethod
    def _station(cls, v: str) -> str:
        if v not in law.BONDI_STATIONS:
            raise ValueError(f"station must be one of {law.BONDI_STATIONS}, got {v!r}")
        return v

    @field_validator("log_status")
    @classmethod
    def _log_status(cls, v: str) -> str:
        if v not in law.BONDI_EVENT_STATUSES:
            raise ValueError(f"log_status must be one of {law.BONDI_EVENT_STATUSES}, got {v!r}")
        return v

    @field_validator("date")
    @classmethod
    def _date_literal(cls, v: str | None) -> str | None:
        return _iso_literal_or_none(v, "conformance row")

    @model_validator(mode="after")
    def _reason_rule(self) -> ConformanceRow:
        _needs_reason(self.status, self.reason, f"conformance row {self.event}")
        return self


# --------------------------------------------------------------------------------------
# Pilot gates (brief rule 4): the client gates are not_applicable by type
# --------------------------------------------------------------------------------------


class PilotGates(LabModel):
    registered_ma_confirmed: NotApplicable = "not_applicable"
    registered_ma_confirmed_reason: str = law.CLIENT_GATE_REASON
    engagement_scope_signed: NotApplicable = "not_applicable"
    engagement_scope_signed_reason: str = law.CLIENT_GATE_REASON
    pilot_smoke_test_green: SmokeStatus
    pilot_smoke_test_green_meaning: str = law.SMOKE_GATE_MEANING
    known_gaps_accepted: list[str] = Field(default_factory=list)
    gate_definition_ref: str = law.PILOT_GATE_DEFINITION_REF
    display_name_finding: str = law.PILOT_GATE_DISPLAY_NAME_FINDING

    @field_validator("registered_ma_confirmed_reason", "engagement_scope_signed_reason")
    @classmethod
    def _reason_present(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("client gate reason must be non-empty")
        return v


# --------------------------------------------------------------------------------------
# Provenance envelope (stamped on every generated file)
# --------------------------------------------------------------------------------------


class Envelope(LabModel):
    source: Literal["synthetic"] = "synthetic"
    generator_version: str = GENERATOR_VERSION
    lab_version: str = LAB_VERSION
    scenario_id: str
    seed: int
    sha256_body: str | None = None
    created_from: list[str] = Field(default_factory=list)

    @field_validator("scenario_id")
    @classmethod
    def _syn_id(cls, v: str) -> str:
        if not law.SYN_ID_RE.match(v):
            raise ValueError(f"scenario_id must start with SYN-, got {v!r}")
        if v == law.DEMO_DEAL_ID:
            raise ValueError(f"scenario_id must never equal the demo id {law.DEMO_DEAL_ID}")
        return v

    @field_validator("sha256_body")
    @classmethod
    def _hex64(cls, v: str | None) -> str | None:
        if v is not None and not _HEX64_RE.match(v):
            raise ValueError("sha256_body must be 64 lowercase hex chars")
        return v

    def as_lines(self) -> list[str]:
        """`key: value` lines in the fixed envelope order (JSON-encoded created_from)."""
        import json

        return [
            f"source: {self.source}",
            f"generator_version: {self.generator_version}",
            f"lab_version: {self.lab_version}",
            f"scenario_id: {self.scenario_id}",
            f"seed: {self.seed}",
            f"sha256_body: {self.sha256_body or ''}",
            f"created_from: {json.dumps(self.created_from, ensure_ascii=False)}",
        ]


# --------------------------------------------------------------------------------------
# Run report
# --------------------------------------------------------------------------------------


class EmittedLanguage(LabModel):
    """BFMS-native prose is never restated: sha256 plus a short excerpt only."""

    source: str
    sha256: str
    excerpt: str = Field(max_length=law.BFMS_EXCERPT_MAX_CHARS)

    @field_validator("sha256")
    @classmethod
    def _hex64(cls, v: str) -> str:
        if not _HEX64_RE.match(v):
            raise ValueError("sha256 must be 64 lowercase hex chars")
        return v


class RunReport(LabModel):
    legend: str = Field(default=law.LEGEND, alias="_legend")
    label_notice: str = law.LABEL_NOTICE
    schema_version: Literal["lab-run-report/1"] = law.REPORT_SCHEMA_VERSION
    run_id: str
    scenario_id: str
    scenario_sha256: str
    derived_from: str | None = None
    seed: int
    asof: str
    generator_version: str = GENERATOR_VERSION
    lab_version: str = LAB_VERSION
    repo_commit: str = "unknown"
    repo_dirty: bool | Literal["unknown"] = "unknown"
    python: str
    pins: dict[str, str] = Field(default_factory=dict)
    fulfillment_tree_sha256_before: str = "unknown"
    fulfillment_tree_sha256_after: str = "unknown"
    environment: dict[str, Any] = Field(default_factory=dict)
    name_collision_check: dict[str, str] = Field(
        default_factory=lambda: {"blocklist": "pass", "web_or_registry": "unknown (not performed)"}
    )
    pilot_gates: PilotGates
    stages: list[StageResult] = Field(default_factory=list)
    conformance_table: list[ConformanceRow] = Field(default_factory=list)
    deal_workflow_mirror: dict[str, Any] = Field(default_factory=dict)
    register_summary: dict[str, Any] = Field(default_factory=dict)
    review: dict[str, Any] = Field(default_factory=dict)
    vocabulary_divergence: dict[str, Any] = Field(default_factory=dict)
    bfms_emitted_language: list[EmittedLanguage] = Field(default_factory=list)
    findings_touched: list[str] = Field(default_factory=list)
    counts: dict[str, int] = Field(default_factory=dict)
    lab_statements: list[str] = Field(default_factory=list)
    forbidden_scan: dict[str, int] = Field(default_factory=dict)
    golden_diff: list[Any] = Field(default_factory=list)
    sealed_at: str | None = None
    content_hash: str | None = None

    # -- validators -------------------------------------------------------------------

    @field_validator("legend")
    @classmethod
    def _legend_verbatim(cls, v: str) -> str:
        if v != law.LEGEND:
            raise ValueError("_legend must be the verbatim QUARANTINE.md legend")
        return v

    @field_validator("scenario_id", "derived_from")
    @classmethod
    def _syn_ids(cls, v: str | None) -> str | None:
        if v is not None and not law.SYN_ID_RE.match(v):
            raise ValueError(f"deal ids must start with SYN-, got {v!r}")
        if v == law.DEMO_DEAL_ID:
            raise ValueError(f"lab ids never equal the demo id {law.DEMO_DEAL_ID}")
        return v

    @field_validator("asof")
    @classmethod
    def _asof_literal(cls, v: str) -> str:
        return _iso_literal_or_none(v, "asof") or v

    @field_validator("repo_commit")
    @classmethod
    def _commit(cls, v: str) -> str:
        if v != "unknown" and not _HEX40_RE.match(v):
            raise ValueError("repo_commit must be 40 lowercase hex chars or 'unknown'")
        return v

    @field_validator("scenario_sha256")
    @classmethod
    def _scenario_hash(cls, v: str) -> str:
        if not _HEX64_RE.match(v):
            raise ValueError("scenario_sha256 must be 64 lowercase hex chars")
        return v

    @field_validator("lab_statements")
    @classmethod
    def _statements_clean(cls, v: list[str]) -> list[str]:
        for statement in v:
            hits = law.forbidden_lab_word_hits(statement)
            if hits:
                raise ValueError(f"lab statement carries forbidden word(s) {hits}: {statement!r}")
            if law.EMMA_WORD.search(statement):
                raise ValueError(f"lab statement carries the MSRB platform token: {statement!r}")
            if law.forbidden_token_hits(statement):
                raise ValueError(f"lab statement carries a rule-3 token: {statement!r}")
        return v

    @field_validator("pins")
    @classmethod
    def _pins_complete(cls, v: dict[str, str]) -> dict[str, str]:
        missing = [k for k in law.PIN_KEYS if k not in v]
        if missing:
            raise ValueError(f"pins missing keys {missing}")
        return v

    @model_validator(mode="after")
    def _stages_and_counts(self) -> RunReport:
        ids = [s.id for s in self.stages]
        if len(ids) != len(set(ids)):
            raise ValueError("stage ids must be unique")
        if ids != sorted(ids):
            raise ValueError("stages must be ordered by id")
        events = [r.event for r in self.conformance_table]
        if len(events) != len(set(events)):
            raise ValueError("conformance rows must be unique per event")
        self.counts = self.compute_counts()
        return self

    # -- computed views ---------------------------------------------------------------

    def compute_counts(self) -> dict[str, int]:
        """Counts over every stage, sub-assertion and conformance status (never typed)."""
        counts = dict.fromkeys(law.FOUR_VALUES, 0)
        for stage in self.stages:
            counts[stage.status] += 1
            for sub in stage.sub_assertions:
                counts[sub.status] += 1
        for row in self.conformance_table:
            counts[row.status] += 1
        return counts

    @property
    def is_complete(self) -> bool:
        return tuple(s.id for s in self.stages) == law.EXPECTED_STAGE_IDS

    def hashable_payload(self) -> dict[str, Any]:
        """Every field except `content_hash`, JSON-mode, keyed by alias."""
        payload = self.model_dump(mode="json", by_alias=True)
        payload.pop("content_hash", None)
        return payload

    def compute_content_hash(self) -> str:
        from labkit import provenance

        return provenance.sha256_text(provenance.canonical_json(self.hashable_payload()))

    def seal(self) -> RunReport:
        """Return a copy with `content_hash` set; the original is untouched."""
        return self.model_copy(update={"content_hash": self.compute_content_hash()})

    def verify(self) -> bool:
        """True iff `content_hash` is present and equals the recomputed hash."""
        return self.content_hash is not None and self.content_hash == self.compute_content_hash()


__all__ = [
    "CallRecord",
    "ConformanceRow",
    "EmittedLanguage",
    "Envelope",
    "LabModel",
    "NotApplicable",
    "PilotGates",
    "RegisterStatus",
    "RunReport",
    "SmokeStatus",
    "StageResult",
    "StageStatus",
    "SubAssertion",
    "worst_status",
]
