from __future__ import annotations

import logging
from pathlib import Path
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
    UniqueConstraint,
    create_engine,
    text,
)
from sqlalchemy.engine import Engine

from ..config import get_settings

logger = logging.getLogger("bond_os_extractor.storage")

metadata = MetaData()

# ---------------------------------------------------------------------------
# Table definitions
# ---------------------------------------------------------------------------

documents = Table(
    "documents", metadata,
    Column("id", String(36), primary_key=True),
    Column("source_file", String(500), nullable=False),
    Column("source_hash", String(64), nullable=False, unique=True),
    Column("extraction_method", String(50)),
    Column("extraction_timestamp", DateTime),
    Column("extraction_version", String(20)),
    Column("completeness_score", Float),
    Column("page_count", Integer),
    Column("primary_classification", String(100)),
    Column("secondary_classification", String(200)),
    Column("tertiary_classification", String(100)),
    Column("size_classification", String(50)),
)

deal_identities = Table(
    "deal_identities", metadata,
    Column("document_id", String(36), primary_key=True),
    Column("cusip_base", String(6)),
    Column("document_type", String(20)),
    Column("dated_date", String(20)),
    Column("sale_date", String(20)),
    Column("delivery_date", String(20)),
    Column("issuer_name", Text),
    Column("issuer_type", String(50)),
    Column("issuer_state", String(2)),
    Column("issuer_county", String(100)),
    Column("borrower_name", Text),
    Column("trustee_name", Text),
    Column("bond_counsel", Text),
    Column("municipal_advisor", Text),
    Column("series_name", String(100)),
    Column("official_title", Text),
)

deal_structures = Table(
    "deal_structures", metadata,
    Column("document_id", String(36), primary_key=True),
    Column("par_amount", Float),
    Column("denomination", Float),
    Column("bond_type", String(50)),
    Column("tax_status", String(50)),
    Column("interest_type", String(50)),
    Column("cab_enabled", Integer),  # SQLite bool
    Column("slb_enabled", Integer),
    Column("green_bond", Integer),
    Column("maturity_type", String(50)),
    Column("final_maturity_date", String(20)),
    Column("optional_redemption_date", String(20)),
    Column("optional_redemption_price", Float),
    Column("credit_enhancement_type", String(50)),
    Column("credit_enhancer_name", Text),
)

maturity_rows = Table(
    "maturity_rows", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String(36), nullable=False),
    Column("maturity_date", String(20)),
    Column("par_amount", Float),
    Column("coupon_rate", Float),
    Column("yield_to_maturity", Float),
    Column("price", Float),
    Column("cusip", String(9)),
    Column("serial_or_term", String(10)),
)

debt_service_rows = Table(
    "debt_service_rows", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String(36), nullable=False),
    Column("fiscal_year", Integer),
    Column("principal", Float),
    Column("interest", Float),
    Column("total", Float),
    Column("outstanding_balance", Float),
)

security_packages = Table(
    "security_packages", metadata,
    Column("document_id", String(36), primary_key=True),
    Column("pledge_type", String(50)),
    Column("pledged_revenues_description", Text),
    Column("lien_position", String(20)),
    Column("real_property_mortgage", Integer),
    Column("equipment_security_interest", Integer),
    Column("min_coverage_ratio", Float),
    Column("additional_bonds_hist_coverage", Float),
    Column("dsrf_type", String(50)),
    Column("dsrf_amount", Float),
)

ratings = Table(
    "ratings", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String(36), nullable=False),
    Column("agency", String(20)),
    Column("rating", String(10)),
    Column("outlook", String(20)),
)

risk_factors = Table(
    "risk_factors", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String(36), nullable=False),
    Column("category", String(50)),
    Column("title", Text),
    Column("severity_implied", String(20)),
    Column("mitigation_described", Integer),
)

sources_uses = Table(
    "sources_uses", metadata,
    Column("document_id", String(36), primary_key=True),
    Column("bond_proceeds", Float),
    Column("original_issue_premium", Float),
    Column("project_fund_deposit", Float),
    Column("debt_service_reserve_deposit", Float),
    Column("capitalized_interest", Float),
    Column("costs_of_issuance", Float),
    Column("underwriter_discount", Float),
    Column("total_sources", Float),
    Column("total_uses", Float),
)

