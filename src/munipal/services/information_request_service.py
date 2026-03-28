"""
Information Request Service for WP8.

Per spec: WP8 transforms gap analysis from binary indicators into actionable
information requests that guide the team toward producing/procuring specific evidence.

Core principles (NON-NEGOTIABLE):
- Every request must be specific enough that the assigned person knows exactly what to produce
- Bond-domain context explains WHY this information matters
- Guidance shows HOW to satisfy requirements
- Priority scoring drives urgency
"""

import logging
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from munipal.core.models.information_request import (
    InformationRequest,
    InformationRequestNote,
)
from munipal.core.models.project import Project
from munipal.core.models.fact import ExtractedFact
from munipal.core.models.user import User
from munipal.core.schemas.information_request import (
    InformationRequestCreate,
    InformationRequestRead,
    InformationRequestSummary,
    InformationRequestUpdate,
    InformationRequestReport,
    RequestsByOwner,
    EvidenceState,
    RequestPriority,
    RequestStatus,
    EvidenceExample,
)
from munipal.services.fact_service import FactService
from munipal.services.playbook_data import (
    INFORMATION_REQUEST_TEMPLATES,
    OWNER_MAP,
    CHECKLIST_ITEMS,
    READINESS_CONFIG,
    SCHEMA_PATHS,
)

logger = logging.getLogger(__name__)


