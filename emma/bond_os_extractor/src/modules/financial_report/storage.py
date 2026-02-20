"""Database tables and operations for financial report documents."""
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

from .schema import FinancialReportRecord

logger = logging.getLogger("bond_os_extractor.modules.financial_report.storage")

module_metadata = MetaData()

financial_reports = Table(
    "financial_reports", module_metadata,
    Column("id", String(36), primary_key=True),
    Column("source_file", String(500), nullable=False),
    Column("source_hash", String(64), nullable=False, unique=True),
    Column("extraction_timestamp", DateTime),
    Column("doc_type", String(30), default="financial_report"),
    Column("completeness_score", Float),
    # Identity
    Column("issuer_name", Text),
    Column("obligor_name", Text),
    # Report metadata
    Column("report_type", String(20)),
    Column("fiscal_period_end", String(20)),
    Column("fiscal_year", Integer),
    # Financials
    Column("total_revenue", Float),
    Column("total_expenses", Float),
    Column("operating_income", Float),
    Column("net_income", Float),
    Column("total_assets", Float),
    Column("total_liabilities", Float),
    Column("total_equity", Float),
    Column("cash_and_equivalents", Float),
    # Bond metrics
    Column("debt_service_coverage_ratio", Float),
    Column("days_cash_on_hand", Integer),
    Column("total_debt_outstanding", Float),
    Column("annual_debt_service", Float),
    # Audit
    Column("auditor_name", Text),
    Column("audit_opinion", String(20)),
    # Flexible metrics stored as JSON text
    Column("key_metrics_json", Text),
)

financial_report_cusips = Table(
    "financial_report_cusips", module_metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("financial_report_id", String(36), nullable=False),
    Column("cusip", String(9), nullable=False),
)

Index("ix_fr_issuer", financial_reports.c.issuer_name)
Index("ix_fr_report_type", financial_reports.c.report_type)
Index("ix_fr_fiscal_year", financial_reports.c.fiscal_year)
Index("ix_fr_source_hash", financial_reports.c.source_hash)


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    return float(val)


def get_tables() -> list[Table]:
    return [financial_reports, financial_report_cusips]


def init_tables(engine: Engine) -> None:
    module_metadata.create_all(engine)
    logger.info("Financial report tables initialized")


def save_financial_report(engine: Engine, record: FinancialReportRecord) -> str:
    """Save a FinancialReportRecord to the database with upsert semantics."""
    import json
    doc_id = record.extraction_id

    with engine.begin() as conn:
        existing = conn.execute(
            text("SELECT id FROM financial_reports WHERE source_hash = :h"),
            {"h": record.source_hash},
        ).fetchone()
        if existing:
            old_id = existing[0]
            logger.info("Replacing existing financial report %s", old_id[:8])
            conn.execute(text("DELETE FROM financial_report_cusips WHERE financial_report_id = :id"), {"id": old_id})
            conn.execute(text("DELETE FROM financial_reports WHERE id = :id"), {"id": old_id})

        conn.execute(financial_reports.insert().values(
            id=doc_id,
            source_file=record.source_file,
            source_hash=record.source_hash,
            extraction_timestamp=record.extraction_timestamp,
            doc_type=record.doc_type,
            completeness_score=record.completeness_score,
            issuer_name=record.issuer_name,
            obligor_name=record.obligor_name,
            report_type=record.report_type,
            fiscal_period_end=str(record.fiscal_period_end) if record.fiscal_period_end else None,
            fiscal_year=record.fiscal_year,
            total_revenue=_float_or_none(record.total_revenue),
            total_expenses=_float_or_none(record.total_expenses),
            operating_income=_float_or_none(record.operating_income),
            net_income=_float_or_none(record.net_income),
            total_assets=_float_or_none(record.total_assets),
            total_liabilities=_float_or_none(record.total_liabilities),
            total_equity=_float_or_none(record.total_equity),
            cash_and_equivalents=_float_or_none(record.cash_and_equivalents),
            debt_service_coverage_ratio=_float_or_none(record.debt_service_coverage_ratio),
            days_cash_on_hand=record.days_cash_on_hand,
            total_debt_outstanding=_float_or_none(record.total_debt_outstanding),
            annual_debt_service=_float_or_none(record.annual_debt_service),
            auditor_name=record.auditor_name,
            audit_opinion=record.audit_opinion,
            key_metrics_json=json.dumps(record.key_metrics) if record.key_metrics else None,
        ))

        for cusip in record.cusip_references:
            conn.execute(financial_report_cusips.insert().values(
                financial_report_id=doc_id, cusip=cusip,
            ))

    logger.info("Saved financial report %s (%s)", doc_id[:8], record.source_file)
    return doc_id


def get_financial_report_stats(engine: Engine) -> dict[str, Any]:
    """Get summary statistics for financial reports."""
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM financial_reports")).scalar() or 0
        avg_completeness = conn.execute(
            text("SELECT AVG(completeness_score) FROM financial_reports")
        ).scalar()

        by_type = {}
        rows = conn.execute(text(
            "SELECT report_type, COUNT(*) as cnt FROM financial_reports "
            "GROUP BY report_type ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_type[row[0] or "unknown"] = row[1]

        avg_dscr = conn.execute(
            text("SELECT AVG(debt_service_coverage_ratio) FROM financial_reports "
                 "WHERE debt_service_coverage_ratio IS NOT NULL")
        ).scalar()

    return {
        "total": total,
        "avg_completeness": round(float(avg_completeness or 0), 3),
        "by_report_type": by_type,
        "avg_dscr": round(float(avg_dscr or 0), 3) if avg_dscr else None,
    }
