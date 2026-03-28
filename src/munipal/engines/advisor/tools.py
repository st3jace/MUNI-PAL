"""Tool definitions for the Municipal Advisor agent.

Each tool maps to an existing Muni-Pal engine capability. Tools marked
with `expensive=True` trigger a confirmation prompt before execution.
"""

from __future__ import annotations

# Tools that require user confirmation before execution
EXPENSIVE_TOOLS = {"run_credit_analysis", "generate_report", "run_risk_benchmark"}

ADVISOR_TOOLS = [
    # ── Corpus Search & Retrieval ──────────────────────────────────────
    {
        "name": "search_corpus",
        "description": (
            "Search the municipal bond corpus for deals by issuer name, CUSIP, "
            "state, sector, or keywords. Returns matching deal summaries with "
            "issuer, par amount, rating, sector, and completeness score."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query: issuer name, CUSIP, state code, or keywords",
                },
                "sector": {
                    "type": "string",
                    "enum": ["wte", "waste", "healthcare"],
                    "description": "Filter by sector (default: wte — richest data)",
                },
                "deal_type": {
                    "type": "string",
                    "description": "Filter by deal type (e.g., revenue, general_obligation)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return (default 10)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_deal_details",
        "description": (
            "Get comprehensive details for a specific deal by CUSIP: financials, "
            "security structure, credit ratings, credit enhancements, risk factors, "
            "and extraction completeness. Returns the full deal record."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cusip": {
                    "type": "string",
                    "description": "The 9-character CUSIP identifier for the deal",
                },
            },
            "required": ["cusip"],
        },
    },
    {
        "name": "get_corpus_stats",
        "description": (
            "Get summary statistics for the bond corpus: total deals, sectors, "
            "average completeness, rating distribution, and data coverage metrics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sector": {
                    "type": "string",
                    "enum": ["wte", "waste", "healthcare", "all"],
                    "description": "Sector to report on (default: all)",
                },
            },
        },
    },
    # ── Revenue & Operational Data ─────────────────────────────────────
    {
        "name": "get_revenue_streams",
        "description": (
            "Query revenue stream data from the corpus: tipping fees, electricity "
            "PPAs, carbon credits, and offtake agreements. Filter by stream type "
            "or issuer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "stream_type": {
                    "type": "string",
                    "enum": ["tipping_fee", "electricity_ppa", "carbon_credit", "offtake", "all"],
                    "description": "Filter by revenue stream type",
                },
                "issuer": {
                    "type": "string",
                    "description": "Filter by issuer name (substring match)",
                },
            },
        },
    },
    {
        "name": "get_operational_metrics",
        "description": (
            "Query operational metrics from the corpus: DSCR series, debt service "
            "schedules, operating expenses, MWh generation, tipping fee escalation. "
            "Filter by metric type or issuer."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metric_type": {
                    "type": "string",
                    "enum": ["dscr", "debt_service", "operating_expenses", "mwh_generation", "escalation", "all"],
                    "description": "Filter by metric type",
                },
                "issuer": {
                    "type": "string",
                    "description": "Filter by issuer name (substring match)",
                },
            },
        },
    },
    # ── Credit Analysis (Engine 2) ─────────────────────────────────────
    {
        "name": "run_credit_analysis",
        "description": (
            "Run the full credit analysis pipeline on a project: 5 Cs assessment, "
            "DSCR-driven bond sizing, 3-statement pro forma model, deal structuring "
            "(covenants, security, pricing), and Standard Model integration "
            "(F_i score, S_Omega, CRI percentile). EXPENSIVE: requires confirmation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string", "description": "Project name"},
                "state": {"type": "string", "description": "State code (e.g., FL, CA)"},
                "sector": {"type": "string", "description": "Sector (e.g., waste, healthcare)"},
                "project_type": {"type": "string", "description": "Project type (e.g., wte, landfill)"},
                "gross_revenue": {"type": "number", "description": "Annual gross revenue ($)"},
                "operating_expenses": {"type": "number", "description": "Annual operating expenses ($)"},
                "existing_debt_service": {"type": "number", "description": "Existing annual debt service ($)"},
                "total_project_cost": {"type": "number", "description": "Total project cost ($)"},
                "equity_contribution": {"type": "number", "description": "Equity/grant contribution ($)"},
                "maturity_years": {"type": "integer", "description": "Bond maturity in years"},
                "target_dscr": {"type": "number", "description": "Target DSCR (default 1.25)"},
                "credit_rating": {"type": "string", "description": "Expected credit rating (e.g., A, BBB+)"},
                "management_experience_years": {"type": "integer", "description": "Management team experience"},
                "prior_defaults": {"type": "boolean", "description": "Any prior defaults?"},
                "audited_financials": {"type": "boolean", "description": "Has audited financials?"},
            },
            "required": ["project_name", "gross_revenue", "operating_expenses", "total_project_cost"],
        },
    },
    # ── Bank Analysis (Engine 1) ───────────────────────────────────────
    {
        "name": "score_banks",
        "description": (
            "Score and rank commercial banks across 4 dimensions: CRE Distress, "
            "Credit Enhancement capacity, Direct Purchase eligibility, and Green "
            "Finance/ESG commitment. Filter by state or asset size."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "enum": ["composite", "cre", "enhancement", "purchase", "green"],
                    "description": "Sort dimension (default: composite)",
                },
                "state": {
                    "type": "string",
                    "description": "Filter by state code",
                },
                "min_assets": {
                    "type": "number",
                    "description": "Minimum total assets ($B)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max banks to return (default 15)",
                },
            },
        },
    },
    {
        "name": "match_banks",
        "description": (
            "Match banks to a specific deal profile. Scores banks on sector fit, "
            "geographic proximity, deal size alignment, green finance capability, "
            "and assigns recommended roles (Lead Underwriter, Syndicate Member, etc.)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "deal_type": {
                    "type": "string",
                    "description": "Deal type (e.g., project_finance, general_obligation)",
                },
                "deal_amount": {
                    "type": "number",
                    "description": "Deal par amount ($M)",
                },
                "state": {
                    "type": "string",
                    "description": "Project state code",
                },
                "sector": {
                    "type": "string",
                    "description": "Sector (e.g., waste, healthcare)",
                },
                "green_eligible": {
                    "type": "boolean",
                    "description": "Is this a green/ESG bond?",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max matches to return (default 10)",
                },
            },
            "required": ["deal_type", "deal_amount", "state"],
        },
    },
    # ── Risk & Benchmarking ────────────────────────────────────────────
    {
        "name": "run_risk_benchmark",
        "description": (
            "Run risk benchmarking against the EMMA corpus: maps project risk "
            "factors to 5 readiness dimensions (technology, construction, market, "
            "regulatory, feedstock), compares to sector benchmarks, identifies gaps. "
            "EXPENSIVE: requires confirmation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "project_name": {
                    "type": "string",
                    "description": "Project name for comparison",
                },
                "risk_factors": {
                    "type": "object",
                    "description": "Risk scores by dimension (0-10 scale)",
                    "properties": {
                        "technology": {"type": "number"},
                        "construction": {"type": "number"},
                        "market": {"type": "number"},
                        "regulatory": {"type": "number"},
                        "feedstock": {"type": "number"},
                    },
                },
            },
            "required": ["project_name"],
        },
    },
    {
        "name": "compare_deals",
        "description": (
            "Compare 2+ deals side-by-side on key metrics: par amount, coupon, "
            "DSCR, ratings, security structure, and completeness. Useful for "
            "identifying comparable transactions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cusips": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of CUSIPs to compare",
                },
                "metrics": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Metrics to compare (e.g., par_amount, coupon, dscr, rating)",
                },
            },
            "required": ["cusips"],
        },
    },
    # ── Report Generation ──────────────────────────────────────────────
    {
        "name": "generate_report",
        "description": (
            "Generate a formatted report (Markdown + JSON) from analysis results. "
            "Report types: credit_analysis, bank_match, combined, risk_benchmark, "
            "deal_comparison, executive_summary. EXPENSIVE: requires confirmation."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": [
                        "credit_analysis",
                        "bank_match",
                        "combined",
                        "risk_benchmark",
                        "deal_comparison",
                        "executive_summary",
                    ],
                    "description": "Type of report to generate",
                },
                "title": {
                    "type": "string",
                    "description": "Report title",
                },
                "content": {
                    "type": "object",
                    "description": "Report content data (from prior tool calls)",
                },
            },
            "required": ["report_type", "title", "content"],
        },
    },
]
