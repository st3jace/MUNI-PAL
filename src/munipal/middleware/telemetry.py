"""
OPS-1001 HTTP telemetry middleware.

Captures every HTTP request/response as a JSONL event for the OPS-1001
telemetry trend assessment pipeline.  Events are appended to a configurable
JSONL file that ``scripts/assess_ops1001_telemetry_trends.py`` consumes.

Usage in FastAPI::

    from munipal.middleware.telemetry import TelemetryMiddleware

    app.add_middleware(TelemetryMiddleware, jsonl_path="telemetry.jsonl")
"""

from __future__ import annotations

import json
import logging
import os
import threading
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("munipal.telemetry")

# Paths excluded from telemetry to avoid health-check noise.
_EXCLUDED_PATHS: frozenset[str] = frozenset({"/", "/health", "/healthz", "/ready", "/readyz"})


class TelemetryMiddleware:
    """Pure ASGI middleware that appends one JSONL line per HTTP request."""

    def __init__(
        self,
        app: Any,
        *,
        jsonl_path: str | os.PathLike[str] = "reports/phase10_postlaunch/ops1001_telemetry_events.jsonl",
        enabled: bool = True,
    ) -> None:
        self.app = app
        self.jsonl_path = str(jsonl_path)
        self.enabled = enabled
        self._lock = threading.Lock()

    async def __call__(self, scope: dict[str, Any], receive: Any, send: Any) -> None:
        if scope["type"] != "http" or not self.enabled:
            await self.app(scope, receive, send)
            return

        request_path: str = scope.get("path", "")
        if request_path in _EXCLUDED_PATHS:
            await self.app(scope, receive, send)
            return

        status_code: int | None = None
        body_chunks: list[bytes] = []
        capture_body = False

        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code, capture_body
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                # Only buffer the body for 403 responses (to detect cross-tenant detail).
                capture_body = status_code == 403
            elif message["type"] == "http.response.body" and capture_body:
                chunk = message.get("body", b"")
                if chunk:
                    body_chunks.append(chunk)
            await send(message)

        timestamp = datetime.now(UTC).isoformat()
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            # If the app raises without sending a response, record as 500.
            status_code = status_code or 500
            raise
        finally:
            if status_code is not None:
                cross_tenant = False
                if status_code == 403 and body_chunks:
                    try:
                        body_text = b"".join(body_chunks).decode("utf-8", errors="replace").lower()
                        cross_tenant = (
                            "cross-tenant" in body_text
                            or "cross tenant" in body_text
                            or "tenant isolation" in body_text
                        )
                    except Exception:
                        pass

                event: dict[str, Any] = {
                    "timestamp": timestamp,
                    "status_code": status_code,
                    "method": scope.get("method", ""),
                    "path": request_path,
                    "detail": _status_detail(status_code),
                    "cross_tenant_denied": cross_tenant,
                }
                self._write_event(event)

    def _write_event(self, event: dict[str, Any]) -> None:
        """Append a single JSONL line.  Thread-safe via lock."""
        line = json.dumps(event, default=str) + "\n"
        try:
            with self._lock:
                with open(self.jsonl_path, "a", encoding="utf-8") as fh:
                    fh.write(line)
        except OSError:
            logger.warning("Failed to write telemetry event to %s", self.jsonl_path, exc_info=True)


def _status_detail(code: int) -> str:
    if code < 300:
        return "ok" if code == 200 else "created" if code == 201 else str(code)
    if code == 401:
        return "Not authenticated"
    if code == 403:
        return "Forbidden"
    if code == 404:
        return "Not found"
    if code == 422:
        return "Validation error"
    if code >= 500:
        return "Internal server error"
    return str(code)
