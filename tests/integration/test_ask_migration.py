"""Run the release migration, then reconnect to durable storage and verify history."""

import importlib.util
from pathlib import Path

from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, delete, event, inspect, select
from sqlalchemy.orm import Session

from munipal.core.models import AskConversation, AskMessage, Base, Playbook, Project, User


def test_migration_and_restart(tmp_path):
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic/versions/20260917_0001_d4e5f6g7h8i0_add_ask_history.py"
    )
    spec = importlib.util.spec_from_file_location("ask_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    url = "sqlite:///" + (tmp_path / "ask.db").as_posix()
    engine = create_engine(url)

    @event.listens_for(engine, "connect")
    def enforce_foreign_keys(connection, record):
        connection.execute("PRAGMA foreign_keys=ON")

    existing_tables = [t for t in Base.metadata.sorted_tables if not t.name.startswith("ask_")]
    Base.metadata.create_all(engine, tables=existing_tables)
    with engine.begin() as connection:
        ctx = MigrationContext.configure(
            connection,
            opts={
                "include_object": lambda obj, name, kind, reflected, compare_to: (
                    kind != "table" or name.startswith("ask_")
                ),
            },
        )
        with Operations.context(ctx):
            migration.upgrade()
        assert compare_metadata(ctx, Base.metadata) == []
    with Session(engine) as session:
        user = User(email="durable@example.test", hashed_password="unused")
        session.add(user)
        session.flush()
        playbook = Playbook(name="Durable", version="1", description="Test", bond_archetype="Test")
        session.add(playbook)
        session.flush()
        project = Project(name="Durable", owner_id=user.id, playbook_id=playbook.id)
        session.add(project)
        session.flush()
        conversation = AskConversation(owner_id=user.id, project_id=project.id, title="Durable")
        session.add(conversation)
        session.flush()
        conversation_id = conversation.id
        for sequence in (2, 1):
            session.add(
                AskMessage(
                    conversation_id=conversation_id,
                    sequence=sequence,
                    role="assistant" if sequence == 2 else "user",
                    kind="refusal" if sequence == 2 else "question",
                    content="Persisted",
                    citations=[],
                )
            )
        session.commit()
    engine.dispose()
    restarted = create_engine(url)
    event.listen(restarted, "connect", enforce_foreign_keys)
    with Session(restarted) as session:
        restored = session.get(AskConversation, conversation_id)
        assert restored.title == "Durable"
        messages = session.scalars(select(AskMessage).order_by(AskMessage.sequence)).all()
        assert [m.sequence for m in messages] == [1, 2]
        assert all(m.created_at and m.updated_at for m in messages)
        session.execute(delete(Project).where(Project.id == restored.project_id))
        session.commit()
        assert session.scalar(select(AskConversation.id)) is None
        assert session.scalar(select(AskMessage.id)) is None
    with restarted.begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert "ask_messages" not in inspect(connection).get_table_names()
        assert "ask_conversations" not in inspect(connection).get_table_names()
    restarted.dispose()
