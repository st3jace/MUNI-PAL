"""Initial database schema for Muni-Pal BFMS.

Revision ID: a1b2c3d4e5f6
Revises:
Create Date: 2026-01-27

Creates all core tables for the Bond Facility Management System:
- users: Authentication and access control
- playbooks: Bond-ready criteria configuration
- projects: Workspace for bond-eligible projects
- artifacts: User-uploaded documents
- chunks: Immutable evidence units from artifacts
- extraction_jobs: Async AI extraction work tracking
- extracted_facts: Core primitive - structured claims with provenance
- fact_chunks: Many-to-many linking facts to source chunks
- fact_revisions: Immutable audit log of fact changes
- evidence_links: Maps facts to checklist/readiness targets
- deliverable_packs: Generated advisor-ready output bundles
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # users
    # -------------------------------------------------------------------------
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('organization', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # -------------------------------------------------------------------------
    # playbooks
    # -------------------------------------------------------------------------
    op.create_table(
        'playbooks',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('bond_archetype', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('schema_paths', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('extractors', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('checklist_items', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('readiness_config', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # -------------------------------------------------------------------------
    # projects
    # -------------------------------------------------------------------------
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('issuer_name', sa.String(255), nullable=True),
        sa.Column('project_location', sa.String(500), nullable=True),
        sa.Column('target_bond_amount', sa.Float(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('playbook_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['playbook_id'], ['playbooks.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )

    # -------------------------------------------------------------------------
    # artifacts
    # -------------------------------------------------------------------------
    op.create_table(
        'artifacts',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=True),
        sa.Column('artifact_type', sa.String(20), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('file_size_bytes', sa.Integer(), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=False),
        sa.Column('is_processed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_artifacts_project_id', 'artifacts', ['project_id'])

    # -------------------------------------------------------------------------
    # chunks
    # -------------------------------------------------------------------------
    op.create_table(
        'chunks',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('chunk_type', sa.String(20), nullable=False),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('sheet_name', sa.String(100), nullable=True),
        sa.Column('section_title', sa.String(255), nullable=True),
        sa.Column('text_content', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('has_image', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_chunks_artifact_id', 'chunks', ['artifact_id'])

    # -------------------------------------------------------------------------
    # extraction_jobs
    # -------------------------------------------------------------------------
    op.create_table(
        'extraction_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('job_type', sa.String(100), nullable=False),
        sa.Column('target_schema_paths', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('artifact_ids', postgresql.JSON(), nullable=False),
        sa.Column('chunk_ids', postgresql.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='queued'),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('processed_chunks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('facts_extracted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_extraction_jobs_project_id', 'extraction_jobs', ['project_id'])
    op.create_index('ix_extraction_jobs_status', 'extraction_jobs', ['status'])

    # -------------------------------------------------------------------------
    # extracted_facts
    # -------------------------------------------------------------------------
    op.create_table(
        'extracted_facts',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('schema_path', sa.String(255), nullable=False),
        sa.Column('criticality', sa.String(20), nullable=False, server_default='secondary'),
        sa.Column('value', postgresql.JSON(), nullable=False),
        sa.Column('value_type', sa.String(50), nullable=False, server_default='string'),
        sa.Column('unit', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('confidence_rationale', sa.Text(), nullable=True),
        sa.Column('review_status', sa.String(20), nullable=False, server_default='pending'),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_note', sa.Text(), nullable=True),
        sa.Column('original_value', postgresql.JSON(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('extraction_job_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['extraction_job_id'], ['extraction_jobs.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_extracted_facts_project_id', 'extracted_facts', ['project_id'])
    op.create_index('ix_extracted_facts_schema_path', 'extracted_facts', ['schema_path'])
    op.create_index('ix_extracted_facts_review_status', 'extracted_facts', ['review_status'])

    # -------------------------------------------------------------------------
    # fact_chunks (many-to-many association)
    # -------------------------------------------------------------------------
    op.create_table(
        'fact_chunks',
        sa.Column('fact_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('chunk_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('excerpt', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['chunk_id'], ['chunks.id'], ),
        sa.ForeignKeyConstraint(['fact_id'], ['extracted_facts.id'], ),
        sa.PrimaryKeyConstraint('fact_id', 'chunk_id'),
    )

    # -------------------------------------------------------------------------
    # fact_revisions
    # -------------------------------------------------------------------------
    op.create_table(
        'fact_revisions',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('revision_number', sa.Integer(), nullable=False),
        sa.Column('previous_value', postgresql.JSON(), nullable=True),
        sa.Column('new_value', postgresql.JSON(), nullable=False),
        sa.Column('previous_status', sa.String(20), nullable=True),
        sa.Column('new_status', sa.String(20), nullable=False),
        sa.Column('changed_by_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('fact_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['changed_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['fact_id'], ['extracted_facts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_fact_revisions_fact_id', 'fact_revisions', ['fact_id'])

    # -------------------------------------------------------------------------
    # evidence_links
    # -------------------------------------------------------------------------
    op.create_table(
        'evidence_links',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('link_type', sa.String(50), nullable=False),
        sa.Column('target_id', sa.String(100), nullable=False),
        sa.Column('contribution_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('fact_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['fact_id'], ['extracted_facts.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_evidence_links_fact_id', 'evidence_links', ['fact_id'])

    # -------------------------------------------------------------------------
    # deliverable_packs
    # -------------------------------------------------------------------------
    op.create_table(
        'deliverable_packs',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('generated_for', sa.String(255), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('include_sections', postgresql.JSON(), nullable=False, server_default='[1,2,3,4,5,6,7,8,9]'),
        sa.Column('include_appendices', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sections', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('facts_included_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('readiness_score_at_generation', sa.Float(), nullable=True),
        sa.Column('warnings', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('pdf_storage_path', sa.String(500), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deliverable_packs_project_id', 'deliverable_packs', ['project_id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_index('ix_deliverable_packs_project_id', table_name='deliverable_packs')
    op.drop_table('deliverable_packs')

    op.drop_index('ix_evidence_links_fact_id', table_name='evidence_links')
    op.drop_table('evidence_links')

    op.drop_index('ix_fact_revisions_fact_id', table_name='fact_revisions')
    op.drop_table('fact_revisions')

    op.drop_table('fact_chunks')

    op.drop_index('ix_extracted_facts_review_status', table_name='extracted_facts')
    op.drop_index('ix_extracted_facts_schema_path', table_name='extracted_facts')
    op.drop_index('ix_extracted_facts_project_id', table_name='extracted_facts')
    op.drop_table('extracted_facts')

    op.drop_index('ix_extraction_jobs_status', table_name='extraction_jobs')
    op.drop_index('ix_extraction_jobs_project_id', table_name='extraction_jobs')
    op.drop_table('extraction_jobs')

    op.drop_index('ix_chunks_artifact_id', table_name='chunks')
    op.drop_table('chunks')

    op.drop_index('ix_artifacts_project_id', table_name='artifacts')
    op.drop_table('artifacts')

    op.drop_table('projects')
    op.drop_table('playbooks')

    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
