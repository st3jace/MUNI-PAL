"""Add v2 deliverable models (WP7, WP8, bifurcated deliverables).

Revision ID: f6a7b8c9d0e1
Revises: d4e5f6a7b8c9
Create Date: 2026-01-31

Creates tables for BFMS v2 iteration:
- WP7 Disclosure Synthesis Engine:
  - disclosure_documents: Synthesized disclosure documents from extracted facts
  - disclosure_sections: Individual sections within disclosure documents
  - tbd_markers: Markers for missing information in disclosure sections

- WP8 Information Request System:
  - information_requests: Actionable requests generated from gap analysis
  - information_request_notes: Notes and updates on information requests

- Bifurcated Deliverables:
  - internal_readiness_reports: Operational control document for sponsor team
  - external_advisory_packages: Professional deliverable for municipal advisors
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f6a7b8c9d0e1'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # WP7: disclosure_documents
    # -------------------------------------------------------------------------
    op.create_table(
        'disclosure_documents',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('completeness_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('playbook_version', sa.String(50), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_disclosure_documents_project_id', 'disclosure_documents', ['project_id'])

    # -------------------------------------------------------------------------
    # WP7: disclosure_sections
    # -------------------------------------------------------------------------
    op.create_table(
        'disclosure_sections',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('section_id', sa.String(100), nullable=False),
        sa.Column('section_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('parent_section_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('content_md', sa.Text(), nullable=False, server_default=''),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('required_fact_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('present_fact_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('tbd_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('supporting_fact_ids', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('conditional_on', sa.String(255), nullable=True),
        sa.Column('is_rendered', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('disclosure_document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['disclosure_document_id'], ['disclosure_documents.id']),
        sa.ForeignKeyConstraint(['parent_section_id'], ['disclosure_sections.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_disclosure_sections_disclosure_document_id', 'disclosure_sections', ['disclosure_document_id'])

    # -------------------------------------------------------------------------
    # WP7: tbd_markers
    # -------------------------------------------------------------------------
    op.create_table(
        'tbd_markers',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('location', sa.String(255), nullable=False),
        sa.Column('missing_fact_paths', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default="'medium'"),
        sa.Column('is_resolved', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by_fact_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('disclosure_document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['disclosure_document_id'], ['disclosure_documents.id']),
        sa.ForeignKeyConstraint(['resolved_by_fact_id'], ['extracted_facts.id']),
        sa.ForeignKeyConstraint(['section_id'], ['disclosure_sections.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_tbd_markers_disclosure_document_id', 'tbd_markers', ['disclosure_document_id'])
    op.create_index('ix_tbd_markers_section_id', 'tbd_markers', ['section_id'])

    # -------------------------------------------------------------------------
    # WP8: information_requests
    # -------------------------------------------------------------------------
    op.create_table(
        'information_requests',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('request_code', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        # What's missing
        sa.Column('missing_fact_paths', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('current_evidence_state', sa.String(20), nullable=False, server_default="'none'"),
        sa.Column('gap_id', sa.String(100), nullable=True),
        # Why it matters (bond domain context)
        sa.Column('why_it_matters', sa.Text(), nullable=False),
        sa.Column('who_needs_it', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('when_needed', sa.String(255), nullable=True),
        sa.Column('consequences', sa.Text(), nullable=False),
        sa.Column('related_requirements', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('regulatory_reference', sa.String(255), nullable=True),
        # Affected items
        sa.Column('affected_checklist_items', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('affected_dimensions', postgresql.JSON(), nullable=False, server_default='[]'),
        # Guidance
        sa.Column('guidance_overview', sa.Text(), nullable=False),
        sa.Column('specific_questions', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('data_points_needed', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('suggested_approach', sa.Text(), nullable=True),
        sa.Column('common_pitfalls', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('time_estimate', sa.String(100), nullable=True),
        sa.Column('examples', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('acceptable_sources', postgresql.JSON(), nullable=False, server_default='[]'),
        # Quality requirements
        sa.Column('minimum_confidence', sa.Float(), nullable=False, server_default='0.80'),
        sa.Column('expected_format', sa.String(255), nullable=True),
        # Assignment
        sa.Column('priority', sa.String(20), nullable=False, server_default="'medium'"),
        sa.Column('suggested_owner', sa.String(255), nullable=True),
        sa.Column('target_date', sa.Date(), nullable=True),
        # Lifecycle
        sa.Column('status', sa.String(20), nullable=False, server_default="'open'"),
        sa.Column('acknowledged_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('acknowledged_by', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deferred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deferred_reason', sa.Text(), nullable=True),
        sa.Column('deferred_review_date', sa.Date(), nullable=True),
        # Resolution tracking
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('resolved_by_fact_ids', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('linked_artifact_id', postgresql.UUID(as_uuid=False), nullable=True),
        # Escalation
        sa.Column('escalation_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_escalated_at', sa.DateTime(timezone=True), nullable=True),
        # Foreign keys
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['acknowledged_by'], ['users.id']),
        sa.ForeignKeyConstraint(['linked_artifact_id'], ['artifacts.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_information_requests_project_id', 'information_requests', ['project_id'])
    op.create_index('ix_information_requests_status', 'information_requests', ['status'])
    op.create_index('ix_information_requests_request_code', 'information_requests', ['request_code'], unique=True)

    # -------------------------------------------------------------------------
    # WP8: information_request_notes
    # -------------------------------------------------------------------------
    op.create_table(
        'information_request_notes',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('note_type', sa.String(50), nullable=False, server_default="'update'"),
        sa.Column('request_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['request_id'], ['information_requests.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_information_request_notes_request_id', 'information_request_notes', ['request_id'])

    # -------------------------------------------------------------------------
    # Bifurcated Deliverables: internal_readiness_reports
    # -------------------------------------------------------------------------
    op.create_table(
        'internal_readiness_reports',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        # Content sections (JSON)
        sa.Column('executive_summary', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('readiness_dashboard', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('gap_analysis', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('information_requests_section', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('checklist_status', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('evidence_index', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('assumption_register', postgresql.JSON(), nullable=False, server_default='{}'),
        # Snapshot metrics
        sa.Column('overall_score', sa.Float(), nullable=True),
        sa.Column('dimension_scores', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('critical_gap_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_gap_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('open_request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overdue_request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('facts_count', sa.Integer(), nullable=False, server_default='0'),
        # Metadata
        sa.Column('playbook_version', sa.String(50), nullable=True),
        sa.Column('bfms_version', sa.String(50), nullable=True),
        sa.Column('pdf_storage_path', sa.String(500), nullable=True),
        sa.Column('md_storage_path', sa.String(500), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        # Foreign keys
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_internal_readiness_reports_project_id', 'internal_readiness_reports', ['project_id'])

    # -------------------------------------------------------------------------
    # Bifurcated Deliverables: external_advisory_packages
    # -------------------------------------------------------------------------
    op.create_table(
        'external_advisory_packages',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('generated_for', sa.String(255), nullable=False),
        sa.Column('is_complete', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_completed_at', sa.DateTime(timezone=True), nullable=True),
        # Content sections (JSON)
        sa.Column('cover_page', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('executive_summary', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('deal_overview', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('financial_tables', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('slb_brief', postgresql.JSON(), nullable=False, server_default='{}'),
        sa.Column('key_assumptions', postgresql.JSON(), nullable=False, server_default='[]'),
        sa.Column('disclaimer', sa.Text(), nullable=False, server_default="''"),
        # Quality metrics
        sa.Column('disclosure_completeness_score', sa.Float(), nullable=True),
        sa.Column('critical_tbd_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('high_tbd_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('readiness_score_at_generation', sa.Float(), nullable=True),
        sa.Column('ready_for_distribution', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('distribution_issues', postgresql.JSON(), nullable=False, server_default='[]'),
        # Metadata
        sa.Column('playbook_version', sa.String(50), nullable=True),
        sa.Column('bfms_version', sa.String(50), nullable=True),
        sa.Column('pdf_storage_path', sa.String(500), nullable=True),
        sa.Column('docx_storage_path', sa.String(500), nullable=True),
        sa.Column('md_storage_path', sa.String(500), nullable=True),
        sa.Column('celery_task_id', sa.String(255), nullable=True),
        # Foreign keys
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('disclosure_document_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['disclosure_document_id'], ['disclosure_documents.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_external_advisory_packages_project_id', 'external_advisory_packages', ['project_id'])


def downgrade() -> None:
    # Drop tables in reverse order of creation (respecting foreign keys)
    op.drop_index('ix_external_advisory_packages_project_id', table_name='external_advisory_packages')
    op.drop_table('external_advisory_packages')

    op.drop_index('ix_internal_readiness_reports_project_id', table_name='internal_readiness_reports')
    op.drop_table('internal_readiness_reports')

    op.drop_index('ix_information_request_notes_request_id', table_name='information_request_notes')
    op.drop_table('information_request_notes')

    op.drop_index('ix_information_requests_request_code', table_name='information_requests')
    op.drop_index('ix_information_requests_status', table_name='information_requests')
    op.drop_index('ix_information_requests_project_id', table_name='information_requests')
    op.drop_table('information_requests')

    op.drop_index('ix_tbd_markers_section_id', table_name='tbd_markers')
    op.drop_index('ix_tbd_markers_disclosure_document_id', table_name='tbd_markers')
    op.drop_table('tbd_markers')

    op.drop_index('ix_disclosure_sections_disclosure_document_id', table_name='disclosure_sections')
    op.drop_table('disclosure_sections')

    op.drop_index('ix_disclosure_documents_project_id', table_name='disclosure_documents')
    op.drop_table('disclosure_documents')
