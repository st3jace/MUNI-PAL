"""
Unit tests for ProjectService.

Tests CRUD operations and business logic for project management.
"""

from uuid import UUID, uuid4

import pytest

from munipal.core.schemas.project import ProjectCreate, ProjectUpdate
from munipal.services.project_service import ProjectService


class TestProjectService:
    """Test suite for ProjectService."""

    @pytest.fixture
    async def service(self, db_session):
        """Provide ProjectService instance."""
        return ProjectService(db_session)

    @pytest.fixture
    async def playbook_and_project(self, factory, db_session):
        """Create a playbook and project for tests."""
        playbook = await factory.create_playbook()
        project = await factory.create_project(playbook["id"])
        await db_session.commit()
        return playbook, project

    async def test_create_project_with_playbook(self, service, factory, db_session):
        """Test creating a project with explicit playbook."""
        playbook = await factory.create_playbook()
        await db_session.commit()

        data = ProjectCreate(
            name="New Test Project",
            description="A new project",
            issuer_name="Test Issuer",
            project_location="Test City",
            target_bond_amount=5000000.0,
            playbook_id=UUID(playbook["id"]),
        )

        owner_id = str(uuid4())
        result = await service.create(data, owner_id)

        assert result.name == "New Test Project"
        assert result.issuer_name == "Test Issuer"
        assert result.playbook_id == UUID(playbook["id"])
        assert result.owner_id == UUID(owner_id)

    async def test_create_project_uses_default_playbook(self, service, factory, db_session):
        """Test creating a project without playbook uses default."""
        playbook = await factory.create_playbook(is_default=True)
        await db_session.commit()

        data = ProjectCreate(
            name="Project Without Playbook",
            issuer_name="Issuer",
        )

        owner_id = str(uuid4())
        result = await service.create(data, owner_id)

        assert result.playbook_id == UUID(playbook["id"])

    async def test_create_project_no_default_playbook_raises(self, service, factory, db_session):
        """Test creating project without playbook when no default exists raises error."""
        # Create a non-default playbook
        await factory.create_playbook(is_default=False)
        await db_session.commit()

        data = ProjectCreate(
            name="Project",
            issuer_name="Issuer",
        )

        with pytest.raises(ValueError, match="No default playbook"):
            await service.create(data, str(uuid4()))

    async def test_get_project(self, service, playbook_and_project, db_session):
        """Test retrieving a project by ID."""
        _, project = playbook_and_project

        result = await service.get(UUID(project["id"]))

        assert result is not None
        assert result.id == UUID(project["id"])
        assert result.name == project["name"]

    async def test_get_nonexistent_project(self, service):
        """Test retrieving a nonexistent project returns None."""
        result = await service.get(uuid4())
        assert result is None

    async def test_list_projects(self, service, factory, db_session):
        """Test listing projects with pagination."""
        playbook = await factory.create_playbook()
        owner_id = str(uuid4())

        for i in range(5):
            await factory.create_project(
                playbook["id"],
                name=f"Project {i}",
                owner_id=owner_id,
            )
        await db_session.commit()

        projects, total = await service.list(owner_id=owner_id, limit=3)

        assert total == 5
        assert len(projects) == 3

    async def test_list_projects_filter_by_owner(self, service, factory, db_session):
        """Test listing projects filters by owner."""
        playbook = await factory.create_playbook()
        owner1 = str(uuid4())
        owner2 = str(uuid4())

        await factory.create_project(playbook["id"], name="Owner1 Project", owner_id=owner1)
        await factory.create_project(playbook["id"], name="Owner2 Project", owner_id=owner2)
        await db_session.commit()

        projects, total = await service.list(owner_id=owner1)

        assert total == 1
        assert projects[0].name == "Owner1 Project"

    async def test_update_project(self, service, playbook_and_project, db_session):
        """Test updating a project."""
        _, project = playbook_and_project

        update_data = ProjectUpdate(
            name="Updated Project Name",
            description="Updated description",
        )

        result = await service.update(UUID(project["id"]), update_data)

        assert result is not None
        assert result.name == "Updated Project Name"
        assert result.description == "Updated description"

    async def test_update_nonexistent_project(self, service):
        """Test updating a nonexistent project returns None."""
        update_data = ProjectUpdate(name="New Name")
        result = await service.update(uuid4(), update_data)
        assert result is None

    async def test_delete_project(self, service, playbook_and_project, db_session):
        """Test deleting a project."""
        _, project = playbook_and_project

        result = await service.delete(UUID(project["id"]))
        assert result is True

        # Verify deletion
        get_result = await service.get(UUID(project["id"]))
        assert get_result is None

    async def test_delete_nonexistent_project(self, service):
        """Test deleting a nonexistent project returns False."""
        result = await service.delete(uuid4())
        assert result is False
