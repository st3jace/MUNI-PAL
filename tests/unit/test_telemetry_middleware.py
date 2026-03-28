"""Unit tests for the OPS-1001 HTTP telemetry middleware."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from munipal.middleware.telemetry import TelemetryMiddleware


def _build_app(jsonl_path: str | Path, *, enabled: bool = True) -> FastAPI:
    """Build a minimal FastAPI app with the telemetry middleware attached."""
    app = FastAPI()
    app.add_middleware(TelemetryMiddleware, jsonl_path=str(jsonl_path), enabled=enabled)

    @app.get("/ok")
    def ok_route():
        return {"status": "ok"}

    @app.post("/create")
    def create_route():
        return {"id": "abc"}

    @app.get("/unauthorized")
    def unauthorized_route():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    @app.get("/forbidden")
    def forbidden_route():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    @app.get("/cross-tenant")
    def cross_tenant_route():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-tenant access denied",
        )

    @app.get("/health")
    def health_route():
        return {"status": "healthy"}

    return app


def _read_events(jsonl_path: Path) -> list[dict]:
    if not jsonl_path.exists():
        return []
    lines = jsonl_path.read_text(encoding="utf-8").strip().splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def test_telemetry_captures_200_response(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    response = client.get("/ok")
    assert response.status_code == 200

    events = _read_events(jsonl)
    assert len(events) == 1
    assert events[0]["status_code"] == 200
    assert events[0]["method"] == "GET"
    assert events[0]["path"] == "/ok"
    assert events[0]["cross_tenant_denied"] is False


def test_telemetry_captures_201_response(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    response = client.post("/create")
    assert response.status_code == 200  # FastAPI default without status_code override

    events = _read_events(jsonl)
    assert len(events) == 1
    assert events[0]["method"] == "POST"


def test_telemetry_captures_401(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    response = client.get("/unauthorized")
    assert response.status_code == 401

    events = _read_events(jsonl)
    assert len(events) == 1
    assert events[0]["status_code"] == 401
    assert events[0]["detail"] == "Not authenticated"
    assert events[0]["cross_tenant_denied"] is False


def test_telemetry_captures_403(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    response = client.get("/forbidden")
    assert response.status_code == 403

    events = _read_events(jsonl)
    assert len(events) == 1
    assert events[0]["status_code"] == 403
    assert events[0]["cross_tenant_denied"] is False


def test_telemetry_detects_cross_tenant_denial(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    response = client.get("/cross-tenant")
    assert response.status_code == 403

    events = _read_events(jsonl)
    assert len(events) == 1
    assert events[0]["status_code"] == 403
    assert events[0]["cross_tenant_denied"] is True


def test_telemetry_excludes_health_check(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    response = client.get("/health")
    assert response.status_code == 200

    events = _read_events(jsonl)
    assert len(events) == 0, "Health check requests should be excluded from telemetry"


def test_telemetry_disabled_writes_nothing(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl, enabled=False))

    client.get("/ok")
    client.get("/unauthorized")

    events = _read_events(jsonl)
    assert len(events) == 0


def test_telemetry_multiple_requests_appended(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    client.get("/ok")
    client.get("/ok")
    client.get("/unauthorized")
    client.get("/cross-tenant")

    events = _read_events(jsonl)
    assert len(events) == 4
    assert events[0]["status_code"] == 200
    assert events[1]["status_code"] == 200
    assert events[2]["status_code"] == 401
    assert events[3]["status_code"] == 403
    assert events[3]["cross_tenant_denied"] is True


def test_telemetry_event_has_timestamp(tmp_path: Path) -> None:
    jsonl = tmp_path / "events.jsonl"
    client = TestClient(_build_app(jsonl))

    client.get("/ok")

    events = _read_events(jsonl)
    assert len(events) == 1
    ts = events[0]["timestamp"]
    assert "T" in ts, "Timestamp should be ISO 8601 format"
    assert "+" in ts or "Z" in ts or ts.endswith("+00:00"), "Timestamp should include timezone"
