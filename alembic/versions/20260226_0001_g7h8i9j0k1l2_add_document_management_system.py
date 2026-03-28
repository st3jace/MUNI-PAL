"""Add Document Management System tables.

Revision ID: g7h8i9j0k1l2
Revises: f6a7b8c9d0e1
Create Date: 2026-02-26

Creates 12 tables for the Document Management System:
- deal_document_types: Extensible registry of document types per deal vertical
- document_templates: Jinja2 templates stored in DB for multi-tenant isolation
- template_clauses: Reusable clause library for contract assembly
- deal_documents: Core document lifecycle (draft → signed → filed → archived)
- deal_document_versions: Immutable version history with SHA-256 hashes
- document_reviews: Parallel review workflow
- document_signers: Dropbox Sign e-signature tracking
- document_audit_log: Immutable compliance audit trail
- virtual_data_rooms: VDR per project for controlled external sharing
- vdr_participants: External party access with NDA gates
- vdr_document_permissions: Per-document granular permissions
- vdr_activity_log: Page-level view analytics

Seeds deal_document_types with 25 municipal finance document types.
"""

from uuid import uuid4

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'g7h8i9j0k1l2'
down_revision = 'f6a7b8c9d0e1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # deal_document_types — extensible registry
    # -------------------------------------------------------------------------
    op.create_table(
        'deal_document_types',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('code', sa.String(100), nullable=False),
        sa.Column('display_name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(50), nullable=False),
        sa.Column('deal_vertical', sa.String(50), nullable=False, server_default='muni'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('default_workflow', sa.String(50), nullable=False, server_default='standard'),
        sa.Column('retention_policy', sa.String(50), nullable=False, server_default='standard_6yr'),
        sa.Column('requires_signature', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deal_document_types_code', 'deal_document_types', ['code'], unique=True)

    # -------------------------------------------------------------------------
    # document_templates — Jinja2 templates in DB
    # -------------------------------------------------------------------------
    op.create_table(
        'document_templates',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('document_type_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('template_body', sa.Text(), nullable=False),
        sa.Column('variable_schema', postgresql.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('tenant_id', sa.String(100), nullable=False, server_default='default'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_type_id'], ['deal_document_types.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_templates_type', 'document_templates', ['document_type_id'])
    op.create_index('ix_document_templates_tenant', 'document_templates', ['tenant_id'])

    # -------------------------------------------------------------------------
    # template_clauses — reusable clause library
    # -------------------------------------------------------------------------
    op.create_table(
        'template_clauses',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('content_json', postgresql.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('tenant_id', sa.String(100), nullable=False, server_default='default'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['template_id'], ['document_templates.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_template_clauses_tenant', 'template_clauses', ['tenant_id'])

    # -------------------------------------------------------------------------
    # deal_documents — core document with lifecycle state machine
    # -------------------------------------------------------------------------
    op.create_table(
        'deal_documents',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('document_number', sa.String(50), nullable=True),
        sa.Column('document_type_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='draft'),
        sa.Column('content_json', postgresql.JSON(), nullable=True),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('content_plaintext', sa.Text(), nullable=True),
        sa.Column('template_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('template_version', sa.Integer(), nullable=True),
        sa.Column('signature_request_id', sa.String(255), nullable=True),
        sa.Column('signature_status', sa.String(30), nullable=True),
        sa.Column('filed_to', sa.String(100), nullable=True),
        sa.Column('filed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('filing_reference', sa.String(255), nullable=True),
        sa.Column('retention_policy', sa.String(50), nullable=False, server_default='standard_6yr'),
        sa.Column('legal_hold', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('retention_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('artifact_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('assigned_to_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_type_id'], ['deal_document_types.id']),
        sa.ForeignKeyConstraint(['template_id'], ['document_templates.id']),
        sa.ForeignKeyConstraint(['artifact_id'], ['artifacts.id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_deal_documents_project', 'deal_documents', ['project_id'])
    op.create_index('ix_deal_documents_type', 'deal_documents', ['document_type_id'])

    # -------------------------------------------------------------------------
    # deal_document_versions — immutable version history
    # -------------------------------------------------------------------------
    op.create_table(
        'deal_document_versions',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('content_json', postgresql.JSON(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('change_summary', sa.Text(), nullable=True),
        sa.Column('snapshot_reason', sa.String(50), nullable=False, server_default='auto_save'),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('storage_path', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['deal_documents.id']),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id', 'version_number', name='uq_doc_version'),
    )
    op.create_index('ix_deal_document_versions_doc', 'deal_document_versions', ['document_id'])

    # -------------------------------------------------------------------------
    # document_reviews — parallel review workflow
    # -------------------------------------------------------------------------
    op.create_table(
        'document_reviews',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('reviewer_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('review_version', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['deal_documents.id']),
        sa.ForeignKeyConstraint(['reviewer_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_reviews_doc', 'document_reviews', ['document_id'])

    # -------------------------------------------------------------------------
    # document_signers — e-signature tracking (Dropbox Sign)
    # -------------------------------------------------------------------------
    op.create_table(
        'document_signers',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('signer_name', sa.String(255), nullable=False),
        sa.Column('signer_email', sa.String(255), nullable=False),
        sa.Column('signer_role', sa.String(100), nullable=False),
        sa.Column('signing_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(30), nullable=False, server_default='pending'),
        sa.Column('dropbox_sign_signer_id', sa.String(255), nullable=True),
        sa.Column('signed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('device_info', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['deal_documents.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_signers_doc', 'document_signers', ['document_id'])

    # -------------------------------------------------------------------------
    # document_audit_log — immutable compliance audit trail
    # -------------------------------------------------------------------------
    op.create_table(
        'document_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('actor_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('actor_email', sa.String(255), nullable=True),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('details', postgresql.JSON(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['deal_documents.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_document_audit_log_doc', 'document_audit_log', ['document_id'])
    op.create_index('ix_document_audit_log_ts', 'document_audit_log', ['timestamp'])

    # -------------------------------------------------------------------------
    # virtual_data_rooms — VDR per project
    # -------------------------------------------------------------------------
    op.create_table(
        'virtual_data_rooms',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('require_nda', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('nda_template_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('watermark_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('default_access_expiry_days', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('settings', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id']),
        sa.ForeignKeyConstraint(['nda_template_id'], ['document_templates.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', name='uq_vdr_project'),
    )

    # -------------------------------------------------------------------------
    # vdr_participants — external party access
    # -------------------------------------------------------------------------
    op.create_table(
        'vdr_participants',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('data_room_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('organization', sa.String(255), nullable=True),
        sa.Column('role', sa.String(30), nullable=False, server_default='viewer'),
        sa.Column('access_token', sa.String(255), nullable=False),
        sa.Column('nda_accepted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('nda_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('access_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['data_room_id'], ['virtual_data_rooms.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('access_token', name='uq_vdr_access_token'),
        sa.UniqueConstraint('data_room_id', 'email', name='uq_vdr_participant_email'),
    )
    op.create_index('ix_vdr_participants_room', 'vdr_participants', ['data_room_id'])

    # -------------------------------------------------------------------------
    # vdr_document_permissions — per-document granular permissions
    # -------------------------------------------------------------------------
    op.create_table(
        'vdr_document_permissions',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('data_room_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=False), nullable=True),
        sa.Column('can_view', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('can_download', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('can_print', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['data_room_id'], ['virtual_data_rooms.id']),
        sa.ForeignKeyConstraint(['document_id'], ['deal_documents.id']),
        sa.ForeignKeyConstraint(['participant_id'], ['vdr_participants.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vdr_doc_perms_room', 'vdr_document_permissions', ['data_room_id'])
    op.create_index('ix_vdr_doc_perms_doc', 'vdr_document_permissions', ['document_id'])

    # -------------------------------------------------------------------------
    # vdr_activity_log — page-level view analytics
    # -------------------------------------------------------------------------
    op.create_table(
        'vdr_activity_log',
        sa.Column('id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('data_room_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('participant_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column('action', sa.String(30), nullable=False),
        sa.Column('page_number', sa.Integer(), nullable=True),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['data_room_id'], ['virtual_data_rooms.id']),
        sa.ForeignKeyConstraint(['participant_id'], ['vdr_participants.id']),
        sa.ForeignKeyConstraint(['document_id'], ['deal_documents.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_vdr_activity_room', 'vdr_activity_log', ['data_room_id'])
    op.create_index('ix_vdr_activity_participant', 'vdr_activity_log', ['participant_id'])
    op.create_index('ix_vdr_activity_doc', 'vdr_activity_log', ['document_id'])
    op.create_index('ix_vdr_activity_ts', 'vdr_activity_log', ['timestamp'])

    # -------------------------------------------------------------------------
    # Seed: Municipal Finance document types (25 types)
    # -------------------------------------------------------------------------
    deal_document_types = sa.table(
        'deal_document_types',
        sa.column('id', sa.String),
        sa.column('code', sa.String),
        sa.column('display_name', sa.String),
        sa.column('category', sa.String),
        sa.column('deal_vertical', sa.String),
        sa.column('description', sa.String),
        sa.column('retention_policy', sa.String),
        sa.column('requires_signature', sa.Boolean),
        sa.column('sort_order', sa.Integer),
    )

    seed_data = [
        # --- Offering & Disclosure ---
        {'code': 'preliminary_official_statement', 'display_name': 'Preliminary Official Statement (POS)', 'category': 'regulatory', 'description': 'Preliminary disclosure document for bond offering. Filed to EMMA per MSRB G-32.', 'retention_policy': 'indefinite', 'requires_signature': False, 'sort_order': 1},
        {'code': 'official_statement', 'display_name': 'Official Statement (OS)', 'category': 'regulatory', 'description': 'Final disclosure document. Must be filed to EMMA within 1 business day of closing.', 'retention_policy': 'indefinite', 'requires_signature': False, 'sort_order': 2},
        {'code': 'continuing_disclosure_agreement', 'display_name': 'Continuing Disclosure Agreement', 'category': 'templated', 'description': 'SEC Rule 15c2-12 annual reporting and material event notice commitment.', 'retention_policy': 'indefinite', 'requires_signature': True, 'sort_order': 3},
        # --- Core Legal ---
        {'code': 'trust_indenture', 'display_name': 'Trust Indenture / Bond Resolution', 'category': 'negotiated', 'description': 'Core contract between issuer and trustee. Defines covenants, flow of funds, events of default.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 10},
        {'code': 'loan_agreement', 'display_name': 'Loan Agreement', 'category': 'negotiated', 'description': 'Direct placement loan agreement between issuer and lender/bank.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 11},
        {'code': 'bond_purchase_agreement', 'display_name': 'Bond Purchase Agreement', 'category': 'negotiated', 'description': 'Agreement between issuer and underwriter for purchase of bonds.', 'retention_policy': 'standard_6yr', 'requires_signature': True, 'sort_order': 12},
        # --- Credit Enhancement ---
        {'code': 'letter_of_credit', 'display_name': 'Letter of Credit', 'category': 'negotiated', 'description': 'Bank LOC providing credit enhancement for bonds.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 20},
        {'code': 'bond_insurance_policy', 'display_name': 'Bond Insurance Policy', 'category': 'templated', 'description': 'Insurance policy providing credit enhancement (from AGM, BAM, etc.).', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': False, 'sort_order': 21},
        {'code': 'standby_bond_purchase_agreement', 'display_name': 'Standby Bond Purchase Agreement', 'category': 'negotiated', 'description': 'Liquidity facility for variable rate demand bonds.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 22},
        # --- Remarketing & Derivatives ---
        {'code': 'remarketing_agreement', 'display_name': 'Remarketing Agreement', 'category': 'negotiated', 'description': 'Agreement with remarketing agent for variable rate bonds.', 'retention_policy': 'standard_6yr', 'requires_signature': True, 'sort_order': 30},
        {'code': 'isda_master_agreement', 'display_name': 'ISDA Master Agreement + Schedule', 'category': 'negotiated', 'description': 'Interest rate swap documentation under ISDA standards.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 31},
        # --- Tax & Compliance ---
        {'code': 'tax_opinion', 'display_name': 'Tax Opinion / Bond Counsel Opinion', 'category': 'professional_report', 'description': 'Legal opinion on tax-exempt status. Required for tax-exempt bonds.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': False, 'sort_order': 40},
        {'code': 'tax_certificate', 'display_name': 'Tax Compliance Certificate (IRS 8038)', 'category': 'templated', 'description': 'IRS Form 8038 filing and post-issuance tax compliance procedures.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 41},
        {'code': 'tax_regulatory_agreement', 'display_name': 'Tax Regulatory Agreement', 'category': 'negotiated', 'description': 'Agreement governing tax-exempt bond compliance requirements.', 'retention_policy': 'bond_life_plus_3yr', 'requires_signature': True, 'sort_order': 42},
        # --- Project Reports ---
        {'code': 'feasibility_study', 'display_name': 'Feasibility Study', 'category': 'professional_report', 'description': 'Independent feasibility analysis of revenue projections and project viability.', 'retention_policy': 'standard_6yr', 'requires_signature': False, 'sort_order': 50},
        {'code': 'engineering_report', 'display_name': 'Engineering Report', 'category': 'professional_report', 'description': 'Technical engineering assessment of project infrastructure.', 'retention_policy': 'standard_6yr', 'requires_signature': False, 'sort_order': 51},
        {'code': 'environmental_assessment', 'display_name': 'Environmental Assessment (Phase I/II)', 'category': 'professional_report', 'description': 'ASTM E1527 Phase I ESA or Phase II environmental site assessment.', 'retention_policy': 'standard_6yr', 'requires_signature': False, 'sort_order': 52},
        {'code': 'appraisal', 'display_name': 'Appraisal', 'category': 'professional_report', 'description': 'USPAP-compliant property or asset valuation.', 'retention_policy': 'standard_6yr', 'requires_signature': False, 'sort_order': 53},
        # --- Closing & Administrative ---
        {'code': 'closing_certificate', 'display_name': 'Closing Certificate', 'category': 'templated', 'description': 'Officer certificate confirming closing conditions met.', 'retention_policy': 'standard_6yr', 'requires_signature': True, 'sort_order': 60},
        {'code': 'board_resolution', 'display_name': 'Board Resolution / Authorizing Ordinance', 'category': 'templated', 'description': 'Governing body authorization for bond issuance.', 'retention_policy': 'indefinite', 'requires_signature': True, 'sort_order': 61},
        {'code': 'closing_checklist', 'display_name': 'Closing Checklist', 'category': 'templated', 'description': 'Master checklist of all closing deliverables and responsible parties.', 'retention_policy': 'standard_6yr', 'requires_signature': False, 'sort_order': 62},
        {'code': 'due_diligence_request_list', 'display_name': 'Due Diligence Request List', 'category': 'templated', 'description': 'Information request list from underwriter or bond counsel.', 'retention_policy': 'standard_6yr', 'requires_signature': False, 'sort_order': 63},
        # --- Cross-Deal Universal ---
        {'code': 'nda', 'display_name': 'Non-Disclosure Agreement', 'category': 'templated', 'description': 'Confidentiality agreement between deal parties.', 'retention_policy': 'standard_6yr', 'requires_signature': True, 'sort_order': 70},
        {'code': 'loi_term_sheet', 'display_name': 'Letter of Intent / Term Sheet', 'category': 'negotiated', 'description': 'Non-binding outline of key transaction terms.', 'retention_policy': 'standard_6yr', 'requires_signature': True, 'sort_order': 71},
        {'code': 'material_event_notice', 'display_name': 'Material Event Notice', 'category': 'regulatory', 'description': 'SEC Rule 15c2-12 material event filing to EMMA.', 'retention_policy': 'indefinite', 'requires_signature': False, 'sort_order': 80},
    ]

    for row in seed_data:
        op.execute(
            deal_document_types.insert().values(
                id=str(uuid4()),
                code=row['code'],
                display_name=row['display_name'],
                category=row['category'],
                deal_vertical='muni',
                description=row['description'],
                retention_policy=row['retention_policy'],
                requires_signature=row['requires_signature'],
                sort_order=row['sort_order'],
            )
        )


def downgrade() -> None:
    op.drop_table('vdr_activity_log')
    op.drop_table('vdr_document_permissions')
    op.drop_table('vdr_participants')
    op.drop_table('virtual_data_rooms')
    op.drop_table('document_audit_log')
    op.drop_table('document_signers')
    op.drop_table('document_reviews')
    op.drop_table('deal_document_versions')
    op.drop_table('deal_documents')
    op.drop_table('template_clauses')
    op.drop_table('document_templates')
    op.drop_table('deal_document_types')
