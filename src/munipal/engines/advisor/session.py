"""Session management for the Municipal Advisor agent.

File-based JSON persistence for conversation state, allowing
multi-turn conversations to resume across sessions.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

logger = logging.getLogger(__name__)

DEFAULT_SESSIONS_DIR = Path(__file__).resolve().parents[4] / "data" / "advisor_sessions"


class AdvisorSession:
    """Persistent conversation session backed by JSON files."""

    def __init__(
        self,
        session_id: str | None = None,
        storage_dir: Path | None = None,
    ):
        self.session_id = session_id or str(uuid4())
        self.storage_dir = storage_dir or DEFAULT_SESSIONS_DIR
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.storage_dir / f"{self.session_id}.json"

        if self.file_path.exists():
            self._load()
        else:
            self.data: dict = {
                "session_id": self.session_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "messages": [],
                "metadata": {},
                "pending_confirmation": None,
            }

    # ── Persistence ────────────────────────────────────────────────────

    def _load(self) -> None:
        with open(self.file_path, encoding="utf-8") as f:
            self.data = json.load(f)

    def save(self) -> None:
        self.data["updated_at"] = datetime.now(timezone.utc).isoformat()
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, default=str)

    # ── Message History ────────────────────────────────────────────────

    @property
    def messages(self) -> list[dict]:
        return self.data["messages"]

    @messages.setter
    def messages(self, value: list[dict]) -> None:
        self.data["messages"] = value

    def add_user_message(self, text: str) -> None:
        self.data["messages"].append({"role": "user", "content": text})

    def add_assistant_message(self, text: str) -> None:
        self.data["messages"].append({"role": "assistant", "content": text})

    # ── Metadata ───────────────────────────────────────────────────────

    @property
    def metadata(self) -> dict:
        return self.data["metadata"]

    def set_metadata(self, key: str, value) -> None:
        self.data["metadata"][key] = value
        self.save()

    # ── Confirmation Queue ─────────────────────────────────────────────

    @property
    def pending_confirmation(self) -> dict | None:
        return self.data.get("pending_confirmation")

    def set_pending_confirmation(self, tool_name: str, tool_input: dict) -> None:
        self.data["pending_confirmation"] = {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "requested_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def clear_pending_confirmation(self) -> dict | None:
        pending = self.data.get("pending_confirmation")
        self.data["pending_confirmation"] = None
        self.save()
        return pending

    # ── Class Methods ──────────────────────────────────────────────────

    @classmethod
    def list_sessions(cls, storage_dir: Path | None = None) -> list[dict]:
        d = storage_dir or DEFAULT_SESSIONS_DIR
        if not d.exists():
            return []
        sessions = []
        for f in sorted(d.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(f, encoding="utf-8") as fh:
                    data = json.load(fh)
                sessions.append({
                    "session_id": data["session_id"],
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at"),
                    "message_count": len(data.get("messages", [])),
                    "metadata": data.get("metadata", {}),
                })
            except (json.JSONDecodeError, KeyError):
                continue
        return sessions

    @classmethod
    def resume(cls, session_id: str, storage_dir: Path | None = None) -> AdvisorSession:
        return cls(session_id=session_id, storage_dir=storage_dir)

    @classmethod
    def delete(cls, session_id: str, storage_dir: Path | None = None) -> bool:
        d = storage_dir or DEFAULT_SESSIONS_DIR
        path = d / f"{session_id}.json"
        if path.exists():
            path.unlink()
            return True
        return False
