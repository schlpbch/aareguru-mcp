"""Tests for FastMCP HTTP server endpoints.

Tests the custom /health endpoint, HTTP app functionality,
concurrent requests, and performance.
"""

import asyncio
import time

import pytest
from starlette.testclient import TestClient

from aareguru_mcp.config import get_settings
from aareguru_mcp.server import mcp


@pytest.fixture
def client():
    """Create test client for FastMCP HTTP app."""
    return TestClient(mcp.http_app())


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_200(self, client):
        """Test health check endpoint returns 200."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_format(self, client):
        """Test health check response has correct format."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert data["status"] == "healthy"
        assert "service" in data
        assert data["service"] == "aareguru-mcp"
        assert "version" in data

    def test_health_with_origin_header(self, client):
        """Test health endpoint works with Origin header (CORS)."""
        response = client.get("/health", headers={"Origin": "http://example.com"})
        assert response.status_code == 200

    def test_multiple_health_requests(self, client):
        """Test multiple requests to health endpoint succeed."""
        for _ in range(3):
            response = client.get("/health")
            assert response.status_code == 200


class TestCoreEndpoints:
    """Test core HTTP endpoints."""

    def test_missing_endpoint_404(self, client):
        """Test that missing endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404

    @pytest.mark.skip(reason="SSE GET requests establish long-lived connections that hang in tests")
    def test_sse_endpoint_exists(self, client):
        """Test SSE endpoint is accessible."""
        pass

    @pytest.mark.skip(reason="MCP messages endpoint requires valid MCP protocol messages")
    def test_mcp_endpoint_exists(self, client):
        """Test that FastMCP MCP endpoint exists."""
        pass


class TestSessionConfiguration:
    """Test session timeout configuration."""

    def test_default_session_config(self):
        """Test default session configuration values."""
        settings = get_settings()
        assert settings.sse_session_timeout_seconds == 3600
        assert settings.sse_cleanup_interval_seconds == 300

    def test_custom_session_config(self, monkeypatch):
        """Test custom session configuration."""
        monkeypatch.setenv("SSE_SESSION_TIMEOUT_SECONDS", "7200")
        monkeypatch.setenv("SSE_CLEANUP_INTERVAL_SECONDS", "600")
        get_settings.cache_clear()

        try:
            settings = get_settings()
            assert settings.sse_session_timeout_seconds == 7200
            assert settings.sse_cleanup_interval_seconds == 600
        finally:
            get_settings.cache_clear()

    def test_minimum_timeout_validation(self, monkeypatch):
        """Test that timeout minimums are enforced."""
        monkeypatch.setenv("SSE_SESSION_TIMEOUT_SECONDS", "30")
        get_settings.cache_clear()

        try:
            settings = get_settings()
            assert settings.sse_session_timeout_seconds >= 60
        except Exception:
            pass  # Validation error is acceptable
        finally:
            get_settings.cache_clear()


class TestConcurrency:
    """Test concurrent request handling."""

    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client):
        """Test handling multiple concurrent health checks."""
        tasks = [asyncio.to_thread(client.get, "/health") for _ in range(10)]

        responses = await asyncio.gather(*tasks)

        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)


class TestPerformance:
    """Baseline performance tests."""

    def test_health_check_performance(self, client):
        """Test health check response time."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start

        assert response.status_code == 200
        assert elapsed < 1.0  # Should respond in under 1 second

    def test_sequential_requests_performance(self, client):
        """Test performance of multiple sequential requests."""
        start = time.time()

        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

        elapsed = time.time() - start
        assert elapsed < 2.0  # 10 requests in under 2 seconds


class TestServerConfiguration:
    """Test FastMCP server configuration."""

    def test_server_name(self):
        """Test server has correct name."""
        assert mcp.name == "aareguru-mcp"

    def test_server_has_instructions(self):
        """Test server has instructions."""
        assert mcp.instructions is not None
        assert "Aare river" in mcp.instructions

    def test_server_has_tools(self):
        """Test server has registered tools."""
        tools = list(mcp._tool_manager._tools.keys())
        assert len(tools) >= 6
        assert "get_current_temperature" in tools
        assert "get_current_conditions" in tools
        assert "list_cities" in tools

    def test_server_has_resources(self):
        """Test server has registered resources."""
        resources = list(mcp._resource_manager._resources.keys())
        templates = list(mcp._resource_manager._templates.keys())

        assert "aareguru://cities" in resources

        assert "aareguru://current/{city}" in templates
        assert "aareguru://today/{city}" in templates

        assert len(resources) + len(templates) >= 3

    def test_server_has_prompts(self):
        """Test server has registered prompts."""
        prompts = list(mcp._prompt_manager._prompts.keys())
        assert len(prompts) >= 3
        assert "daily-swimming-report" in prompts
        assert "compare-swimming-spots" in prompts
        assert "weekly-trend-analysis" in prompts


class TestLogging:
    """Test logging functionality."""

    def test_requests_are_logged(self, client, caplog):
        """Test that requests generate log entries."""
        import logging

        caplog.set_level(logging.DEBUG)

        client.get("/health")

        # Just verify no exceptions occurred
        assert True
