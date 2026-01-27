"""
Unit tests for FactService.

Tests fact CRUD, review workflow, revision history, and conflict detection.
Per spec: ExtractedFact is THE CORE PRIMITIVE.
"""

from uuid import UUID, uuid4

import pytest

from munipal.core.schemas.base import ReviewStatus, CriticalityTier
from munipal.core.schemas.fact import FactReviewRequest
from munipal.services.fact_service import FactService, FactConflictDetector


class TestFactService:
    """Test suite for FactService."""

    @pytest.fixture
    async def service(self, db_session):
        """Provide FactService instance."""
        return FactService(db_session)

    @pytest.fixture
    async def project_with_facts(self, factory, db_session):
        """Create project with facts for testing."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        facts = []
        for i, (path, value, status) in enumerate([
            ("project.name", "Test Project", "pending"),
            ("capital.project-cost", 50000000.0, "approved"),
            ("project.location", "Test City", "pending"),
            ("revenue.annual", 5000000.0, "rejected"),
        ]):
            fact = await factory.create_fact(
                project["id"],
                job["id"],
                schema_path=path,
                value=value,
                review_status=status,
                confidence_score=0.90 - (i * 0.05),
            )
            facts.append(fact)

        await db_session.commit()

        return {
            "project": project,
            "artifact": artifact,
            "job": job,
            "facts": facts,
        }

    # -------------------------------------------------------------------------
    # Query Tests
    # -------------------------------------------------------------------------

    async def test_get_fact(self, service, project_with_facts):
        """Test retrieving a fact by ID."""
        fact_data = project_with_facts["facts"][0]

        result = await service.get_fact(UUID(fact_data["id"]))

        assert result is not None
        assert result.id == fact_data["id"]
        assert result.schema_path == fact_data["schema_path"]
        assert result.value == fact_data["value"]

    async def test_get_nonexistent_fact(self, service):
        """Test retrieving nonexistent fact returns None."""
        result = await service.get_fact(uuid4())
        assert result is None

    async def test_list_facts(self, service, project_with_facts):
        """Test listing facts for a project."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(UUID(project_id))

        assert total == 4
        assert len(facts) == 4

    async def test_list_facts_filter_by_status(self, service, project_with_facts):
        """Test filtering facts by review status."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            status_filter=ReviewStatus.PENDING,
        )

        assert total == 2
        assert all(f.review_status == "pending" for f in facts)

    async def test_list_facts_filter_by_schema_path_prefix(self, service, project_with_facts):
        """Test filtering facts by schema path prefix."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            schema_path_prefix="project.",
        )

        assert total == 2
        assert all(f.schema_path.startswith("project.") for f in facts)

    async def test_list_facts_filter_by_min_confidence(self, service, project_with_facts):
        """Test filtering facts by minimum confidence."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            min_confidence=0.85,
        )

        assert all(f.confidence_score >= 0.85 for f in facts)

    async def test_list_facts_pagination(self, service, project_with_facts):
        """Test facts pagination."""
        project_id = project_with_facts["project"]["id"]

        facts, total = await service.list_facts(
            UUID(project_id),
            limit=2,
            offset=0,
        )

        assert total == 4
        assert len(facts) == 2

    async def test_get_facts_by_schema_path(self, service, project_with_facts):
        """Test getting facts by exact schema path."""
        project_id = project_with_facts["project"]["id"]

        facts = await service.get_facts_by_schema_path(
            UUID(project_id),
            "project.name",
        )

        assert len(facts) == 1
        assert facts[0].schema_path == "project.name"

    async def test_get_facts_by_schema_path_approved_only(self, service, project_with_facts):
        """Test getting only approved facts for a schema path."""
        project_id = project_with_facts["project"]["id"]

        # Get all facts for capital.project-cost (which is approved)
        all_facts = await service.get_facts_by_schema_path(
            UUID(project_id),
            "capital.project-cost",
        )
        approved_facts = await service.get_facts_by_schema_path(
            UUID(project_id),
            "capital.project-cost",
            approved_only=True,
        )

        assert len(all_facts) == 1
        assert len(approved_facts) == 1

    async def test_get_pending_review_count(self, service, project_with_facts):
        """Test getting counts by review status."""
        project_id = project_with_facts["project"]["id"]

        counts = await service.get_pending_review_count(UUID(project_id))

        assert counts["pending"] == 2
        assert counts["approved"] == 1
        assert counts["rejected"] == 1
        assert counts["needs_revision"] == 0

    # -------------------------------------------------------------------------
    # Review Workflow Tests
    # -------------------------------------------------------------------------

    async def test_approve_fact(self, service, project_with_facts, reviewer_id, db_session):
        """Test approving a fact."""
        pending_fact = project_with_facts["facts"][0]

        result = await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            note="Looks good",
        )

        assert result.review_status == ReviewStatus.APPROVED.value
        assert result.reviewed_by == reviewer_id
        assert result.review_note == "Looks good"
        assert result.reviewed_at is not None

    async def test_approve_fact_with_correction(self, service, project_with_facts, reviewer_id):
        """Test approving a fact with corrected value."""
        pending_fact = project_with_facts["facts"][0]
        original_value = pending_fact["value"]

        result = await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            corrected_value="Corrected Project Name",
            note="Fixed typo",
        )

        assert result.review_status == ReviewStatus.APPROVED.value
        assert result.value == "Corrected Project Name"
        assert result.original_value == original_value

    async def test_reject_fact(self, service, project_with_facts, reviewer_id):
        """Test rejecting a fact."""
        pending_fact = project_with_facts["facts"][0]

        result = await service.reject_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            reason="Incorrect extraction",
        )

        assert result.review_status == ReviewStatus.REJECTED.value
        assert result.review_note == "Incorrect extraction"

    async def test_request_revision(self, service, project_with_facts, reviewer_id):
        """Test flagging a fact for revision."""
        pending_fact = project_with_facts["facts"][0]

        result = await service.request_revision(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            revision_note="Please verify against source document",
        )

        assert result.review_status == ReviewStatus.NEEDS_REVISION.value
        assert result.review_note == "Please verify against source document"

    async def test_review_nonexistent_fact_raises(self, service, reviewer_id):
        """Test reviewing nonexistent fact raises error."""
        review = FactReviewRequest(
            action=ReviewStatus.APPROVED,
            note="Test",
        )

        with pytest.raises(ValueError, match="not found"):
            await service.review_fact(uuid4(), UUID(reviewer_id), review)

    # -------------------------------------------------------------------------
    # Revision History Tests
    # -------------------------------------------------------------------------

    async def test_revision_created_on_review(self, service, project_with_facts, reviewer_id):
        """Test that reviewing a fact creates a revision record."""
        pending_fact = project_with_facts["facts"][0]

        await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
        )

        revisions = await service.list_revisions(UUID(pending_fact["id"]))

        assert len(revisions) == 1
        assert revisions[0].previous_status == "pending"
        assert revisions[0].new_status == ReviewStatus.APPROVED.value
        assert revisions[0].revision_number == 1

    async def test_multiple_revisions_tracked(self, service, project_with_facts, reviewer_id):
        """Test that multiple reviews create sequential revisions."""
        pending_fact = project_with_facts["facts"][0]

        # First review: request revision
        await service.request_revision(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            revision_note="Need more info",
        )

        # Second review: approve
        await service.approve_fact(
            UUID(pending_fact["id"]),
            UUID(reviewer_id),
            note="Now looks good",
        )

        revisions = await service.list_revisions(UUID(pending_fact["id"]))

        assert len(revisions) == 2
        assert revisions[0].revision_number == 1
        assert revisions[0].new_status == ReviewStatus.NEEDS_REVISION.value
        assert revisions[1].revision_number == 2
        assert revisions[1].new_status == ReviewStatus.APPROVED.value

    # -------------------------------------------------------------------------
    # Serialization Tests
    # -------------------------------------------------------------------------

    async def test_fact_to_read_schema(self, service, project_with_facts):
        """Test converting fact to read schema."""
        fact_data = project_with_facts["facts"][0]
        fact = await service.get_fact(UUID(fact_data["id"]))

        schema = service.fact_to_read_schema(fact)

        assert schema.id == UUID(fact_data["id"])
        assert schema.schema_path == fact_data["schema_path"]
        assert schema.value == fact_data["value"]

    async def test_fact_to_summary_schema(self, service, project_with_facts):
        """Test converting fact to summary schema."""
        fact_data = project_with_facts["facts"][0]
        fact = await service.get_fact(UUID(fact_data["id"]))

        schema = service.fact_to_summary_schema(fact)

        assert schema.id == UUID(fact_data["id"])
        assert schema.schema_path == fact_data["schema_path"]
        assert schema.value == fact_data["value"]
        assert schema.review_status == ReviewStatus.PENDING


class TestFactConflictDetector:
    """Test suite for FactConflictDetector."""

    @pytest.fixture
    async def detector(self, db_session):
        """Provide FactConflictDetector instance."""
        return FactConflictDetector(db_session)

    @pytest.fixture
    async def project_with_conflicts(self, factory, db_session):
        """Create project with conflicting facts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Create conflicting facts for same schema path
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=50000000.0,
            confidence_score=0.95,
            review_status="pending",
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="capital.project-cost",
            value=55000000.0,
            confidence_score=0.85,
            review_status="pending",
        )

        # Non-conflicting fact
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Test",
            confidence_score=0.90,
            review_status="pending",
        )

        await db_session.commit()

        return project

    async def test_find_conflicts(self, detector, project_with_conflicts):
        """Test finding conflicting facts."""
        conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"])
        )

        assert len(conflicts) == 1
        assert conflicts[0]["schema_path"] == "capital.project-cost"
        assert conflicts[0]["fact_count"] == 2
        assert conflicts[0]["unique_value_count"] == 2

    async def test_find_conflicts_specific_path(self, detector, project_with_conflicts):
        """Test finding conflicts for specific schema path."""
        conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"]),
            schema_path="capital.project-cost",
        )

        assert len(conflicts) == 1

        # Non-existent path
        no_conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"]),
            schema_path="nonexistent.path",
        )

        assert len(no_conflicts) == 0

    async def test_auto_resolve_highest_confidence(self, detector, project_with_conflicts, db_session):
        """Test auto-resolving conflicts with highest confidence strategy."""
        resolutions = await detector.auto_resolve_conflicts(
            UUID(project_with_conflicts["id"]),
            strategy="highest_confidence",
        )

        assert len(resolutions) == 1
        assert resolutions[0]["schema_path"] == "capital.project-cost"
        assert len(resolutions[0]["rejected_ids"]) == 1

        # Verify no more conflicts
        remaining_conflicts = await detector.find_conflicts(
            UUID(project_with_conflicts["id"])
        )
        assert len(remaining_conflicts) == 0

    async def test_auto_resolve_unknown_strategy_raises(self, detector, project_with_conflicts):
        """Test that unknown resolution strategy raises error."""
        with pytest.raises(ValueError, match="Unknown resolution strategy"):
            await detector.auto_resolve_conflicts(
                UUID(project_with_conflicts["id"]),
                strategy="unknown_strategy",
            )

    async def test_no_conflicts_when_values_match(self, factory, detector, db_session):
        """Test that duplicate facts with same value don't count as conflicts."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        artifact = await factory.create_artifact(project["id"])
        job = await factory.create_extraction_job(project["id"], artifact["id"])

        # Same value, different confidence
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Same Value",
            confidence_score=0.95,
        )
        await factory.create_fact(
            project["id"],
            job["id"],
            schema_path="project.name",
            value="Same Value",
            confidence_score=0.85,
        )
        await db_session.commit()

        conflicts = await detector.find_conflicts(UUID(project["id"]))

        assert len(conflicts) == 0
