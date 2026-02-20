"""Unified data loader for the Fundamental Scoring Engine.

Loads and normalizes data from three distinct sources into a common
format consumable by the scoring engine:

  1. Bond corpus (SQLite) — OS extractions, financial reports, rating actions
  2. Equity ticker data (CSV) — daily price history, annual/quarterly financials
  3. EMMA crawler (JSON) — secondary market trade data, real-time ratings

This module handles the impedance mismatch between bond data (sparse,
irregular, document-sourced) and equity data (dense, daily, standardized).
"""
from __future__ import annotations

import csv
import json
import logging
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine

from ..config import get_settings, PROJECT_ROOT, MUNIPAL_ROOT

logger = logging.getLogger("bond_os_extractor.analysis.data_loader")

# Default path to waste ticker data (external to workspace)
DEFAULT_TICKER_DIR = Path(
    r"C:\Users\st3ja\OneDrive\Documents\PROJECTS\AZRFO\QF\WTE\waste_tickers"
)

EMMA_DATA_DIR = MUNIPAL_ROOT / "emma" / "emma_crawler" / "output" / "data"


def _parse_financial_value(val: str | None) -> float | None:
    """Parse a financial value string like '25,204,000,000' or '' to float."""
    if not val or not val.strip():
        return None
    clean = val.strip().replace(",", "").replace('"', "")
    if clean in ("-", "--", "N/A", "n/a"):
        return None
    try:
        return float(clean)
    except (ValueError, InvalidOperation):
        return None


# ---------------------------------------------------------------------------
# Bond corpus loaders (SQLite)
# ---------------------------------------------------------------------------

def load_os_records(engine: Engine) -> list[dict[str, Any]]:
    """Load all Official Statement records from the bond corpus."""
    query = """
        SELECT
            d.id, d.source_file, d.completeness_score,
            di.cusip_base, di.issuer_name, di.borrower_name,
            di.issuer_state, di.series_name,
            ds.par_amount, ds.bond_type, ds.tax_status, ds.interest_type,
            ds.final_maturity_date, ds.credit_enhancement_type,
            ds.credit_enhancer_name,
            sp.pledge_type, sp.lien_position,
            sp.min_coverage_ratio, sp.additional_bonds_hist_coverage,
            sp.dsrf_type, sp.dsrf_amount
        FROM documents d
        LEFT JOIN deal_identities di ON d.id = di.document_id
        LEFT JOIN deal_structures ds ON d.id = ds.document_id
        LEFT JOIN security_packages sp ON d.id = sp.document_id
    """
    with engine.connect() as conn:
        rows = conn.execute(text(query)).fetchall()

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "source_file": r[1],
            "completeness_score": r[2],
            "cusip_base": r[3],
            "issuer_name": r[4],
            "borrower_name": r[5],
            "issuer_state": r[6],
            "series_name": r[7],
            "par_amount": r[8],
            "bond_type": r[9],
            "tax_status": r[10],
            "interest_type": r[11],
            "final_maturity_date": r[12],
            "credit_enhancement_type": r[13],
            "credit_enhancer_name": r[14],
            "pledge_type": r[15],
            "lien_position": r[16],
            "min_coverage_ratio": r[17],
            "additional_bonds_hist_coverage": r[18],
            "dsrf_type": r[19],
            "dsrf_amount": r[20],
        })
    logger.info("Loaded %d OS records from corpus", len(records))
    return records


