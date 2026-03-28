"""Tool executor — routes agent tool calls to existing Muni-Pal engines.

Each function returns a JSON-serializable dict that gets fed back to Claude
as a tool_result. Direct Python imports are used (no HTTP calls required),
so the Bank Analyzer and Credit Analyzer don't need to be running as
separate services.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────

_PROJECT_ROOT = Path(__file__).resolve().parents[4]
_EMMA_ROOT = _PROJECT_ROOT / "emma" / "bond_os_extractor"
_CORPUS_DB = _EMMA_ROOT / "data" / "waste" / "corpus.db"
_REPORTS_DIR = _PROJECT_ROOT / "reports" / "advisor"

_TOUCAN_DIR = Path(
    r"C:\Users\st3ja\OneDrive\Documents\MEGA\PROJECTS\INNOVATION FACTORY\TOUCAN"
)


def _ensure_reports_dir() -> Path:
    _REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    return _REPORTS_DIR


# ── Corpus Helpers ─────────────────────────────────────────────────────

def _get_db(sector: str = "wte") -> Path:
    db = _EMMA_ROOT / "data" / sector / "corpus.db"
    if not db.exists():
        # Fallback chain: wte -> waste -> healthcare
        for fallback in ["wte", "waste", "healthcare"]:
            fb = _EMMA_ROOT / "data" / fallback / "corpus.db"
            if fb.exists():
                return fb
        return _CORPUS_DB
    return db


def _query_db(sql: str, params: tuple = (), sector: str = "wte") -> list[dict]:
    db_path = _get_db(sector)
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    except sqlite3.OperationalError as e:
        logger.warning("DB query failed: %s", e)
        return []
    finally:
        conn.close()


# ── Tool Implementations ──────────────────────────────────────────────


def execute_search_corpus(args: dict) -> dict:
    query = args.get("query", "")
    sector = args.get("sector", "wte")
    limit = args.get("limit", 10)
    deal_type = args.get("deal_type")

    conditions = []
    params = []

    if query:
        conditions.append(
            "(di.issuer_name LIKE ? OR di.cusip_base LIKE ? OR di.issuer_state LIKE ?)"
        )
        q = f"%{query}%"
        params.extend([q, q, q])

    if deal_type:
        conditions.append("ds.bond_type LIKE ?")
        params.append(f"%{deal_type}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT di.document_id, di.cusip_base, di.issuer_name, di.issuer_state,
               di.issuer_type, ds.par_amount, ds.bond_type,
               ds.tax_status, doc.completeness_score,
               r.rating, r.agency
        FROM deal_identities di
        JOIN documents doc ON di.document_id = doc.id
        LEFT JOIN deal_structures ds ON di.document_id = ds.document_id
        LEFT JOIN (
            SELECT document_id, rating, agency
            FROM ratings GROUP BY document_id
        ) r ON di.document_id = r.document_id
        {where}
        ORDER BY doc.completeness_score DESC
        LIMIT ?
    """
    params.append(limit)
    rows = _query_db(sql, tuple(params), sector)
    return {"results": rows, "total": len(rows), "query": query, "sector": sector}


def execute_get_deal_details(args: dict) -> dict:
    cusip = args["cusip"]
    # Search by cusip_base (6 char) or full document_id
    rows = _query_db(
        "SELECT * FROM deal_identities WHERE cusip_base LIKE ? OR document_id LIKE ?",
        (f"%{cusip}%", f"%{cusip}%"),
    )
    if not rows:
        return {"error": f"No deal found for CUSIP {cusip}"}

    deal = rows[0]
    doc_id = deal["document_id"]

    # Enrich with related data
    structure = _query_db(
        "SELECT * FROM deal_structures WHERE document_id = ?", (doc_id,)
    )
    risk_factors = _query_db(
        "SELECT * FROM risk_factors WHERE document_id = ?", (doc_id,)
    )
    security = _query_db(
        "SELECT * FROM security_packages WHERE document_id = ?", (doc_id,)
    )
    ratings = _query_db(
        "SELECT * FROM ratings WHERE document_id = ?", (doc_id,)
    )
    sources_uses = _query_db(
        "SELECT * FROM sources_uses WHERE document_id = ?", (doc_id,)
    )
    maturities = _query_db(
        "SELECT * FROM maturity_rows WHERE document_id = ?", (doc_id,)
    )
    debt_service = _query_db(
        "SELECT * FROM debt_service_rows WHERE document_id = ?", (doc_id,)
    )

    deal["structure"] = structure[0] if structure else None
    deal["risk_factors"] = risk_factors
    deal["security_packages"] = security
    deal["ratings"] = ratings
    deal["sources_uses"] = sources_uses[0] if sources_uses else None
    deal["maturities"] = maturities[:10]  # limit for context window
    deal["debt_service"] = debt_service[:10]
    return deal


