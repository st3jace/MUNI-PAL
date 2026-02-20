"""Add artifact extraction status tracking.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-01-27

Adds columns to track whether an artifact has had facts extracted:
- is_extracted: Boolean flag indicating extraction complete
- last_extraction_job_id: References the last extraction job
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c3d4e5f6a7b8'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add is_extracted column with default False
    op.add_column(
        'artifacts',
        sa.Column('is_extracted', sa.Boolean(), nullable=False, server_default='false')
    )

    # Add last_extraction_job_id column (nullable reference)
    op.add_column(
        'artifacts',
        sa.Column('last_extraction_job_id', postgresql.UUID(as_uuid=False), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('artifacts', 'last_extraction_job_id')
    op.drop_column('artifacts', 'is_extracted')
