"""Add private Register deals, intake, purchases and immutable reports.

Revision ID: e5f6g7h8i9j0
Revises: d4e5f6g7h8i0
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "e5f6g7h8i9j0"
down_revision = "d4e5f6g7h8i0"
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column(n, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        for n in ("created_at", "updated_at")
    ]


def upgrade():
    uuid = sa.String(36).with_variant(postgresql.UUID(as_uuid=False), "postgresql")
    op.create_table(
        "register_deals",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("owner_id", uuid, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("tenant_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("legal_name", sa.String(255), nullable=False),
        sa.Column("professional_contact", sa.String(1000), nullable=False),
        sa.Column("consent_version", sa.String(50), nullable=False),
        sa.Column("payment_status", sa.String(30), nullable=False),
        sa.Column("amount_cents", sa.Integer()),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("quote_note", sa.Text()),
        sa.Column("quote_version", sa.Integer(), nullable=False),
        sa.Column("quoted_by", uuid, sa.ForeignKey("users.id")),
        sa.Column("checkout_session_id", sa.String(255), unique=True),
        sa.Column("checkout_url", sa.Text()),
        sa.Column("payment_intent_id", sa.String(255), unique=True),
        sa.Column("report_sequence", sa.Integer(), nullable=False),
        *timestamps(),
    )
    op.create_index("ix_register_deals_owner_id", "register_deals", ["owner_id"])
    op.create_table(
        "register_documents",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "deal_id", uuid, sa.ForeignKey("register_deals.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("filename", sa.String(200), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("extracted", sa.JSON(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("deal_id", "sha256", name="uq_register_document_hash"),
    )
    op.create_table(
        "register_folders",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "deal_id", uuid, sa.ForeignKey("register_deals.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("updated_by", uuid, sa.ForeignKey("users.id")),
        *timestamps(),
    )
    op.create_table(
        "register_reports",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "deal_id", uuid, sa.ForeignKey("register_deals.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("published_by", uuid, sa.ForeignKey("users.id")),
        sa.Column("candidate_count", sa.Integer(), nullable=False),
        sa.Column("document_count", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("deal_id", "version", name="uq_register_report_version"),
    )
    op.create_table(
        "register_payment_reversals",
        sa.Column("payment_intent_id", sa.String(255), primary_key=True),
        *timestamps(),
    )
    for table in ("register_documents", "register_folders", "register_reports"):
        op.create_index(f"ix_{table}_deal_id", table, ["deal_id"])
    if op.get_bind().dialect.name == "postgresql":
        # API-owned tables: no direct Supabase Data API/browser access. BFMS uses a
        # privileged server connection; users authenticate only through FastAPI.
        for table in (
            "register_deals",
            "register_documents",
            "register_folders",
            "register_reports",
            "register_payment_reversals",
        ):
            op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
            op.execute(f"REVOKE ALL ON TABLE {table} FROM PUBLIC")


def downgrade():
    for table in (
        "register_payment_reversals",
        "register_reports",
        "register_folders",
        "register_documents",
        "register_deals",
    ):
        op.drop_table(table)
