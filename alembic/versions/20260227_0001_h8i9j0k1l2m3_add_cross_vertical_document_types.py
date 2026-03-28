"""Add cross-vertical document types for PE/RE/project-finance workflows.

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2026-02-27

Extends deal_document_types with legal workflows identified in Sub-Agent 6
research artifacts (fund formation, deal execution, and sector-specific docs).
"""

from uuid import uuid4

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "h8i9j0k1l2m3"
down_revision = "g7h8i9j0k1l2"
branch_labels = None
depends_on = None


NEW_DOCUMENT_TYPES = [
    {
        "code": "limited_partnership_agreement",
        "display_name": "Limited Partnership Agreement (LPA)",
        "category": "negotiated",
        "deal_vertical": "pe",
        "description": "Fund constitutional document covering waterfall, governance, and LP rights.",
        "retention_policy": "indefinite",
        "requires_signature": True,
        "sort_order": 200,
    },
    {
        "code": "private_placement_memorandum",
        "display_name": "Private Placement Memorandum (PPM)",
        "category": "regulatory",
        "deal_vertical": "pe",
        "description": "Fund offering memorandum for institutional investors.",
        "retention_policy": "indefinite",
        "requires_signature": False,
        "sort_order": 201,
    },
    {
        "code": "side_letter",
        "display_name": "Investor Side Letter",
        "category": "negotiated",
        "deal_vertical": "pe",
        "description": "Investor-specific rights and reporting accommodations.",
        "retention_policy": "indefinite",
        "requires_signature": True,
        "sort_order": 202,
    },
    {
        "code": "subscription_agreement",
        "display_name": "Subscription Agreement",
        "category": "templated",
        "deal_vertical": "pe",
        "description": "Investor subscription package with suitability reps and commitment terms.",
        "retention_policy": "standard_6yr",
        "requires_signature": True,
        "sort_order": 203,
    },
    {
        "code": "purchase_and_sale_agreement",
        "display_name": "Purchase and Sale Agreement (SPA)",
        "category": "negotiated",
        "deal_vertical": "pe",
        "description": "Acquisition agreement with reps, warranties, indemnities, and closing mechanics.",
        "retention_policy": "standard_6yr",
        "requires_signature": True,
        "sort_order": 210,
    },
    {
        "code": "credit_agreement",
        "display_name": "Credit Agreement",
        "category": "negotiated",
        "deal_vertical": "pe",
        "description": "Senior or mezzanine debt facility agreement with covenant package.",
        "retention_policy": "bond_life_plus_3yr",
        "requires_signature": True,
        "sort_order": 211,
    },
    {
        "code": "operating_agreement",
        "display_name": "Operating Agreement",
        "category": "negotiated",
        "deal_vertical": "re",
        "description": "Entity governance and member economics agreement.",
        "retention_policy": "indefinite",
        "requires_signature": True,
        "sort_order": 212,
    },
    {
        "code": "tip_fee_agreement",
        "display_name": "Tip Fee Agreement",
        "category": "negotiated",
        "deal_vertical": "project_finance",
        "description": "Waste intake contract with volume and pricing escalation mechanics.",
        "retention_policy": "bond_life_plus_3yr",
        "requires_signature": True,
        "sort_order": 220,
    },
    {
        "code": "power_purchase_agreement",
        "display_name": "Power Purchase Agreement (PPA)",
        "category": "negotiated",
        "deal_vertical": "project_finance",
        "description": "Electricity offtake contract with pricing and availability terms.",
        "retention_policy": "bond_life_plus_3yr",
        "requires_signature": True,
        "sort_order": 221,
    },
    {
        "code": "interconnection_agreement",
        "display_name": "Interconnection Agreement",
        "category": "negotiated",
        "deal_vertical": "project_finance",
        "description": "Grid interconnection terms and operational responsibilities.",
        "retention_policy": "bond_life_plus_3yr",
        "requires_signature": True,
        "sort_order": 222,
    },
    {
        "code": "environmental_permit",
        "display_name": "Environmental Permit and Compliance Pack",
        "category": "regulatory",
        "deal_vertical": "project_finance",
        "description": "Environmental permits, approvals, and monitoring obligations.",
        "retention_policy": "indefinite",
        "requires_signature": False,
        "sort_order": 223,
    },
    {
        "code": "lease_agreement",
        "display_name": "Lease Agreement",
        "category": "negotiated",
        "deal_vertical": "re",
        "description": "Tenant lease terms governing rent, escalation, and remedies.",
        "retention_policy": "standard_6yr",
        "requires_signature": True,
        "sort_order": 230,
    },
    {
        "code": "property_management_agreement",
        "display_name": "Property Management Agreement",
        "category": "negotiated",
        "deal_vertical": "re",
        "description": "Third-party property operations and service-level agreement.",
        "retention_policy": "standard_6yr",
        "requires_signature": True,
        "sort_order": 231,
    },
]


def upgrade() -> None:
    deal_document_types = sa.table(
        "deal_document_types",
        sa.column("id", sa.String),
        sa.column("code", sa.String),
        sa.column("display_name", sa.String),
        sa.column("category", sa.String),
        sa.column("deal_vertical", sa.String),
        sa.column("description", sa.String),
        sa.column("retention_policy", sa.String),
        sa.column("requires_signature", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )

    for row in NEW_DOCUMENT_TYPES:
        op.execute(
            deal_document_types.insert().values(
                id=str(uuid4()),
                code=row["code"],
                display_name=row["display_name"],
                category=row["category"],
                deal_vertical=row["deal_vertical"],
                description=row["description"],
                retention_policy=row["retention_policy"],
                requires_signature=row["requires_signature"],
                sort_order=row["sort_order"],
            )
        )


def downgrade() -> None:
    for row in NEW_DOCUMENT_TYPES:
        op.execute(
            sa.text("DELETE FROM deal_document_types WHERE code = :code").bindparams(
                code=row["code"]
            )
        )
