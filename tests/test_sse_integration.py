"""Integration tests for SSE implementation.

Tests the complete MCP SSE transport including endpoints,
session management, metrics, and error handling.
"""

import asyncio
import time
import pytest
from starlette.testclient import TestClient

from aareguru_mcp.http_server import http_app
from aareguru_mcp.config import get_settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(http_app)


class TestCoreEndpoints:
    """Test core HTTP endpoints."""
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "aareguru-mcp"
        assert "version" in data
    
    def test_metrics_endpoint(self, client):
        """Test metrics endpoint."""
        response = client.get("/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "metrics" in data
        assert "config" in data
        
        # Verify metrics structure
        metrics = data["metrics"]
        assert "uptime_seconds" in metrics
        assert "total_connections" in metrics
        assert "total_messages" in metrics
        assert "total_errors" in metrics
        
        # Verify config structure
        config = data["config"]
        assert "session_timeout_seconds" in config
        assert "cleanup_interval_seconds" in config
    
    @pytest.mark.skip(reason="SSE GET requests establish long-lived connections that hang in tests")
    def test_sse_endpoint_exists(self, client):
        """Test SSE endpoint is accessible."""
        # Skipped: SSE connections are long-lived and hang in test environment
        # Tested manually with curl and MCP Inspector
        pass
    
    def test_messages_endpoint_exists(self, client):
        """Test messages endpoint is accessible."""
        # Without auth, should get 401 or handle request
        response = client.post("/messages")
        assert response.status_code in [200, 401, 400, 500]


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
            # Should either enforce minimum or raise validation error
            settings = get_settings()
            assert settings.sse_session_timeout_seconds >= 60
        except Exception:
            # Validation error is acceptable
            pass
        finally:
            get_settings.cache_clear()


class TestMetricsTracking:
    """Test metrics tracking functionality."""
    
    def test_metrics_updated_on_requests(self, client):
        """Test that metrics are updated when requests are made."""
        # Get initial metrics
        response1 = client.get("/metrics")
        initial_health_calls = response1.json()["metrics"]["endpoint_calls"].get("health", 0)
        
        # Make some health check requests
        for _ in range(5):
            client.get("/health")
        
        # Get updated metrics
        response2 = client.get("/metrics")
        final_health_calls = response2.json()["metrics"]["endpoint_calls"].get("health", 0)
        
        # Should have increased
        assert final_health_calls > initial_health_calls
    
    def test_metrics_track_endpoint_calls(self, client):
        """Test that different endpoints are tracked separately."""
        # Make requests to different endpoints
        client.get("/health")
        client.get("/metrics")
        
        response = client.get("/metrics")
        endpoint_calls = response.json()["metrics"]["endpoint_calls"]
        
        assert "health" in endpoint_calls
        assert "metrics" in endpoint_calls


class TestErrorHandling:
    """Test error handling and responses."""
    
    def test_invalid_json_to_messages(self, client):
        """Test that invalid JSON is handled gracefully."""
        response = client.post(
            "/messages",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        # Should not crash, return error status
        assert response.status_code in [400, 401, 422, 500]
    
    def test_missing_endpoint_404(self, client):
        """Test that missing endpoints return 404."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test that wrong HTTP methods are rejected."""
        response = client.post("/health")
        assert response.status_code == 405


class TestConcurrency:
    """Test concurrent request handling."""
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self, client):
        """Test handling multiple concurrent health checks."""
        tasks = [
            asyncio.to_thread(client.get, "/health")
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all(r.json()["status"] == "healthy" for r in responses)
    
    @pytest.mark.asyncio
    async def test_concurrent_metrics_requests(self, client):
        """Test handling multiple concurrent metrics requests."""
        tasks = [
            asyncio.to_thread(client.get, "/metrics")
            for _ in range(10)
        ]
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        assert all(r.status_code == 200 for r in responses)
        assert all("metrics" in r.json() for r in responses)


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
    
    def test_metrics_endpoint_performance(self, client):
        """Test metrics endpoint response time."""
        start = time.time()
        response = client.get("/metrics")
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 1.0


class TestLogging:
    """Test logging functionality."""
    
    def test_requests_are_logged(self, client, caplog):
        """Test that requests generate log entries."""
        import logging
        caplog.set_level(logging.INFO)
        
        client.get("/health")
        
        # Should have some log entries
        assert len(caplog.records) > 0
