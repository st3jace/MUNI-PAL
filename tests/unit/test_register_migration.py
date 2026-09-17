"""Exercise the new migration and persistence against a fresh file database."""

import importlib.util
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from munipal.core.models.register import RegisterDeal, RegisterReport


def test_register_migration_persists_across_connections(tmp_path):
    path = (
        Path(__file__).resolve().parents[2]
        / "alembic/versions/20260917_0002_e5f6g7h8i9j0_register_portal.py"
    )
    spec = importlib.util.spec_from_file_location("register_migration", path)
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)
    url = f"sqlite:///{tmp_path / 'migration.db'}"
    engine = create_engine(url)
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE users (id VARCHAR(36) PRIMARY KEY)"))
        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()
        tables = inspect(connection).get_table_names()
        assert {
            "register_deals",
            "register_documents",
            "register_folders",
            "register_reports",
            "register_payment_reversals",
        } <= set(tables)
        connection.execute(
            text("INSERT INTO register_payment_reversals(payment_intent_id) VALUES ('pi_persist')")
        )
        connection.execute(text("INSERT INTO users(id) VALUES ('owner')"))
        with Session(bind=connection) as session:
            deal = RegisterDeal(
                owner_id="owner",
                tenant_id="tenant",
                name="Saved deal",
                legal_name="Borrower",
                professional_contact="Counsel",
            )
            session.add(deal)
            session.flush()
            report = RegisterReport(
                deal_id=deal.id,
                version=1,
                candidate_count=2,
                document_count=1,
                content=b"private report snapshot",
                sha256="a" * 64,
            )
            session.add(report)
            session.flush()
    engine.dispose()
    engine = create_engine(url)
    with engine.begin() as connection:
        assert (
            connection.scalar(text("SELECT payment_intent_id FROM register_payment_reversals"))
            == "pi_persist"
        )
        assert (
            connection.scalar(text("SELECT content FROM register_reports"))
            == b"private report snapshot"
        )
        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()
        assert inspect(connection).get_table_names() == ["users"]
    engine.dispose()