def execute_get_corpus_stats(args: dict) -> dict:
    sector = args.get("sector", "all")
    sectors = ["wte", "waste", "healthcare"] if sector == "all" else [sector]
    stats = {}
    for s in sectors:
        docs = _query_db("SELECT COUNT(*) as cnt FROM documents", sector=s)
        avg_comp = _query_db(
            "SELECT AVG(completeness_score) as avg_pct FROM documents", sector=s
        )
        ratings = _query_db(
            "SELECT rating, COUNT(*) as cnt FROM ratings "
            "GROUP BY rating ORDER BY cnt DESC",
            sector=s,
        )
        rev_streams = _query_db(
            "SELECT COUNT(*) as cnt FROM revenue_streams", sector=s
        )
        # operational_metrics may not exist in all sector DBs
        op_metrics = _query_db(
            "SELECT COUNT(*) as cnt FROM operational_metrics", sector=s
        )
        rating_actions = _query_db(
            "SELECT COUNT(*) as cnt FROM rating_actions", sector=s
        )
        event_filings = _query_db(
            "SELECT COUNT(*) as cnt FROM event_filings", sector=s
        )
        stats[s] = {
            "total_documents": docs[0]["cnt"] if docs else 0,
            "avg_completeness": round(avg_comp[0]["avg_pct"] or 0, 1) if avg_comp else 0,
            "rating_distribution": {r["rating"]: r["cnt"] for r in ratings},
            "revenue_streams": rev_streams[0]["cnt"] if rev_streams else 0,
            "operational_metrics": op_metrics[0]["cnt"] if op_metrics else 0,
            "rating_actions": rating_actions[0]["cnt"] if rating_actions else 0,
            "event_filings": event_filings[0]["cnt"] if event_filings else 0,
        }
    return stats


