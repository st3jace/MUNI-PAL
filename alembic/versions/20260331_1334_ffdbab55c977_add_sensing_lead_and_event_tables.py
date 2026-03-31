"""add sensing lead and event tables

Revision ID: ffdbab55c977
Revises: i9j0k1l2m3n4
Create Date: 2026-03-31 13:34:14.982535+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "ffdbab55c977"
down_revision: Union[str, None] = "i9j0k1l2m3n4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sensing_leads",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("organization", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("sector", sa.String(length=50), nullable=False),
        sa.Column("deal_size_estimate", sa.Float(), nullable=True),
        sa.Column("state", sa.String(length=5), nullable=True),
        sa.Column("expected_rating", sa.String(length=10), nullable=True),
        sa.Column("referral_source", sa.String(length=255), nullable=True),
        sa.Column("funnel_stage", sa.String(length=50), nullable=False),
        sa.Column("market_intel_json", sa.Text(), nullable=True),
        sa.Column("benchmark_json", sa.Text(), nullable=True),
        sa.Column("readiness_json", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sensing_leads_email"), "sensing_leads", ["email"], unique=False
    )

    op.create_table(
        "sensing_events",
        sa.Column("id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("lead_id", sa.String(length=36), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("sector", sa.String(length=50), nullable=True),
        sa.Column("event_data", sa.Text(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_sensing_events_lead_id"),
        "sensing_events",
        ["lead_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_sensing_events_session_id"),
        "sensing_events",
        ["session_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_sensing_events_session_id"), table_name="sensing_events")
    op.drop_index(op.f("ix_sensing_events_lead_id"), table_name="sensing_events")
    op.drop_table("sensing_events")
    op.drop_index(op.f("ix_sensing_leads_email"), table_name="sensing_leads")
    op.drop_table("sensing_leads")
