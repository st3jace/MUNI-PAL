"""Add durable Ask conversations and messages.

Revision ID: d4e5f6g7h8i0
Revises: c3d4e5f6g7h9
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "d4e5f6g7h8i0"
down_revision = "c3d4e5f6g7h9"
branch_labels = None
depends_on = None


def timestamps():
    return [
        sa.Column(name, sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now())
        for name in ("created_at", "updated_at")
    ]


def upgrade():
    uuid = sa.String(36).with_variant(postgresql.UUID(as_uuid=False), "postgresql")
    op.create_table(
        "ask_conversations",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("owner_id", uuid, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", uuid, sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_id", uuid, sa.ForeignKey("artifacts.id", ondelete="CASCADE")),
        sa.Column("title", sa.String(120), nullable=False),
        sa.Column("next_sequence", sa.Integer(), nullable=False, server_default="1"),
        *timestamps(),
    )
    op.create_index("ix_ask_conversations_owner_id", "ask_conversations", ["owner_id"])
    op.create_index("ix_ask_conversations_project_id", "ask_conversations", ["project_id"])
    op.create_table(
        "ask_messages",
        sa.Column("id", uuid, primary_key=True),
        sa.Column(
            "conversation_id",
            uuid,
            sa.ForeignKey("ask_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("kind", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("citations", sa.JSON(), nullable=False),
        *timestamps(),
        sa.UniqueConstraint("conversation_id", "sequence", name="uq_ask_message_sequence"),
    )
    op.create_index("ix_ask_messages_conversation_id", "ask_messages", ["conversation_id"])


def downgrade():
    op.drop_table("ask_messages")
    op.drop_table("ask_conversations")