def execute_get_revenue_streams(args: dict) -> dict:
    stream_type = args.get("stream_type", "all")
    issuer = args.get("issuer")

    conditions = []
    params = []
    if stream_type and stream_type != "all":
        conditions.append("r.stream_type = ?")
        params.append(stream_type)
    if issuer:
        conditions.append("di.issuer_name LIKE ?")
        params.append(f"%{issuer}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT r.*, di.issuer_name, di.cusip_base
        FROM revenue_streams r
        JOIN deal_identities di ON r.document_id = di.document_id
        {where}
        ORDER BY di.issuer_name
    """
    rows = _query_db(sql, tuple(params))
    return {"results": rows, "total": len(rows)}


def execute_get_operational_metrics(args: dict) -> dict:
    metric_type = args.get("metric_type", "all")
    issuer = args.get("issuer")

    conditions = []
    params = []
    if metric_type and metric_type != "all":
        conditions.append("o.metric_type = ?")
        params.append(metric_type)
    if issuer:
        conditions.append("di.issuer_name LIKE ?")
        params.append(f"%{issuer}%")

    where = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT o.*, di.issuer_name, di.cusip_base
        FROM operational_metrics o
        JOIN deal_identities di ON o.document_id = di.document_id
        {where}
        ORDER BY di.issuer_name, o.metric_type
    """
    rows = _query_db(sql, tuple(params))
    return {"results": rows, "total": len(rows)}


def execute_run_credit_analysis(args: dict) -> dict:
    """Run the full credit analysis pipeline via Engine 2."""
    try:
        from munipal.engines.credit_analyzer.models import (
            ManagementProfile,
            ProjectInputs,
        )
        from munipal.engines.credit_analyzer.five_cs import assess_five_cs
        from munipal.engines.credit_analyzer.bond_sizing import size_bond
        from munipal.engines.credit_analyzer.financial_model import build_financial_model
        from munipal.engines.credit_analyzer.deal_structuring import structure_deal
        from munipal.engines.credit_analyzer.standard_model import integrate_standard_model
        from munipal.engines.credit_analyzer.models import CreditAnalysisResult

        project = ProjectInputs(
            project_name=args.get("project_name", "Unnamed Project"),
            state=args.get("state", ""),
            sector=args.get("sector", "waste"),
            project_type=args.get("project_type", "wte"),
            gross_revenue=args["gross_revenue"],
            operating_expenses=args["operating_expenses"],
            existing_debt_service=args.get("existing_debt_service", 0),
            total_project_cost=args["total_project_cost"],
            equity_contribution=args.get("equity_contribution", 0),
            maturity_years=args.get("maturity_years", 30),
            credit_rating=args.get("credit_rating"),
            management=ManagementProfile(
                experience_years=args.get("management_experience_years", 10),
                prior_defaults=args.get("prior_defaults", False),
                audited_financials=args.get("audited_financials", True),
            ),
        )

        target_dscr = args.get("target_dscr", 1.25)
        five_cs = assess_five_cs(project)
        sizing = size_bond(project, target_dscr=target_dscr)
        fin_model = build_financial_model(project, sizing)
        deal = structure_deal(project, five_cs, sizing)

        credit_opinion = "not_rated_weak"
        if five_cs.composite_score >= 70 and sizing.min_dscr >= 1.25:
            credit_opinion = "investment_grade"
        elif five_cs.composite_score >= 55:
            credit_opinion = "crossover"
        elif five_cs.composite_score >= 40:
            credit_opinion = "not_rated_adequate"

        result = CreditAnalysisResult(
            project_name=project.project_name,
            analysis_timestamp=datetime.now(timezone.utc),
            five_cs=five_cs,
            financial_model=fin_model,
            bond_sizing=sizing,
            deal_structure=deal,
            credit_opinion=credit_opinion,
        )
        result = integrate_standard_model(result, project)

        return json.loads(result.model_dump_json())

    except ImportError as e:
        return {"error": f"Credit Analyzer not available: {e}"}
    except Exception as e:
        logger.exception("Credit analysis failed")
        return {"error": f"Credit analysis failed: {e}"}


def execute_score_banks(args: dict) -> dict:
    """Score banks via Engine 1."""
    try:
        from munipal.engines.bank_analyzer.ingest import load_all_banks
        from munipal.engines.bank_analyzer.scoring import score_all_banks

        banks = load_all_banks(_TOUCAN_DIR)
        scorecards = score_all_banks(banks)

        sort_by = args.get("sort_by", "composite")
        state = args.get("state")
        min_assets = args.get("min_assets")
        limit = args.get("limit", 15)

        filtered = scorecards[:]
        if state:
            filtered = [s for s in filtered if s.state and s.state.upper() == state.upper()]
        if min_assets:
            filtered = [s for s in filtered if s.total_assets >= min_assets * 1e9]

        sort_keys = {
            "composite": lambda s: -s.composite_score,
            "cre": lambda s: -s.cre_distress.score,
            "enhancement": lambda s: -s.credit_enhancement.score,
            "purchase": lambda s: -s.direct_purchase.score,
            "green": lambda s: -s.green_finance.score,
        }
        filtered.sort(key=sort_keys.get(sort_by, sort_keys["composite"]))
        filtered = filtered[:limit]

        return {
            "total": len(filtered),
            "sort_by": sort_by,
            "banks": [
                {
                    "bank_name": s.bank_name,
                    "state": s.state,
                    "total_assets_b": round(s.total_assets / 1e9, 1),
                    "composite_score": round(s.composite_score, 1),
                    "cre_distress": round(s.cre_distress.score, 1),
                    "credit_enhancement": round(s.credit_enhancement.score, 1),
                    "direct_purchase": round(s.direct_purchase.score, 1),
                    "green_finance": round(s.green_finance.score, 1),
                }
                for s in filtered
            ],
        }
    except ImportError as e:
        return {"error": f"Bank Analyzer not available: {e}"}
    except Exception as e:
        logger.exception("Bank scoring failed")
        return {"error": f"Bank scoring failed: {e}"}


def execute_match_banks(args: dict) -> dict:
    """Match banks to a deal profile via Engine 1."""
    try:
        from munipal.engines.bank_analyzer.ingest import load_all_banks
        from munipal.engines.bank_analyzer.scoring import score_all_banks
        from munipal.engines.bank_analyzer.matching import match_banks_to_deal
        from munipal.engines.bank_analyzer.models import DealMatchRequest

        banks = load_all_banks(_TOUCAN_DIR)
        scorecards = score_all_banks(banks)

        deal_req = DealMatchRequest(
            deal_type=args.get("deal_type", "project_finance"),
            deal_amount=args.get("deal_amount", 25) * 1e6,
            state=args.get("state", ""),
            sector=args.get("sector", "waste"),
            green_eligible=args.get("green_eligible", False),
        )

        result = match_banks_to_deal(scorecards, deal_req)
        return json.loads(result.model_dump_json())

    except ImportError as e:
        return {"error": f"Bank Analyzer not available: {e}"}
    except Exception as e:
        logger.exception("Bank matching failed")
        return {"error": f"Bank matching failed: {e}"}


def execute_run_risk_benchmark(args: dict) -> dict:
    """Run risk benchmarking against the EMMA corpus."""
    try:
        # Use corpus data to build benchmark
        risk_data = _query_db("SELECT * FROM risk_factors LIMIT 100")
        rating_data = _query_db(
            "SELECT r.*, di.issuer_name FROM ratings r "
            "JOIN deal_identities di ON r.document_id = di.document_id"
        )

        project_risks = args.get("risk_factors", {})
        project_name = args.get("project_name", "Unknown")

        # Build sector benchmarks from corpus
        risk_counts = {}
        for r in risk_data:
            cat = r.get("category", "unknown")
            risk_counts[cat] = risk_counts.get(cat, 0) + 1

        return {
            "project_name": project_name,
            "project_risks": project_risks,
            "corpus_risk_factors": len(risk_data),
            "risk_category_distribution": risk_counts,
            "rated_deals": len(rating_data),
            "benchmark_summary": (
                f"Benchmarked against {len(risk_data)} risk factors from "
                f"{len(rating_data)} rated deals in the corpus."
            ),
        }
    except Exception as e:
        logger.exception("Risk benchmark failed")
        return {"error": f"Risk benchmark failed: {e}"}


def execute_compare_deals(args: dict) -> dict:
    cusips = args["cusips"]
    deals = []
    for cusip in cusips:
        rows = _query_db(
            "SELECT di.cusip_base, di.issuer_name, di.issuer_state, "
            "ds.par_amount, ds.bond_type, ds.tax_status, "
            "doc.completeness_score, r.rating, r.agency "
            "FROM deal_identities di "
            "JOIN documents doc ON di.document_id = doc.id "
            "LEFT JOIN deal_structures ds ON di.document_id = ds.document_id "
            "LEFT JOIN (SELECT document_id, rating, agency FROM ratings GROUP BY document_id) r "
            "ON di.document_id = r.document_id "
            "WHERE di.cusip_base LIKE ? OR di.document_id LIKE ?",
            (f"%{cusip}%", f"%{cusip}%"),
        )
        if rows:
            deals.append(rows[0])

    if not deals:
        return {"error": "No matching deals found"}

    return {"deals": deals, "count": len(deals)}


def execute_generate_report(args: dict) -> dict:
    """Generate a formatted report and save to disk."""
    report_type = args["report_type"]
    title = args["title"]
    content = args.get("content", {})

    _ensure_reports_dir()
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"{report_type}_{ts}"

    # Build markdown report
    md_lines = [f"# {title}", ""]
    md_lines.append(f"**Report Type:** {report_type}")
    md_lines.append(f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    md_lines.append("")

    if isinstance(content, dict):
        for key, value in content.items():
            md_lines.append(f"## {key.replace('_', ' ').title()}")
            md_lines.append("")
            if isinstance(value, (dict, list)):
                md_lines.append(f"```json\n{json.dumps(value, indent=2, default=str)}\n```")
            else:
                md_lines.append(str(value))
            md_lines.append("")

    md_lines.append("---")
    md_lines.append("*Generated by Muni-Pal Advisor*")

    md_path = _REPORTS_DIR / f"{base}.md"
    json_path = _REPORTS_DIR / f"{base}.json"

    md_path.write_text("\n".join(md_lines), encoding="utf-8")
    json_path.write_text(
        json.dumps({"title": title, "type": report_type, "content": content}, indent=2, default=str),
        encoding="utf-8",
    )

    return {
        "status": "generated",
        "report_type": report_type,
        "md_path": str(md_path),
        "json_path": str(json_path),
    }


# ── Dispatcher ─────────────────────────────────────────────────────────

TOOL_DISPATCH = {
    "search_corpus": execute_search_corpus,
    "get_deal_details": execute_get_deal_details,
    "get_corpus_stats": execute_get_corpus_stats,
    "get_revenue_streams": execute_get_revenue_streams,
    "get_operational_metrics": execute_get_operational_metrics,
    "run_credit_analysis": execute_run_credit_analysis,
    "score_banks": execute_score_banks,
    "match_banks": execute_match_banks,
    "run_risk_benchmark": execute_run_risk_benchmark,
    "compare_deals": execute_compare_deals,
    "generate_report": execute_generate_report,
}


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by name and return JSON result string."""
    fn = TOOL_DISPATCH.get(tool_name)
    if fn is None:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})
    try:
        result = fn(tool_input)
        return json.dumps(result, default=str)
    except Exception as e:
        logger.exception("Tool execution failed: %s", tool_name)
        return json.dumps({"error": f"Tool {tool_name} failed: {e}"})
