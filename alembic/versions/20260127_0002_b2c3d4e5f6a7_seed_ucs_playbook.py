"""Seed UCS CAB+SLB playbook configuration.

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-01-27

Inserts the default UCS Waste-to-Energy CAB+SLB Revenue Bond playbook
with schema paths, extractors, checklist items, and readiness config.
"""

import json
from uuid import uuid4

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

# UCS Playbook ID (fixed for reproducibility)
UCS_PLAYBOOK_ID = "00000000-0000-0000-0000-000000000001"


def upgrade() -> None:
    # Get playbook data from the application module
    from munipal.services.playbook_data import UCS_PLAYBOOK_CONFIG

    # Insert the UCS playbook
    op.execute(
        sa.text("""
            INSERT INTO playbooks (
                id, name, version, description, bond_archetype,
                is_active, is_default,
                schema_paths, extractors, checklist_items, readiness_config,
                created_at, updated_at
            ) VALUES (
                :id, :name, :version, :description, :bond_archetype,
                :is_active, :is_default,
                :schema_paths, :extractors, :checklist_items, :readiness_config,
                NOW(), NOW()
            )
        """).bindparams(
            id=UCS_PLAYBOOK_ID,
            name=UCS_PLAYBOOK_CONFIG["name"],
            version=UCS_PLAYBOOK_CONFIG["version"],
            description=UCS_PLAYBOOK_CONFIG["description"],
            bond_archetype=UCS_PLAYBOOK_CONFIG["bond_archetype"],
            is_active=True,
            is_default=True,
            schema_paths=json.dumps(UCS_PLAYBOOK_CONFIG["schema_paths"]),
            extractors=json.dumps(UCS_PLAYBOOK_CONFIG["extractors"]),
            checklist_items=json.dumps(UCS_PLAYBOOK_CONFIG["checklist_items"]),
            readiness_config=json.dumps(UCS_PLAYBOOK_CONFIG["readiness_config"]),
        )
    )


def downgrade() -> None:
    # Remove the seeded playbook
    op.execute(
        sa.text("DELETE FROM playbooks WHERE id = :id").bindparams(
            id=UCS_PLAYBOOK_ID
        )
    )
