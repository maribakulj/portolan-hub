"""Smoke tests for the meta endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient

from portolan_api.main import create_app


def test_health_returns_ok() -> None:
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "timestamp" in body


def test_version_exposes_metadata() -> None:
    client = TestClient(create_app())
    resp = client.get("/version")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "portolan-hub"
    assert body["api"] == "0"
    assert "version" in body


def test_openapi_schema_is_served() -> None:
    client = TestClient(create_app())
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    schema = resp.json()
    assert schema["openapi"].startswith("3.")
    assert "/health" in schema["paths"]


def test_unknown_route_returns_uniform_error() -> None:
    client = TestClient(create_app())
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "http_404"
