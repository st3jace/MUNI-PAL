"""Stage driver S00-S18 for `lab/twin-bfms` (BUILD-SPEC 5).

One async method per stage, each returning a `labkit.types.StageResult` whose status is
folded from its sub-assertions by `StageResult.from_sub_assertions` (never passed in).
Every BFMS call goes through `Driver.call`, which records method / path / status code
into the current stage; a call that raises (httpx ASGITransport re-raises application
errors) is recorded with `status_code=None` and a body hash, and becomes a `fail`
sub-assertion -- nothing under `src/` is ever patched.

Endpoints and parameters are exactly the ones the probe proved (`scratchpad/probe`):
`?reviewer_id=` on approve/reject, `?sync=true` on deliverables, explicit
`target_schema_paths` (one job per intake artifact, critic M4),
`DealDocumentService.transition_status` service-direct (route defect F11), a
`DealDocumentType` seeded with lab wording, `DOCUMENT_MANAGEMENT_V1=true`, and never
`GET /api/v1/playbooks/{id}` (F11).

`munipal` is imported lazily inside methods so that `harness.standalone()` can pin the
environment before the package is first imported.
"""

from __future__ import annotations

import hashlib
import importlib
import json
import platform
import re
import shutil
import subprocess
import traceback
from dataclasses import dataclass, field
from datetime import date as _date
from pathlib import Path
from typing import Any

from labkit import law, post_close, replay
from labkit import names as names_mod
from labkit import scenario as scenario_mod
from labkit.harness import (
    EXTRACTION_ROUTE_MODULE,
    LLM_CLIENT_CLASS,
    LabContext,
    engines_modules_loaded,
)
from labkit.provenance import (
    PackManifest,
    audit_file,
    sha256_bytes,
    sha256_file,
    sha256_text,
    tree_sha256,
    write_md,
)
from labkit.report import emitted
from labkit.types import CallRecord, EmittedLanguage, Envelope, StageResult, SubAssertion

REPO_ROOT: Path = law.LAB_ROOT.parents[1]
EXPORTS_DIR_NAME = "exports"
WASTE_TERM_RE = re.compile(r"\b(feedstock|tipping|slb|cab)\b", re.IGNORECASE)
INT_COMPARED_PATHS: frozenset[str] = frozenset({"capital.project-cost"})
CLOSING_UPLOAD_FOLDER = "04_CLOSING-DOCUMENTS"
CDA_TYPE_CODE = "continuing_disclosure_agreement"
CDA_DOC_ID = "continuing-disclosure-agreement"
#: Event-log rows that would move the CDA DealDocument to `filed`; none is carried today.
CDA_FILING_EVENTS: frozenset[str] = frozenset({"cda_filed"})
ENGINES_NOT_LOADED_REASON = "shared interpreter possible; enforced by S18.engines_modules_unchanged and the import fence"
PIN_DRIFT_REASON = "demo drifted; regenerate packs deliberately"
DELIVERABLE_DISCLAIMER_MARKERS: tuple[str, ...] = ("## Disclaimer", "does not constitute investment advice")
REVIEW_STATEMENT = (
    "review performed by lab-scripted-reviewer - not a human, not a Bond Strategist; "
    "pass means the review endpoints work"
)
#: pilot-navigation-system.md section 5.4 / 5.5 rows, paraphrased (critic M5: never quoted).
PILOT_NAV_54_ROWS: tuple[str, ...] = (
    "5.4 market intelligence report for a sector and geography",
    "5.4 readiness assessment from the old-pack sensing input profile",
    "5.4 cost-of-issuance benchmarking pull",
    "5.4 credit-spread monitor with the benchmark curve and platform trades",
    "5.4 batch sensing run over the twelve-entity test file",
)
PILOT_NAV_55_ROWS: tuple[str, ...] = (
    "5.5 public readiness tool vs backend readiness endpoint",
    "5.5 public benchmarking data vs backend sensing endpoint",
    "5.5 public credit-spread data vs backend data",
    "5.5 public market-intelligence data vs backend corpus query",
    "5.5 brand voice and terminology between site and platform",
)


class _FailedCall:
    """Stand-in response for a call that raised inside the ASGI app."""

    def __init__(self, exc: BaseException) -> None:
        self.status_code: int | None = None
        self.exception = exc
        self.text = f"{type(exc).__name__}: {exc}"
        self.headers: dict[str, str] = {}

    def json(self) -> Any:
        return {"detail": self.text, "type": type(self.exception).__name__}


def _body_hash(resp: Any) -> str:
    try:
        return sha256_text(resp.text)[:16]
    except Exception:  # noqa: BLE001
        return "unhashable"


def _expected_value(path: str, value: str) -> Any:
    if path in INT_COMPARED_PATHS:
        return int(re.sub(r"[^\d]", "", value))
    return value


def _observed_value(path: str, value: Any) -> Any:
    if path in INT_COMPARED_PATHS:
        try:
            return int(float(value))
        except (TypeError, ValueError):
            return value
    return str(value) if value is not None else None