revenue_streams = Table(
    "revenue_streams", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String(36), nullable=False),
    Column("stream_type", String(30), nullable=False),  # carbon_credit|tipping_fee|electricity_ppa|offtake
    Column("counterparty", Text),
    Column("counterparty_credit_rating", String(20)),
    Column("contract_term_years", Integer),
    Column("contract_expiry_date", String(20)),
    Column("pricing_mechanism", String(30)),
    Column("current_rate", Float),
    Column("rate_escalator_pct", Float),
    Column("minimum_obligation", Float),
    Column("estimated_annual_revenue", Float),
    Column("assigned_as_security", Integer),  # SQLite bool
    Column("take_or_pay", Integer),  # SQLite bool
    Column("details_json", Text),  # Full sub-model as JSON for type-specific fields
)

operational_metrics = Table(
    "operational_metrics", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("document_id", String(36), nullable=False),
    Column("metric_type", String(30), nullable=False),  # dscr|debt_service|generation|escalation|opex
    Column("year", Integer),
    Column("value", Float),
    Column("value2", Float),  # secondary value (e.g., interest for debt_service)
    Column("value3", Float),  # tertiary (e.g., total for debt_service)
    Column("label", String(50)),  # sub-label (e.g., "historical", "projected", "minimum_required")
    Column("details_json", Text),
)

classifications = Table(
    "classifications", metadata,
    Column("document_id", String(36), primary_key=True),
    Column("primary_type", String(100)),
    Column("secondary_type", String(200)),
    Column("credit_quality", String(100)),
    Column("size_band", String(50)),
)

# Cross-module document index (tracks all document types in one place)
document_index = Table(
    "document_index", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source_hash", String(64), nullable=False),
    Column("source_file", String(500), nullable=False),
    Column("doc_type", String(30), nullable=False),  # official_statement | rating_action | event_filing | financial_report
    Column("module_record_id", String(36)),  # ID in the module's own table
    Column("extraction_timestamp", DateTime),
    Column("issuer_name", Text),
    Column("completeness_score", Float),
    Column("provenance_class", String(64), nullable=False, default="unknown"),
    UniqueConstraint("source_hash", "doc_type", name="uq_docidx_source_hash_doc_type"),
)

# Indexes
Index("ix_docs_bond_type", deal_structures.c.bond_type)
Index("ix_docs_tax_status", deal_structures.c.tax_status)
Index("ix_docs_interest_type", deal_structures.c.interest_type)
Index("ix_docs_issuer_state", deal_identities.c.issuer_state)
Index("ix_docs_par_amount", deal_structures.c.par_amount)
Index("ix_operational_metrics_doc", operational_metrics.c.document_id)
Index("ix_operational_metrics_type", operational_metrics.c.metric_type)
Index("ix_revenue_streams_doc", revenue_streams.c.document_id)
Index("ix_revenue_streams_type", revenue_streams.c.stream_type)
Index("ix_docidx_doc_type", document_index.c.doc_type)
Index("ix_docidx_issuer", document_index.c.issuer_name)
Index("ix_docidx_provenance", document_index.c.provenance_class)


# ---------------------------------------------------------------------------
# Database operations
# ---------------------------------------------------------------------------

