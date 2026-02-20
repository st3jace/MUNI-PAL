"""Add manual fact support.

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-01-29

Adds support for manually-entered facts:
- source_type: Distinguishes 'extracted' vs 'manual' facts
- extraction_job_id: Made nullable for manual facts
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b8'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add source_type column with default 'extracted' for existing facts
    # Note: index=True in add_column creates the index automatically
    op.add_column(
        'extracted_facts',
        sa.Column(
            'source_type',
            sa.String(20),
            nullable=False,
            server_default='extracted',
        )
    )

    # Create index for source_type column (if not exists)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_extracted_facts_source_type
        ON extracted_facts (source_type)
    """)

    # Make extraction_job_id nullable (for manual facts)
    op.alter_column(
        'extracted_facts',
        'extraction_job_id',
        existing_type=sa.String(36),  # UUID stored as string
        nullable=True,
    )


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_extracted_facts_source_type', 'extracted_facts')

    # Make extraction_job_id required again
    # Note: This will fail if there are manual facts with NULL extraction_job_id
    op.alter_column(
        'extracted_facts',
        'extraction_job_id',
        existing_type=sa.String(36),
        nullable=False,
    )

    # Remove source_type column
    op.drop_column('extracted_facts', 'source_type')
