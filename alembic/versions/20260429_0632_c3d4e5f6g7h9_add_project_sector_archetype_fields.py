"""add project sector archetype fields

Revision ID: c3d4e5f6g7h9
Revises: b2c3d4e5f6g8
Create Date: 2026-04-29 06:32:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision: str = "c3d4e5f6g7h9"
down_revision: Union[str, None] = "b2c3d4e5f6g8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("sector", sa.String(length=100), nullable=True))
    op.add_column("projects", sa.Column("subsector", sa.String(length=150), nullable=True))
    op.add_column("projects", sa.Column("archetype_id", sa.String(length=150), nullable=True))
    op.add_column("projects", sa.Column("archetype_version", sa.String(length=20), nullable=True))
    op.create_index("ix_projects_sector", "projects", ["sector"], unique=False)
    op.create_index("ix_projects_subsector", "projects", ["subsector"], unique=False)
    op.create_index("ix_projects_archetype_id", "projects", ["archetype_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_projects_archetype_id", table_name="projects")
    op.drop_index("ix_projects_subsector", table_name="projects")
    op.drop_index("ix_projects_sector", table_name="projects")
    op.drop_column("projects", "archetype_version")
    op.drop_column("projects", "archetype_id")
    op.drop_column("projects", "subsector")
    op.drop_column("projects", "sector")