class InformationRequestService:
    """
    Service for managing information requests.

    Per WP8 spec: Generate structured prompts that help the team fill gaps
    with context on why it matters.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session

    # -------------------------------------------------------------------------
    # Request Management
    # -------------------------------------------------------------------------

    async def create_request(
        self, request: InformationRequestCreate
    ) -> InformationRequest:
        """Create a new information request."""
        # Generate request code
        request_code = await self._generate_request_code(request.project_id)

        info_request = InformationRequest(
            id=str(uuid4()),
            project_id=str(request.project_id),
            request_code=request_code,
            title=request.title,
            missing_fact_paths=request.missing_fact_paths,
            current_evidence_state=self._enum_value(request.current_evidence_state),
            gap_id=request.gap_id,
            # Bond domain context
            why_it_matters=request.why_it_matters,
            who_needs_it=request.who_needs_it,
            when_needed=request.when_needed,
            consequences=request.consequences,
            related_requirements=request.related_requirements,
            regulatory_reference=request.regulatory_reference,
            # Affected items
            affected_checklist_items=request.affected_checklist_items,
            affected_dimensions=request.affected_dimensions,
            # Guidance
            guidance_overview=request.guidance_overview,
            specific_questions=request.specific_questions,
            data_points_needed=request.data_points_needed,
            suggested_approach=request.suggested_approach,
            common_pitfalls=request.common_pitfalls,
            time_estimate=request.time_estimate,
            # Examples and sources
            examples=[e.model_dump() for e in request.examples],
            acceptable_sources=request.acceptable_sources,
            # Quality requirements
            minimum_confidence=request.minimum_confidence,
            expected_format=request.expected_format,
            # Assignment
            priority=self._enum_value(request.priority),
            suggested_owner=request.suggested_owner,
            target_date=request.target_date,
            # Status
            status=RequestStatus.OPEN.value,
        )

        self.session.add(info_request)
        await self.session.flush()
        await self.session.refresh(info_request)
        return info_request

    async def get_request(self, request_id: UUID) -> InformationRequest | None:
        """Get an information request by ID."""
        result = await self.session.execute(
            select(InformationRequest)
            .options(selectinload(InformationRequest.notes))
            .where(InformationRequest.id == str(request_id))
        )
        return result.scalar_one_or_none()

    async def list_requests(
        self,
        project_id: UUID,
        status: RequestStatus | None = None,
        priority: RequestPriority | None = None,
        owner: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[InformationRequest], int]:
        """List information requests with filters."""
        base_query = select(InformationRequest).where(
            InformationRequest.project_id == str(project_id)
        )

        if status:
            base_query = base_query.where(
                InformationRequest.status == status.value
            )
        if priority:
            base_query = base_query.where(
                InformationRequest.priority == priority.value
            )
        if owner:
            base_query = base_query.where(
                InformationRequest.suggested_owner == owner
            )

        # Get count
        count_result = await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )
        total = count_result.scalar() or 0

        # Get results
        query = (
            base_query.order_by(
                # Priority order: critical > high > medium > low
                InformationRequest.priority.desc(),
                InformationRequest.created_at.desc(),
            )
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        requests = list(result.scalars().all())

        return requests, total

    async def update_request(
        self, request_id: UUID, update: InformationRequestUpdate, user_id: UUID | None = None
    ) -> InformationRequest | None:
        """Update an information request."""
        request = await self.get_request(request_id)
        if not request:
            return None

        # Update fields
        if update.status:
            old_status = request.status
            new_status = self._enum_value(update.status)
            request.status = new_status

            # Track status transitions
            now = datetime.now(timezone.utc)
            if (
                new_status == RequestStatus.IN_PROGRESS.value
                and old_status == RequestStatus.OPEN.value
            ):
                request.acknowledged_at = now
                request.acknowledged_by = await self._resolve_existing_user_id(user_id)
            elif new_status == RequestStatus.SUBMITTED.value:
                request.submitted_at = now
            elif new_status == RequestStatus.RESOLVED.value:
                request.resolved_at = now
            elif new_status == RequestStatus.DEFERRED.value:
                request.deferred_at = now
                request.deferred_reason = update.deferred_reason
                request.deferred_review_date = update.deferred_review_date

        if update.suggested_owner is not None:
            request.suggested_owner = update.suggested_owner
        if update.target_date is not None:
            request.target_date = update.target_date

        # Add note if provided
        if update.notes:
            note = InformationRequestNote(
                id=str(uuid4()),
                request_id=str(request_id),
                content=update.notes,
                note_type="update",
                created_by_id=str(user_id) if user_id else str(uuid4()),
            )
            self.session.add(note)

        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def resolve_request(
        self,
        request_id: UUID,
        fact_ids: list[UUID],
        resolution_notes: str | None = None,
    ) -> InformationRequest | None:
        """Resolve an information request with accepted facts."""
        request = await self.get_request(request_id)
        if not request:
            return None

        request.status = RequestStatus.RESOLVED.value
        request.resolved_at = datetime.now(timezone.utc)
        request.resolved_by_fact_ids = [str(fid) for fid in fact_ids]
        request.resolution_notes = resolution_notes

        await self.session.flush()
        await self.session.refresh(request)
        return request

    async def link_evidence(
        self, request_id: UUID, artifact_id: UUID, notes: str | None = None
    ) -> InformationRequest | None:
        """Link an artifact as evidence for a request."""
        request = await self.get_request(request_id)
        if not request:
            return None

        request.linked_artifact_id = str(artifact_id)
        request.status = RequestStatus.SUBMITTED.value
        request.submitted_at = datetime.now(timezone.utc)

        if notes:
            note = InformationRequestNote(
                id=str(uuid4()),
                request_id=str(request_id),
                content=notes,
                note_type="update",
                created_by_id=str(uuid4()),  # Would need actual user
            )
            self.session.add(note)

        await self.session.flush()
        await self.session.refresh(request)
        return request

    # -------------------------------------------------------------------------
    # Gap-to-Request Generation
    # -------------------------------------------------------------------------

    async def generate_requests_from_gaps(
        self, project_id: UUID
    ) -> list[InformationRequest]:
        """
        Generate information requests from gap analysis.

        Per WP8 spec: Each gap type maps to a request template.
        """
        logger.info(f"Generating information requests for project {project_id}")

        # Get approved facts
        facts = await self._get_approved_facts(project_id)
        facts_by_path = FactService.select_preferred_facts_by_path(facts)

        # Get existing requests to avoid duplicates
        existing_requests = await self._get_existing_request_paths(project_id)

        # Find gaps and generate requests
        generated_requests = []
        request_counter = await self._get_request_counter(project_id)
        project_token = self._project_code_token(project_id)

        for template in INFORMATION_REQUEST_TEMPLATES:
            trigger_paths = template["trigger_fact_paths"]

            # Check if any trigger path is missing
            missing_paths = [p for p in trigger_paths if p not in facts_by_path]
            if not missing_paths:
                continue

            # Check if request already exists for these paths
            path_key = ",".join(sorted(missing_paths))
            if path_key in existing_requests:
                continue

            # Determine evidence state
            evidence_state = self._determine_evidence_state(
                trigger_paths, facts_by_path
            )

            # Calculate priority
            priority = self._calculate_priority(
                template, missing_paths, trigger_paths
            )

            # Determine owner
            owner = self._suggest_owner(missing_paths)

            # Determine affected items
            affected_checklist = self._find_affected_checklist_items(missing_paths)
            affected_dimensions = self._find_affected_dimensions(missing_paths)

            # Generate request code
            request_counter += 1
            phase = template.get("trigger_phase", "P1")
            request_code = self._build_request_code(
                project_token=project_token,
                counter=request_counter,
                phase=phase,
            )

            # Create request
            request = InformationRequest(
                id=str(uuid4()),
                project_id=str(project_id),
                request_code=request_code,
                title=template["title_template"],
                missing_fact_paths=missing_paths,
                current_evidence_state=evidence_state.value,
                # Bond domain context
                why_it_matters=template["why_it_matters"],
                who_needs_it=template["who_needs_it"],
                when_needed=template["when_needed"],
                consequences=template["consequences"],
                related_requirements=template.get("related_requirements", []),
                regulatory_reference=template.get("regulatory_reference"),
                # Affected items
                affected_checklist_items=affected_checklist,
                affected_dimensions=affected_dimensions,
                # Guidance
                guidance_overview=template["guidance_overview"],
                specific_questions=template["specific_questions"],
                data_points_needed=template["data_points_needed"],
                suggested_approach=template.get("suggested_approach"),
                common_pitfalls=template.get("common_pitfalls", []),
                time_estimate=template.get("time_estimate"),
                # Examples
                examples=template.get("examples", []),
                acceptable_sources=template.get("acceptable_sources", []),
                # Quality
                minimum_confidence=template.get("minimum_confidence", 0.80),
                expected_format=template.get("expected_format"),
                # Assignment
                priority=priority.value,
                suggested_owner=owner or template.get("default_owner"),
                status=RequestStatus.OPEN.value,
            )

            self.session.add(request)
            generated_requests.append(request)

        await self.session.flush()
        for request in generated_requests:
            await self.session.refresh(request)
        logger.info(f"Generated {len(generated_requests)} information requests")

        return generated_requests

    def _determine_evidence_state(
        self,
        paths: list[str],
        facts_by_path: dict[str, ExtractedFact],
    ) -> EvidenceState:
        """Determine the current evidence state for a set of paths."""
        present = [p for p in paths if p in facts_by_path]

        if not present:
            return EvidenceState.NONE

        # Check for conflicts or weak evidence
        has_weak = any(
            facts_by_path[p].confidence_score < 0.70 for p in present
        )

        if len(present) < len(paths):
            return EvidenceState.PARTIAL

        if has_weak:
            return EvidenceState.WEAK

        return EvidenceState.PARTIAL

    def _calculate_priority(
        self,
        template: dict,
        missing_paths: list[str],
        all_paths: list[str],
    ) -> RequestPriority:
        """Calculate priority based on gap severity and impact."""
        default_priority = template.get("default_priority", "medium")

        # Check for critical paths
        critical_missing = 0
        for path in missing_paths:
            for path_def in SCHEMA_PATHS:
                if path_def["path"] == path and path_def.get("criticality") == "critical":
                    critical_missing += 1
                    break

        # Upgrade priority based on critical paths
        if critical_missing >= 2:
            return RequestPriority.CRITICAL
        elif critical_missing == 1:
            return RequestPriority.HIGH
        elif default_priority == "critical":
            return RequestPriority.CRITICAL
        elif default_priority == "high":
            return RequestPriority.HIGH
        elif default_priority == "medium":
            return RequestPriority.MEDIUM
        else:
            return RequestPriority.LOW

    def _suggest_owner(self, paths: list[str]) -> str | None:
        """Suggest owner based on schema path domains."""
        if not paths:
            return None

        # Find most common domain
        domains = [p.split(".")[0] for p in paths]
        domain_counts = {}
        for d in domains:
            domain_counts[d] = domain_counts.get(d, 0) + 1

        primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0]

        # Match against owner map
        for pattern, owner in OWNER_MAP.items():
            if pattern.startswith(primary_domain):
                return owner

        return "Sponsor"

    def _find_affected_checklist_items(self, paths: list[str]) -> list[str]:
        """Find checklist items affected by missing paths."""
        affected = []
        for item in CHECKLIST_ITEMS:
            required = item.get("required_schema_paths", [])
            if any(p in required for p in paths):
                affected.append(item["item_code"])
        return affected

    def _find_affected_dimensions(self, paths: list[str]) -> list[str]:
        """Find readiness dimensions affected by missing paths."""
        affected = []
        for dim_key, dim_config in READINESS_CONFIG["dimensions"].items():
            contributing = dim_config.get("contributing_paths", [])
            if any(p in contributing for p in paths):
                affected.append(dim_key)
        return list(set(affected))

    # -------------------------------------------------------------------------
    # Reporting
    # -------------------------------------------------------------------------

    async def get_report(self, project_id: UUID) -> InformationRequestReport:
        """Get a summary report of information requests."""
        requests, total = await self.list_requests(project_id, limit=1000)

        # Count by status
        status_counts = {s: 0 for s in RequestStatus}
        for req in requests:
            status = RequestStatus(req.status)
            status_counts[status] += 1

        # Count by priority
        priority_counts = {p: 0 for p in RequestPriority}
        for req in requests:
            priority = RequestPriority(req.priority)
            priority_counts[priority] += 1

        # Find overdue
        today = date.today()
        overdue = []
        for req in requests:
            if (
                req.target_date
                and req.target_date < today
                and req.status in [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value]
            ):
                overdue.append(req)

        # Group by owner
        by_owner = {}
        for req in requests:
            owner = req.suggested_owner or "Unassigned"
            if owner not in by_owner:
                by_owner[owner] = {
                    "owner": owner,
                    "open_count": 0,
                    "in_progress_count": 0,
                    "overdue_count": 0,
                    "requests": [],
                }
            by_owner[owner]["requests"].append(req)
            if req.status == RequestStatus.OPEN.value:
                by_owner[owner]["open_count"] += 1
            elif req.status == RequestStatus.IN_PROGRESS.value:
                by_owner[owner]["in_progress_count"] += 1

        return InformationRequestReport(
            project_id=project_id,
            open_count=status_counts[RequestStatus.OPEN],
            in_progress_count=status_counts[RequestStatus.IN_PROGRESS],
            submitted_count=status_counts[RequestStatus.SUBMITTED],
            resolved_count=status_counts[RequestStatus.RESOLVED],
            deferred_count=status_counts[RequestStatus.DEFERRED],
            critical_count=priority_counts[RequestPriority.CRITICAL],
            high_count=priority_counts[RequestPriority.HIGH],
            medium_count=priority_counts[RequestPriority.MEDIUM],
            low_count=priority_counts[RequestPriority.LOW],
            overdue_count=len(overdue),
            overdue_requests=[self.request_to_summary(r) for r in overdue],
            by_owner=[
                RequestsByOwner(
                    owner=data["owner"],
                    open_count=data["open_count"],
                    in_progress_count=data["in_progress_count"],
                    overdue_count=data["overdue_count"],
                    requests=[self.request_to_summary(r) for r in data["requests"]],
                )
                for data in by_owner.values()
            ],
        )

    # -------------------------------------------------------------------------
    # Helper Methods
    # -------------------------------------------------------------------------

    async def _resolve_existing_user_id(self, user_id: UUID | None) -> str | None:
        """Return a user-id string only when a matching user row exists."""
        if user_id is None:
            return None

        user_id_str = str(user_id)
        user = await self.session.get(User, user_id_str)
        if user is None:
            logger.warning(
                "Skipping information-request user link because user does not exist: %s",
                user_id_str,
            )
            return None
        return user_id_str

    async def project_exists(self, project_id: UUID) -> bool:
        """Return True when project exists, False otherwise."""
        return await self.session.get(Project, str(project_id)) is not None

    async def _get_approved_facts(self, project_id: UUID) -> list[ExtractedFact]:
        """Get all approved facts for a project."""
        fact_service = FactService(self.session)
        return await fact_service.get_active_approved_facts(project_id)

    async def _get_existing_request_paths(self, project_id: UUID) -> set[str]:
        """Get path keys for existing non-resolved requests."""
        result = await self.session.execute(
            select(InformationRequest.missing_fact_paths).where(
                InformationRequest.project_id == str(project_id),
                InformationRequest.status != RequestStatus.RESOLVED.value,
            )
        )
        existing = set()
        for row in result.scalars().all():
            if row:
                existing.add(",".join(sorted(row)))
        return existing

    async def _get_request_counter(self, project_id: UUID) -> int:
        """Get current request counter for a project."""
        result = await self.session.execute(
            select(func.count()).where(
                InformationRequest.project_id == str(project_id)
            )
        )
        return result.scalar() or 0

    async def _generate_request_code(self, project_id: UUID) -> str:
        """Generate a unique request code."""
        counter = await self._get_request_counter(project_id)
        return self._build_request_code(
            project_token=self._project_code_token(project_id),
            counter=counter + 1,
        )

    @staticmethod
    def _project_code_token(project_id: UUID) -> str:
        """Build deterministic project token for globally unique request codes."""
        return str(project_id).replace("-", "").upper()

    @staticmethod
    def _build_request_code(
        project_token: str,
        counter: int,
        phase: str | None = None,
    ) -> str:
        """Build request code with optional phase context."""
        if phase:
            return f"IR-{project_token}-{phase}-{counter:03d}"
        return f"IR-{project_token}-{counter:03d}"

    @staticmethod
    def _enum_value(value: Any) -> Any:
        """Return enum value for Enum-like objects; passthrough plain values."""
        return value.value if hasattr(value, "value") else value

    # -------------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------------

    def request_to_read_schema(
        self, request: InformationRequest
    ) -> InformationRequestRead:
        """Convert model to read schema."""
        # Calculate overdue status
        today = date.today()
        is_overdue = (
            request.target_date is not None
            and request.target_date < today
            and request.status in [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value]
        )
        days_overdue = 0
        if is_overdue and request.target_date:
            days_overdue = (today - request.target_date).days

        return InformationRequestRead(
            id=UUID(request.id),
            project_id=UUID(request.project_id),
            request_code=request.request_code,
            title=request.title,
            missing_fact_paths=request.missing_fact_paths,
            current_evidence_state=EvidenceState(request.current_evidence_state),
            gap_id=request.gap_id,
            why_it_matters=request.why_it_matters,
            who_needs_it=request.who_needs_it,
            when_needed=request.when_needed,
            consequences=request.consequences,
            related_requirements=request.related_requirements,
            regulatory_reference=request.regulatory_reference,
            affected_checklist_items=request.affected_checklist_items,
            affected_dimensions=request.affected_dimensions,
            guidance_overview=request.guidance_overview,
            specific_questions=request.specific_questions,
            data_points_needed=request.data_points_needed,
            suggested_approach=request.suggested_approach,
            common_pitfalls=request.common_pitfalls,
            time_estimate=request.time_estimate,
            examples=[EvidenceExample(**e) for e in request.examples] if request.examples else [],
            acceptable_sources=request.acceptable_sources,
            minimum_confidence=request.minimum_confidence,
            expected_format=request.expected_format,
            priority=RequestPriority(request.priority),
            suggested_owner=request.suggested_owner,
            target_date=request.target_date,
            status=RequestStatus(request.status),
            acknowledged_at=request.acknowledged_at,
            acknowledged_by=UUID(request.acknowledged_by) if request.acknowledged_by else None,
            submitted_at=request.submitted_at,
            resolved_at=request.resolved_at,
            deferred_at=request.deferred_at,
            deferred_reason=request.deferred_reason,
            deferred_review_date=request.deferred_review_date,
            resolution_notes=request.resolution_notes,
            resolved_by_fact_ids=[UUID(fid) for fid in request.resolved_by_fact_ids] if request.resolved_by_fact_ids else [],
            linked_artifact_id=UUID(request.linked_artifact_id) if request.linked_artifact_id else None,
            escalation_level=request.escalation_level,
            last_escalated_at=request.last_escalated_at,
            is_overdue=is_overdue,
            days_overdue=days_overdue,
            created_at=request.created_at,
            updated_at=request.updated_at,
        )

    def request_to_summary(
        self, request: InformationRequest
    ) -> InformationRequestSummary:
        """Convert model to summary schema."""
        today = date.today()
        is_overdue = (
            request.target_date is not None
            and request.target_date < today
            and request.status in [RequestStatus.OPEN.value, RequestStatus.IN_PROGRESS.value]
        )
        days_overdue = 0
        if is_overdue and request.target_date:
            days_overdue = (today - request.target_date).days

        return InformationRequestSummary(
            id=UUID(request.id),
            request_code=request.request_code,
            title=request.title,
            priority=RequestPriority(request.priority),
            status=RequestStatus(request.status),
            suggested_owner=request.suggested_owner,
            target_date=request.target_date,
            is_overdue=is_overdue,
            days_overdue=days_overdue,
            created_at=request.created_at,
        )
