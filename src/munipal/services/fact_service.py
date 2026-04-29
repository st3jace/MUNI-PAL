"""
Fact management service.

Per spec: ExtractedFact is THE CORE PRIMITIVE.
Handles CRUD operations, review workflow, and versioning.
"""

import logging
import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from munipal.core.models.artifact import Chunk
from munipal.core.models.fact import (
    ExtractedFact,
    FactChunkAssociation,
    FactRevision,
    EvidenceLink,
)
from munipal.core.schemas.base import ReviewStatus, CriticalityTier, SourceType
from munipal.core.schemas.fact import (
    SourceReference,
    ExtractedFactCreate,
    ExtractedFactRead,
    ExtractedFactSummary,
    FactDuplicateClassification,
    FactLifecycleState,
    FactReviewRequest,
    FactRevisionRead,
    ManualFactCreate,
    MissingPathInfo,
    ChunkReference,
)
from munipal.services.audit_service import AuditService
from munipal.services.playbook_data import SCHEMA_PATHS, CHECKLIST_ITEMS, READINESS_CONFIG

logger = logging.getLogger(__name__)


class FactService:
    """
    Service for managing extracted facts.

    Handles:
    - CRUD operations for facts
    - Review workflow (approve, reject, needs_revision)
    - Revision history for audit logging
    - Evidence linking to checklist/readiness
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    # -------------------------------------------------------------------------
    # Canonicalization / Lifecycle
    # -------------------------------------------------------------------------

    @staticmethod
    def _normalize_value_for_hash(value: Any) -> str:
        """Deterministic normalization for fingerprint and semantic matching."""
        if isinstance(value, str):
            return value.strip()
        try:
            return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)
        except TypeError:
            return str(value)

    @classmethod
    def _semantic_key(cls, value: Any, unit: str | None) -> str:
        normalized = cls._normalize_value_for_hash(value).lower()
        normalized = re.sub(r"\s+", " ", normalized).strip()
        normalized = re.sub(r"[^a-z0-9.\- ]+", "", normalized)
        unit_norm = (unit or "").strip().lower()
        return f"{normalized}|{unit_norm}"

    @classmethod
    def _compute_fingerprint(
        cls,
        *,
        project_id: str,
        schema_path: str,
        value: Any,
        unit: str | None,
    ) -> str:
        raw = (
            f"{project_id}|{schema_path}|{cls._normalize_value_for_hash(value)}|"
            f"{(unit or '').strip().lower()}"
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @staticmethod
    def _source_trust_score(fact: ExtractedFact) -> float:
        source_type = (fact.source_type or "extracted").lower()
        if source_type == "manual":
            base = 0.78
        elif source_type == "extracted":
            base = 0.68
        else:
            base = 0.60

        age_days = FactService._age_days(fact.created_at)
        recency_bonus = max(0.0, 0.20 - min(age_days, 180) / 900.0)
        return round(max(0.0, min(1.0, base + recency_bonus)), 3)

    @staticmethod
    def _age_days(created_at: datetime | None) -> int:
        if not created_at:
            return 0
        normalized = created_at
        if normalized.tzinfo is None:
            normalized = normalized.replace(tzinfo=timezone.utc)
        return max(0, (datetime.now(timezone.utc) - normalized).days)

    @staticmethod
    def _created_timestamp(created_at: datetime | None) -> float:
        if not created_at:
            return 0.0
        normalized = created_at
        if normalized.tzinfo is None:
            normalized = normalized.replace(tzinfo=timezone.utc)
        return normalized.timestamp()

    @classmethod
    def _publication_priority_key(cls, fact: ExtractedFact) -> tuple[float, float, float, float, float, str]:
        """
        Priority key for deterministic per-path fact selection.

        Canonical facts win first, then review/canonical/confidence ordering, then recency/id.
        """
        return (
            1.0 if fact.is_canonical else 0.0,
            cls._review_status_weight(fact.review_status),
            float(fact.canonical_score or 0.0),
            float(fact.confidence_score or 0.0),
            cls._created_timestamp(fact.created_at),
            fact.id,
        )

    @classmethod
    def select_preferred_facts_by_path(
        cls,
        facts: list[ExtractedFact],
    ) -> dict[str, ExtractedFact]:
        """Select one deterministic preferred fact per schema path."""
        candidates_by_path: dict[str, list[ExtractedFact]] = defaultdict(list)
        for fact in facts:
            candidates_by_path[fact.schema_path].append(fact)

        selected: dict[str, ExtractedFact] = {}
        for schema_path, candidates in candidates_by_path.items():
            selected[schema_path] = max(candidates, key=cls._publication_priority_key)

        return {schema_path: selected[schema_path] for schema_path in sorted(selected.keys())}

    @staticmethod
    def _review_status_weight(review_status: str) -> float:
        if review_status == ReviewStatus.APPROVED.value:
            return 1.0
        if review_status == ReviewStatus.PENDING.value:
            return 0.55
        if review_status == ReviewStatus.NEEDS_REVISION.value:
            return 0.35
        return 0.10

    def _canonical_score(self, fact: ExtractedFact) -> float:
        confidence = max(0.0, min(1.0, float(fact.confidence_score or 0.0)))
        trust = self._source_trust_score(fact)
        review_weight = self._review_status_weight(fact.review_status)
        score = (confidence * 0.55) + (trust * 0.30) + (review_weight * 0.15)
        return round(max(0.0, min(1.0, score)), 3)

    async def refresh_canonicalization_for_path(
        self,
        project_id: UUID | str,
        schema_path: str,
        actor_id: UUID | str | None = None,
        reason: str | None = None,
        source_action: str | None = None,
    ) -> None:
        """Recompute dedup metadata and canonical selection for one path."""
        project_id_str = str(project_id)
        resolved_actor_id = str(actor_id) if actor_id else "system"
        resolved_reason = reason or "canonical_refresh"
        resolved_source_action = source_action or "canonical_refresh"

        result = await self.session.execute(
            select(ExtractedFact).where(
                and_(
                    ExtractedFact.project_id == project_id_str,
                    ExtractedFact.schema_path == schema_path,
                )
            )
        )
        facts = list(result.scalars().all())
        if not facts:
            return
        previous_canonical_ids = {fact.id for fact in facts if fact.is_canonical}
        facts_by_id = {fact.id: fact for fact in facts}

        active_candidates: list[ExtractedFact] = []
        fingerprint_counts: dict[str, int] = defaultdict(int)
        semantic_counts: dict[str, int] = defaultdict(int)
        semantic_key_by_fact: dict[str, str] = {}

        for fact in facts:
            fact.fingerprint = self._compute_fingerprint(
                project_id=project_id_str,
                schema_path=schema_path,
                value=fact.value,
                unit=fact.unit,
            )
            fact.source_trust_score = self._source_trust_score(fact)
            fact.canonical_score = self._canonical_score(fact)

            if fact.lifecycle_state == FactLifecycleState.ARCHIVED.value:
                fact.is_canonical = False
                fact.duplicate_classification = FactDuplicateClassification.UNIQUE.value
                continue
            if fact.review_status == ReviewStatus.REJECTED.value:
                fact.is_canonical = False
                fact.lifecycle_state = FactLifecycleState.REJECTED.value
                fact.duplicate_classification = FactDuplicateClassification.UNIQUE.value
                continue

            if fact.lifecycle_state in {
                FactLifecycleState.ACTIVE.value,
                FactLifecycleState.PENDING_REVIEW.value,
            }:
                active_candidates.append(fact)
                fingerprint_counts[fact.fingerprint] += 1
                key = self._semantic_key(fact.value, fact.unit)
                semantic_key_by_fact[fact.id] = key
                semantic_counts[key] += 1

        normalized_value_set = {
            self._semantic_key(fact.value, fact.unit) for fact in active_candidates
        }

        for fact in active_candidates:
            duplicate_classification = FactDuplicateClassification.UNIQUE.value
            if fingerprint_counts.get(fact.fingerprint, 0) > 1:
                duplicate_classification = FactDuplicateClassification.DUPLICATE_EXACT.value
            elif semantic_counts.get(semantic_key_by_fact.get(fact.id, ""), 0) > 1:
                duplicate_classification = FactDuplicateClassification.DUPLICATE_SEMANTIC.value
            elif len(normalized_value_set) > 1:
                duplicate_classification = FactDuplicateClassification.CANDIDATE_CONFLICT.value

            fact.duplicate_classification = duplicate_classification
            if fact.review_status == ReviewStatus.PENDING.value:
                fact.lifecycle_state = FactLifecycleState.PENDING_REVIEW.value
            else:
                fact.lifecycle_state = FactLifecycleState.ACTIVE.value
            fact.is_canonical = False

        if active_candidates:
            active_candidates.sort(
                key=lambda item: (
                    self._review_status_weight(item.review_status),
                    item.canonical_score,
                    item.confidence_score,
                    self._created_timestamp(item.created_at),
                    item.id,  # deterministic tie-breaker for stable canonical selection
                ),
                reverse=True,
            )
            active_candidates[0].is_canonical = True
            active_candidates[0].duplicate_classification = FactDuplicateClassification.UNIQUE.value

        current_canonical_ids = {fact.id for fact in facts if fact.is_canonical}
        promoted_ids = sorted(current_canonical_ids - previous_canonical_ids)
        demoted_ids = sorted(previous_canonical_ids - current_canonical_ids)

        if promoted_ids or demoted_ids:
            replacement_fact_id = promoted_ids[0] if promoted_ids else None

            for demoted_id in demoted_ids:
                demoted_fact = facts_by_id[demoted_id]
                AuditService.emit_event(
                    actor_id=resolved_actor_id,
                    action="demote",
                    target_type="fact",
                    target_id=demoted_fact.id,
                    project_id=project_id_str,
                    metadata={
                        "schema_path": schema_path,
                        "reason": resolved_reason,
                        "source_action": resolved_source_action,
                        "replacement_fact_id": replacement_fact_id,
                        "canonical_score": demoted_fact.canonical_score,
                        "review_status": demoted_fact.review_status,
                        "lifecycle_state": demoted_fact.lifecycle_state,
                    },
                )

            for promoted_id in promoted_ids:
                promoted_fact = facts_by_id[promoted_id]
                AuditService.emit_event(
                    actor_id=resolved_actor_id,
                    action="promote_canonical",
                    target_type="fact",
                    target_id=promoted_fact.id,
                    project_id=project_id_str,
                    metadata={
                        "schema_path": schema_path,
                        "reason": resolved_reason,
                        "source_action": resolved_source_action,
                        "replaced_fact_ids": demoted_ids,
                        "canonical_score": promoted_fact.canonical_score,
                        "review_status": promoted_fact.review_status,
                        "lifecycle_state": promoted_fact.lifecycle_state,
                    },
                )

    async def get_project_schema_paths(
        self,
        project_id: UUID | str,
        include_archived: bool = True,
    ) -> list[str]:
        """Return deterministic list of schema paths currently present for a project."""
        project_id_str = str(project_id)
        query = select(ExtractedFact.schema_path).where(
            ExtractedFact.project_id == project_id_str
        )
        if not include_archived:
            query = query.where(
                ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value
            )
        result = await self.session.execute(
            query.distinct().order_by(ExtractedFact.schema_path.asc())
        )
        return [row.schema_path for row in result]

    async def refresh_canonicalization_for_project(
        self,
        project_id: UUID | str,
        actor_id: UUID | str | None = None,
        reason: str | None = None,
        source_action: str | None = None,
    ) -> list[str]:
        """Refresh canonicalization for all schema paths in a project."""
        schema_paths = await self.get_project_schema_paths(project_id)
        for schema_path in schema_paths:
            await self.refresh_canonicalization_for_path(
                project_id=project_id,
                schema_path=schema_path,
                actor_id=actor_id,
                reason=reason,
                source_action=source_action,
            )
        return schema_paths

    async def canonical_snapshot_for_project(
        self,
        project_id: UUID | str,
        include_archived: bool = True,
    ) -> dict[str, dict[str, Any]]:
        """
        Build a deterministic snapshot of canonical/duplicate/lifecycle state per path.

        This is used for dataset replay/regression checks to ensure repeated refreshes
        yield stable outputs for the same corpus.
        """
        project_id_str = str(project_id)
        query = (
            select(ExtractedFact)
            .where(ExtractedFact.project_id == project_id_str)
            .order_by(ExtractedFact.schema_path.asc(), ExtractedFact.id.asc())
        )
        if not include_archived:
            query = query.where(
                ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value
            )

        result = await self.session.execute(query)
        facts = list(result.scalars().all())
        snapshot: dict[str, dict[str, Any]] = {}
        for fact in facts:
            normalized_value = self._normalize_value_for_hash(fact.value)
            value_hash = hashlib.sha256(normalized_value.encode("utf-8")).hexdigest()
            path_snapshot = snapshot.setdefault(
                fact.schema_path,
                {
                    "fact_count": 0,
                    "canonical_fact_ids": [],
                    "canonical_value_hashes": [],
                    "facts": [],
                },
            )
            path_snapshot["fact_count"] += 1
            path_snapshot["facts"].append(
                {
                    "fact_id": fact.id,
                    "value_hash": value_hash,
                    "review_status": fact.review_status,
                    "lifecycle_state": fact.lifecycle_state,
                    "duplicate_classification": fact.duplicate_classification,
                    "is_canonical": fact.is_canonical,
                    "canonical_score": round(float(fact.canonical_score or 0.0), 6),
                }
            )
            if fact.is_canonical:
                path_snapshot["canonical_fact_ids"].append(fact.id)
                path_snapshot["canonical_value_hashes"].append(value_hash)

        return snapshot

    async def archive_fact(
        self,
        fact_id: UUID,
        reviewer_id: UUID,
        reason_code: str,
        note: str,
    ) -> ExtractedFact:
        """Archive a superseded/redundant fact."""
        fact = await self.get_fact(fact_id)
        if not fact:
            raise ValueError(f"Fact {fact_id} not found")
        if fact.lifecycle_state == FactLifecycleState.ARCHIVED.value:
            return fact

        previous_value = fact.value
        previous_status = fact.review_status

        fact.lifecycle_state = FactLifecycleState.ARCHIVED.value
        fact.archive_reason_code = reason_code
        fact.archive_note = note
        fact.archived_by = str(reviewer_id)
        fact.archived_at = datetime.now(timezone.utc)
        if fact.review_status == ReviewStatus.PENDING.value:
            fact.review_status = ReviewStatus.NEEDS_REVISION.value

        await self._create_revision(
            fact=fact,
            previous_value=previous_value,
            previous_status=previous_status,
            changed_by_id=reviewer_id,
            change_reason=f"Archived: {reason_code}. {note}",
        )

        await self.refresh_canonicalization_for_path(
            fact.project_id,
            fact.schema_path,
            actor_id=reviewer_id,
            reason=f"archive:{reason_code}",
            source_action="archive_fact",
        )
        await self.session.commit()
        await self.session.refresh(fact)
        return fact

    async def unarchive_fact(
        self,
        fact_id: UUID,
        reviewer_id: UUID,
        note: str | None = None,
    ) -> ExtractedFact:
        """Restore an archived fact to active lifecycle state."""
        fact = await self.get_fact(fact_id)
        if not fact:
            raise ValueError(f"Fact {fact_id} not found")

        previous_value = fact.value
        previous_status = fact.review_status

        fact.lifecycle_state = FactLifecycleState.ACTIVE.value
        fact.archive_reason_code = None
        fact.archive_note = note
        fact.archived_by = None
        fact.archived_at = None

        await self._create_revision(
            fact=fact,
            previous_value=previous_value,
            previous_status=previous_status,
            changed_by_id=reviewer_id,
            change_reason=f"Unarchived: {note or 'restored to active'}",
        )

        await self.refresh_canonicalization_for_path(
            fact.project_id,
            fact.schema_path,
            actor_id=reviewer_id,
            reason="unarchive",
            source_action="unarchive_fact",
        )
        await self.session.commit()
        await self.session.refresh(fact)
        return fact

    async def get_conflict_queue(
        self,
        project_id: UUID,
        criticality: str | None = None,
        phase: str | None = None,
        max_age_days: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return unresolved conflict/stale pending queue for reviewers."""
        conflict_detector = FactConflictDetector(self.session)
        conflicts = await conflict_detector.find_conflicts(project_id)

        queue_items: list[dict[str, Any]] = []
        for conflict in conflicts:
            queue_item = {
                "queue_type": "conflict",
                "schema_path": conflict["schema_path"],
                "criticality": conflict.get("criticality"),
                "phase": conflict.get("phase"),
                "fact_count": conflict["fact_count"],
                "oldest_pending_days": conflict.get("oldest_pending_days", 0),
                "facts": conflict["facts"],
            }
            queue_items.append(queue_item)

        stale_query = select(ExtractedFact).where(
            and_(
                ExtractedFact.project_id == str(project_id),
                ExtractedFact.review_status == ReviewStatus.PENDING.value,
                ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value,
            )
        )
        stale_result = await self.session.execute(stale_query)
        for fact in stale_result.scalars().all():
            if max_age_days is not None and fact.created_at:
                age_days = self._age_days(fact.created_at)
                if age_days <= max_age_days:
                    continue
            queue_items.append(
                {
                    "queue_type": "stale_pending",
                    "schema_path": fact.schema_path,
                    "criticality": fact.criticality,
                    "phase": self._phase_for_schema_path(fact.schema_path),
                    "fact_id": fact.id,
                    "oldest_pending_days": (
                        self._age_days(fact.created_at)
                    ),
                }
            )

        if criticality:
            queue_items = [item for item in queue_items if item.get("criticality") == criticality]
        if phase:
            queue_items = [item for item in queue_items if item.get("phase") == phase]

        queue_items.sort(
            key=lambda item: (
                0 if item.get("criticality") == "critical" else 1,
                -(item.get("oldest_pending_days") or 0),
            )
        )
        return queue_items

    @staticmethod
    def _phase_for_schema_path(schema_path: str) -> str | None:
        for item in CHECKLIST_ITEMS:
            all_paths = item.get("required_schema_paths", []) + item.get("optional_schema_paths", [])
            if schema_path in all_paths:
                return item.get("phase")
        return None

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    async def get_active_approved_facts(
        self,
        project_id: UUID | str,
        schema_paths: list[str] | None = None,
    ) -> list[ExtractedFact]:
        """Return active approved facts for a project, optionally filtered by path."""
        project_id_str = str(project_id)
        query = (
            select(ExtractedFact)
            .options(
                selectinload(ExtractedFact.source_chunks)
                .selectinload(FactChunkAssociation.chunk)
                .selectinload(Chunk.artifact),
            )
            .where(
                and_(
                    ExtractedFact.project_id == project_id_str,
                    ExtractedFact.review_status == ReviewStatus.APPROVED.value,
                    ExtractedFact.lifecycle_state == FactLifecycleState.ACTIVE.value,
                )
            )
        )
        if schema_paths is not None:
            if not schema_paths:
                return []
            query = query.where(ExtractedFact.schema_path.in_(schema_paths))

        query = query.order_by(
            ExtractedFact.schema_path.asc(),
            ExtractedFact.is_canonical.desc(),
            ExtractedFact.canonical_score.desc(),
            ExtractedFact.confidence_score.desc(),
            ExtractedFact.created_at.desc(),
            ExtractedFact.id.desc(),
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_active_approved_facts_by_path(
        self,
        project_id: UUID | str,
        schema_paths: list[str] | None = None,
    ) -> dict[str, ExtractedFact]:
        """Return preferred active approved fact per schema path."""
        facts = await self.get_active_approved_facts(
            project_id=project_id,
            schema_paths=schema_paths,
        )
        return self.select_preferred_facts_by_path(facts)

    async def get_fact(self, fact_id: UUID) -> ExtractedFact | None:
        """
        Get a fact by ID with all relationships loaded.

        Args:
            fact_id: The fact UUID

        Returns:
            ExtractedFact with relationships or None
        """
        result = await self.session.execute(
            select(ExtractedFact)
            .options(
                selectinload(ExtractedFact.source_chunks)
                .selectinload(FactChunkAssociation.chunk)
                .selectinload(Chunk.artifact),
                selectinload(ExtractedFact.revisions),
                selectinload(ExtractedFact.evidence_links),
            )
            .where(ExtractedFact.id == str(fact_id))
        )
        return result.scalar_one_or_none()

    async def list_facts(
        self,
        project_id: UUID,
        status_filter: ReviewStatus | None = None,
        schema_path_prefix: str | None = None,
        min_confidence: float | None = None,
        criticality: CriticalityTier | None = None,
        include_archived: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ExtractedFact], int]:
        """
        List facts for a project with filters.

        Args:
            project_id: Project UUID
            status_filter: Filter by review status
            schema_path_prefix: Filter by schema path prefix
            min_confidence: Minimum confidence threshold
            criticality: Filter by criticality tier
            limit: Max results to return
            offset: Pagination offset

        Returns:
            Tuple of (facts list, total count)
        """
        # Build base query
        base_query = select(ExtractedFact).where(
            ExtractedFact.project_id == str(project_id)
        )
        if not include_archived:
            base_query = base_query.where(
                ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value
            )

        # Apply filters
        if status_filter:
            base_query = base_query.where(
                ExtractedFact.review_status == status_filter.value
            )
        if schema_path_prefix:
            base_query = base_query.where(
                ExtractedFact.schema_path.startswith(schema_path_prefix)
            )
        if min_confidence is not None:
            base_query = base_query.where(
                ExtractedFact.confidence_score >= min_confidence
            )
        if criticality:
            base_query = base_query.where(
                ExtractedFact.criticality == criticality.value
            )

        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0

        # Get paginated results with relationships
        query = (
            base_query.options(
                selectinload(ExtractedFact.source_chunks).selectinload(
                    FactChunkAssociation.chunk
                )
            )
            .order_by(ExtractedFact.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        facts = list(result.scalars().all())

        return facts, total

    async def get_facts_by_schema_path(
        self,
        project_id: UUID,
        schema_path: str,
        approved_only: bool = False,
        include_archived: bool = False,
    ) -> list[ExtractedFact]:
        """
        Get all facts for a specific schema path.

        Args:
            project_id: Project UUID
            schema_path: Exact schema path to match
            approved_only: Only return approved facts

        Returns:
            List of matching facts
        """
        query = select(ExtractedFact).where(
            and_(
                ExtractedFact.project_id == str(project_id),
                ExtractedFact.schema_path == schema_path,
            )
        )
        if not include_archived:
            query = query.where(
                ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value
            )

        if approved_only:
            query = query.where(
                and_(
                    ExtractedFact.review_status == ReviewStatus.APPROVED.value,
                    ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value,
                )
            )

        result = await self.session.execute(
            query.order_by(ExtractedFact.confidence_score.desc())
        )
        return list(result.scalars().all())

    async def get_pending_review_count(self, project_id: UUID) -> dict[str, int]:
        """
        Get count of facts by review status.

        Args:
            project_id: Project UUID

        Returns:
            Dict with counts by status
        """
        result = await self.session.execute(
            select(
                ExtractedFact.review_status,
                func.count(ExtractedFact.id).label("count"),
            )
            .where(ExtractedFact.project_id == str(project_id))
            .where(ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value)
            .group_by(ExtractedFact.review_status)
        )

        counts = {status.value: 0 for status in ReviewStatus}
        for row in result:
            counts[row.review_status] = row.count

        return counts

    # -------------------------------------------------------------------------
    # Manual Fact Creation
    # -------------------------------------------------------------------------

    async def create_manual_fact(
        self,
        request: ManualFactCreate,
        created_by: UUID,
        auto_approve: bool = False,
    ) -> ExtractedFact:
        """
        Create a manually-entered fact.

        Manual facts have source_type='manual', confidence_score=1.0,
        and no extraction job or source chunks.

        Args:
            request: ManualFactCreate with project_id, schema_path, value, etc.
            created_by: User creating the fact
            auto_approve: If True, fact is immediately approved

        Returns:
            Created ExtractedFact
        """
        # Look up criticality from schema path config
        schema_config = self._get_schema_path_config(request.schema_path)
        criticality = schema_config.get("criticality", "secondary")

        # Create the fact
        now = datetime.now(timezone.utc)
        review_status = ReviewStatus.APPROVED.value if auto_approve else ReviewStatus.PENDING.value

        fact = ExtractedFact(
            project_id=str(request.project_id),
            schema_path=request.schema_path,
            criticality=criticality,
            source_type=SourceType.MANUAL.value,
            value=request.value,
            value_type=request.value_type,
            unit=request.unit,
            confidence_score=1.0,  # User is authoritative source
            confidence_rationale=request.note or "Manually entered by user",
            review_status=review_status,
            lifecycle_state=(
                FactLifecycleState.ACTIVE.value
                if auto_approve
                else FactLifecycleState.PENDING_REVIEW.value
            ),
            extraction_job_id=None,  # Manual facts don't have extraction jobs
        )

        if auto_approve:
            fact.reviewed_by = str(created_by)
            fact.reviewed_at = now
            fact.review_note = "Auto-approved on creation"

        self.session.add(fact)
        await self.session.flush()  # Get the ID

        # Create initial revision for audit trail
        revision = FactRevision(
            fact_id=fact.id,
            revision_number=1,
            previous_value=None,
            new_value=request.value,
            previous_status=None,
            new_status=review_status,
            changed_by_id=str(created_by),
            change_reason="Manual fact created" + (" (auto-approved)" if auto_approve else ""),
        )
        self.session.add(revision)

        await self.refresh_canonicalization_for_path(
            project_id=request.project_id,
            schema_path=request.schema_path,
            actor_id=created_by,
            reason="manual_fact_created",
            source_action="create_manual_fact",
        )

        await self.session.commit()
        await self.session.refresh(fact)

        logger.info(
            f"Created manual fact {fact.id} for path {request.schema_path} "
            f"by user {created_by} (auto_approve={auto_approve})"
        )

        return fact

    def _get_schema_path_config(self, schema_path: str) -> dict:
        """Get configuration for a schema path from playbook data."""
        for path_config in SCHEMA_PATHS:
            if path_config["path"] == schema_path:
                return path_config
        return {}

    async def get_missing_paths(
        self,
        project_id: UUID,
        phase: str | None = None,
        criticality: str | None = None,
    ) -> list[MissingPathInfo]:
        """
        Get schema paths that don't have approved facts yet.

        Includes paths from:
        1. Checklist items (required and optional paths)
        2. Readiness config contributing_paths

        This ensures Readiness gaps align with Checklist outstanding items.

        Args:
            project_id: Project UUID
            phase: Optional phase filter (P1, P2, etc.)
            criticality: Optional criticality filter

        Returns:
            List of MissingPathInfo for paths needing facts
        """
        # Get all approved facts for the project
        result = await self.session.execute(
            select(ExtractedFact.schema_path)
            .where(
                and_(
                    ExtractedFact.project_id == str(project_id),
                    ExtractedFact.review_status == ReviewStatus.APPROVED.value,
                    ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value,
                )
            )
            .distinct()
        )
        approved_paths = {row[0] for row in result}

        # Build lookup of schema path configs
        path_configs = {p["path"]: p for p in SCHEMA_PATHS}

        # Build lookup: path -> (phase, item_code, item_title) from checklist items
        # Include both required and optional paths
        path_to_item: dict[str, tuple[str, str, str]] = {}
        for item in CHECKLIST_ITEMS:
            all_paths = item.get("required_schema_paths", []) + item.get("optional_schema_paths", [])
            for path in all_paths:
                if path not in path_to_item:
                    path_to_item[path] = (item["phase"], item["item_code"], item["title"])

        # Collect all paths that contribute to readiness from READINESS_CONFIG
        readiness_paths: set[str] = set()
        dimension_for_path: dict[str, str] = {}
        for dim_key, dim_config in READINESS_CONFIG.get("dimensions", {}).items():
            for path in dim_config.get("contributing_paths", []):
                readiness_paths.add(path)
                if path not in dimension_for_path:
                    dimension_for_path[path] = dim_config.get("name", dim_key)

        # Combine all paths: from checklist items + readiness contributing paths
        all_relevant_paths = set(path_to_item.keys()) | readiness_paths

        # Collect missing paths
        missing = []
        for path in all_relevant_paths:
            if path in approved_paths:
                continue

            config = path_configs.get(path, {})
            path_criticality = config.get("criticality", "secondary")

            if criticality and path_criticality != criticality:
                continue

            # Get checklist item info if available
            if path in path_to_item:
                item_phase, item_code, item_title = path_to_item[path]
            else:
                # Path is only in READINESS_CONFIG, not in any checklist item
                # Use the dimension name as context
                dim_name = dimension_for_path.get(path, "Readiness")
                item_phase = "N/A"
                item_code = "READINESS"
                item_title = f"{dim_name} Dimension"

            if phase and item_phase != phase and item_phase != "N/A":
                continue

            missing.append(
                MissingPathInfo(
                    schema_path=path,
                    display_name=config.get("display_name", path),
                    criticality=CriticalityTier(path_criticality),
                    value_type=config.get("value_type", "string"),
                    phase=item_phase,
                    item_code=item_code,
                    item_title=item_title,
                )
            )

        # Sort by criticality (critical first) then by phase
        criticality_order = {"critical": 0, "material": 1, "secondary": 2}
        phase_order = {"P1": 0, "P2": 1, "P3": 2, "P4": 3, "P5": 4, "P6": 5, "N/A": 6}

        def get_crit_str(c):
            return c.value if hasattr(c, 'value') else str(c)

        missing.sort(key=lambda m: (
            criticality_order.get(get_crit_str(m.criticality), 3),
            phase_order.get(m.phase, 7),
        ))

        return missing

    # -------------------------------------------------------------------------
    # Review Workflow
    # -------------------------------------------------------------------------

    async def review_fact(
        self,
        fact_id: UUID,
        reviewer_id: UUID,
        review: FactReviewRequest,
    ) -> ExtractedFact:
        """
        Submit a review for a fact.

        Per spec: "AI proposes; humans approve."

        Args:
            fact_id: Fact to review
            reviewer_id: User submitting review
            review: Review action and details

        Returns:
            Updated fact

        Raises:
            ValueError: If fact not found or invalid transition
        """
        fact = await self.get_fact(fact_id)
        if not fact:
            raise ValueError(f"Fact {fact_id} not found")

        self._require_approvable_provenance(fact, review)

        # Capture previous state for revision
        previous_value = fact.value
        previous_status = fact.review_status

        # Update based on action
        now = datetime.now(timezone.utc)

        if review.action == ReviewStatus.APPROVED:
            fact.review_status = ReviewStatus.APPROVED.value
            fact.lifecycle_state = FactLifecycleState.ACTIVE.value

            # Handle corrections
            if review.corrected_value is not None:
                fact.original_value = previous_value
                fact.value = review.corrected_value
                logger.info(
                    f"Fact {fact_id} approved with correction by {reviewer_id}"
                )
            else:
                logger.info(f"Fact {fact_id} approved by {reviewer_id}")

        elif review.action == ReviewStatus.REJECTED:
            fact.review_status = ReviewStatus.REJECTED.value
            fact.lifecycle_state = FactLifecycleState.REJECTED.value
            logger.info(f"Fact {fact_id} rejected by {reviewer_id}")

        elif review.action == ReviewStatus.NEEDS_REVISION:
            fact.review_status = ReviewStatus.NEEDS_REVISION.value
            fact.lifecycle_state = FactLifecycleState.PENDING_REVIEW.value
            logger.info(f"Fact {fact_id} flagged for revision by {reviewer_id}")

        else:
            raise ValueError(f"Invalid review action: {review.action}")

        fact.reviewed_by = str(reviewer_id)
        fact.reviewed_at = now
        fact.review_note = review.note

        # Create revision record
        await self._create_revision(
            fact=fact,
            previous_value=previous_value,
            previous_status=previous_status,
            changed_by_id=reviewer_id,
            change_reason=review.note,
        )

        await self.refresh_canonicalization_for_path(
            project_id=fact.project_id,
            schema_path=fact.schema_path,
            actor_id=reviewer_id,
            reason=f"review:{review.action if isinstance(review.action, str) else review.action.value}",
            source_action="review_fact",
        )

        await self.session.commit()
        await self.session.refresh(fact)

        return fact

    async def approve_fact(
        self,
        fact_id: UUID,
        reviewer_id: UUID,
        corrected_value: Any | None = None,
        note: str | None = None,
    ) -> ExtractedFact:
        """
        Convenience method to approve a fact.

        Args:
            fact_id: Fact to approve
            reviewer_id: User approving
            corrected_value: Optional corrected value
            note: Optional review note

        Returns:
            Approved fact
        """
        review = FactReviewRequest(
            action=ReviewStatus.APPROVED,
            corrected_value=corrected_value,
            note=note,
        )
        return await self.review_fact(fact_id, reviewer_id, review)

    async def reject_fact(
        self,
        fact_id: UUID,
        reviewer_id: UUID,
        reason: str | None = None,
    ) -> ExtractedFact:
        """
        Convenience method to reject a fact.

        Args:
            fact_id: Fact to reject
            reviewer_id: User rejecting
            reason: Rejection reason

        Returns:
            Rejected fact
        """
        review = FactReviewRequest(
            action=ReviewStatus.REJECTED,
            note=reason,
        )
        return await self.review_fact(fact_id, reviewer_id, review)

    async def request_revision(
        self,
        fact_id: UUID,
        reviewer_id: UUID,
        revision_note: str,
    ) -> ExtractedFact:
        """
        Flag a fact as needing revision.

        Args:
            fact_id: Fact to flag
            reviewer_id: User requesting revision
            revision_note: What needs to be fixed

        Returns:
            Updated fact
        """
        review = FactReviewRequest(
            action=ReviewStatus.NEEDS_REVISION,
            note=revision_note,
        )
        return await self.review_fact(fact_id, reviewer_id, review)

    @staticmethod
    def _require_approvable_provenance(
        fact: ExtractedFact,
        review: FactReviewRequest,
    ) -> None:
        """Require extracted facts to carry immutable source evidence before approval."""
        if review.action != ReviewStatus.APPROVED:
            return
        if fact.source_type == SourceType.MANUAL.value:
            return
        if not fact.source_chunks:
            raise ValueError(
                "Extracted facts require source evidence before they can be approved"
            )
        for assoc in fact.source_chunks:
            chunk = getattr(assoc, "chunk", None)
            if chunk is None or not getattr(chunk, "artifact_id", None):
                raise ValueError(
                    "Extracted facts require source evidence before they can be approved"
                )

    @staticmethod
    def _source_ref_sort_key(source_ref: SourceReference) -> tuple[str, str, int, str]:
        return (
            str(source_ref.artifact_id),
            source_ref.chunk_type,
            int(source_ref.sequence_number),
            str(source_ref.chunk_id),
        )

    @classmethod
    def _provenance_fingerprint(cls, source_refs: list[SourceReference]) -> str | None:
        if not source_refs:
            return None
        payload = [
            ref.model_dump(mode="json")
            for ref in sorted(source_refs, key=cls._source_ref_sort_key)
        ]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    # -------------------------------------------------------------------------
    # Revision History
    # -------------------------------------------------------------------------

    async def _create_revision(
        self,
        fact: ExtractedFact,
        previous_value: Any,
        previous_status: str,
        changed_by_id: UUID,
        change_reason: str | None = None,
    ) -> FactRevision:
        """
        Create a revision record for audit logging.

        Args:
            fact: The fact being modified
            previous_value: Value before change
            previous_status: Status before change
            changed_by_id: User making change
            change_reason: Why the change was made

        Returns:
            New FactRevision record
        """
        # Get next revision number
        result = await self.session.execute(
            select(func.coalesce(func.max(FactRevision.revision_number), 0))
            .where(FactRevision.fact_id == fact.id)
        )
        max_rev = result.scalar() or 0

        revision = FactRevision(
            fact_id=fact.id,
            revision_number=max_rev + 1,
            previous_value=previous_value,
            new_value=fact.value,
            previous_status=previous_status,
            new_status=fact.review_status,
            changed_by_id=str(changed_by_id),
            change_reason=change_reason,
        )

        self.session.add(revision)
        return revision

    async def list_revisions(self, fact_id: UUID) -> list[FactRevision]:
        """
        Get full revision history for a fact.

        Args:
            fact_id: Fact UUID

        Returns:
            List of revisions, oldest first
        """
        result = await self.session.execute(
            select(FactRevision)
            .where(FactRevision.fact_id == str(fact_id))
            .order_by(FactRevision.revision_number.asc())
        )
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Evidence Links
    # -------------------------------------------------------------------------

    async def create_evidence_link(
        self,
        fact_id: UUID,
        link_type: str,
        target_id: str,
        contribution_weight: float = 1.0,
    ) -> EvidenceLink:
        """
        Link a fact to a checklist item, readiness dimension, etc.

        Args:
            fact_id: Fact to link
            link_type: Type of link (checklist_item, readiness_dimension, etc.)
            target_id: ID of target entity
            contribution_weight: Weight of contribution (0.0-1.0)

        Returns:
            New EvidenceLink
        """
        link = EvidenceLink(
            fact_id=str(fact_id),
            link_type=link_type,
            target_id=target_id,
            contribution_weight=contribution_weight,
        )
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)

        logger.info(f"Created evidence link: fact {fact_id} -> {link_type}:{target_id}")
        return link

    async def get_evidence_for_target(
        self,
        link_type: str,
        target_id: str,
        project_id: UUID,
        approved_only: bool = True,
    ) -> list[ExtractedFact]:
        """
        Get all facts linked to a target (checklist item, dimension, etc.).

        Args:
            link_type: Type of link to filter
            target_id: Target entity ID
            project_id: Project to scope query
            approved_only: Only return approved facts

        Returns:
            List of facts linked to target
        """
        query = (
            select(ExtractedFact)
            .join(EvidenceLink)
            .where(
                and_(
                    EvidenceLink.link_type == link_type,
                    EvidenceLink.target_id == target_id,
                    ExtractedFact.project_id == str(project_id),
                )
            )
        )

        if approved_only:
            query = query.where(
                ExtractedFact.review_status == ReviewStatus.APPROVED.value
            )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    # -------------------------------------------------------------------------
    # Serialization Helpers
    # -------------------------------------------------------------------------

    def fact_to_read_schema(self, fact: ExtractedFact) -> ExtractedFactRead:
        """
        Convert ExtractedFact model to read schema.

        Args:
            fact: Database model

        Returns:
            Pydantic schema
        """
        source_chunks = []
        source_refs = []
        # Manual facts don't have source chunks - check source_type first
        # to avoid triggering lazy load on the relationship
        if fact.source_type != SourceType.MANUAL.value:
            # Only try to access source_chunks for extracted facts
            try:
                if fact.source_chunks:
                    for assoc in fact.source_chunks:
                        chunk = assoc.chunk
                        chunk_ref = ChunkReference(
                            chunk_id=UUID(chunk.id),
                            artifact_id=UUID(chunk.artifact_id),
                            page_number=chunk.page_number,
                            sheet_name=chunk.sheet_name,
                            excerpt=assoc.excerpt,
                        )
                        source_chunks.append(chunk_ref)

                        artifact = getattr(chunk, "artifact", None)
                        if artifact is not None:
                            source_refs.append(
                                SourceReference(
                                    chunk_id=chunk_ref.chunk_id,
                                    artifact_id=chunk_ref.artifact_id,
                                    page_number=chunk.page_number,
                                    sheet_name=chunk.sheet_name,
                                    excerpt=assoc.excerpt,
                                    artifact_filename=artifact.filename,
                                    artifact_display_name=artifact.display_name,
                                    storage_path=artifact.storage_path,
                                    chunk_type=chunk.chunk_type,
                                    sequence_number=chunk.sequence_number,
                                    section_title=chunk.section_title,
                                    content_hash=chunk.content_hash,
                                )
                            )
            except Exception:
                # If lazy loading fails, keep the response available rather than
                # failing unrelated reads; get_fact eagerly loads provenance.
                pass
        source_refs = sorted(source_refs, key=self._source_ref_sort_key)

        return ExtractedFactRead(
            id=UUID(fact.id),
            schema_path=fact.schema_path,
            criticality=CriticalityTier(fact.criticality),
            source_type=SourceType(fact.source_type),
            value=fact.value,
            value_type=fact.value_type,
            unit=fact.unit,
            confidence_score=fact.confidence_score,
            confidence_rationale=fact.confidence_rationale,
            project_id=UUID(fact.project_id),
            extraction_job_id=UUID(fact.extraction_job_id) if fact.extraction_job_id else None,
            review_status=ReviewStatus(fact.review_status),
            reviewed_by=UUID(fact.reviewed_by) if fact.reviewed_by else None,
            reviewed_at=fact.reviewed_at,
            review_note=fact.review_note,
            source_chunks=source_chunks,
            source_refs=source_refs,
            provenance_fingerprint=self._provenance_fingerprint(source_refs),
            original_value=fact.original_value,
            fingerprint=fact.fingerprint,
            duplicate_classification=FactDuplicateClassification(
                fact.duplicate_classification or FactDuplicateClassification.UNIQUE.value
            ),
            source_trust_score=fact.source_trust_score,
            canonical_score=fact.canonical_score,
            is_canonical=fact.is_canonical,
            lifecycle_state=FactLifecycleState(
                fact.lifecycle_state or FactLifecycleState.ACTIVE.value
            ),
            archive_reason_code=fact.archive_reason_code,
            archive_note=fact.archive_note,
            archived_by=UUID(fact.archived_by) if fact.archived_by else None,
            archived_at=fact.archived_at,
            created_at=fact.created_at,
            updated_at=fact.updated_at,
        )

    def fact_to_summary_schema(self, fact: ExtractedFact) -> ExtractedFactSummary:
        """
        Convert ExtractedFact model to summary schema.

        Args:
            fact: Database model

        Returns:
            Pydantic summary schema
        """
        return ExtractedFactSummary(
            id=UUID(fact.id),
            schema_path=fact.schema_path,
            value=fact.value,
            confidence_score=fact.confidence_score,
            review_status=ReviewStatus(fact.review_status),
            criticality=CriticalityTier(fact.criticality),
            source_type=SourceType(fact.source_type),
            duplicate_classification=FactDuplicateClassification(
                fact.duplicate_classification or FactDuplicateClassification.UNIQUE.value
            ),
            is_canonical=fact.is_canonical,
            lifecycle_state=FactLifecycleState(
                fact.lifecycle_state or FactLifecycleState.ACTIVE.value
            ),
        )

    def revision_to_schema(self, revision: FactRevision) -> FactRevisionRead:
        """
        Convert FactRevision model to schema.

        Args:
            revision: Database model

        Returns:
            Pydantic schema
        """
        return FactRevisionRead(
            id=UUID(revision.id),
            fact_id=UUID(revision.fact_id),
            revision_number=revision.revision_number,
            previous_value=revision.previous_value,
            new_value=revision.new_value,
            previous_status=(
                ReviewStatus(revision.previous_status)
                if revision.previous_status
                else None
            ),
            new_status=ReviewStatus(revision.new_status),
            changed_by=UUID(revision.changed_by_id),
            change_reason=revision.change_reason,
            created_at=revision.created_at,
            updated_at=revision.updated_at,
        )


# -----------------------------------------------------------------------------
# Conflict Detection
# -----------------------------------------------------------------------------


class FactConflictDetector:
    """
    Detects conflicts between extracted facts.

    Per spec: When multiple extractions produce different values
    for the same schema path, flag for human review.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_conflicts(
        self,
        project_id: UUID,
        schema_path: str | None = None,
    ) -> list[dict]:
        """
        Find conflicting facts (same schema path, different values).

        Args:
            project_id: Project to search
            schema_path: Optional specific path to check

        Returns:
            List of conflict records with grouped facts
        """
        # Find schema paths with multiple non-rejected facts
        query = (
            select(
                ExtractedFact.schema_path,
                func.count(ExtractedFact.id).label("fact_count"),
            )
            .where(
                and_(
                    ExtractedFact.project_id == str(project_id),
                    ExtractedFact.review_status != ReviewStatus.REJECTED.value,
                    ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value,
                )
            )
            .group_by(ExtractedFact.schema_path)
            .having(func.count(ExtractedFact.id) > 1)
        )

        if schema_path:
            query = query.where(ExtractedFact.schema_path == schema_path)

        result = await self.session.execute(query)
        conflict_paths = [row.schema_path for row in result]

        conflicts = []
        for path in conflict_paths:
            # Get all facts for this path
            facts_result = await self.session.execute(
                select(ExtractedFact)
                .where(
                    and_(
                        ExtractedFact.project_id == str(project_id),
                        ExtractedFact.schema_path == path,
                        ExtractedFact.review_status != ReviewStatus.REJECTED.value,
                        ExtractedFact.lifecycle_state != FactLifecycleState.ARCHIVED.value,
                    )
                )
                .order_by(ExtractedFact.confidence_score.desc())
            )
            facts = list(facts_result.scalars().all())

            # Check if values actually differ
            unique_values = set()
            for f in facts:
                # Serialize value for comparison
                val_str = str(f.value)
                unique_values.add(val_str)

            if len(unique_values) > 1:
                oldest_pending_days = 0
                pending_facts = [f for f in facts if f.review_status == ReviewStatus.PENDING.value]
                if pending_facts:
                    oldest_created = min((f.created_at for f in pending_facts if f.created_at), default=None)
                    if oldest_created:
                        oldest_pending_days = FactService._age_days(oldest_created)

                conflicts.append({
                    "schema_path": path,
                    "fact_count": len(facts),
                    "unique_value_count": len(unique_values),
                    "criticality": facts[0].criticality if facts else None,
                    "phase": FactService._phase_for_schema_path(path),
                    "oldest_pending_days": oldest_pending_days,
                    "facts": [
                        {
                            "id": f.id,
                            "value": f.value,
                            "confidence": f.confidence_score,
                            "status": f.review_status,
                            "lifecycle_state": f.lifecycle_state,
                            "duplicate_classification": f.duplicate_classification,
                            "is_canonical": f.is_canonical,
                            "extraction_job_id": f.extraction_job_id,
                        }
                        for f in facts
                    ],
                    "highest_confidence_id": facts[0].id if facts else None,
                })

        return conflicts

    async def auto_resolve_conflicts(
        self,
        project_id: UUID,
        strategy: str = "highest_confidence",
    ) -> list[dict]:
        """
        Automatically resolve conflicts using specified strategy.

        Args:
            project_id: Project to process
            strategy: Resolution strategy (highest_confidence, most_recent)

        Returns:
            List of resolution records
        """
        conflicts = await self.find_conflicts(project_id)
        resolutions = []

        for conflict in conflicts:
            if strategy == "highest_confidence":
                # Keep the fact with highest confidence
                winner_id = conflict["highest_confidence_id"]
                loser_ids = [
                    f["id"] for f in conflict["facts"]
                    if f["id"] != winner_id
                ]
            else:
                raise ValueError(f"Unknown resolution strategy: {strategy}")

            # Mark losers as rejected
            for loser_id in loser_ids:
                await self.session.execute(
                    ExtractedFact.__table__.update()
                    .where(ExtractedFact.id == loser_id)
                    .values(
                        review_status=ReviewStatus.REJECTED.value,
                        lifecycle_state=FactLifecycleState.REJECTED.value,
                        review_note=f"Auto-rejected: conflict resolution ({strategy})",
                    )
                )

            resolutions.append({
                "schema_path": conflict["schema_path"],
                "winner_id": winner_id,
                "rejected_ids": loser_ids,
                "strategy": strategy,
            })

            service = FactService(self.session)
            await service.refresh_canonicalization_for_path(
                project_id,
                conflict["schema_path"],
                actor_id="system",
                reason=f"auto_resolve:{strategy}",
                source_action="resolve_conflicts",
            )

        await self.session.commit()

        logger.info(
            f"Auto-resolved {len(resolutions)} conflicts for project {project_id}"
        )
        return resolutions
