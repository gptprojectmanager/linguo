#!/usr/bin/env python3
"""
Unit test suite for Linguo Remote Coach API Server (scripts/linguo_server.py).
Tests authentication, /health liveness and readiness probes, Prometheus /metrics exposition,
Gate 2 sensitive moderation, and error handling using httpx AsyncClient.
"""

import sys
from pathlib import Path
import pytest
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from scripts import linguo_server


@pytest.fixture
def client_factory():
    def _create():
        transport = httpx.ASGITransport(app=linguo_server.app)
        return httpx.AsyncClient(transport=transport, base_url="http://testserver")
    return _create


@pytest.mark.asyncio
class TestServerObservabilityAndHealth:
    async def test_health_liveness(self, client_factory):
        async with client_factory() as client:
            resp = await client.get("/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "ok"
            assert data["service"] == "linguo-remote-backend"
            assert "version" in data

    async def test_health_readiness(self, client_factory):
        async with client_factory() as client:
            resp = await client.get("/health/ready")
            assert resp.status_code in (200, 503)
            data = resp.json()
            assert "checks" in data
            assert "workspace_writable" in data["checks"]

    async def test_prometheus_metrics_exposition(self, client_factory):
        async with client_factory() as client:
            resp = await client.get("/metrics")
            assert resp.status_code == 200
            content = resp.text
            assert "linguo_requests_total" in content or "# HELP" in content
            assert "text/plain" in resp.headers.get("content-type", "")

    async def test_trace_id_header_propagation(self, client_factory):
        custom_trace = "trc-test-suite-999"
        async with client_factory() as client:
            resp = await client.get("/health", headers={"X-Trace-Id": custom_trace})
            assert resp.status_code == 200
            assert resp.headers.get("X-Trace-Id") == custom_trace


@pytest.mark.asyncio
class TestAuthenticationGate:
    async def test_unauthorized_missing_token(self, client_factory):
        async with client_factory() as client:
            resp = await client.post("/coach", json={"phrase": "I want to speak English"})
            assert resp.status_code == 401
            assert "Missing Authorization header" in resp.json()["detail"]

    async def test_forbidden_invalid_token(self, client_factory):
        async with client_factory() as client:
            resp = await client.post(
                "/coach",
                json={"phrase": "I want to speak English"},
                headers={"Authorization": "Bearer wrong-token-123"}
            )
            assert resp.status_code == 403
            assert "Invalid or unauthorized" in resp.json()["detail"]

    async def test_empty_phrase_bad_request(self, client_factory):
        async with client_factory() as client:
            resp = await client.post(
                "/coach",
                json={"phrase": "   "},
                headers={"Authorization": f"Bearer {linguo_server.API_SECRET_TOKEN}"}
            )
            assert resp.status_code == 400


@pytest.mark.asyncio
class TestGate2SafetyInServer:
    async def test_detect_sensitive_in_server(self):
        assert linguo_server.detect_sensitive_content("He bought an illegal gun") is True
        assert linguo_server.detect_sensitive_content("Heroin and cocaine dealer") is True
        assert linguo_server.detect_sensitive_content("Let's review grammar together") is False

    async def test_audit_sensitive_category_rejected(self, client_factory):
        async with client_factory() as client:
            resp = await client.post(
                "/audit",
                json={"category": "SENSITIVE_NO_CARD", "samples": []},
                headers={"Authorization": f"Bearer {linguo_server.API_SECRET_TOKEN}"}
            )
            assert resp.status_code == 400
            assert "Cannot audit" in resp.json()["detail"]


class TestJsonHelper:
    def test_clean_json_text_markdown_block(self):
        raw = "Here is your JSON:\n```json\n{\"test\": 123}\n```\nEnjoy!"
        cleaned = linguo_server.clean_json_text(raw)
        assert cleaned == '{"test": 123}'

    def test_clean_json_text_embedded_braces(self):
        raw = "Preamble {\"status\": \"ok\"} trailing text"
        cleaned = linguo_server.clean_json_text(raw)
        assert cleaned == '{"status": "ok"}'
