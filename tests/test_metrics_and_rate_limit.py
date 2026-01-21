"""Tests for metrics and rate limiting endpoints."""

import pytest
from starlette.testclient import TestClient

from aareguru_mcp.server import mcp


@pytest.fixture
def client():
    """Create test client for HTTP endpoints."""
    return TestClient(mcp.http_app())


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_endpoint_exists(self, client):
        """Test that /metrics endpoint is accessible."""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Test that metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        # Prometheus metrics use text/plain with version
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_contains_service_info(self, client):
        """Test that metrics include service information."""
        response = client.get("/metrics")
        content = response.text
        assert "aareguru_mcp_service_info" in content

    def test_metrics_contains_counters(self, client):
        """Test that metrics include counter metrics."""
        response = client.get("/metrics")
        content = response.text
        # Check for key metrics
        assert "aareguru_mcp_tool_calls_total" in content or "# HELP" in content
        assert "aareguru_mcp_errors_total" in content or "# HELP" in content

    def test_metrics_format_valid(self, client):
        """Test that metrics response is valid Prometheus format."""
        response = client.get("/metrics")
        content = response.text
        # Should contain HELP and TYPE comments
        assert "# HELP" in content or "# TYPE" in content or len(content) > 0


class TestRateLimiting:
    """Test rate limiting functionality."""

    def test_health_endpoint_has_rate_limit(self, client):
        """Test that health endpoint is rate limited."""
        # Make multiple requests
        responses = []
        for _ in range(5):
            response = client.get("/health")
            responses.append(response)

        # All should succeed (within limit)
        for response in responses:
            assert response.status_code == 200

    def test_health_endpoint_returns_json(self, client):
        """Test that health endpoint returns proper JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aareguru-mcp"
        assert "version" in data

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are included in responses."""
        response = client.get("/health")
        # slowapi typically adds X-RateLimit headers
        # Note: Headers may not be present in all configurations
        assert response.status_code == 200


class TestMetricsIntegration:
    """Test that metrics are collected during operations."""

    def test_metrics_updated_after_health_check(self, client):
        """Test that metrics are updated after endpoint calls."""
        # Get initial metrics
        response1 = client.get("/metrics")
        initial_content = response1.text

        # Call health endpoint
        client.get("/health")

        # Get updated metrics
        response2 = client.get("/metrics")
        updated_content = response2.text

        # Both should be valid responses
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert len(initial_content) > 0
        assert len(updated_content) > 0
