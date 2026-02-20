"""Add extracted_facts canonicalization and archive lifecycle columns.

Revision ID: a7b8c9d0e1f2
Revises: f6a7b8c9d0e1
Create Date: 2026-02-19

This reconciles runtime schema with the V2 dedup/archive model:
- dedup fingerprints and duplicate classification
- canonical score and canonical flag
- lifecycle/archive state metadata
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "a7b8c9d0e1f2"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS fingerprint VARCHAR(128)
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS duplicate_classification VARCHAR(32) NOT NULL DEFAULT 'unique'
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS source_trust_score DOUBLE PRECISION NOT NULL DEFAULT 0.5
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS canonical_score DOUBLE PRECISION NOT NULL DEFAULT 0.0
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN NOT NULL DEFAULT false
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS lifecycle_state VARCHAR(20) NOT NULL DEFAULT 'active'
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archive_reason_code VARCHAR(64)
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archive_note TEXT
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archived_by UUID
        """
    )
    op.execute(
        """
        ALTER TABLE extracted_facts
        ADD COLUMN IF NOT EXISTS archived_at TIMESTAMPTZ
        """
    )

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_extracted_facts_archived_by_users'
            ) THEN
                ALTER TABLE extracted_facts
                ADD CONSTRAINT fk_extracted_facts_archived_by_users
                FOREIGN KEY (archived_by) REFERENCES users(id);
            END IF;
        END$$;
        """
    )

    op.execute(
        """
        UPDATE extracted_facts
        SET lifecycle_state = CASE
            WHEN review_status = 'rejected' THEN 'rejected'
            WHEN review_status = 'pending' THEN 'pending_review'
            ELSE 'active'
        END
        """
    )

    op.execute(
        """
        UPDATE extracted_facts
        SET duplicate_classification = 'unique'
        WHERE duplicate_classification IS NULL OR duplicate_classification = ''
        """
    )

    op.execute(
        """
        UPDATE extracted_facts
        SET source_trust_score = 0.5
        WHERE source_trust_score IS NULL
        """
    )

    op.execute(
        """
        UPDATE extracted_facts
        SET canonical_score = 0.0
        WHERE canonical_score IS NULL
        """
    )

    op.execute(
        """
        UPDATE extracted_facts
        SET is_canonical = false
        WHERE is_canonical IS NULL
        """
    )

    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_extracted_facts_fingerprint
        ON extracted_facts (fingerprint)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_extracted_facts_duplicate_classification
        ON extracted_facts (duplicate_classification)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_extracted_facts_is_canonical
        ON extracted_facts (is_canonical)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_extracted_facts_lifecycle_state
        ON extracted_facts (lifecycle_state)
        """
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_extracted_facts_lifecycle_state")
    op.execute("DROP INDEX IF EXISTS ix_extracted_facts_is_canonical")
    op.execute("DROP INDEX IF EXISTS ix_extracted_facts_duplicate_classification")
    op.execute("DROP INDEX IF EXISTS ix_extracted_facts_fingerprint")

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM pg_constraint
                WHERE conname = 'fk_extracted_facts_archived_by_users'
            ) THEN
                ALTER TABLE extracted_facts
                DROP CONSTRAINT fk_extracted_facts_archived_by_users;
            END IF;
        END$$;
        """
    )

    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS archived_at")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS archived_by")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS archive_note")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS archive_reason_code")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS lifecycle_state")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS is_canonical")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS canonical_score")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS source_trust_score")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS duplicate_classification")
    op.execute("ALTER TABLE extracted_facts DROP COLUMN IF EXISTS fingerprint")