def load_financial_reports(engine: Engine) -> list[dict[str, Any]]:
    """Load all financial report records from the corpus."""
    query = """
        SELECT
            id, source_file, completeness_score,
            issuer_name, obligor_name, report_type,
            fiscal_period_end, fiscal_year,
            total_revenue, total_expenses, operating_income, net_income,
            total_assets, total_liabilities, total_equity,
            cash_and_equivalents,
            debt_service_coverage_ratio, days_cash_on_hand,
            total_debt_outstanding, annual_debt_service,
            auditor_name, audit_opinion
        FROM financial_reports
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("financial_reports table not found or empty")
            return []

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "source_file": r[1],
            "completeness_score": r[2],
            "issuer_name": r[3],
            "obligor_name": r[4],
            "report_type": r[5],
            "fiscal_period_end": r[6],
            "fiscal_year": r[7],
            "total_revenue": r[8],
            "total_expenses": r[9],
            "operating_income": r[10],
            "net_income": r[11],
            "total_assets": r[12],
            "total_liabilities": r[13],
            "total_equity": r[14],
            "cash_and_equivalents": r[15],
            "debt_service_coverage_ratio": r[16],
            "days_cash_on_hand": r[17],
            "total_debt_outstanding": r[18],
            "annual_debt_service": r[19],
            "auditor_name": r[20],
            "audit_opinion": r[21],
        })
    logger.info("Loaded %d financial reports from corpus", len(records))
    return records


def load_rating_actions(engine: Engine) -> list[dict[str, Any]]:
    """Load all rating action records from the corpus."""
    query = """
        SELECT
            id, source_file, completeness_score,
            issuer_name, obligor_name, agency,
            action_type, previous_rating, new_rating,
            previous_outlook, new_outlook,
            action_date, sector
        FROM rating_actions
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("rating_actions table not found or empty")
            return []

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "source_file": r[1],
            "completeness_score": r[2],
            "issuer_name": r[3],
            "obligor_name": r[4],
            "agency": r[5],
            "action_type": r[6],
            "previous_rating": r[7],
            "new_rating": r[8],
            "previous_outlook": r[9],
            "new_outlook": r[10],
            "action_date": r[11],
            "sector": r[12],
        })
    logger.info("Loaded %d rating actions from corpus", len(records))
    return records


def load_os_ratings(engine: Engine) -> list[dict[str, Any]]:
    """Load ratings from OS extractions (document-embedded ratings)."""
    query = """
        SELECT r.document_id, r.agency, r.rating, r.outlook,
               di.issuer_name, di.borrower_name
        FROM ratings r
        LEFT JOIN deal_identities di ON r.document_id = di.document_id
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            return []

    return [
        {
            "document_id": r[0],
            "agency": r[1],
            "rating": r[2],
            "outlook": r[3],
            "issuer_name": r[4],
            "borrower_name": r[5],
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# Equity ticker loaders (CSV files)
# ---------------------------------------------------------------------------

def get_ticker_dir(ticker: str, base_dir: Path | None = None) -> Path | None:
    """Get the directory for a specific ticker's data."""
    base = base_dir or DEFAULT_TICKER_DIR
    # Try exact case first, then uppercase
    for name in [ticker, ticker.upper(), ticker.lower()]:
        d = base / name
        if d.is_dir():
            return d
    return None


