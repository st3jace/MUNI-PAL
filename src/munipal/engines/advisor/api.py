"""Municipal Advisor API — FastAPI endpoints with SSE streaming.

Run with:
    uvicorn munipal.engines.advisor.api:app --port 8300 --reload

Or:
    python -m munipal.engines.advisor
"""

from __future__ import annotations

import json
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .agent import AdvisorAgent
from .session import AdvisorSession

logger = logging.getLogger("advisor.api")

app = FastAPI(
    title="Muni-Pal Municipal Advisor",
    description=(
        "Agentic municipal bond advisor — orchestrates credit analysis, "
        "bank matching, corpus search, and report generation through "
        "natural language conversation."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3001",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response Models ─────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message")
    session_id: Optional[str] = Field(None, description="Session ID to resume")


class ChatResponse(BaseModel):
    session_id: str
    response: str
    message_count: int


class SessionInfo(BaseModel):
    session_id: str
    created_at: str | None
    updated_at: str | None
    message_count: int
    metadata: dict


# ── Routes ─────────────────────────────────────────────────────────────


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": "0.1.0", "engine": "municipal_advisor"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Send a message and get a complete response (non-streaming)."""
    session = (
        AdvisorSession.resume(request.session_id)
        if request.session_id
        else AdvisorSession()
    )
    agent = AdvisorAgent(session=session)

    try:
        response_text = agent.query(request.message)
    except Exception as e:
        logger.exception("Agent query failed")
        raise HTTPException(status_code=500, detail=str(e))

    return ChatResponse(
        session_id=session.session_id,
        response=response_text,
        message_count=len(session.messages),
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Send a message and stream the response via SSE."""
    session = (
        AdvisorSession.resume(request.session_id)
        if request.session_id
        else AdvisorSession()
    )
    agent = AdvisorAgent(session=session)

    def event_generator():
        # Send session_id first
        yield f"data: {json.dumps({'type': 'session', 'session_id': session.session_id})}\n\n"

        try:
            for event in agent.query_stream(request.message):
                yield f"data: {json.dumps(event, default=str)}\n\n"
        except Exception as e:
            logger.exception("Streaming failed")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── Session Management ─────────────────────────────────────────────────


@app.get("/sessions", response_model=list[SessionInfo])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100),
) -> list[SessionInfo]:
    """List recent advisor sessions."""
    sessions = AdvisorSession.list_sessions()
    return [
        SessionInfo(
            session_id=s["session_id"],
            created_at=s.get("created_at"),
            updated_at=s.get("updated_at"),
            message_count=s.get("message_count", 0),
            metadata=s.get("metadata", {}),
        )
        for s in sessions[:limit]
    ]


@app.get("/sessions/{session_id}")
async def get_session(session_id: str) -> dict:
    """Get full session history."""
    try:
        session = AdvisorSession.resume(session_id)
        return {
            "session_id": session.session_id,
            "created_at": session.data.get("created_at"),
            "updated_at": session.data.get("updated_at"),
            "messages": session.messages,
            "metadata": session.metadata,
            "pending_confirmation": session.pending_confirmation,
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Session not found")


@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str) -> dict:
    """Delete a session."""
    if AdvisorSession.delete(session_id):
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


# ── Entrypoint ─────────────────────────────────────────────────────────


def main() -> None:
    import uvicorn
    uvicorn.run(
        "munipal.engines.advisor.api:app",
        host="0.0.0.0",
        port=8300,
        reload=True,
    )


if __name__ == "__main__":
    main()
