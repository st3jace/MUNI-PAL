"""ELA-56 public sensing deployment route-boundary tests."""

from fastapi.testclient import TestClient

from munipal.sensing_app import app as sensing_app
from munipal.services.sensing_pilot_funnel import SENSING_PILOT_FUNNEL_CONTRACT


def _route_paths(app):
    return {getattr(route, "path", "") for route in app.routes}


def test_public_sensing_app_does_not_mount_bfms_admin_route_families():
    """Standalone public deployment must not mount the full BFMS/admin API."""
    paths = _route_paths(sensing_app)
    blocked_prefixes = SENSING_PILOT_FUNNEL_CONTRACT.deployment_scope.blocked_bfms_route_prefixes

    for prefix in blocked_prefixes:
        assert not any(path.startswith(prefix) for path in paths), prefix


def test_public_sensing_app_bfms_admin_urls_return_not_found():
    """Representative BFMS/admin URLs should not resolve in the public app at all."""
    client = TestClient(sensing_app)

    blocked_urls = [
        "/api/v1/auth/login",
        "/api/v1/projects/",
        "/api/v1/artifacts/upload",
        "/api/v1/facts/",
        "/api/v1/deal-documents/",
        "/api/v1/templates/",
        "/api/v1/stripe/create-checkout-session",
    ]

    for url in blocked_urls:
        response = client.get(url)
        assert response.status_code == 404, url


def test_public_sensing_app_keeps_sensing_admin_routes_authenticated_or_excluded():
    """Sensing lead-admin routes may exist, but only behind auth in public deployment."""
    paths = _route_paths(sensing_app)
    client = TestClient(sensing_app)

    for route in SENSING_PILOT_FUNNEL_CONTRACT.deployment_scope.protected_sensing_admin_routes:
        concrete_route = route.replace("{lead_id}", "00000000-0000-4000-8000-000000000001")
        if route not in paths:
            response = client.get(concrete_route)
            assert response.status_code == 404, route
            continue

        method = "delete" if route == "/api/v1/sensing/leads/{lead_id}" else "get"
        if route.endswith("/funnel"):
            method = "patch"
        elif route.endswith("/convert-to-project"):
            method = "post"
        response = getattr(client, method)(concrete_route)
        assert response.status_code in {401, 403}, route


def test_public_sensing_deployment_document_names_sensing_app_entrypoint():
    doc = "docs/architecture/SENSING_PILOT_FUNNEL.md"
    text = open(doc, encoding="utf-8").read().lower()

    assert "munipal.sensing_app" in text
    assert "do not deploy munipal.main" in text
    assert "route-boundary" in text
