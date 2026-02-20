"""Database tables and operations for rating action documents."""
from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    text,
)
from sqlalchemy.engine import Engine

from .schema import RatingActionRecord

logger = logging.getLogger("bond_os_extractor.modules.rating_action.storage")

# Use a separate MetaData so module tables don't collide with OS tables
module_metadata = MetaData()

rating_actions = Table(
    "rating_actions", module_metadata,
    Column("id", String(36), primary_key=True),
    Column("source_file", String(500), nullable=False),
    Column("source_hash", String(64), nullable=False, unique=True),
    Column("extraction_timestamp", DateTime),
    Column("doc_type", String(30), default="rating_action"),
    Column("completeness_score", Float),
    # Core fields
    Column("issuer_name", Text),
    Column("obligor_name", Text),
    Column("agency", String(20)),
    Column("action_type", String(30)),
    Column("previous_rating", String(20)),
    Column("new_rating", String(20)),
    Column("previous_outlook", String(20)),
    Column("new_outlook", String(20)),
    Column("action_date", String(20)),
    Column("effective_date", String(20)),
    Column("bond_type", String(50)),
    Column("rationale_summary", Text),
    Column("sector", String(50)),
)

rating_action_factors = Table(
    "rating_action_factors", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rating_action_id", String(36), nullable=False),
    Column("factor_type", String(20), nullable=False),  # key_factor | strength | challenge
    Column("text", Text, nullable=False),
)

rating_action_cusips = Table(
    "rating_action_cusips", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rating_action_id", String(36), nullable=False),
    Column("cusip", String(9), nullable=False),
)

rating_action_series = Table(
    "rating_action_series", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("rating_action_id", String(36), nullable=False),
    Column("series_name", Text, nullable=False),
)

# Indexes
Index("ix_ra_agency", rating_actions.c.agency)
Index("ix_ra_action_type", rating_actions.c.action_type)
Index("ix_ra_issuer", rating_actions.c.issuer_name)
Index("ix_ra_source_hash", rating_actions.c.source_hash)
Index("ix_ra_action_date", rating_actions.c.action_date)


def get_tables() -> list[Table]:
    """Return all SQLAlchemy tables for this module."""
    return [rating_actions, rating_action_factors, rating_action_cusips, rating_action_series]


def init_tables(engine: Engine) -> None:
    """Create rating action tables if they don't exist."""
    module_metadata.create_all(engine)
    logger.info("Rating action tables initialized")


def save_rating_action(engine: Engine, record: RatingActionRecord) -> str:
    """Save a RatingActionRecord to the database. Returns the extraction ID.

    Uses upsert semantics: if a record with the same source_hash exists,
    it is replaced.
    """
    doc_id = record.extraction_id

    with engine.begin() as conn:
        # Check for existing record with same hash
        existing = conn.execute(
            text("SELECT id FROM rating_actions WHERE source_hash = :h"),
            {"h": record.source_hash},
        ).fetchone()
        if existing:
            old_id = existing[0]
            logger.info("Replacing existing rating action %s", old_id[:8])
            for tbl_name in ["rating_action_series", "rating_action_cusips", "rating_action_factors"]:
                conn.execute(
                    text(f"DELETE FROM {tbl_name} WHERE rating_action_id = :id"),
                    {"id": old_id},
                )
            conn.execute(
                text("DELETE FROM rating_actions WHERE id = :id"),
                {"id": old_id},
            )

        # Main record
        conn.execute(rating_actions.insert().values(
            id=doc_id,
            source_file=record.source_file,
            source_hash=record.source_hash,
            extraction_timestamp=record.extraction_timestamp,
            doc_type=record.doc_type,
            completeness_score=record.completeness_score,
            issuer_name=record.issuer_name,
            obligor_name=record.obligor_name,
            agency=record.agency,
            action_type=record.action_type,
            previous_rating=record.previous_rating,
            new_rating=record.new_rating,
            previous_outlook=record.previous_outlook,
            new_outlook=record.new_outlook,
            action_date=str(record.action_date) if record.action_date else None,
            effective_date=str(record.effective_date) if record.effective_date else None,
            bond_type=record.bond_type,
            rationale_summary=record.rationale_summary,
            sector=record.sector,
        ))

        # Key factors, strengths, challenges
        for factor in record.key_factors:
            conn.execute(rating_action_factors.insert().values(
                rating_action_id=doc_id,
                factor_type="key_factor",
                text=factor,
            ))
        for strength in record.credit_strengths:
            conn.execute(rating_action_factors.insert().values(
                rating_action_id=doc_id,
                factor_type="strength",
                text=strength,
            ))
        for challenge in record.credit_challenges:
            conn.execute(rating_action_factors.insert().values(
                rating_action_id=doc_id,
                factor_type="challenge",
                text=challenge,
            ))

        # CUSIPs
        for cusip in record.cusip_references:
            conn.execute(rating_action_cusips.insert().values(
                rating_action_id=doc_id,
                cusip=cusip,
            ))

        # Affected series
        for series in record.bond_series_affected:
            conn.execute(rating_action_series.insert().values(
                rating_action_id=doc_id,
                series_name=series,
            ))

    logger.info("Saved rating action %s (%s)", doc_id[:8], record.source_file)
    return doc_id


def get_rating_action_stats(engine: Engine) -> dict[str, Any]:
    """Get summary statistics for rating actions."""
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM rating_actions")).scalar() or 0
        avg_completeness = conn.execute(
            text("SELECT AVG(completeness_score) FROM rating_actions")
        ).scalar()

        by_agency = {}
        rows = conn.execute(text(
            "SELECT agency, COUNT(*) as cnt FROM rating_actions "
            "GROUP BY agency ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_agency[row[0] or "unknown"] = row[1]

        by_action = {}
        rows = conn.execute(text(
            "SELECT action_type, COUNT(*) as cnt FROM rating_actions "
            "GROUP BY action_type ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_action[row[0] or "unknown"] = row[1]

    return {
        "total": total,
        "avg_completeness": round(float(avg_completeness or 0), 3),
        "by_agency": by_agency,
        "by_action_type": by_action,
    }


def query_rating_actions(
    engine: Engine,
    agency: str | None = None,
    action_type: str | None = None,
    issuer: str | None = None,
) -> list[dict[str, Any]]:
    """Query rating actions with optional filters."""
    clauses = ["1=1"]
    if agency:
        clauses.append(f"agency = '{agency}'")
    if action_type:
        clauses.append(f"action_type = '{action_type}'")
    if issuer:
        clauses.append(f"issuer_name LIKE '%{issuer}%'")

    where = " AND ".join(clauses)
    query = f"""
        SELECT id, source_file, completeness_score, issuer_name, agency,
               action_type, previous_rating, new_rating, new_outlook,
               action_date, sector
        FROM rating_actions
        WHERE {where}
        ORDER BY action_date DESC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()

    return [
        {
            "id": r[0],
            "source_file": r[1],
            "completeness": r[2],
            "issuer_name": r[3],
            "agency": r[4],
            "action_type": r[5],
            "previous_rating": r[6],
            "new_rating": r[7],
            "new_outlook": r[8],
            "action_date": r[9],
            "sector": r[10],
        }
        for r in rows
    ]