def init_database(db_path: Path | None = None) -> Engine:
    """Create SQLite database and all tables."""
    if db_path is None:
        db_path = get_settings().database_path
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    metadata.create_all(engine)

    # Create views
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE VIEW IF NOT EXISTS v_deal_summary AS
            SELECT
                d.id,
                d.source_file,
                d.completeness_score,
                d.primary_classification,
                d.secondary_classification,
                d.size_classification,
                di.issuer_name,
                di.issuer_state,
                di.series_name,
                di.cusip_base,
                ds.par_amount,
                ds.bond_type,
                ds.tax_status,
                ds.interest_type,
                ds.cab_enabled,
                ds.slb_enabled,
                sp.pledge_type,
                sp.min_coverage_ratio
            FROM documents d
            LEFT JOIN deal_identities di ON d.id = di.document_id
            LEFT JOIN deal_structures ds ON d.id = ds.document_id
            LEFT JOIN security_packages sp ON d.id = sp.document_id
        """))
        conn.commit()

    logger.info("Database initialized at %s", db_path)
    return engine


def _float_or_none(val: Any) -> float | None:
    if val is None:
        return None
    return float(val)


def _str_or_none(val: Any) -> str | None:
    if val is None:
        return None
    return str(val)


def _infer_document_provenance_class(source_file: str) -> str:
    normalized = source_file.replace("\\", "/").strip().lower()
    if not normalized:
        return "unknown"
    if normalized == "test.pdf" or normalized.endswith("/test.pdf"):
        return "test_fixture"
    if "analysis/cchci_obligor_profile.json" in normalized:
        return "backfill_obligor_profile"
    if "research/corpus/healthcare/healthcare_credit_drivers.json" in normalized:
        return "backfill_research_corpus"
    if "risk_implementation_guide.json" in normalized:
        return "backfill_waste_feedstock"
    if normalized.endswith(".pdf"):
        return "extracted_pdf"
    if normalized.endswith(".json"):
        return "extracted_json"
    return "derived_other"


def save_deal_record(engine: Engine, record: Any) -> str:
    """Save a DealRecord to the database. Returns document ID.
    If a record with the same source_hash exists, it is replaced."""
    from ..schema.deal_record import DealRecord
    assert isinstance(record, DealRecord)

    doc_id = record.extraction_id

    with engine.begin() as conn:
        # Check for existing record with same hash
        existing = conn.execute(
            text("SELECT id FROM documents WHERE source_hash = :h"),
            {"h": record.source_hash},
        ).fetchone()
        if existing:
            old_id = existing[0]
            logger.info("Replacing existing record %s for %s", old_id[:8], record.source_file)
            for tbl_name in [
                "classifications", "sources_uses", "risk_factors", "ratings",
                "security_packages", "debt_service_rows", "maturity_rows",
                "deal_structures", "deal_identities", "revenue_streams",
                "operational_metrics",
            ]:
                conn.execute(text(f"DELETE FROM {tbl_name} WHERE document_id = :id"), {"id": old_id})
            conn.execute(text("DELETE FROM documents WHERE id = :id"), {"id": old_id})

        # Documents
        conn.execute(documents.insert().values(
            id=doc_id,
            source_file=record.source_file,
            source_hash=record.source_hash,
            extraction_timestamp=record.extraction_timestamp,
            extraction_version=record.extraction_version,
            completeness_score=record.completeness_score,
            primary_classification=record.primary_classification,
            secondary_classification=record.secondary_classification,
            tertiary_classification=record.tertiary_classification,
            size_classification=record.size_classification,
        ))

        # Deal Identity
        ident = record.identity
        conn.execute(deal_identities.insert().values(
            document_id=doc_id,
            cusip_base=ident.cusip_base,
            document_type=ident.document_type,
            dated_date=_str_or_none(ident.dated_date),
            sale_date=_str_or_none(ident.sale_date),
            delivery_date=_str_or_none(ident.delivery_date),
            issuer_name=ident.issuer_name,
            issuer_type=ident.issuer_type,
            issuer_state=ident.issuer_state,
            issuer_county=ident.issuer_county,
            borrower_name=ident.borrower_name,
            trustee_name=ident.trustee_name,
            bond_counsel=ident.bond_counsel,
            municipal_advisor=ident.municipal_advisor,
            series_name=ident.series_name,
            official_title=ident.official_title,
        ))

        # Deal Structure
        struct = record.structure
        conn.execute(deal_structures.insert().values(
            document_id=doc_id,
            par_amount=_float_or_none(struct.par_amount),
            denomination=_float_or_none(struct.denomination),
            bond_type=struct.bond_type,
            tax_status=struct.tax_status,
            interest_type=struct.interest_type,
            cab_enabled=int(struct.cab_enabled),
            slb_enabled=int(struct.slb_enabled),
            green_bond=int(struct.green_bond),
            maturity_type=struct.maturity_type,
            final_maturity_date=_str_or_none(struct.final_maturity_date),
            optional_redemption_date=_str_or_none(struct.optional_redemption_date),
            optional_redemption_price=_float_or_none(struct.optional_redemption_price),
            credit_enhancement_type=struct.credit_enhancement_type,
            credit_enhancer_name=struct.credit_enhancer_name,
        ))

        # Maturity rows
        if record.maturity_schedule:
            for row in record.maturity_schedule.rows:
                conn.execute(maturity_rows.insert().values(
                    document_id=doc_id,
                    maturity_date=_str_or_none(row.maturity_date),
                    par_amount=_float_or_none(row.par_amount),
                    coupon_rate=_float_or_none(row.coupon_rate),
                    yield_to_maturity=_float_or_none(row.yield_to_maturity),
                    price=_float_or_none(row.price),
                    cusip=row.cusip,
                    serial_or_term=row.serial_or_term,
                ))

        # Security
        if record.security:
            sec = record.security
            conn.execute(security_packages.insert().values(
                document_id=doc_id,
                pledge_type=sec.pledge_type,
                pledged_revenues_description=sec.pledged_revenues_description,
                lien_position=sec.lien_position,
                real_property_mortgage=int(sec.real_property_mortgage),
                equipment_security_interest=int(sec.equipment_security_interest),
                min_coverage_ratio=_float_or_none(
                    sec.rate_covenant.minimum_coverage_ratio if sec.rate_covenant else None
                ),
                additional_bonds_hist_coverage=_float_or_none(
                    sec.additional_bonds_test.historical_coverage_required if sec.additional_bonds_test else None
                ),
                dsrf_type=sec.debt_service_reserve_fund.requirement_type if sec.debt_service_reserve_fund else None,
                dsrf_amount=_float_or_none(
                    sec.debt_service_reserve_fund.amount if sec.debt_service_reserve_fund else None
                ),
            ))

        # Debt service rows
        if record.debt_service:
            for row in record.debt_service.rows:
                conn.execute(debt_service_rows.insert().values(
                    document_id=doc_id,
                    fiscal_year=row.fiscal_year,
                    principal=_float_or_none(row.principal),
                    interest=_float_or_none(row.interest),
                    total=_float_or_none(row.total),
                    outstanding_balance=_float_or_none(row.outstanding_balance),
                ))

        # Ratings
        if record.ratings:
            for r in record.ratings.ratings:
                conn.execute(ratings.insert().values(
                    document_id=doc_id,
                    agency=r.agency,
                    rating=r.rating,
                    outlook=r.outlook,
                ))

        # Risk factors
        if record.risk_factors:
            for rf in record.risk_factors.risks:
                conn.execute(risk_factors.insert().values(
                    document_id=doc_id,
                    category=rf.category,
                    title=rf.title,
                    severity_implied=rf.severity_implied,
                    mitigation_described=int(rf.mitigation_described),
                ))

        # Sources and uses
        if record.sources_uses:
            su = record.sources_uses
            conn.execute(sources_uses.insert().values(
                document_id=doc_id,
                bond_proceeds=_float_or_none(su.bond_proceeds),
                original_issue_premium=_float_or_none(su.original_issue_premium),
                project_fund_deposit=_float_or_none(su.project_fund_deposit),
                debt_service_reserve_deposit=_float_or_none(su.debt_service_reserve_deposit),
                capitalized_interest=_float_or_none(su.capitalized_interest),
                costs_of_issuance=_float_or_none(su.costs_of_issuance),
                underwriter_discount=_float_or_none(su.underwriter_discount),
                total_sources=_float_or_none(su.total_sources),
                total_uses=_float_or_none(su.total_uses),
            ))

        # Revenue streams
        if record.revenue_streams:
            import json as _json

            rs = record.revenue_streams
            for tf in rs.tipping_fees:
                conn.execute(revenue_streams.insert().values(
                    document_id=doc_id,
                    stream_type="tipping_fee",
                    counterparty=", ".join(tf.counterparties) if tf.counterparties else None,
                    contract_term_years=tf.contract_term_years,
                    contract_expiry_date=_str_or_none(tf.contract_expiry_date),
                    current_rate=_float_or_none(tf.current_rate),
                    rate_escalator_pct=_float_or_none(tf.rate_escalator_pct),
                    minimum_obligation=_float_or_none(tf.minimum_annual_tonnage),
                    estimated_annual_revenue=_float_or_none(tf.guaranteed_annual_revenue),
                    take_or_pay=int(tf.put_or_pay),
                    details_json=_json.dumps(tf.model_dump(mode="json", exclude_none=True)),
                ))

            for ppa in rs.electricity_ppas:
                conn.execute(revenue_streams.insert().values(
                    document_id=doc_id,
                    stream_type="electricity_ppa",
                    counterparty=ppa.counterparty,
                    counterparty_credit_rating=ppa.counterparty_credit_rating,
                    contract_term_years=ppa.contract_term_years,
                    contract_expiry_date=_str_or_none(ppa.contract_expiry_date),
                    current_rate=_float_or_none(ppa.price_per_mwh or ppa.price_per_kwh),
                    rate_escalator_pct=_float_or_none(ppa.price_escalator_pct),
                    minimum_obligation=_float_or_none(ppa.minimum_delivery_obligation_mwh),
                    assigned_as_security=int(ppa.assigned_as_security),
                    details_json=_json.dumps(ppa.model_dump(mode="json", exclude_none=True)),
                ))

            for cc in rs.carbon_credits:
                conn.execute(revenue_streams.insert().values(
                    document_id=doc_id,
                    stream_type="carbon_credit",
                    counterparty=cc.counterparty,
                    contract_term_years=cc.contract_term_years,
                    current_rate=_float_or_none(cc.price_per_credit),
                    minimum_obligation=_float_or_none(cc.estimated_annual_credits),
                    assigned_as_security=int(cc.assigned_as_security),
                    details_json=_json.dumps(cc.model_dump(mode="json", exclude_none=True)),
                ))

            for oa in rs.offtake_agreements:
                conn.execute(revenue_streams.insert().values(
                    document_id=doc_id,
                    stream_type="offtake",
                    counterparty=oa.counterparty,
                    counterparty_credit_rating=oa.counterparty_credit_rating,
                    contract_term_years=oa.contract_term_years,
                    contract_expiry_date=_str_or_none(oa.contract_expiry_date),
                    pricing_mechanism=oa.pricing_mechanism,
                    minimum_obligation=_float_or_none(oa.minimum_purchase_obligation),
                    estimated_annual_revenue=_float_or_none(oa.estimated_annual_revenue),
                    assigned_as_security=int(oa.assigned_as_security),
                    take_or_pay=int(oa.take_or_pay),
                    details_json=_json.dumps(oa.model_dump(mode="json", exclude_none=True)),
                ))

        # Operational metrics (from ai_operational_metrics extractor)
        if hasattr(record, '_operational_metrics') and record._operational_metrics:
            import json as _json2
            for metric in record._operational_metrics:
                conn.execute(operational_metrics.insert().values(
                    document_id=doc_id,
                    metric_type=metric.get("metric_type", ""),
                    year=metric.get("year"),
                    value=_float_or_none(metric.get("value")),
                    value2=_float_or_none(metric.get("value2")),
                    value3=_float_or_none(metric.get("value3")),
                    label=metric.get("label"),
                    details_json=_json2.dumps(metric.get("details", {})) if metric.get("details") else None,
                ))

        # Classifications
        conn.execute(classifications.insert().values(
            document_id=doc_id,
            primary_type=record.primary_classification,
            secondary_type=record.secondary_classification,
            credit_quality=record.tertiary_classification,
            size_band=record.size_classification,
        ))

    logger.info("Saved deal %s (%s) to database", doc_id[:8], record.source_file)
    return doc_id


def get_corpus_stats(engine: Engine) -> dict[str, Any]:
    """Get summary statistics about the corpus."""
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM documents")).scalar() or 0
        avg_completeness = conn.execute(
            text("SELECT AVG(completeness_score) FROM documents")
        ).scalar()

        by_type = {}
        rows = conn.execute(text(
            "SELECT primary_classification, COUNT(*) as cnt FROM documents "
            "GROUP BY primary_classification ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_type[row[0] or "UNCLASSIFIED"] = row[1]

        by_size = {}
        rows = conn.execute(text(
            "SELECT size_classification, COUNT(*) as cnt FROM documents "
            "GROUP BY size_classification ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_size[row[0] or "UNKNOWN"] = row[1]

    return {
        "total_deals": total,
        "avg_completeness": round(float(avg_completeness or 0), 3),
        "by_type": by_type,
        "by_size": by_size,
    }


def search_deals(
    engine: Engine,
    bond_type: str | None = None,
    min_par: float | None = None,
    max_par: float | None = None,
    state: str | None = None,
    cab: bool | None = None,
    slb: bool | None = None,
) -> list[dict[str, Any]]:
    """Search the corpus with filters."""
    clauses: list[str] = ["1=1"]
    if bond_type:
        clauses.append(f"ds.bond_type = '{bond_type}'")
    if min_par is not None:
        clauses.append(f"ds.par_amount >= {min_par}")
    if max_par is not None:
        clauses.append(f"ds.par_amount <= {max_par}")
    if state:
        clauses.append(f"di.issuer_state = '{state.upper()}'")
    if cab is not None:
        clauses.append(f"ds.cab_enabled = {int(cab)}")
    if slb is not None:
        clauses.append(f"ds.slb_enabled = {int(slb)}")

    where = " AND ".join(clauses)
    query = f"""
        SELECT d.id, d.source_file, d.completeness_score,
               di.issuer_name, di.issuer_state, di.series_name,
               ds.par_amount, ds.bond_type, ds.interest_type,
               d.primary_classification, d.size_classification
        FROM documents d
        LEFT JOIN deal_identities di ON d.id = di.document_id
        LEFT JOIN deal_structures ds ON d.id = ds.document_id
        WHERE {where}
        ORDER BY ds.par_amount DESC
    """

    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()

    return [
        {
            "id": r[0],
            "source_file": r[1],
            "completeness": r[2],
            "issuer_name": r[3],
            "state": r[4],
            "series": r[5],
            "par_amount": r[6],
            "bond_type": r[7],
            "interest_type": r[8],
            "classification": r[9],
            "size": r[10],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Module integration
# ---------------------------------------------------------------------------

def init_module_tables(engine: Engine, modules: list[Any] | None = None) -> None:
    """Initialize database tables for all registered modules."""
    if modules is None:
        from ..modules.registry import get_registry
        registry = get_registry()
        modules = registry.modules

    for mod in modules:
        try:
            for table in mod.db_tables():
                table.metadata.create_all(engine)
            logger.info("Initialized tables for module: %s", mod.name)
        except Exception as exc:
            logger.warning("Failed to init tables for %s: %s", mod.name, exc)


def save_to_document_index(
    engine: Engine,
    source_hash: str,
    source_file: str,
    doc_type: str,
    module_record_id: str,
    extraction_timestamp: Any = None,
    issuer_name: str | None = None,
    completeness_score: float | None = None,
    provenance_class: str | None = None,
) -> None:
    """Add or update an entry in the cross-module document index."""
    with engine.begin() as conn:
        # Upsert: delete existing then insert
        existing = conn.execute(
            text(
                "SELECT id FROM document_index "
                "WHERE source_hash = :h AND doc_type = :doc_type"
            ),
            {"h": source_hash, "doc_type": doc_type},
        ).fetchone()
        if existing:
            conn.execute(
                text("DELETE FROM document_index WHERE id = :id"),
                {"id": existing[0]},
            )

        resolved_provenance = provenance_class or _infer_document_provenance_class(source_file)
        conn.execute(document_index.insert().values(
            source_hash=source_hash,
            source_file=source_file,
            doc_type=doc_type,
            module_record_id=module_record_id,
            extraction_timestamp=extraction_timestamp,
            issuer_name=issuer_name,
            completeness_score=completeness_score,
            provenance_class=resolved_provenance,
        ))


def get_document_index_stats(engine: Engine) -> dict[str, Any]:
    """Get statistics from the document index across all modules."""
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM document_index")).scalar() or 0

        by_type = {}
        rows = conn.execute(text(
            "SELECT doc_type, COUNT(*) as cnt FROM document_index "
            "GROUP BY doc_type ORDER BY cnt DESC"
        )).fetchall()
        for row in rows:
            by_type[row[0]] = row[1]

    return {"total_documents": total, "by_type": by_type}
