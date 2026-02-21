"""Add tenant_id to projects for Phase 8 tenant isolation foundation.

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-02-20
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "b8c9d0e1f2a3"
down_revision = "a7b8c9d0e1f2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "tenant_id",
            sa.String(length=100),
            nullable=False,
            server_default="default",
        ),
    )
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"], unique=False)

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                """
                UPDATE projects AS p
                SET tenant_id = COALESCE(NULLIF(TRIM(u.organization), ''), 'default')
                FROM users AS u
                WHERE p.owner_id = u.id
                """
            )
        )
    else:
        op.execute(
            sa.text(
                """
                UPDATE projects
                SET tenant_id = COALESCE(
                    (
                        SELECT NULLIF(TRIM(users.organization), '')
                        FROM users
                        WHERE users.id = projects.owner_id
                    ),
                    'default'
                )
                """
            )
        )

    op.alter_column("projects", "tenant_id", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_projects_tenant_id", table_name="projects")
    op.drop_column("projects", "tenant_id")
