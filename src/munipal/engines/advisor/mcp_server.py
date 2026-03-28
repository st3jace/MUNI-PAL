"""
Muni-Pal Advisor — MCP Server
================================

Exposes the Muni-Pal Municipal Advisor as an MCP (Model Context Protocol)
server so Claude Code can call Muni-Pal operations directly from the IDE.

Usage:
    cd src && python -m munipal.engines.advisor.mcp_server

Configured in .mcp.json at the project root:
    {
      "mcpServers": {
        "munipal-advisor": {
          "command": "python",
          "args": ["-m", "munipal.engines.advisor.mcp_server"],
          "cwd": "<project_root>/src"
        }
      }
    }

This gives Claude Code access to tools like:
    - advisor_chat        (conversational advisor with full context)
    - search_deals        (quick corpus search)
    - get_deal_details    (deep deal lookup)
    - corpus_stats        (corpus summary)
    - score_banks         (bank scoring)
    - match_banks         (bank-deal matching)
    - run_credit_analysis (full 5-stage pipeline)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure src/ is on path
_SRC_DIR = Path(__file__).resolve().parents[2]
if str(_SRC_DIR.parent) not in sys.path:
    sys.path.insert(0, str(_SRC_DIR.parent))


# ---------------------------------------------------------------------------
# MCP Protocol (stdio JSON-RPC) — binary I/O to avoid Windows text-mode
# mangling \r\n in Content-Length header framing.
# ---------------------------------------------------------------------------

if hasattr(sys.stdin, "buffer"):
    _stdin = sys.stdin.buffer
else:
    _stdin = sys.stdin

if hasattr(sys.stdout, "buffer"):
    _stdout = sys.stdout.buffer
else:
    _stdout = sys.stdout


def _read_message() -> dict | None:
    """Read a JSON-RPC message from stdin (binary, Content-Length framed)."""
    headers: dict[str, str] = {}
    while True:
        raw_line = _stdin.readline()
        if not raw_line:
            return None
        line = raw_line.decode("utf-8", errors="replace").strip()
        if line == "":
            break
        if ":" in line:
            key, val = line.split(":", 1)
            headers[key.strip().lower()] = val.strip()

    content_length = int(headers.get("content-length", 0))
    if content_length == 0:
        return None

    body = _stdin.read(content_length)
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return None


def _send_message(msg: dict) -> None:
    """Send a JSON-RPC message to stdout (binary, Content-Length framed)."""
    body = json.dumps(msg).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    _stdout.write(header)
    _stdout.write(body)
    _stdout.flush()


def _send_result(req_id, result: dict) -> None:
    _send_message({"jsonrpc": "2.0", "id": req_id, "result": result})


def _send_error(req_id, code: int, message: str) -> None:
    _send_message({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


# ---------------------------------------------------------------------------
# Persistent Session
# ---------------------------------------------------------------------------

_SESSION_ID: str | None = None


def _get_agent():
    """Lazy-init the advisor agent with a persistent session."""
    global _SESSION_ID
    from munipal.engines.advisor.agent import AdvisorAgent
    from munipal.engines.advisor.session import AdvisorSession

    if _SESSION_ID:
        session = AdvisorSession.resume(_SESSION_ID)
    else:
        session = AdvisorSession()
        _SESSION_ID = session.session_id

    return AdvisorAgent(session=session)


# ---------------------------------------------------------------------------
# Tool Definitions (MCP format)
# ---------------------------------------------------------------------------

MCP_TOOLS = [
    {
        "name": "advisor_chat",
        "description": (
            "Send a message to the Muni-Pal Municipal Advisor. "
            "The advisor can search the bond corpus, run credit analysis, "
            "match banks to deals, benchmark risk, compare deals, and "
            "generate reports. It maintains conversation context across calls."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Your message to the municipal advisor",
                },
                "new_session": {
                    "type": "boolean",
                    "description": "Start a fresh session (default: false)",
                },
            },
            "required": ["message"],
        },
    },
    {
        "name": "search_deals",
        "description": (
            "Quick search of the Muni-Pal bond corpus by issuer, CUSIP, "
            "state, or keyword. Returns matching deal summaries."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query (issuer name, CUSIP, state, keyword)",
                },
                "sector": {
                    "type": "string",
                    "enum": ["wte", "waste", "healthcare"],
                    "description": "Sector filter (default: wte)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 10)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_deal_details",
        "description": (
            "Get comprehensive details for a bond deal by CUSIP: financials, "
            "security structure, ratings, risk factors, debt service schedule."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cusip": {
                    "type": "string",
                    "description": "CUSIP or document ID to look up",
                },
            },
            "required": ["cusip"],
        },
    },
    {
        "name": "corpus_stats",
        "description": (
            "Get summary statistics for the Muni-Pal bond corpus: "
            "total deals, ratings distribution, revenue streams, metrics."
        ),
        "inputSchema": {
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
    {
        "name": "score_banks",
        "description": (
            "Score and rank commercial banks across CRE Distress, Credit "
            "Enhancement, Direct Purchase, and Green Finance dimensions."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "enum": ["composite", "cre", "enhancement", "purchase", "green"],
                },
                "state": {"type": "string", "description": "Filter by state code"},
                "limit": {"type": "integer", "description": "Max results (default 15)"},
            },
        },
    },
    {
        "name": "match_banks",
        "description": (
            "Match banks to a specific deal profile: sector, amount, state, "
            "green eligibility. Returns ranked bank matches with role assignments."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "deal_type": {"type": "string", "description": "e.g. project_finance, general_obligation"},
                "deal_amount": {"type": "number", "description": "Deal par amount ($M)"},
                "state": {"type": "string", "description": "Project state code"},
                "sector": {"type": "string", "description": "Sector"},
                "green_eligible": {"type": "boolean"},
            },
            "required": ["deal_type", "deal_amount", "state"],
        },
    },
    {
        "name": "run_credit_analysis",
        "description": (
            "Run the full 5-stage credit analysis pipeline: 5 Cs assessment, "
            "bond sizing, 3-statement model, deal structuring, Standard Model. "
            "Returns comprehensive credit opinion with F_i score and S_Omega."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_name": {"type": "string"},
                "gross_revenue": {"type": "number", "description": "Annual gross revenue ($)"},
                "operating_expenses": {"type": "number", "description": "Annual OpEx ($)"},
                "total_project_cost": {"type": "number", "description": "Total project cost ($)"},
                "state": {"type": "string"},
                "sector": {"type": "string"},
                "maturity_years": {"type": "integer"},
                "target_dscr": {"type": "number"},
                "credit_rating": {"type": "string"},
            },
            "required": ["project_name", "gross_revenue", "operating_expenses", "total_project_cost"],
        },
    },
]


# ---------------------------------------------------------------------------
# Tool Execution
# ---------------------------------------------------------------------------

def _execute_tool(name: str, arguments: dict) -> dict:
    """Execute a Muni-Pal MCP tool."""
    from munipal.engines.advisor.executor import (
        execute_search_corpus,
        execute_get_deal_details,
        execute_get_corpus_stats,
        execute_score_banks,
        execute_match_banks,
        execute_run_credit_analysis,
    )

    if name == "advisor_chat":
        global _SESSION_ID
        if arguments.get("new_session"):
            _SESSION_ID = None
        agent = _get_agent()
        response = agent.query(arguments["message"])
        return {"response": response, "session_id": _SESSION_ID}

    tool_map = {
        "search_deals": execute_search_corpus,
        "get_deal_details": execute_get_deal_details,
        "corpus_stats": execute_get_corpus_stats,
        "score_banks": execute_score_banks,
        "match_banks": execute_match_banks,
        "run_credit_analysis": execute_run_credit_analysis,
    }

    fn = tool_map.get(name)
    if fn:
        return fn(arguments)

    return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# MCP Server Main Loop
# ---------------------------------------------------------------------------

def main():
    """Run the MCP server (stdio transport with Content-Length framing)."""
    while True:
        msg = _read_message()
        if msg is None:
            break

        req_id = msg.get("id")
        method = msg.get("method", "")

        if method == "initialize":
            _send_result(req_id, {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "munipal-advisor",
                    "version": "0.1.0",
                },
            })

        elif method == "notifications/initialized":
            pass  # No response needed

        elif method == "tools/list":
            _send_result(req_id, {"tools": MCP_TOOLS})

        elif method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            try:
                result = _execute_tool(tool_name, arguments)
                _send_result(req_id, {
                    "content": [
                        {"type": "text", "text": json.dumps(result, indent=2, default=str)},
                    ],
                })
            except Exception as exc:
                _send_result(req_id, {
                    "content": [
                        {"type": "text", "text": f"Error: {exc}"},
                    ],
                    "isError": True,
                })

        elif method == "resources/list":
            _send_result(req_id, {"resources": []})

        elif method == "prompts/list":
            _send_result(req_id, {"prompts": []})

        else:
            if req_id is not None:
                _send_error(req_id, -32601, f"Method not found: {method}")


if __name__ == "__main__":
    main()
