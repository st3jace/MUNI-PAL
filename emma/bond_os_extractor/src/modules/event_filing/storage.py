"""Database tables and operations for event filing documents."""
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

from .schema import EventFilingRecord

logger = logging.getLogger("bond_os_extractor.modules.event_filing.storage")

module_metadata = MetaData()

event_filings = Table(
    "event_filings", module_metadata,
    Column("id", String(36), primary_key=True),
    Column("source_file", String(500), nullable=False),
    Column("source_hash", String(64), nullable=False, unique=True),
    Column("extraction_timestamp", DateTime),
    Column("doc_type", String(30), default="event_filing"),
    Column("completeness_score", Float),
    # Core fields
    Column("issuer_name", Text),
    Column("event_type", String(30)),
    Column("filing_date", String(20)),
    Column("event_date", String(20)),
    Column("event_category", String(50)),
    Column("event_summary", Text),
    Column("financial_impact", Text),
    Column("action_required", Integer),  # SQLite bool
    Column("affected_par_amount", String(50)),
    Column("next_steps", Text),
)

event_filing_cusips = Table(
    "event_filing_cusips", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_filing_id", String(36), nullable=False),
    Column("cusip", String(9), nullable=False),
)

event_filing_series = Table(
    "event_filing_series", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_filing_id", String(36), nullable=False),
    Column("series_name", Text, nullable=False),
)

event_filing_parties = Table(
    "event_filing_parties", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("event_filing_id", String(36), nullable=False),
    Column("party_name", Text, nullable=False),
)

Index("ix_ef_event_type", event_filings.c.event_type)
Index("ix_ef_event_category", event_filings.c.event_category)
Index("ix_ef_issuer", event_filings.c.issuer_name)
Index("ix_ef_source_hash", event_filings.c.source_hash)


def get_tables() -> list[Table]:
    return [event_filings, event_filing_cusips, event_filing_series, event_filing_parties]


def init_tables(engine: Engine) -> None:
    module_metadata.create_all(engine)
    logger.info("Event filing tables initialized")


def save_event_filing(engine: Engine, record: EventFilingRecord) -> str:
    """Save an EventFilingRecord to the database with upsert semantics."""
    doc_id = record.extraction_id

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM event_filings WHERE source_hash = :h"),
            {"h": record.source_hash},
        ).fetchone()
        if existing:
            old_id = existing[0]
            logger.info("Replacing existing event filing %s", old_id[:8])
            for tbl in ["event_filing_parties", "event_filing_series", "event_filing_cusips"]:
                conn.execute(text(f"DELETE FROM {tbl} WHERE event_filing_id = :id"), {"id": old_id})
            conn.execute(text("DELETE FROM event_filings WHERE id = :id"), {"id": old_id})

        conn.execute(event_filings.insert().values(
            id=doc_id,
            source_file=record.source_file,
            source_hash=record.source_hash,
            extraction_timestamp=record.extraction_timestamp,
            doc_type=record.doc_type,
            completeness_score=record.completeness_score,
            issuer_name=record.issuer_name,
            event_type=record.event_type,
            filing_date=str(record.filing_date) if record.filing_date else None,
            event_date=str(record.event_date) if record.event_date else None,
            event_category=record.event_category,
            event_summary=record.event_summary,
            financial_impact=record.financial_impact,
            action_required=int(record.action_required),
            affected_par_amount=record.affected_par_amount,
            next_steps=record.next_steps,
        ))

        for cusip in record.cusip_references:
            conn.execute(event_filing_cusips.insert().values(
                event_filing_id=doc_id, cusip=cusip,
            ))
        for series in record.affected_series:
            conn.execute(event_filing_series.insert().values(
                event_filing_id=doc_id, series_name=series,
            ))
        for party in record.related_parties:
            conn.execute(event_filing_parties.insert().values(
                event_filing_id=doc_id, party_name=party,
            ))

    logger.info("Saved event filing %s (%s)", doc_id[:8], record.source_file)
    return doc_id


def get_event_filing_stats(engine: Engine) -> dict[str, Any]:
    """Get summary statistics for event filings."""
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM event_filings")).scalar() or 0
        avg_completeness = conn.execute(
            text("SELECT AVG(completeness_score) FROM event_filings")
        ).scalar()

        by_type = {}
        rows = conn.execute(text(
            "SELECT event_type, COUNT(*) as cnt FROM event_filings "
            "GROUP BY event_type ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_type[row[0] or "unknown"] = row[1]

        by_category = {}
        rows = conn.execute(text(
            "SELECT event_category, COUNT(*) as cnt FROM event_filings "
            "GROUP BY event_category ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_category[row[0] or "unknown"] = row[1]

    return {
        "total": total,
        "avg_completeness": round(float(avg_completeness or 0), 3),
        "by_event_type": by_type,
        "by_category": by_category,
    }