def git_read_only(*args: str) -> str | None:
    """Read-only git query at the repo root; None when git is unavailable."""
    try:
        out = subprocess.run(["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, timeout=30, check=False)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout


def repo_commit() -> str:
    head = (git_read_only("rev-parse", "HEAD") or "").strip()
    return head if re.fullmatch(r"[0-9a-f]{40}", head) else "unknown"


def repo_dirty() -> bool | str:
    status = git_read_only("status", "--porcelain")
    if status is None:
        return "unknown"
    return bool(status.strip())


def cusip_like_tokens(text: str) -> list[str]:
    """Same qualifier as the generator: a strict nine-char hit counts only with a digit."""
    hits = [m.group(0) for m in law.CUSIP_NEAR_WORD_RE.finditer(text)]
    hits += [m.group(0) for m in law.CUSIP_LIKE_STRICT_RE.finditer(text) if any(ch.isdigit() for ch in m.group(0))]
    return hits


@dataclass
class DriverOutput:
    stages: list[StageResult]
    conformance_rows: list[Any]
    deal_workflow_mirror: dict[str, Any]
    register_summary: dict[str, Any]
    review: dict[str, Any]
    vocabulary_divergence: dict[str, Any]
    bfms_emitted_language: list[EmittedLanguage]
    findings_touched: list[str]
    lab_statements: list[str]
    environment: dict[str, Any]
    pins: dict[str, str]
    fulfillment_tree_before: str
    fulfillment_tree_after: str
    fence_class_violation: bool
    repo_commit: str
    repo_dirty: bool | str
    python: str
    forbidden_scan: dict[str, int] = field(default_factory=dict)


class Driver:
    """Drives one scenario through S00-S18 against an attached or standalone harness."""

    def __init__(self, ctx: LabContext, sc: scenario_mod.Scenario, pack_root: Path, run_dir: Path, run_id: str) -> None:
        self.ctx = ctx
        self.sc = sc
        self.pack_root = Path(pack_root)
        self.run_dir = Path(run_dir)
        self.run_id = run_id
        self.calls: list[CallRecord] = []
        self.stages: list[StageResult] = []
        self.state: dict[str, Any] = {}
        self.findings: set[str] = set()
        self.emitted: list[EmittedLanguage] = []
        self.statements: list[str] = [law.LABEL_NOTICE]
        self.fence_class_violation = False
        self.conformance_rows: list[Any] = []
        self.mirror: dict[str, Any] = {}
        self.register_summary: dict[str, Any] = {"status_counts": {}, "obligations": 0, "gaps": 0, "open_items": 0, "unbound_vault_files": [], "base_equivalence": "not_applicable"}
        self.review: dict[str, Any] = {"actor": "lab-scripted-reviewer (NOT a human)", "approved_facts": 0, "rejected_facts": 0, "extracted_by_rules": 0, "entered_manually": 0}
        self.vocab: dict[str, Any] = {}
        self.intake_manifest = json.loads((self.pack_root / "intake" / "intake-manifest.json").read_text(encoding="utf-8"))
        self.pack_manifest = PackManifest.load(self.pack_root)
        self.pack_files: frozenset[str] = frozenset(e["path"] for e in self.pack_manifest["files"])
        self.event_rows = replay.read_event_log(self.pack_root / "bondi" / "event_log.csv")
        self.envelope = Envelope(scenario_id=sc.deal_id, seed=sc.seed)
        self.tree_before = ""
        self.tree_after = ""
        self.commit = "unknown"
        self.dirty: bool | str = "unknown"

    # ------------------------------------------------------------------ plumbing

    async def call(self, method: str, path: str, *, note: str = "", **kwargs: Any) -> Any:
        try:
            resp = await self.ctx.client.request(method, path, headers=self.ctx.headers, **kwargs)
        except Exception as exc:  # noqa: BLE001 - recorded, never hidden
            failed = _FailedCall(exc)
            self.calls.append(CallRecord(method=method, path=path, status_code=None, note=f"raised {type(exc).__name__}; body sha256 {_body_hash(failed)}"))
            return failed
        self.calls.append(CallRecord(method=method, path=path, status_code=resp.status_code, note=note))
        return resp

    def _stage(self, **fields: Any) -> StageResult:
        fields.setdefault("calls", list(self.calls))
        self.calls = []
        result = StageResult.from_sub_assertions(**fields)
        self.stages.append(result)
        return result

    async def _guarded(self, fn: Any, meta: dict[str, Any]) -> StageResult:
        try:
            return await fn()
        except Exception as exc:  # noqa: BLE001 - a stage always returns a StageResult
            tb = traceback.format_exc()
            return self._stage(
                **meta,
                assertion=meta.pop("assertion", "stage raised"),
                sub_assertions=[SubAssertion(key="exception", status="fail", reason=f"{type(exc).__name__}: {str(exc)[:200]}", observed={"traceback_sha256": sha256_text(tb)[:16]})],
                observed={"traceback_tail": tb[-1200:]},
            )

    @staticmethod
    def _sub(key: str, ok: bool, *, observed: Any = None, expected: Any = None, reason: str = "") -> SubAssertion:
        return SubAssertion(key=key, status="pass" if ok else "fail", observed=observed, expected=expected, reason=reason if not ok else "")

    @staticmethod
    def _unknown(key: str, reason: str, *, observed: Any = None) -> SubAssertion:
        return SubAssertion(key=key, status="unknown", reason=reason, observed=observed)

    @staticmethod
    def _na(key: str, reason: str) -> SubAssertion:
        return SubAssertion(key=key, status="not_applicable", reason=reason)

    def _ok(self, resp: Any, *codes: int) -> bool:
        return resp.status_code in (codes or (200,))

    def _call_sub(self, key: str, resp: Any, *codes: int) -> SubAssertion:
        ok = self._ok(resp, *codes)
        return self._sub(key, ok, observed=resp.status_code, expected=list(codes or (200,)), reason="" if ok else f"HTTP {resp.status_code}; body sha256 {_body_hash(resp)}")

    def _export(self, name: str, content: str, source: str) -> tuple[Path, int]:
        """Persist a BFMS export under runs/<run_id>/exports; returns (path, platform-token count)."""
        count = len(law.EMMA_WORD.findall(content))
        path = self.run_dir / EXPORTS_DIR_NAME / name
        body = law.EMMA_WORD.sub("<platform token>", content)
        write_md(path, body, self.envelope.model_copy(update={"created_from": [source]}))
        self.emitted.append(emitted(source, content))
        return path, count

    # ------------------------------------------------------------------ S00

    async def s00_harness(self) -> StageResult:
        meta = {"id": "S00", "station": "all", "bfms_stage": "WP1 harness", "deal_phase": "engagement", "pilot_stage": "none"}
        return await self._guarded(lambda: self._s00(meta), meta)

    async def _s00(self, meta: dict[str, Any]) -> StageResult:
        ctx = self.ctx
        self.tree_before = post_close.fulfillment_tree_sha256()
        self.commit = repo_commit()
        self.dirty = repo_dirty()
        health = await self.call("GET", "/health", note="status code only; body carries a rule-3 path (M6)")
        corpus = ctx.corpus_available()
        engines_now = engines_modules_loaded()
        self.state["engines_at_s00"] = engines_now
        # llm_forbidden is derived, not echoed: constructing the extraction route's client
        # attribute must raise (the harness swapped it for a raising stand-in)
        route_mod = importlib.import_module(EXTRACTION_ROUTE_MODULE)
        llm_construct: str
        try:
            getattr(route_mod, LLM_CLIENT_CLASS)()
            llm_construct = "constructed"
        except ValueError as exc:
            llm_construct = f"raised ValueError: {str(exc)[:80]}"
        except Exception as exc:  # noqa: BLE001 - any other error is not the stand-in
            llm_construct = f"raised {type(exc).__name__}"
        llm_forbidden = llm_construct.startswith("raised ValueError")
        subs = [
            self._call_sub("health_status_code", health, 200),
            self._sub("app_is_full_bfms", ctx.route_count() > 100, observed=ctx.route_count(), expected="> 100 routes"),
            self._sub("anthropic_key_empty", not ctx.anthropic_key_present(), observed=ctx.anthropic_key_present(), expected=False),
            self._sub("llm_forbidden", llm_forbidden, observed=llm_construct, expected="constructing the route's client attribute raises ValueError", reason="the extraction route's client attribute can be constructed; LLM path reachable"),
            self._sub("sensing_corpus_unavailable", not any(corpus.values()), observed=corpus, expected={"healthcare": False, "waste": False}, reason="Class D corpus visible; fence-class abort"),
            self._sub("sensing_pinned_under_run_dir", str(ctx.sensing_extractor_path()).startswith(str(ctx.run_dir)), observed=str(ctx.sensing_extractor_path())[-60:], expected="<run>/empty-root/no-corpus"),
            # one status in both harness modes: the interpreter may be shared (pytest), so the
            # row is not_applicable by rule and S18 asserts the module set is unchanged
            SubAssertion(key="engines_not_loaded", status="not_applicable", reason=ENGINES_NOT_LOADED_REASON, observed=engines_now),
        ]
        if any(corpus.values()):
            self.fence_class_violation = True
            self.findings.add("F15")
        if self.commit == "unknown":
            subs.append(self._unknown("repo_commit", "git unavailable; commit recorded unknown"))
        else:
            subs.append(self._sub("repo_commit", True, observed=self.commit))
        self.findings.add("F15")
        return self._stage(
            **meta,
            assertion="/health 200; app is munipal.main; no key; corpus unreachable; engines untouched",
            sub_assertions=subs,
            observed={"mode": ctx.mode, "python": platform.python_version(), "repo_commit": self.commit, "repo_dirty": self.dirty, "fulfillment_tree_sha256_before": self.tree_before, "celery_dispatch": ctx.celery_dispatch, "harness_notes": ctx.notes},
        )

    # ------------------------------------------------------------------ S01

    async def s01_scenario(self) -> StageResult:
        meta = {"id": "S01", "station": "2_conduit", "bfms_stage": "WP1 data contracts", "deal_phase": "engagement", "pilot_stage": "intake"}
        return await self._guarded(lambda: self._s01(meta), meta)

    async def _s01(self, meta: dict[str, Any]) -> StageResult:
        sc = self.sc
        table_problems = names_mod.check_table()
        party_problems: list[str] = []
        for party in sc.data["parties"]:
            if party.get("name") is None:
                continue
            try:
                names_mod.require_tabled(party["name"])
            except (names_mod.NameNotTabled, names_mod.NameCollision) as exc:
                party_problems.append(str(exc))
        core_diff = scenario_mod.base_core_vs_demo(sc.data)
        # re-run the contract validation here so the row is derived (load() validated once
        # before the Driver existed; a mutated `sc.data` or contract would otherwise pass silently)
        validation_error = ""
        try:
            scenario_mod.validate(sc.data, sc.contract)
        except scenario_mod.ScenarioError as exc:
            validation_error = str(exc)[:300]
        subs = [
            self._sub("deal_v0_and_lab_block_valid", not validation_error, observed={"deal_v0_schema": sc.deal_v0_schema_note, "required": list(sc.contract.required), "validation_error": validation_error or None}, reason=validation_error),
            self._sub("mode_synthetic", sc.data.get("mode") == "synthetic", observed=sc.data.get("mode")),
            self._sub("name_table_clean", not table_problems, observed=table_problems, reason="; ".join(table_problems)[:300]),
            self._sub("party_names_tabled_and_blocklist_clean", not party_problems, observed=party_problems, reason="; ".join(party_problems)[:300]),
            self._sub("stations_present", isinstance(sc.data.get("stations"), dict) and bool(sc.data["stations"]), observed=sorted(sc.data.get("stations") or {})),
            self._sub("base_core_equals_demo_core", not core_diff, observed=core_diff, expected=[], reason=f"core differs from fulfillment/demo scenario at {core_diff[:6]}"),
        ]
        self.findings.add("F10")
        if sc.derived_from is not None:
            base = scenario_mod.load_base_of(sc) or {}
            observed = sorted(scenario_mod.diff_paths(sc.data, base))
            expected = sorted(sc.knob_delta)
            subs.append(self._sub("variant_diff_equals_knob_delta", observed == expected, observed=observed, expected=expected, reason=f"materialised diff {observed} != knob_delta keys {expected}"))
        else:
            subs.append(self._na("variant_diff_equals_knob_delta", "base scenario; no knob_delta"))
        return self._stage(**meta, assertion="valid deal-v0 + lab block; names tabled; stations; variant diff == knob_delta", sub_assertions=subs,
                           observed={"deal_id": sc.deal_id, "derived_from": sc.derived_from, "deal_v0_contract_source": sc.contract.source, "deal_v0_path": sc.contract.path})

    # ------------------------------------------------------------------ S02

    async def s02_pack(self) -> StageResult:
        meta = {"id": "S02", "station": "6_borrower_prep", "bfms_stage": "WP2 inputs", "deal_phase": "diligence", "pilot_stage": "document_request"}
        return await self._guarded(lambda: self._s02(meta), meta)

    def _emma_allowance(self, rel: str) -> tuple[int, str | None]:
        for allowed_rel, heading, count in law.EMMA_ALLOWLIST:
            if allowed_rel == rel:
                return count, heading
        return 0, None

    async def _s02(self, meta: dict[str, Any]) -> StageResult:
        generate_pack = importlib.import_module("labkit.generate_pack")
        from munipal.services.extraction.rules_based_extractor import RulesBasedExtractor

        sc = self.sc
        subs: list[SubAssertion] = []
        regen_a = self.run_dir / "regen-a"
        regen_b = self.run_dir / "regen-b"
        try:
            res_a = generate_pack.generate(sc.path, regen_a)
            res_b = generate_pack.generate(sc.path, regen_b)
            bytes_a = res_a.manifest_path.read_bytes()
            bytes_b = res_b.manifest_path.read_bytes()
            committed = (self.pack_root / law.PACK_MANIFEST_NAME).read_bytes()
            subs.append(self._sub("two_generations_byte_identical", bytes_a == bytes_b, observed=sha256_bytes(bytes_a)[:16], expected=sha256_bytes(bytes_b)[:16]))
            subs.append(self._sub("regenerated_equals_committed", bytes_a == committed, observed=sha256_bytes(bytes_a)[:16], expected=sha256_bytes(committed)[:16], reason="committed pack differs from a fresh generation; regenerate deliberately"))
        finally:
            shutil.rmtree(regen_a, ignore_errors=True)
            shutil.rmtree(regen_b, ignore_errors=True)

        problems: list[str] = []
        token_total = 0
        token_where: list[str] = []
        rule3_hits = 0
        listed = {e["path"]: e for e in self.pack_manifest["files"]}
        on_disk = {p.relative_to(self.pack_root).as_posix() for p in self.pack_root.rglob("*") if p.is_file()}
        on_disk.discard(law.PACK_MANIFEST_NAME)
        if set(listed) != on_disk:
            problems.append(f"manifest/disk mismatch: {sorted(set(listed) ^ on_disk)[:5]}")
        for rel in sorted(on_disk & set(listed)):
            path = self.pack_root / rel
            allowed, heading = self._emma_allowance(rel)
            problems += [f"{rel}: {p}" for p in audit_file(path, emma_allowed=allowed)]
            if sha256_file(path) != listed[rel]["sha256"]:
                problems.append(f"{rel}: sha256 differs from the manifest")
            text = path.read_text(encoding="utf-8")
            rule3_hits += len(law.forbidden_token_hits(text))
            n = len(law.EMMA_WORD.findall(text))
            token_total += n
            if n:
                token_where.append(rel)
                if heading is not None:
                    lines = text.split("\n")
                    start = next((i for i, line in enumerate(lines) if line.startswith(heading)), None)
                    if start is None:
                        problems.append(f"{rel}: heading {heading!r} missing")
                    else:
                        end = next((i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")), len(lines))
                        inside = sum(len(law.EMMA_WORD.findall(line)) for line in lines[start + 1 : end])
                        if inside != allowed:
                            problems.append(f"{rel}: {inside} token line(s) under {heading!r}, pinned {allowed}")
            if cusip_like_tokens(text):
                problems.append(f"{rel}: CUSIP-like token")
        subs.append(self._sub("legend_and_envelope_every_file", not problems, observed=problems[:8], reason="; ".join(problems)[:300]))
        subs.append(self._sub("zero_rule3_tokens", rule3_hits == 0, observed=rule3_hits, expected=0, reason="rule-3 token in the committed pack (fence-class)"))
        subs.append(self._sub("platform_token_only_in_cda_quote", token_total == 1 and token_where == ["closing-documents/03-continuing-disclosure-agreement.md"], observed={"count": token_total, "files": token_where}, expected={"count": 1, "files": ["closing-documents/03-continuing-disclosure-agreement.md"]}, reason="platform token outside the pinned CDA quote (fence-class)"))
        self.findings.add("F6")

        extractor = RulesBasedExtractor()
        misses: list[str] = []
        for entry in self.intake_manifest["upload_order"]:
            text = (self.pack_root / entry["path"]).read_text(encoding="utf-8")
            facts = extractor.extract([{"id": entry["artifact_key"], "text_content": text}], list(entry["expected_paths"]))
            by_path: dict[str, list[Any]] = {}
            for f in facts:
                by_path.setdefault(f.schema_path, []).append(f.value)
            for p in entry["expected_paths"]:
                want = _expected_value(p, sc.intake_facts[p])
                got = by_path.get(p, [])
                if len(got) != 1 or got[0] != want:
                    misses.append(f"{entry['artifact_key']}:{p} -> {got!r} != {want!r}")
        subs.append(self._sub("intake_readable_by_rules_extractor", not misses, observed=misses[:6], reason="; ".join(misses)[:300]))
        if any(s.status == "fail" for s in subs if s.key in ("zero_rule3_tokens", "platform_token_only_in_cda_quote")):
            self.fence_class_violation = True
        return self._stage(**meta, assertion="deterministic pack == committed; legend+envelope everywhere; token pinned; intake round-trips", sub_assertions=subs,
                           observed={"pack_manifest_sha256": sha256_file(self.pack_root / law.PACK_MANIFEST_NAME), "files": len(listed), "absent_by_scenario": len(self.pack_manifest["absent_by_scenario"])})

    # ------------------------------------------------------------------ S03

    async def s03_project(self) -> StageResult:
        meta = {"id": "S03", "station": "1_facility", "bfms_stage": "WP1", "checklist_phase": "P1", "deal_phase": "engagement", "pilot_stage": "intake"}
        return await self._guarded(lambda: self._s03(meta), meta)

    def _party(self, role: str) -> str | None:
        for p in self.sc.data["parties"]:
            if p.get("role") == role:
                return p.get("name")
        return None

    async def _s03(self, meta: dict[str, Any]) -> StageResult:
        from munipal.services.deal_workflow import (
            build_deal_workflow_from_seed,
            initialize_deal_workflow_from_pilot,
            validate_deal_workflow,
        )
        from munipal.services.pilot_onboarding import (
            build_pilot_onboarding_workflow,
            validate_pilot_onboarding_workflow,
        )

        sc = self.sc
        lab = sc.lab
        subs: list[SubAssertion] = []
        seed = await self.call("POST", "/api/v1/playbooks/seed")
        subs.append(self._call_sub("playbook_seed", seed, 201, 200))
        playbook_id = seed.json().get("id") if self._ok(seed, 201, 200) else None
        listing = await self.call("GET", "/api/v1/playbooks/")
        versions = [p.get("version") for p in (listing.json().get("playbooks", []) if self._ok(listing) else [])]
        if versions and all(v == "0.3.0" for v in versions):
            subs.append(self._sub("seeded_playbook_version", True, observed=versions))
        else:
            subs.append(self._unknown("seeded_playbook_version", f"seeded playbook version(s) {versions} other than 0.3.0 (reported, not judged)", observed=versions))
        self.findings.update({"F8", "F11"})
        instrument = sc.data["instrument"]
        body = {
            "name": f"{sc.deal_id} {instrument['title']}",
            "description": law.LEGEND,
            "issuer_name": self._party("conduit_issuer"),
            "project_location": sc.data["obligated_person"]["city"],
            "target_bond_amount": float(instrument["par"]),
            "sector": lab["sector"],
            "subsector": lab["subsector"],
            "archetype_id": lab["archetype_id"],
            "archetype_version": lab.get("archetype_version"),
            "playbook_id": playbook_id,
        }
        created = await self.call("POST", "/api/v1/projects/", json=body)
        subs.append(self._call_sub("project_created", created, 201))
        project: dict[str, Any] = created.json() if self._ok(created, 201) else {}
        self.state["project_id"] = project.get("id")
        echoed = {k: project.get(k) for k in ("sector", "subsector", "archetype_id")}
        wanted = {"sector": lab["sector"], "subsector": lab["subsector"], "archetype_id": lab["archetype_id"]}
        subs.append(self._sub("sector_subsector_archetype_echoed", echoed == wanted, observed=echoed, expected=wanted))

        pilot = validate_pilot_onboarding_workflow(build_pilot_onboarding_workflow(str(lab["sector_playbook_key"])))
        self.state["pilot"] = pilot
        stage_ids = [str(getattr(s.stage, "value", s.stage)) for s in pilot.stages]
        gate_ids = sorted(g.gate_id for g in pilot.pre_pilot_gates if g.required)
        subs.append(self._sub("pilot_workflow_seven_stages", stage_ids == ["intake", "document_request", "upload", "extraction", "review", "readiness", "handoff"], observed=stage_ids))
        subs.append(self._sub("pilot_three_required_gate_ids", gate_ids == ["engagement_scope_signed", "pilot_smoke_test_green", "registered_ma_confirmed"], observed=gate_ids))

        closing_literal = sc.closing
        year_literal = closing_literal or instrument.get("dated")
        if year_literal is None:
            subs.append(self._unknown("deal_workflow_seeded", "no closing/dated literal in the scenario; workflow year cannot be read (never computed)"))
            return self._stage(**meta, assertion="project + pilot + deal workflow", sub_assertions=subs, observed={"project_id": self.state.get("project_id")})
        closing_date = _date.fromisoformat(closing_literal) if closing_literal else None
        dw = build_deal_workflow_from_seed(
            deal_id=sc.deal_id,
            name=instrument["title"],
            year=int(year_literal[:4]),
            borrower=self._party("obligated_person") or "Borrower",
            conduit_issuer=self._party("conduit_issuer") or "Conduit Issuer",
            sector=lab["sector"],
            par_amount_usd=float(instrument["par"]),
            bond_counsel=self._party("bond_counsel") or "Bond Counsel",
            municipal_advisor=self._party("municipal_advisor") or "Municipal Advisor",
            underwriter=self._party("underwriter") or "Underwriter",
            trustee=self._party("trustee") or "Trustee",
            target_closing_date=closing_date,
        )
        validate_deal_workflow(dw)
        self.state["deal_workflow"] = dw
        subs.append(self._sub("deal_workflow_mirror_only", dw.metadata.liability_boundary == "mirror_only", observed=dw.metadata.liability_boundary, expected="mirror_only"))
        counterparties = {p.counterparty: p.role for p in dw.working_group}
        missing_names: list[str] = []
        role_divergence: list[str] = []
        for party in sc.data["parties"]:
            if not party.get("bfms_party_role") or party.get("name") is None:
                continue
            if party["name"] not in counterparties:
                missing_names.append(f"{party['role']}={party['name']}")
            elif counterparties[party["name"]] != party["bfms_party_role"] and party["bfms_party_role"] != "Other":
                role_divergence.append(f"{party['role']}: scenario {party['bfms_party_role']!r} vs seed {counterparties[party['name']]!r}")
        subs.append(self._sub("working_group_carries_every_scenario_party", not missing_names, observed=missing_names, expected=[], reason=f"parties absent from the working group: {missing_names}"))
        self.vocab["deal_workflow_role_only"] = role_divergence
        if closing_date is None:
            subs.append(self._unknown("deal_workflow_from_pilot", "closing is null in the scenario; from-pilot initialisation skipped (deal_workflow.py:379 would fall back to today's date)"))
        else:
            dw2 = initialize_deal_workflow_from_pilot(
                pilot,
                deal_id=f"{sc.deal_id}-P",
                borrower=self._party("obligated_person") or "Borrower",
                conduit_issuer=self._party("conduit_issuer") or "Conduit Issuer",
                advisor=self._party("municipal_advisor") or "Municipal Advisor",
                reviewer="lab-scripted-reviewer",
                target_closing_date=closing_date,
            )
            validate_deal_workflow(dw2)
            subs.append(self._sub("deal_workflow_from_pilot", dw2.metadata.deal_workflow_tracking_enabled and dw2.metadata.pilot_workflow_id == pilot.workflow_id, observed={"tracking": dw2.metadata.deal_workflow_tracking_enabled, "pilot_workflow_id": dw2.metadata.pilot_workflow_id, "documents": len(dw2.documents)}))
        return self._stage(**meta, assertion="201; sector echoed; pilot workflow valid; deal workflow mirror_only with every party", sub_assertions=subs,
                           observed={"project_id": self.state.get("project_id"), "playbook_id": playbook_id, "documents": [d.id for d in dw.documents], "role_divergence": role_divergence})

    # ------------------------------------------------------------------ S04

    async def s04_request(self) -> StageResult:
        meta = {"id": "S04", "station": "6_borrower_prep", "bfms_stage": "WP2", "deal_phase": "diligence", "pilot_stage": "document_request"}
        return await self._guarded(lambda: self._s04(meta), meta)

    async def _s04(self, meta: dict[str, Any]) -> StageResult:
        from munipal.services.pilot_onboarding import _OPERATOR_WORKSPACE_FOLDERS

        sc = self.sc
        pilot = self.state["pilot"]
        key_by_display = {a.display_name: a.artifact_key for a in pilot.playbook.required_artifacts}
        present = {e["artifact_key"] for e in self.intake_manifest["upload_order"]}
        dropped = {d["artifact_key"] for d in self.intake_manifest.get("dropped", [])}
        knob = (sc.lab.get("knobs") or {}).get("drop_required_artifact")
        subs: list[SubAssertion] = []
        unmapped: list[str] = []
        missing_required: list[str] = []
        missing_recommended: list[str] = []
        for item in pilot.document_request_list:
            m = re.match(r"^(.*) \((required|recommended)\)$", item)
            if not m or m.group(1) not in key_by_display:
                unmapped.append(item)
                continue
            key, level = key_by_display[m.group(1)], m.group(2)
            if key in present:
                continue
            if level == "required":
                missing_required.append(key)
            elif key not in dropped:
                missing_recommended.append(key)
        subs.append(self._sub("request_list_maps_to_artifact_keys", not unmapped, observed=unmapped))
        undeclared = [k for k in missing_required if k != knob]
        subs.append(self._sub("every_required_artifact_present_or_declared", not undeclared, observed=missing_required, reason=f"required artifact(s) missing without a knob: {undeclared}"))
        # the `declared_gap` row exists only when a knob names the missing artifact (the knob
        # is the experiment); a base scenario carries no such row
        if knob and knob in missing_required:
            subs.append(SubAssertion(key="declared_gap", status="pass", observed=knob, reason=f"knob drop_required_artifact={knob}"))
            self.state["declared_gap"] = knob
        elif knob:
            subs.append(self._sub("declared_gap", False, observed=knob, reason=f"knob names {knob} but the pack still carries it"))
        subs.append(self._sub("recommended_present_or_listed_absent", not missing_recommended, observed=missing_recommended))
        folders = {e["folder"] for e in self.intake_manifest["upload_order"]}
        subs.append(self._sub("workspace_folders_subset", folders <= set(_OPERATOR_WORKSPACE_FOLDERS), observed=sorted(folders)))
        waste_hits = [item for item in pilot.document_request_list if WASTE_TERM_RE.search(item)]
        subs.append(self._sub("no_waste_term_in_request_list", not waste_hits, observed=waste_hits))
        self.state["present_artifacts"] = present
        return self._stage(**meta, assertion="document_request_list maps 1:1 onto the intake pack; required present or declared", sub_assertions=subs,
                           observed={"request_list": list(pilot.document_request_list), "present": sorted(present), "dropped": sorted(dropped)})

    # ------------------------------------------------------------------ S05

    async def s05_vault(self) -> StageResult:
        meta = {"id": "S05", "station": "6_borrower_prep", "bfms_stage": "WP2 Artifact Vault", "deal_phase": "diligence", "pilot_stage": "upload"}
        return await self._guarded(lambda: self._s05(meta), meta)

    async def _upload_and_process(self, rel: str, display_name: str) -> dict[str, Any]:
        path = self.pack_root / rel
        data = path.read_bytes()
        text = data.decode("utf-8")
        up = await self.call("POST", "/api/v1/artifacts/upload", data={"project_id": self.state["project_id"], "display_name": display_name}, files={"file": (path.name, data, "text/plain")})
        rec: dict[str, Any] = {"rel": rel, "display_name": display_name, "upload_status": up.status_code, "sha256": sha256_bytes(data), "artifact_id": None, "processing_error": None, "chunk_hash_ok": False, "chunks": 0, "response_keys": []}
        if not self._ok(up, 202):
            rec["error"] = f"upload HTTP {up.status_code} body {_body_hash(up)}"
            return rec
        body = up.json()
        rec["artifact_id"] = body.get("id")
        rec["processing_error"] = body.get("processing_error")
        rec["response_keys"] = sorted(body.keys())
        proc = await self.call("POST", f"/api/v1/artifacts/{rec['artifact_id']}/process")
        rec["process_status"] = proc.status_code
        if not self._ok(proc):
            rec["error"] = f"process HTTP {proc.status_code} body {_body_hash(proc)}"
            return rec
        chunks = await self.call("GET", f"/api/v1/artifacts/{rec['artifact_id']}/chunks")
        if not self._ok(chunks):
            rec["error"] = f"chunks HTTP {chunks.status_code}"
            return rec
        items = chunks.json().get("chunks", [])
        rec["chunks"] = len(items)
        rec["chunk_hash_ok"] = len(items) >= 1 and items[0].get("content_hash") == sha256_text(text)
        rec["chunk_page"] = items[0].get("page_number") if items else None
        return rec

    async def _s05(self, meta: dict[str, Any]) -> StageResult:
        records: list[dict[str, Any]] = []
        for entry in self.intake_manifest["upload_order"]:
            records.append(await self._upload_and_process(entry["path"], entry["artifact_key"]))
        closing_docs = sorted(p for p in self.pack_files if p.startswith("closing-documents/") and p.endswith(".md"))
        for rel in closing_docs:
            records.append(await self._upload_and_process(rel, f"{CLOSING_UPLOAD_FOLDER}/{Path(rel).name}"))
        dup_source = next((e for e in self.intake_manifest["upload_order"] if e["artifact_key"] == "subsidy_stack"), self.intake_manifest["upload_order"][0])
        dup = await self._upload_and_process(dup_source["path"], dup_source["artifact_key"] + " (re-upload)")
        first_id = next((r["artifact_id"] for r in records if r["rel"] == dup_source["path"]), None)
        listing = await self.call("GET", "/api/v1/artifacts/", params={"project_id": self.state["project_id"], "limit": 100})
        listed = listing.json() if self._ok(listing) else {}
        total = listed.get("total", len(listed.get("artifacts", [])) if isinstance(listed, dict) else None)
        expected_total = len(records) + 1
        errors = [f"{r['rel']}: {r['error']}" for r in records + [dup] if r.get("error")]
        subs = [
            self._sub("uploads_accepted_and_processed", not errors, observed=errors[:6], reason="; ".join(errors)[:300]),
            self._sub("one_chunk_with_sha256_of_text", all(r["chunk_hash_ok"] for r in records), observed=[r["rel"] for r in records if not r["chunk_hash_ok"]], expected=[]),
            self._sub("processing_error_null", all(r.get("processing_error") is None for r in records), observed=[r["processing_error"] for r in records if r.get("processing_error")]),
            self._sub("artifact_count", total == expected_total, observed=total, expected=expected_total),
            self._sub("artifact_dedup", dup.get("artifact_id") is not None and dup["artifact_id"] == first_id, observed={"first": first_id, "second": dup.get("artifact_id")}, expected="same artifact id for identical bytes", reason="second artifact id created for identical bytes; no artifact-level hash (F9)"),
            self._sub("artifact_level_sha256", any("sha256" in k or "content_hash" in k for k in dup.get("response_keys", [])), observed=dup.get("response_keys"), expected="a sha256 / content_hash key on ArtifactRead", reason="ArtifactRead carries no artifact-level hash (F9; docs/architecture/BFMS_DATA_MODEL_PRIMITIVES.md)"),
        ]
        self.findings.add("F9")
        self.state["intake_artifacts"] = {r["display_name"]: r for r in records if r["rel"].startswith("intake/")}
        self.state["uploads_done"] = not errors
        return self._stage(**meta, assertion="every intake and closing file uploaded, processed, chunk-hashed; dedup observed (F9)", sub_assertions=subs,
                           observed={"records": records, "duplicate": dup, "total_listed": total}, evidence_refs=[e["path"] for e in self.intake_manifest["upload_order"]])

    # ------------------------------------------------------------------ S06

    async def s06_extraction(self) -> StageResult:
        meta = {"id": "S06", "station": "6_borrower_prep", "bfms_stage": "WP3 Controlled Intelligence", "deal_phase": "diligence", "pilot_stage": "extraction"}
        return await self._guarded(lambda: self._s06(meta), meta)

    async def _s06(self, meta: dict[str, Any]) -> StageResult:
        sc = self.sc
        subs: list[SubAssertion] = []
        modes: list[str] = []
        job_errors: list[str] = []
        for entry in self.intake_manifest["upload_order"]:
            rec = self.state["intake_artifacts"].get(entry["artifact_key"])
            if not rec or not rec.get("artifact_id"):
                job_errors.append(f"{entry['artifact_key']}: no artifact")
                continue
            created = await self.call("POST", "/api/v1/extraction/", json={"project_id": self.state["project_id"], "artifact_ids": [rec["artifact_id"]], "target_schema_paths": list(entry["expected_paths"])})
            if not self._ok(created, 200, 201, 202):
                job_errors.append(f"{entry['artifact_key']}: create HTTP {created.status_code} body {_body_hash(created)}")
                continue
            job_id = created.json().get("job_id")
            run = await self.call("POST", f"/api/v1/extraction/{job_id}/run")
            if not self._ok(run):
                job_errors.append(f"{entry['artifact_key']}: run HTTP {run.status_code} body {_body_hash(run)}")
                continue
            body = run.json()
            modes.append(str(body.get("extraction_mode")))
            if body.get("status") != "completed":
                job_errors.append(f"{entry['artifact_key']}: status {body.get('status')}")
        mode_ok = bool(modes) and all(m == "rules_based_fallback" for m in modes)
        subs.append(self._sub("extraction_mode_rules_based_fallback", mode_ok, observed=sorted(set(modes)), expected=["rules_based_fallback"], reason="an extraction job did not take the rules-based fallback (fence-class: LLM path)"))
        if not mode_ok:
            self.fence_class_violation = True
        subs.append(self._sub("one_job_per_intake_artifact_completed", not job_errors, observed=job_errors, reason="; ".join(job_errors)[:300]))
        self.state["extraction_mode"] = modes[0] if modes else "unknown"

        listing = await self.call("GET", "/api/v1/facts/", params={"project_id": self.state["project_id"], "limit": 500})
        facts = listing.json().get("facts", []) if self._ok(listing) else []
        by_path: dict[str, list[dict[str, Any]]] = {}
        for f in facts:
            by_path.setdefault(f["schema_path"], []).append(f)
        found: dict[str, Any] = {}
        contradictions: list[str] = []
        unknown_paths: list[str] = []
        present_paths = sc.present_intake_paths
        # one sub-assertion per intake path: pass (found, equal), fail (contradiction),
        # unknown (no fact, or the artifact is absent by scenario knob) -- never rounded up
        for p in present_paths:
            items = by_path.get(p, [])
            if not items:
                unknown_paths.append(p)
                subs.append(self._unknown(f"path_{p}", "present path yielded no fact"))
                continue
            got = _observed_value(p, items[0]["value"])
            want = _expected_value(p, sc.intake_facts[p])
            if got == want:
                found[p] = items[0]["id"]
                subs.append(self._sub(f"path_{p}", True, observed="found; equals scenario"))
            else:
                contradictions.append(f"{p}: {got!r} != {want!r}")
                subs.append(self._sub(f"path_{p}", False, observed=got, expected=want, reason="found value contradicts the scenario"))
        dropped = list(sc.dropped_intake_paths)
        for p in dropped:
            subs.append(self._unknown(f"path_{p}", "no intake line: artifact absent by scenario knob"))

        details: dict[str, dict[str, Any]] = {}
        provenance_missing: list[str] = []
        confidence_off: list[str] = []
        for p, fid in found.items():
            detail = await self.call("GET", f"/api/v1/facts/{fid}")
            if not self._ok(detail):
                provenance_missing.append(f"{p}: HTTP {detail.status_code}")
                continue
            d = detail.json()
            details[p] = {"id": fid, "confidence_score": d.get("confidence_score"), "source_refs": len(d.get("source_refs") or []), "source_chunks": len(d.get("source_chunks") or []), "is_canonical": d.get("is_canonical")}
            if not (d.get("source_refs") or d.get("source_chunks")):
                provenance_missing.append(p)
            if d.get("confidence_score") != 0.72:
                confidence_off.append(f"{p}={d.get('confidence_score')}")
        subs.append(self._sub("every_fact_has_chunk_provenance", not provenance_missing, observed=provenance_missing, reason=f"facts without Artifact->Chunk provenance: {provenance_missing[:5]}"))
        subs.append(self._sub("confidence_score_0_72", not confidence_off, observed=confidence_off))
        self.state["found_facts"] = found
        self.state["fact_details"] = details
        self.review["extracted_by_rules"] = len(facts)
        self.findings.add("F12")
        return self._stage(**meta, assertion="rules-based fallback; one job per artifact; found values equal the scenario; unknowns counted", sub_assertions=subs,
                           observed={"facts_total": len(facts), "found": len(found), "unknown_present": unknown_paths, "unknown_dropped": dropped, "modes": modes})

    # ------------------------------------------------------------------ S07

    async def s07_review(self) -> StageResult:
        meta = {"id": "S07", "station": "6_borrower_prep", "bfms_stage": "WP3 human review", "deal_phase": "drafting", "pilot_stage": "review"}
        return await self._guarded(lambda: self._s07(meta), meta)

    async def _s07(self, meta: dict[str, Any]) -> StageResult:
        sc = self.sc
        plan = sc.lab["review_plan"]
        reject_paths = [p for p in plan.get("reject", []) if p in self.state.get("found_facts", {})]
        approved: set[str] = set()
        rejected: set[str] = set()
        errors: list[str] = []
        first_approved_id = first_rejected_id = None
        for p, fid in self.state.get("found_facts", {}).items():
            if p in reject_paths:
                resp = await self.call("POST", f"/api/v1/facts/{fid}/reject", params={"reviewer_id": self.ctx.reviewer_id, "reason": "lab review plan: rejected by script"})
                if self._ok(resp) and resp.json().get("review_status") == "rejected":
                    rejected.add(p)
                    first_rejected_id = first_rejected_id or fid
                else:
                    errors.append(f"reject {p}: HTTP {resp.status_code}")
            else:
                resp = await self.call("POST", f"/api/v1/facts/{fid}/approve", params={"reviewer_id": self.ctx.reviewer_id})
                if self._ok(resp) and resp.json().get("review_status") == "approved":
                    approved.add(p)
                    first_approved_id = first_approved_id or fid
                else:
                    errors.append(f"approve {p}: HTTP {resp.status_code}")
        counts_resp = await self.call("GET", "/api/v1/facts/counts", params={"project_id": self.state["project_id"]})
        counts = counts_resp.json() if self._ok(counts_resp) else {}
        matched = len(self.state.get("found_facts", {}))
        subs = [
            self._sub("review_calls_succeeded", not errors, observed=errors, reason="; ".join(errors)[:300]),
            self._sub("approved_count", counts.get("approved") == matched - len(rejected), observed=counts.get("approved"), expected=matched - len(rejected)),
            self._sub("rejected_count", counts.get("rejected") == len(reject_paths) and len(reject_paths) == len(plan.get("reject", [])), observed=counts.get("rejected"), expected=len(plan.get("reject", []))),
        ]
        revisions_ok: list[bool] = []
        for fid in (first_approved_id, first_rejected_id):
            if fid is None:
                continue
            rev = await self.call("GET", f"/api/v1/facts/{fid}/revisions")
            revisions_ok.append(self._ok(rev) and len(rev.json()) >= 1)
        subs.append(self._sub("revisions_logged", bool(revisions_ok) and all(revisions_ok), observed=revisions_ok))
        details = self.state.get("fact_details", {})
        no_ref = [p for p in approved if not (details.get(p, {}).get("source_refs") or details.get(p, {}).get("source_chunks"))]
        subs.append(self._sub("approved_facts_have_chunk_refs", not no_ref, observed=no_ref))
        subs.append(self._na("bond_strategist_review_rows", "not_applicable (no human seat): pilot-nav 'Bond Strategist reviews' rows"))
        self.state["approved_paths"] = frozenset(approved)
        self.review["approved_facts"] = len(approved)
        self.review["rejected_facts"] = len(rejected)
        self.statements.append(REVIEW_STATEMENT)
        return self._stage(**meta, assertion="scripted approve/reject; counts; revisions; provenance on approved facts", sub_assertions=subs,
                           observed={"approved_paths": sorted(approved), "rejected_paths": sorted(rejected), "counts": counts})

    # ------------------------------------------------------------------ S08

    async def s08_checklist(self) -> StageResult:
        meta = {"id": "S08", "station": "3_issuance", "bfms_stage": "WP4", "checklist_phase": "P1-P6", "deal_phase": "drafting", "pilot_stage": "readiness"}
        return await self._guarded(lambda: self._s08(meta), meta)

    async def _s08(self, meta: dict[str, Any]) -> StageResult:
        from munipal.services.checklist_service import ChecklistService

        pid = self.state["project_id"]
        approved = set(self.state.get("approved_paths", frozenset()))
        # the not_applicable test uses the scenario FAMILY's full intake path set (every path
        # the pack could carry, i.e. the base intake_facts keys), not the materialised pack's
        # present paths: an item whose paths a knob dropped (LAB03) is scored, not excused
        family_paths = set(self.sc.intake_facts)
        dropped_paths = set(self.sc.dropped_intake_paths)
        details = self.state.get("fact_details", {})
        thresholds = ChecklistService(self.ctx.session)  # read-only: min_confidence per path
        # BFMS counts a path as covered only when the approved fact clears the path's
        # min_confidence; rules-based facts carry 0.72 (F17), so the expectation is mechanical.
        confident = {p for p in approved if (details.get(p, {}).get("confidence_score") or 0.0) >= thresholds._get_min_confidence(p)}
        first = [await self.call("GET", "/api/v1/checklist/", params={"project_id": pid}), await self.call("GET", "/api/v1/checklist/summary", params={"project_id": pid}), await self.call("GET", "/api/v1/checklist/gaps", params={"project_id": pid})]
        second = [await self.call("GET", "/api/v1/checklist/", params={"project_id": pid}), await self.call("GET", "/api/v1/checklist/summary", params={"project_id": pid}), await self.call("GET", "/api/v1/checklist/gaps", params={"project_id": pid})]
        defs_resp = await self.call("GET", "/api/v1/checklist/definitions")
        subs = [self._call_sub(f"http_{name}", r, 200) for name, r in zip(("list", "summary", "gaps"), first, strict=True)]
        identical = all(self._ok(a) and self._ok(b) and a.text == b.text for a, b in zip(first, second, strict=True))
        subs.append(self._sub("two_calls_identical", identical, reason="checklist responses differ between two identical calls (non-determinism)"))
        items = first[0].json().get("checklist_items", []) if self._ok(first[0]) else []
        defs = {d["item_code"]: d for d in (defs_resp.json() if self._ok(defs_resp) else [])}
        subs.append(self._sub("nineteen_items", len(items) == 19, observed=len(items), expected=19, reason="CHECKLIST_ITEMS constant drifted"))
        item_status: dict[str, str] = {}
        checklist_only: set[str] = set()
        for item in sorted(items, key=lambda i: i["item_code"]):
            code = item["item_code"]
            required = list(defs.get(code, {}).get("required_schema_paths", []))
            status_literal = item.get("status")
            item_status[code] = str(status_literal)
            if required and not (set(required) & family_paths):
                subs.append(self._na(f"item_{code}", "UCS CHECKLIST_ITEMS constant; no required path in the housing intake family (F8)"))
                continue
            checklist_only |= {p for p in required if p not in family_paths}
            expected_covered = len(set(required) & confident)
            expected_low = sorted((set(required) & approved) - confident)
            dropped_here = sorted(set(required) & dropped_paths)
            observed_covered = item.get("covered_paths_count")
            observed_low = sorted(item.get("low_confidence_paths") or [])
            ok = observed_covered == expected_covered and observed_low == expected_low
            dropped_note = f"; {len(dropped_here)} path(s) absent by scenario knob" if dropped_here else ""
            subs.append(SubAssertion(key=f"item_{code}", status="pass" if ok else "fail", observed={"status": status_literal, "covered": observed_covered, "required": item.get("required_paths_count"), "missing": item.get("missing_paths"), "low_confidence": observed_low, "dropped_by_knob": dropped_here}, expected={"covered": expected_covered, "low_confidence": expected_low}, reason=f"bfms status={status_literal}; covered {observed_covered}/{item.get('required_paths_count')}; low_confidence {len(observed_low)}{dropped_note}"))
        summary = first[1].json() if self._ok(first[1]) else {}
        self.vocab["checklist_only"] = sorted(checklist_only)
        self.findings.update({"F5", "F8"})
        if any((item.get("low_confidence_paths") or []) for item in items):
            self.findings.add("F17")
            self.vocab["finding_f17"] = "rules-based fallback facts carry confidence 0.72, below the min_confidence of most checklist paths; approved facts stay low-confidence and the item stays blocked (checklist_service.py::compute_item_status)"
        return self._stage(**meta, assertion="19 items; per-item coverage == required ∩ approved; two calls identical", sub_assertions=subs,
                           observed={"item_status": item_status, "can_proceed_to_next": {k: v.get("can_proceed_to_next") for k, v in summary.items()} if isinstance(summary, dict) else None, "gaps": first[2].json() if self._ok(first[2]) else None})

    # ------------------------------------------------------------------ S09

    async def s09_readiness(self) -> StageResult:
        meta = {"id": "S09", "station": "4_structure", "bfms_stage": "WP4 readiness", "deal_phase": "drafting", "pilot_stage": "readiness"}
        return await self._guarded(lambda: self._s09(meta), meta)

    async def _s09(self, meta: dict[str, Any]) -> StageResult:
        from munipal.services.readiness_service import SECTOR_READINESS_PROFILES

        pid = self.state["project_id"]
        approved = set(self.state.get("approved_paths", frozenset()))
        r1 = await self.call("GET", "/api/v1/readiness/", params={"project_id": pid})
        r2 = await self.call("GET", "/api/v1/readiness/", params={"project_id": pid})
        gaps = await self.call("GET", "/api/v1/readiness/gaps", params={"project_id": pid})
        expl = await self.call("GET", "/api/v1/readiness/explanation", params={"project_id": pid})
        subs = [self._call_sub("http_readiness", r1, 200), self._call_sub("http_gaps", gaps, 200), self._call_sub("http_explanation", expl, 200)]
        subs.append(self._sub("byte_identical_across_calls", self._ok(r1) and self._ok(r2) and r1.text == r2.text, reason="readiness differs between two identical calls"))
        body = r1.json() if self._ok(r1) else {}
        profile = SECTOR_READINESS_PROFILES.get(self.sc.lab["subsector"], {})
        expected_names = sorted(str(v) for v in profile.get("dimension_names", {}).values())
        dims = body.get("dimensions", {}) or {}
        observed_names = sorted(str(v.get("dimension_name")) for v in dims.values()) if isinstance(dims, dict) else []
        subs.append(self._sub("dimension_names_match_housing_profile", observed_names == expected_names, observed=observed_names, expected=expected_names, reason="wrong readiness profile"))
        score = body.get("overall_score")
        subs.append(self._sub("overall_score_in_range", isinstance(score, int | float) and 0 <= score <= 10, observed=score))
        ucs_hits = [n for n in observed_names if WASTE_TERM_RE.search(n)]
        subs.append(self._sub("no_ucs_term_in_dimension_display_names", not ucs_hits, observed=ucs_hits))
        profile_paths: set[str] = set()
        for cfg in (profile.get("dimensions") or {}).values():
            profile_paths |= set(cfg.get("contributing_paths", []))
        expected_gaps = sorted(profile_paths - approved)
        gap_body = gaps.json() if self._ok(gaps) else {}
        observed_gaps = sorted({g["schema_path"] for key in ("critical_gaps", "material_gaps", "secondary_gaps") for g in gap_body.get(key, [])})
        subs.append(SubAssertion(key="gap_set", status="pass" if observed_gaps == expected_gaps else "fail", observed=observed_gaps, expected=expected_gaps, reason=f"gaps={len(observed_gaps)}: {observed_gaps}"))
        if body.get("recommendation"):
            self.emitted.append(emitted("readiness.recommendation", str(body["recommendation"])))
        ex = expl.json() if self._ok(expl) else {}
        for key in ("recommendation", "summary"):
            if ex.get(key):
                self.emitted.append(emitted(f"readiness.explanation.{key}", str(ex[key])))
        self.vocab["readiness_profile_only"] = sorted(profile_paths - set(self.sc.intake_facts))
        self.vocab["readiness_dimension_keys_ucs_legacy"] = sorted(str(k) for k in dims) if isinstance(dims, dict) else []
        self.vocab["finding"] = "F5"
        self.findings.add("F5")
        return self._stage(**meta, assertion="housing profile names; deterministic; gap set == profile paths minus approved", sub_assertions=subs,
                           observed={"overall_score": score, "dimension_scores": {k: (v.get("score") if isinstance(v, dict) else v) for k, v in dims.items()} if isinstance(dims, dict) else None, "gaps": observed_gaps})

    # ------------------------------------------------------------------ S10

    async def s10_requests_disclosure(self) -> StageResult:
        meta = {"id": "S10", "station": "2_conduit", "bfms_stage": "WP4 gaps -> WP6 disclosure", "checklist_phase": "P4", "deal_phase": "drafting", "pilot_stage": "readiness"}
        return await self._guarded(lambda: self._s10(meta), meta)

    async def _s10(self, meta: dict[str, Any]) -> StageResult:
        pid = self.state["project_id"]
        gen = await self.call("POST", "/api/v1/information-requests/generate", params={"project_id": pid})
        rep = await self.call("GET", f"/api/v1/information-requests/report/{pid}")
        generated = gen.json().get("generated_count") if self._ok(gen) else None
        report = rep.json() if self._ok(rep) else {}
        subs = [
            self._call_sub("http_generate_requests", gen, 200),
            # templates fire per gap (the probe's 13 was a healthcare project); the count is
            # an observation the golden freezes, not a lab assertion
            SubAssertion(key="generated_count", status="pass" if isinstance(generated, int) and generated > 0 else "fail", observed=generated, expected="> 0 (observed count frozen by the golden)", reason=f"generated={generated}"),
            self._sub("report_open_count_equals_generated", report.get("open_count") == generated, observed=report.get("open_count"), expected=generated),
        ]
        disc = await self.call("POST", "/api/v1/disclosure/generate", json={"project_id": pid})
        subs.append(self._call_sub("http_disclosure_generate", disc, 200))
        doc_id = disc.json().get("document_id") if self._ok(disc) else None
        completeness = None
        tbd = 0
        token_count = 0
        if doc_id:
            doc = await self.call("GET", f"/api/v1/disclosure/{doc_id}")
            completeness = doc.json().get("completeness_score") if self._ok(doc) else None
            export = await self.call("GET", f"/api/v1/disclosure/{doc_id}/export", params={"format": "md"})
            if self._ok(export):
                content = str(export.json().get("content", ""))
                tbd = content.count("[TBD")
                _path, token_count = self._export("disclosure.md", content, "disclosure.export.md")
            subs.append(self._call_sub("http_disclosure_export", export, 200))
        subs.append(self._sub("completeness_below_one", isinstance(completeness, int | float) and completeness < 1.0, observed=completeness, expected="< 1.0"))
        subs.append(SubAssertion(key="tbd_markers_present", status="pass" if tbd > 0 else "fail", observed=tbd, expected="> 0", reason=f"tbd_markers={tbd}"))
        subs.append(self._sub("no_platform_token_in_export", token_count == 0, observed=token_count, expected=0))
        return self._stage(**meta, assertion="13 requests; report open_count; disclosure incomplete with TBD markers; no platform token", sub_assertions=subs,
                           observed={"generated_count": generated, "open_count": report.get("open_count"), "completeness_score": completeness, "tbd_markers": tbd})

    # ------------------------------------------------------------------ S11

    async def s11_models(self) -> StageResult:
        meta = {"id": "S11", "station": "4_structure", "bfms_stage": "WP5 Financial & Performance Models", "deal_phase": "pricing", "pilot_stage": "none"}
        self.statements.append("S11 not run: sizing and pricing engines are out of bounds by law; the pricing timeline entry stays planned")
        return self._stage(**meta, assertion="NOT RUN by law (BFMS spec: no sizing / pricing / approval)", sub_assertions=[self._na("wp5_models", "out of bounds by law (brief rule 5; engines fenced); no call made")], reason="out of bounds by law")

    # ------------------------------------------------------------------ S12

    async def s12_handoff(self) -> StageResult:
        meta = {"id": "S12", "station": "5_buyers", "bfms_stage": "WP6 Warm Handoff Pack", "checklist_phase": "P6", "deal_phase": "pre-closing", "pilot_stage": "handoff"}
        return await self._guarded(lambda: self._s12(meta), meta)

    async def _s12(self, meta: dict[str, Any]) -> StageResult:
        from munipal.services.sector_playbooks import get_sector_playbook

        pid = self.state["project_id"]
        created = await self.call("POST", "/api/v1/deliverables/", params={"sync": "true"}, json={"project_id": pid, "title": f"{self.sc.deal_id} lab handoff pack (synthetic)", "generated_for": "internal_lab_review", "include_appendices": True})
        body = created.json() if self._ok(created, 202) else {}
        subs = [self._call_sub("http_pack_create_sync", created, 202), self._sub("pack_completed", body.get("status") == "completed", observed=body.get("status")), self._sub("sections_generated_9", body.get("sections_generated") == 9, observed=body.get("sections_generated"), expected=9)]
        pack_id = body.get("pack_id")
        token_count = 0
        markers_present = False
        sector_disclaimers_present = False
        if pack_id:
            status = await self.call("GET", f"/api/v1/deliverables/{pack_id}/status")
            subs.append(self._call_sub("http_pack_status", status, 200))
            export = await self.call("GET", f"/api/v1/deliverables/{pack_id}/export/markdown")
            subs.append(self._call_sub("http_pack_export_markdown", export, 200))
            if self._ok(export):
                content = str(export.json().get("content", ""))
                markers_present = all(m in content for m in DELIVERABLE_DISCLAIMER_MARKERS)
                texts = [d.text for d in get_sector_playbook(str(self.sc.lab["sector_playbook_key"])).liability_disclaimers]
                sector_disclaimers_present = any(t in content for t in texts)
                _path, token_count = self._export("deliverable-pack.md", content, "deliverables.export.markdown")
        subs.append(self._sub("mandatory_disclaimer_present", markers_present, observed=markers_present, expected=True, reason="the pack's own disclaimer block is missing from the markdown export"))
        # a real sub-assertion (expected fail today = F16, listed in report.KNOWN_GAP_KEYS):
        # a src fix or a regression changes the golden view and reddens the ratchet
        subs.append(self._sub("sector_liability_disclaimers_present", sector_disclaimers_present, observed=sector_disclaimers_present, expected=True, reason="deliverable pack ignores the sector playbook liability_disclaimers (F16; deliverable_service.py)"))
        subs.append(self._sub("no_platform_token_in_export", token_count == 0, observed=token_count, expected=0))
        internal = await self.call("POST", "/api/v1/advisory-packages/internal/generate", json={"project_id": pid})
        subs.append(self._call_sub("http_internal_report_generate", internal, 200))
        report_id = internal.json().get("report_id") if self._ok(internal) else None
        if report_id:
            iexp = await self.call("GET", f"/api/v1/advisory-packages/internal/{report_id}/export", params={"format": "md"})
            subs.append(self._call_sub("http_internal_report_export", iexp, 200))
            if self._ok(iexp):
                self._export("internal-readiness-report.md", str(iexp.json().get("content", "")), "advisory_packages.internal.export.md")
        subs.append(self._na("export_pdf_docx", "not_applicable (markdown only; PDF export queues Celery)"))
        subs.append(self._na("bond_strategist_review_rows", "not_applicable (no human seat)"))
        subs.append(self._na("external_advisory_package", "not generated: nothing is ready for distribution in a lab (TR-1)"))
        self.findings.add("F16")
        return self._stage(**meta, assertion="pack completed with 9 sections; markdown export carries the mandatory and sector disclaimers; internal report exported", sub_assertions=subs,
                           observed={"pack_id": pack_id, "sector_playbook_disclaimers_in_pack": sector_disclaimers_present, "finding": "F16 deliverable pack ignores sector playbook liability_disclaimers (deliverable_service.py)"})

    # ------------------------------------------------------------------ S13

    async def s13_deal_documents(self) -> StageResult:
        meta = {"id": "S13", "station": "4_structure", "bfms_stage": "deal-documents v1", "deal_phase": "drafting", "pilot_stage": "none"}
        return await self._guarded(lambda: self._s13(meta), meta)

    async def _s13(self, meta: dict[str, Any]) -> StageResult:
        from uuid import UUID, uuid4

        from munipal.core.models.deal_document import DealDocumentType
        from munipal.services.deal_document_service import DealDocumentService

        pid = self.state["project_id"]
        type_id = str(uuid4())
        self.ctx.session.add(DealDocumentType(
            id=type_id, code=CDA_TYPE_CODE, display_name="Continuing Disclosure Agreement", category="templated",
            deal_vertical="muni", description="Synthetic lab seed: Rule 15c2-12 annual report and event notice undertaking (lab wording).",
            default_workflow="standard", retention_policy="indefinite", requires_signature=True, is_active=True, sort_order=1,
        ))
        await self.ctx.session.flush()
        content_json = {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": law.LEGEND}]}]}
        created = await self.call("POST", "/api/v1/deal-documents/", json={"project_id": pid, "document_type_id": type_id, "title": "Continuing Disclosure Agreement (synthetic lab draft)", "content_json": content_json})
        subs = [self._call_sub("http_document_create", created, 201)]
        doc_id = created.json().get("id") if self._ok(created, 201) else None
        cda_fired = any(r["event"] == "cda_executed" and r["status"] == "fired" and r["date"] for r in self.event_rows)
        final_status = "draft"
        transitions: list[str] = []
        if doc_id and cda_fired:
            svc = DealDocumentService(self.ctx.session)
            for st in ("under_review", "approved", "execution", "signed"):
                try:
                    out = await svc.transition_status(UUID(doc_id), new_status=st, user_id=self.ctx.reviewer_id, comment="lab replay (service-direct; route defect F11)")
                    final_status = str(getattr(out.status, "value", out.status))
                    transitions.append(f"{st}:{final_status}")
                except ValueError as exc:
                    transitions.append(f"{st}:ValueError {str(exc)[:80]}")
                    break
            subs.append(self._sub("reaches_signed", final_status == "signed", observed=final_status, expected="signed", reason="; ".join(transitions)[:300]))
        elif doc_id:
            subs.append(self._unknown("reaches_signed", "cda_executed not fired in the event log; document left in draft"))
        else:
            subs.append(self._sub("reaches_signed", False, reason="no document created"))
        if doc_id:
            versions = await self.call("GET", f"/api/v1/deal-documents/{doc_id}/versions")
            n_versions = len(versions.json()) if self._ok(versions) else 0
            subs.append(self._sub("version_snapshot_recorded", n_versions >= 1, observed=n_versions, expected=">= 1") if cda_fired else self._unknown("version_snapshot_recorded", "no transition attempted"))
            checklist = await self.call("GET", f"/api/v1/deal-documents/checklist/{pid}")
            rows = checklist.json() if self._ok(checklist) else []
            row = next((r for r in rows if r.get("document_type_code") == CDA_TYPE_CODE), None)
            subs.append(self._sub("closing_checklist_row_present", row is not None and row.get("document_id") == doc_id, observed=row))
        # derived from the event log: `filed` is reached iff a CDA filing event fired
        filing_fired = sorted(r["event"] for r in self.event_rows if r["event"] in CDA_FILING_EVENTS and r["status"] == "fired" and r["date"])
        subs.append(self._sub("filed_never_applied", (final_status == "filed") == bool(filing_fired), observed={"final_status": final_status, "cda_filing_events_fired": filing_fired}, expected="filed iff a CDA filing event fired in the log", reason="document status disagrees with the event log on filing"))
        self.state["cda_signed"] = final_status == "signed"
        self.findings.update({"F11", "F14"})
        return self._stage(**meta, assertion="type seeded with lab wording; document created; service-direct lifecycle to signed; checklist row", sub_assertions=subs,
                           observed={"document_id": doc_id, "final_status_literal": final_status, "transitions": transitions, "route_defect": "POST /api/v1/deal-documents/{id}/status raises (F11); never called"})

    # ------------------------------------------------------------------ S14

    async def s14_replay(self) -> StageResult:
        meta = {"id": "S14", "station": "1_facility", "bfms_stage": "deal_workflow mirror", "deal_phase": "engagement", "pilot_stage": "none"}
        return await self._guarded(lambda: self._s14(meta), meta)

    async def _s14(self, meta: dict[str, Any]) -> StageResult:
        workflow = self.state.get("deal_workflow")
        if workflow is None:
            return self._stage(**meta, assertion="event log replay", sub_assertions=[self._unknown("workflow_available", "S03 built no deal workflow; replay skipped")])
        evidence = replay.Evidence(
            project_created=bool(self.state.get("project_id")),
            uploads_done=bool(self.state.get("uploads_done")),
            approved_paths=frozenset(self.state.get("approved_paths", frozenset())),
            pack_files=self.pack_files,
            cda_signed_in_bfms=bool(self.state.get("cda_signed")),
            closing_literal=self.sc.closing,
            deal_status=self.sc.deal_status,
        )
        result = replay.apply(self.event_rows, workflow, evidence)
        self.conformance_rows = result.rows
        self.mirror = result.mirror()
        failed = [r.event for r in result.rows if r.status == "fail"]
        subs = [
            self._sub("one_row_per_event", len(result.rows) == len(self.event_rows), observed=len(result.rows), expected=len(self.event_rows)),
            self._sub("validation_after_every_event", not any("validation failed" in r.reason for r in result.rows), observed=[r.event for r in result.rows if "validation failed" in r.reason]),
            self._sub("applied_mappings_match", not failed, observed=failed, reason=f"rows where the mapping applied but the state differs: {failed}"),
        ]
        return self._stage(**meta, assertion="one conformance row per log row; states advance only on fired, dated, evidenced events", sub_assertions=subs,
                           observed={"counts": result.counts, "phase": self.mirror.get("deal_phase"), "closing_date": self.mirror.get("closing_date")})

    # ------------------------------------------------------------------ S15

    async def s15_register(self) -> StageResult:
        meta = {"id": "S15", "station": "6_borrower_prep", "bfms_stage": "post-close Obligation Register", "deal_phase": "post-closing", "pilot_stage": "none"}
        return await self._guarded(lambda: self._s15(meta), meta)

    async def _s15(self, meta: dict[str, Any]) -> StageResult:
        sc = self.sc
        closing_fired = any(r["event"] == "closing" and r["status"] == "fired" and r["date"] for r in self.event_rows)
        gate_status, gate_reason = post_close.gate(sc.deal_status, closing_fired)
        pin_subs = self._pin_subs()
        if gate_status == "not_applicable":
            self.register_summary["base_equivalence"] = "not_applicable"
            self.tree_after = post_close.fulfillment_tree_sha256()
            return self._stage(**meta, assertion="Obligation Register over the pack", sub_assertions=[self._na("register_gate", gate_reason), *pin_subs], reason=gate_reason)
        run = post_close.run_register(self.pack_root, self.run_dir, sc.asof, self.envelope)
        self.tree_after = post_close.fulfillment_tree_sha256()
        subs = [
            self._sub("four_statuses_only", not run.fifth_status, observed=run.fifth_status, reason=f"fifth status {run.fifth_status}"),
            self._sub("fulfillment_tree_unchanged", self.tree_before == self.tree_after, observed=self.tree_after[:16], expected=self.tree_before[:16], reason="fulfillment/ tree changed during the run"),
            *pin_subs,
            self._sub("register_outputs_written", len(run.written) >= 9, observed=run.written),
        ]
        demo = post_close.demo_build(sc.asof)
        diffs = post_close.compare(run.result, demo)
        late_afs = bool((sc.lab.get("knobs") or {}).get("late_afs"))
        if late_afs:
            lab_by_id = {r["obligation_id"]: r["status"] for r in run.result["register"]}
            demo_by_id = {r["obligation_id"]: r["status"] for r in demo["register"]}
            flipped = sorted(k for k in lab_by_id if lab_by_id[k] != demo_by_id.get(k))
            expected_flipped = ["OB-01", "OB-09", "OB-10"]
            ok = flipped == expected_flipped and all(lab_by_id[k] == "evidence missing" for k in flipped) and len(run.result["gaps"]) == len(demo["gaps"]) + 3 and len(run.result["vault_index"]) == len(demo["vault_index"]) - 3
            subs.append(self._sub("late_afs_delta", ok, observed={"flipped": flipped, "gaps": len(run.result["gaps"]), "vault_files": len(run.result["vault_index"])}, expected={"flipped": expected_flipped, "gaps": len(demo["gaps"]) + 3, "vault_files": len(demo["vault_index"]) - 3}, reason="late_afs delta differs from the expected OB-01/09/10 flip"))
            subs.append(self._na("base_equivalence", "late_afs knob: register differs from the demo by construction"))
            self.register_summary["base_equivalence"] = "not_applicable"
        else:
            subs.append(self._sub("base_equivalence", not diffs, observed=diffs[:6], expected=[], reason="; ".join(diffs)[:300]))
            self.register_summary["base_equivalence"] = "pass" if not diffs else "fail"
        self.register_summary.update({
            "status_counts": dict(run.status_counts),
            "obligations": len(run.result["register"]),
            "gaps": len(run.result["gaps"]),
            "open_items": len(run.result["open_items"]),
            "unbound_vault_files": run.summary["unbound_vault_files"],
            "vault_files": len(run.result["vault_index"]),
            "candidates": len(run.result["candidates"]),
            "asof": run.result["asof"],
            "result_sha256": post_close.result_sha256(run.result),
        })
        return self._stage(**meta, assertion="four statuses; base-equivalent to the demo (or the declared late_afs delta); tree and pin unchanged", sub_assertions=subs,
                           observed={"status_counts": run.status_counts, "written": run.written, "demo_diff_count": len(diffs)}, evidence_refs=["post-close/approved-inputs.csv", "post-close/vault/"])

    def _live_pins(self) -> dict[str, str]:
        """Pins computed from the files themselves at run time (never copied from _pins.json)."""
        fmt = scenario_mod.BONDI_FORMAT_PATH
        return {
            "run_py_sha256": post_close.run_py_sha256(),
            "build_fixtures_sha256": sha256_file(post_close.DEMO_DIR / "build_fixtures.py"),
            "pack_manifest_sha256": sha256_file(self.pack_root / law.PACK_MANIFEST_NAME),
            "bondi_format_json_sha256": sha256_file(fmt) if fmt.is_file() else "absent",
        }

    def _pin_subs(self) -> list[SubAssertion]:
        """Every live pin compared to `packs/_pins.json` in-run; a mismatch is a fail row."""
        pins_doc = json.loads((law.LAB_ROOT / "packs" / "_pins.json").read_text(encoding="utf-8"))
        live = self._live_pins()
        subs: list[SubAssertion] = []
        for key, sub_key in (("run_py_sha256", "run_py_pin_matches"), ("build_fixtures_sha256", "build_fixtures_pin_matches"), ("bondi_format_json_sha256", "bondi_format_pin_matches")):
            pinned = str(pins_doc.get(key, "absent"))
            subs.append(self._sub(sub_key, live[key] == pinned, observed=live[key][:16], expected=pinned[:16], reason=PIN_DRIFT_REASON))
        pinned_manifest = (pins_doc.get("pack_manifest_sha256") or {}).get(self.sc.deal_id) if isinstance(pins_doc.get("pack_manifest_sha256"), dict) else None
        subs.append(self._sub("pack_manifest_pin_matches", live["pack_manifest_sha256"] == pinned_manifest, observed=live["pack_manifest_sha256"][:16], expected=str(pinned_manifest)[:16], reason=PIN_DRIFT_REASON))
        return subs

    # ------------------------------------------------------------------ S16

    async def s16_gates(self) -> StageResult:
        meta = {"id": "S16", "station": "5_buyers", "bfms_stage": "pilot_onboarding pre-pilot gates", "deal_phase": "engagement", "pilot_stage": "none"}
        return await self._guarded(lambda: self._s16(meta), meta)

    async def _s16(self, meta: dict[str, Any]) -> StageResult:
        from munipal.services.pilot_onboarding import _PRE_PILOT_GATES

        ids = sorted(g.gate_id for g in _PRE_PILOT_GATES if g.required)
        display = {g.gate_id: g.display_name for g in _PRE_PILOT_GATES}
        f7 = [gid for gid, name in display.items() if law.FORBIDDEN_SOURCES_RE.search(name)]
        subs = [
            self._sub("three_required_gate_ids", ids == ["engagement_scope_signed", "pilot_smoke_test_green", "registered_ma_confirmed"], observed=ids),
            self._na("registered_ma_confirmed", law.CLIENT_GATE_REASON),
            self._na("engagement_scope_signed", law.CLIENT_GATE_REASON),
        ]
        if f7:
            self.findings.add("F7")
        self.statements.append("registered_ma_confirmed and engagement_scope_signed are reported not_applicable (internal lab; no client) and are never written to any pilot record")
        self.statements.append(law.SMOKE_GATE_MEANING)
        return self._stage(**meta, assertion="gate definitions read; client gates not_applicable by type; smoke gate computed at seal", sub_assertions=subs,
                           observed={"gate_ids": ids, "display_name_finding": "F7" if f7 else None, "gates_with_old_pack_name": f7})

    # ------------------------------------------------------------------ S17

    async def s17_sensing(self) -> StageResult:
        meta = {"id": "S17", "station": "6_borrower_prep", "bfms_stage": "pilot-nav 5.4 sensing / 5.5 cross-platform", "deal_phase": "closed", "pilot_stage": "none"}
        subs = [self._na(f"row_{i}", f"{row}: not_applicable (Class D corpus per QUARANTINE.md; sensing is the public surface, rule 3)") for i, row in enumerate(PILOT_NAV_54_ROWS, start=1)]
        subs += [self._na(f"row_{i}", f"{row}: not_applicable (public site and API are Stephen's hands, F1)") for i, row in enumerate(PILOT_NAV_55_ROWS, start=len(PILOT_NAV_54_ROWS) + 1)]
        self.findings.add("F1")
        self.statements.append("S17 rows are not_applicable by rule (Class D corpus fence; production surfaces out of the lab's hands); no measurement was attempted")
        return self._stage(**meta, assertion="no call; rows listed from pilot-navigation-system.md 5.4/5.5, paraphrased", sub_assertions=subs, reason="not_applicable by rule")

    # ------------------------------------------------------------------ S18 (seal callback + scan)

    def forbidden_scan(self) -> dict[str, int]:
        """Scan runs/<run_id>/** (before the report is written)."""
        cda_rel = "closing-documents/03-continuing-disclosure-agreement.md"
        cda_sha = sha256_file(self.pack_root / cda_rel) if (self.pack_root / cda_rel).is_file() else None
        provenance_tokens = 0
        token_outside = 0
        cusip = 0
        for path in sorted(p for p in self.run_dir.rglob("*") if p.is_file()):
            if path.suffix.lower() in (".db", ".sqlite"):
                continue
            data = path.read_bytes()
            text = data.decode("utf-8", errors="replace")
            provenance_tokens += len(law.forbidden_token_hits(text))
            n = len(law.EMMA_WORD.findall(text))
            allowed = 1 if cda_sha is not None and hashlib.sha256(data).hexdigest() == cda_sha else 0
            token_outside += max(0, n - allowed)
            cusip += len(cusip_like_tokens(text))
        return {"provenance_tokens": provenance_tokens, "emma_outside_allowlist": token_outside, "forbidden_words_in_lab_statements": sum(len(law.forbidden_lab_word_hits(s)) for s in self.statements), "cusip_like": cusip}

    def seal_stage(self, scan: dict[str, int]) -> Any:
        engines_now = engines_modules_loaded()
        engines_unchanged = engines_now == self.state.get("engines_at_s00", [])

        def _make(status: str, reason: str, diff: list[Any]) -> StageResult:
            subs = [
                self._sub("forbidden_scan_clean", sum(scan.values()) == 0, observed=scan, reason=f"forbidden scan hits {scan}"),
                self._sub("engines_modules_unchanged", engines_unchanged, observed=engines_now, expected=self.state.get("engines_at_s00", [])),
                SubAssertion(key="golden", status=status, reason=reason if status != "pass" else "", observed={"deltas": len(diff)}),
            ]
            self.calls = []
            return StageResult.from_sub_assertions(id="S18", station="all", bfms_stage="report", deal_phase="closed", pilot_stage="none",
                                                   assertion="report verifies; golden diff empty; zero forbidden tokens", sub_assertions=subs)

        return _make

    # ------------------------------------------------------------------ orchestration

    async def run_all(self) -> DriverOutput:
        for fn in (self.s00_harness, self.s01_scenario, self.s02_pack, self.s03_project, self.s04_request, self.s05_vault,
                   self.s06_extraction, self.s07_review, self.s08_checklist, self.s09_readiness, self.s10_requests_disclosure,
                   self.s11_models, self.s12_handoff, self.s13_deal_documents, self.s14_replay, self.s15_register,
                   self.s16_gates, self.s17_sensing):
            await fn()
        if not self.tree_after:
            self.tree_after = post_close.fulfillment_tree_sha256()
        pins = self._live_pins()
        corpus = self.ctx.corpus_available()
        environment = {
            "db": "sqlite+aiosqlite:///:memory:",
            "app": "munipal.main:app",
            "auth_mode": "AUTH_ENFORCEMENT_V2=true",
            "extraction_mode": self.state.get("extraction_mode", "unknown"),
            "anthropic_key_present": self.ctx.anthropic_key_present(),
            "celery_dispatch": self.ctx.celery_dispatch,
            # "env": MUNIPAL_ROOT was in the environment before munipal was first imported
            # (standalone); "attr-patched": only the sensing attribute patch is effective
            "munipal_root_pinned": self.ctx.munipal_root_pin,
            "sensing_corpus_available": corpus,
            "harness_mode": self.ctx.mode,
            "deal_v0_schema": self.sc.deal_v0_schema_note,
        }
        self.vocab.setdefault("checklist_only", [])
        self.vocab.setdefault("readiness_profile_only", [])
        self.vocab.setdefault("archetype_only", self._archetype_only())
        self.vocab.setdefault("finding", "F5")
        scan = self.forbidden_scan()
        return DriverOutput(
            stages=list(self.stages), conformance_rows=list(self.conformance_rows), deal_workflow_mirror=dict(self.mirror),
            register_summary=dict(self.register_summary), review=dict(self.review), vocabulary_divergence=dict(self.vocab),
            bfms_emitted_language=list(self.emitted), findings_touched=sorted(self.findings), lab_statements=list(self.statements),
            environment=environment, pins=pins, fulfillment_tree_before=self.tree_before, fulfillment_tree_after=self.tree_after,
            fence_class_violation=self.fence_class_violation, repo_commit=self.commit, repo_dirty=self.dirty,
            python=platform.python_version(), forbidden_scan=scan,
        )

    def _archetype_only(self) -> list[str]:
        try:
            from munipal.services.sector_archetypes import resolve_archetype

            archetype = resolve_archetype(self.sc.lab["sector"], self.sc.lab["subsector"])
            paths = set(getattr(archetype, "required_evidence_paths", ()) or ())
            return sorted(paths - set(self.sc.intake_facts))
        except Exception:  # noqa: BLE001 - observational only
            return []


def run_id_for(sc: scenario_mod.Scenario, commit: str) -> str:
    """Run id over the scenario file bytes, the base file bytes (variants) and the commit."""
    return f"{sc.deal_id}__{sc.asof}__{sha256_bytes(sc.raw_bytes + b'||' + sc.base_raw_bytes + b'||' + commit.encode('ascii'))[:8]}"


def scan_pack_tree(root: Path) -> str:
    return tree_sha256(root)


__all__ = [
    "CLOSING_UPLOAD_FOLDER",
    "PILOT_NAV_54_ROWS",
    "PILOT_NAV_55_ROWS",
    "REVIEW_STATEMENT",
    "Driver",
    "DriverOutput",
    "cusip_like_tokens",
    "git_read_only",
    "repo_commit",
    "repo_dirty",
    "run_id_for",
    "scan_pack_tree",
]
