"""add lead email sequence fields

Revision ID: a1b2c3d4e5f7
Revises: ffdbab55c977
Create Date: 2026-04-09 18:00:00.000000+00:00
"""

from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, None] = "ffdbab55c977"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "sensing_leads",
        sa.Column("email_sequence_step", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sensing_leads",
        sa.Column("last_email_sent_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "sensing_leads",
        sa.Column("unsubscribed", sa.Boolean(), nullable=False, server_default="0"),
    )
    op.add_column(
        "sensing_leads",
        sa.Column("unsubscribe_token", sa.String(36), nullable=False, server_default=""),
    )
    # Backfill existing rows with unique tokens
    conn = op.get_bind()
    if conn.dialect.name == "postgresql":
        # A server-side backfill also works when exporting the complete migration
        # chain as SQL for a fresh hosted database. Offline connections cannot
        # fetch rows. PostgreSQL 13+ provides gen_random_uuid() in core.
        op.execute(sa.text("UPDATE sensing_leads SET unsubscribe_token = gen_random_uuid()::text WHERE unsubscribe_token = ''"))
    else:
        leads = conn.execute(sa.text("SELECT id FROM sensing_leads WHERE unsubscribe_token = ''")).fetchall()
        for row in leads:
            conn.execute(
                sa.text("UPDATE sensing_leads SET unsubscribe_token = :token WHERE id = :id"),
                {"token": str(uuid4()), "id": row[0]},
            )
    op.create_unique_constraint("uq_sensing_leads_unsubscribe_token", "sensing_leads", ["unsubscribe_token"])


def downgrade() -> None:
    op.drop_constraint("uq_sensing_leads_unsubscribe_token", "sensing_leads", type_="unique")
    op.drop_column("sensing_leads", "unsubscribe_token")
    op.drop_column("sensing_leads", "unsubscribed")
    op.drop_column("sensing_leads", "last_email_sent_at")
    op.drop_column("sensing_leads", "email_sequence_step")