def load_ticker_history(
    ticker: str,
    base_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load daily price history for a ticker.

    Returns list of dicts with: date, open, high, low, close, adj_close, volume, change.
    Sorted by date ascending.
    """
    d = get_ticker_dir(ticker, base_dir)
    if d is None:
        logger.warning("No directory found for ticker %s", ticker)
        return []

    # Find the main history file (longest one = most data)
    history_files = list(d.glob(f"{ticker.upper()}-history.csv")) + list(
        d.glob(f"{ticker.lower()}-history.csv")
    )
    if not history_files:
        # Try with different casing
        history_files = [f for f in d.glob("*-history.csv")]
    if not history_files:
        history_files = [f for f in d.glob("*history*.csv")]

    if not history_files:
        logger.warning("No history CSV found for %s in %s", ticker, d)
        return []

    # Use the largest file (most data points)
    csv_path = max(history_files, key=lambda f: f.stat().st_size)

    records = []
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            date_str = row.get("Date", "")
            if not date_str:
                continue
            # Parse change percentage
            change_str = row.get("Change", "")
            change_val = None
            if change_str and change_str.strip().rstrip("%"):
                try:
                    change_val = float(change_str.strip().rstrip("%")) / 100.0
                except ValueError:
                    pass

            records.append({
                "date": date_str,
                "open": _parse_financial_value(row.get("Open")),
                "high": _parse_financial_value(row.get("High")),
                "low": _parse_financial_value(row.get("Low")),
                "close": _parse_financial_value(row.get("Close")),
                "adj_close": _parse_financial_value(
                    row.get("Adj. Close") or row.get("Adj Close")
                ),
                "volume": _parse_financial_value(row.get("Volume")),
                "change": change_val,
            })

    # Sort by date ascending
    records.sort(key=lambda r: r["date"])
    logger.info("Loaded %d price records for %s", len(records), ticker)
    return records


def load_ticker_financials(
    ticker: str,
    period: str = "annual",
    base_dir: Path | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Load financial statement data for a ticker.

    Returns dict with keys: 'financials', 'balance_sheet', 'cash_flow'.
    Each value is a list of dicts with 'name' and period columns.

    Only available for tickers with CSV financials (WM, CREG; others have XLSX only).
    """
    d = get_ticker_dir(ticker, base_dir)
    if d is None:
        return {}

    prefix = f"{ticker.upper()}_{period}"
    result: dict[str, list[dict[str, Any]]] = {}

    file_map = {
        "financials": f"{prefix}_financials.csv",
        "balance_sheet": f"{prefix}_balance-sheet.csv",
        "cash_flow": f"{prefix}_cash-flow.csv",
    }

    for key, filename in file_map.items():
        csv_path = d / filename
        if not csv_path.exists():
            # Try lowercase
            csv_path = d / filename.lower()
        if not csv_path.exists():
            continue

        rows = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            if not headers:
                continue

            for row in reader:
                if not row or not row[0].strip():
                    continue
                item_name = row[0].strip()
                # Build dict: name + each period column
                item = {"name": item_name}
                for i, col in enumerate(headers[1:], 1):
                    if i < len(row):
                        item[col.strip()] = _parse_financial_value(row[i])
                rows.append(item)

        result[key] = rows
        logger.info(
            "Loaded %d line items from %s/%s",
            len(rows), ticker, filename,
        )

    return result


def get_latest_financials(
    ticker: str,
    base_dir: Path | None = None,
) -> dict[str, float | None]:
    """Extract key financial metrics from the most recent period.

    Returns a flat dict with standardized metric names and their values.
    Uses the most recent non-TTM column for balance sheet/cash flow,
    and TTM for income statement items (if available).
    """
    data = load_ticker_financials(ticker, "annual", base_dir)
    if not data:
        return {}

    def _find_row(rows: list[dict], name: str) -> dict | None:
        """Find a row by exact or prefix match on the name field."""
        name_lower = name.lower().strip()
        for row in rows:
            row_name = row.get("name", "").strip().lower()
            if row_name == name_lower:
                return row
        return None

    def _get_latest_value(row: dict | None, prefer_ttm: bool = False) -> float | None:
        """Get the most recent non-None value from a row."""
        if row is None:
            return None
        # Try TTM first if preferred
        if prefer_ttm and row.get("ttm") is not None:
            return row["ttm"]
        # Otherwise find the most recent date column
        date_cols = [k for k in row.keys() if k not in ("name", "ttm")]
        # Sort date columns descending
        date_cols.sort(reverse=True)
        for col in date_cols:
            val = row.get(col)
            if val is not None:
                return val
        # Fallback to TTM
        return row.get("ttm")

    metrics: dict[str, float | None] = {}

    # Income statement (prefer TTM)
    fin = data.get("financials", [])
    metrics["total_revenue"] = _get_latest_value(_find_row(fin, "TotalRevenue"), True)
    metrics["cost_of_revenue"] = _get_latest_value(
        _find_row(fin, "CostOfRevenue"), True
    )
    metrics["gross_profit"] = _get_latest_value(_find_row(fin, "GrossProfit"), True)
    metrics["operating_expense"] = _get_latest_value(
        _find_row(fin, "OperatingExpense"), True
    )
    metrics["operating_income"] = _get_latest_value(
        _find_row(fin, "OperatingIncome"), True
    )
    metrics["net_income"] = _get_latest_value(
        _find_row(fin, "NetIncome") or _find_row(fin, "NetIncomeCommonStockholders"),
        True,
    )
    metrics["ebitda"] = _get_latest_value(_find_row(fin, "EBITDA"), True)
    metrics["depreciation"] = _get_latest_value(
        _find_row(fin, "DepreciationAndAmortizationInIncomeStatement")
        or _find_row(fin, "ReconciledDepreciation"),
        True,
    )

    # Balance sheet (most recent period, not TTM)
    bs = data.get("balance_sheet", [])
    metrics["total_assets"] = _get_latest_value(_find_row(bs, "TotalAssets"))
    metrics["current_assets"] = _get_latest_value(_find_row(bs, "CurrentAssets"))
    metrics["total_liabilities"] = _get_latest_value(
        _find_row(bs, "TotalLiabilitiesNetMinorityInterest")
        or _find_row(bs, "TotalLiabilities"),
    )
    metrics["current_liabilities"] = _get_latest_value(
        _find_row(bs, "CurrentLiabilities")
    )
    metrics["total_equity"] = _get_latest_value(
        _find_row(bs, "StockholdersEquity")
        or _find_row(bs, "TotalEquityGrossMinorityInterest"),
    )
    metrics["total_debt"] = _get_latest_value(_find_row(bs, "TotalDebt"))
    metrics["net_debt"] = _get_latest_value(_find_row(bs, "NetDebt"))
    metrics["cash"] = _get_latest_value(
        _find_row(bs, "CashAndCashEquivalents")
        or _find_row(bs, "CashCashEquivalentsAndShortTermInvestments"),
    )

    # Cash flow (prefer TTM)
    cf = data.get("cash_flow", [])
    metrics["operating_cash_flow"] = _get_latest_value(
        _find_row(cf, "OperatingCashFlow"), True
    )
    metrics["capital_expenditure"] = _get_latest_value(
        _find_row(cf, "CapitalExpenditure"), True
    )
    metrics["free_cash_flow"] = _get_latest_value(
        _find_row(cf, "FreeCashFlow"), True
    )

    return metrics


def get_revenue_history(
    ticker: str,
    base_dir: Path | None = None,
    max_years: int = 10,
) -> list[tuple[str, float]]:
    """Extract multi-year revenue series for CAGR calculation.

    Returns list of (period_label, revenue_value) tuples sorted chronologically.
    Capped to the most recent `max_years` periods to avoid inflating CAGR
    with early-stage hyper-growth that doesn't reflect current fundamentals.
    """
    data = load_ticker_financials(ticker, "annual", base_dir)
    fin = data.get("financials", [])
    if not fin:
        return []

    # Find TotalRevenue row
    rev_row = None
    for row in fin:
        if row.get("name", "").strip().lower() == "totalrevenue":
            rev_row = row
            break
    if rev_row is None:
        return []

    # Extract all dated values (skip 'name' and 'ttm')
    series = []
    for key, val in rev_row.items():
        if key in ("name", "ttm") or val is None:
            continue
        series.append((key, val))

    # Sort chronologically (date strings like "12/31/2024")
    series.sort(key=lambda x: x[0])

    # Cap to most recent max_years+1 data points (for max_years intervals)
    if len(series) > max_years + 1:
        series = series[-(max_years + 1):]

    return series


# ---------------------------------------------------------------------------
# EMMA crawler loaders (JSON files)
# ---------------------------------------------------------------------------

def load_emma_bond_data(cusip_hash: str | None = None) -> list[dict[str, Any]]:
    """Load EMMA crawler data (snapshot, trades, ratings) from JSON files.

    If cusip_hash is provided, loads only that CUSIP. Otherwise loads all.
    """
    if not EMMA_DATA_DIR.exists():
        logger.warning("EMMA data directory not found: %s", EMMA_DATA_DIR)
        return []

    if cusip_hash:
        json_path = EMMA_DATA_DIR / f"{cusip_hash}.json"
        if json_path.exists():
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [data]
        return []

    records = []
    for json_path in EMMA_DATA_DIR.glob("A*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            records.append(data)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Failed to load %s: %s", json_path.name, exc)

    logger.info("Loaded %d EMMA bond records", len(records))
    return records


def get_emma_ratings(bond_data: dict) -> list[dict[str, str]]:
    """Extract current ratings from EMMA bond data."""
    return [
        {
            "agency": r.get("agency", ""),
            "rating": r.get("rating", ""),
            "outlook": r.get("outlook", ""),
            "as_of": r.get("as_of", ""),
        }
        for r in bond_data.get("ratings", [])
        if r.get("rating")  # Skip empty ratings
    ]


def get_emma_trades(bond_data: dict) -> list[dict[str, Any]]:
    """Extract trade history from EMMA bond data."""
    return [
        {
            "trade_date": t.get("trade_date", ""),
            "settlement_date": t.get("settlement_date", ""),
            "price": _parse_financial_value(t.get("price")),
            "yield": t.get("yield"),
            "trade_amount": _parse_financial_value(
                str(t.get("trade_amount", "")).replace(",", "")
            ),
            "trade_type": t.get("trade_type", ""),
        }
        for t in bond_data.get("trades", [])
    ]


# ---------------------------------------------------------------------------
# Obligor-specific loaders (for synthetic return series)
# ---------------------------------------------------------------------------

def _name_matches(text: str, search_terms: list[str]) -> bool:
    """Check if any search term is a substring of text (case-insensitive)."""
    text_lower = text.lower()
    return any(term in text_lower for term in search_terms)


def load_emma_bonds_by_issuer(
    issuer_name: str,
    aliases: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load all EMMA bonds whose security_name matches the issuer.

    Checks security_name against issuer_name and all aliases
    (case-insensitive substring match).
    """
    if not EMMA_DATA_DIR.exists():
        return []
    search_terms = [issuer_name.lower()]
    if aliases:
        search_terms.extend(a.lower() for a in aliases)

    matches = []
    for json_path in EMMA_DATA_DIR.glob("A*.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            sec_name = (data.get("snapshot", {}).get("security_name", "") or "").lower()
            if _name_matches(sec_name, search_terms):
                matches.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    logger.info("Found %d EMMA bonds for issuer '%s'", len(matches), issuer_name)
    return matches


def load_rating_actions_for_obligor(
    engine: Engine,
    obligor_name: str,
    aliases: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load rating actions for a specific obligor."""
    all_actions = load_rating_actions(engine)
    search_terms = [obligor_name.lower()]
    if aliases:
        search_terms.extend(a.lower() for a in aliases)

    matches = []
    for r in all_actions:
        text = ((r.get("issuer_name") or "") + " " + (r.get("obligor_name") or "")).lower()
        if _name_matches(text, search_terms):
            matches.append(r)
    return matches


def load_financial_reports_for_obligor(
    engine: Engine,
    obligor_name: str,
    aliases: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load financial reports for a specific obligor."""
    all_reports = load_financial_reports(engine)
    search_terms = [obligor_name.lower()]
    if aliases:
        search_terms.extend(a.lower() for a in aliases)

    matches = []
    for r in all_reports:
        text = ((r.get("issuer_name") or "") + " " + (r.get("obligor_name") or "")).lower()
        if _name_matches(text, search_terms):
            matches.append(r)
    return matches


# ---------------------------------------------------------------------------
# Risk benchmarking loaders
# ---------------------------------------------------------------------------

def load_risk_factors(engine: Engine) -> list[dict[str, Any]]:
    """Load all risk factors from the risk_factors table."""
    query = """
        SELECT id, document_id, category, title,
               severity_implied, mitigation_described
        FROM risk_factors
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("risk_factors table not found or empty")
            return []

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "document_id": r[1],
            "category": r[2],
            "title": r[3],
            "severity_implied": r[4],
            "mitigation_described": bool(r[5]) if r[5] is not None else False,
        })
    logger.info("Loaded %d risk factors from corpus", len(records))
    return records


def load_rating_action_factors(engine: Engine) -> list[dict[str, Any]]:
    """Load all rating action factors with parent action context.

    Joins rating_action_factors with rating_actions to get the agency,
    action type, issuer name, and rating alongside each factor.
    """
    query = """
        SELECT
            raf.id, raf.rating_action_id, raf.factor_type, raf.text,
            ra.agency, ra.action_type, ra.issuer_name,
            ra.new_rating, ra.sector
        FROM rating_action_factors raf
        LEFT JOIN rating_actions ra ON raf.rating_action_id = ra.id
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("rating_action_factors table not found or empty")
            return []

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "rating_action_id": r[1],
            "factor_type": r[2],    # key_factor | strength | challenge
            "text": r[3],
            "agency": r[4],
            "action_type": r[5],
            "issuer_name": r[6],
            "new_rating": r[7],
            "sector": r[8],
        })
    logger.info("Loaded %d rating action factors from corpus", len(records))
    return records


def load_security_packages(engine: Engine) -> list[dict[str, Any]]:
    """Load all security packages from the security_packages table."""
    query = """
        SELECT document_id, pledge_type, lien_position,
               min_coverage_ratio, additional_bonds_hist_coverage,
               dsrf_type, dsrf_amount, pledged_revenues_description
        FROM security_packages
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("security_packages table not found or empty")
            return []

    records = []
    for r in rows:
        records.append({
            "document_id": r[0],
            "pledge_type": r[1],
            "lien_position": r[2],
            "min_coverage_ratio": r[3],
            "additional_bonds_hist_coverage": r[4],
            "dsrf_type": r[5],
            "dsrf_amount": r[6],
            "pledged_revenues_description": r[7],
        })
    logger.info("Loaded %d security packages from corpus", len(records))
    return records


def load_rationale_summaries(engine: Engine) -> list[dict[str, Any]]:
    """Load rating action rationale summaries with issuer context.

    Returns records where rationale_summary is not null, providing
    the narrative reasoning behind rating agency decisions.
    """
    query = """
        SELECT id, issuer_name, agency, action_type,
               new_rating, rationale_summary
        FROM rating_actions
        WHERE rationale_summary IS NOT NULL
          AND rationale_summary != ''
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("rating_actions table not found or empty")
            return []

    records = []
    for r in rows:
        records.append({
            "id": r[0],
            "issuer_name": r[1],
            "agency": r[2],
            "action_type": r[3],
            "new_rating": r[4],
            "rationale_summary": r[5],
        })
    logger.info("Loaded %d rationale summaries from corpus", len(records))
    return records


def load_credit_enhancements(engine: Engine) -> list[dict[str, Any]]:
    """Load credit enhancement data from deal structures.

    Joins deal_structures with deal_identities to include issuer context.
    Filters out records with no credit enhancement.
    """
    query = """
        SELECT ds.document_id, ds.credit_enhancement_type,
               ds.credit_enhancer_name,
               di.issuer_name
        FROM deal_structures ds
        LEFT JOIN deal_identities di ON ds.document_id = di.document_id
        WHERE ds.credit_enhancement_type IS NOT NULL
          AND ds.credit_enhancement_type != ''
          AND LOWER(ds.credit_enhancement_type) != 'none'
    """
    with engine.connect() as conn:
        try:
            rows = conn.execute(text(query)).fetchall()
        except Exception:
            logger.warning("deal_structures/deal_identities tables not found")
            return []

    records = []
    for r in rows:
        records.append({
            "document_id": r[0],
            "credit_enhancement_type": r[1],
            "credit_enhancer_name": r[2],
            "issuer_name": r[3],
        })
    logger.info("Loaded %d credit enhancements from corpus", len(records))
    return records
