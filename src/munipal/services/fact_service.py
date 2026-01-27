"""
Fact management service.

Per spec: ExtractedFact is THE CORE PRIMITIVE.
Handles CRUD operations, review workflow, and versioning.
"""

import logging
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
from munipal.core.schemas.base import ReviewStatus, CriticalityTier
from munipal.core.schemas.fact import (
    ExtractedFactCreate,
    ExtractedFactRead,
    ExtractedFactSummary,
    FactReviewRequest,
    FactRevisionRead,
    ChunkReference,
)

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
    # Query Methods
    # -------------------------------------------------------------------------

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
                selectinload(ExtractedFact.source_chunks).selectinload(
                    FactChunkAssociation.chunk
                ),
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

        if approved_only:
            query = query.where(
                ExtractedFact.review_status == ReviewStatus.APPROVED.value
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
            .group_by(ExtractedFact.review_status)
        )

        counts = {status.value: 0 for status in ReviewStatus}
        for row in result:
            counts[row.review_status] = row.count

        return counts

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

        # Capture previous state for revision
        previous_value = fact.value
        previous_status = fact.review_status

        # Update based on action
        now = datetime.now(timezone.utc)

        if review.action == ReviewStatus.APPROVED:
            fact.review_status = ReviewStatus.APPROVED.value

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
            logger.info(f"Fact {fact_id} rejected by {reviewer_id}")

        elif review.action == ReviewStatus.NEEDS_REVISION:
            fact.review_status = ReviewStatus.NEEDS_REVISION.value
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
        for assoc in fact.source_chunks:
            chunk = assoc.chunk
            source_chunks.append(
                ChunkReference(
                    chunk_id=UUID(chunk.id),
                    artifact_id=UUID(chunk.artifact_id),
                    page_number=chunk.page_number,
                    sheet_name=chunk.sheet_name,
                    excerpt=assoc.excerpt,
                )
            )

        return ExtractedFactRead(
            id=UUID(fact.id),
            schema_path=fact.schema_path,
            criticality=CriticalityTier(fact.criticality),
            value=fact.value,
            value_type=fact.value_type,
            unit=fact.unit,
            confidence_score=fact.confidence_score,
            confidence_rationale=fact.confidence_rationale,
            project_id=UUID(fact.project_id),
            extraction_job_id=UUID(fact.extraction_job_id),
            review_status=ReviewStatus(fact.review_status),
            reviewed_by=UUID(fact.reviewed_by) if fact.reviewed_by else None,
            reviewed_at=fact.reviewed_at,
            review_note=fact.review_note,
            source_chunks=source_chunks,
            original_value=fact.original_value,
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
                conflicts.append({
                    "schema_path": path,
                    "fact_count": len(facts),
                    "unique_value_count": len(unique_values),
                    "facts": [
                        {
                            "id": f.id,
                            "value": f.value,
                            "confidence": f.confidence_score,
                            "status": f.review_status,
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
                        review_note=f"Auto-rejected: conflict resolution ({strategy})",
                    )
                )

            resolutions.append({
                "schema_path": conflict["schema_path"],
                "winner_id": winner_id,
                "rejected_ids": loser_ids,
                "strategy": strategy,
            })

        await self.session.commit()

        logger.info(
            f"Auto-resolved {len(resolutions)} conflicts for project {project_id}"
        )
        return resolutions
