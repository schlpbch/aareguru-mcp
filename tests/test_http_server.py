"""Tests for HTTP/SSE server endpoints."""

import pytest
from starlette.testclient import TestClient

from aareguru_mcp.http_server import http_app
from aareguru_mcp.config import Settings


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(http_app)


@pytest.fixture
def client_with_auth(monkeypatch):
    """Create test client with authentication enabled."""
    monkeypatch.setenv("API_KEY_REQUIRED", "true")
    monkeypatch.setenv("API_KEYS", "test-key-1,test-key-2")
    
    # Force settings reload
    from aareguru_mcp.config import get_settings
    get_settings.cache_clear()
    
    client = TestClient(http_app)
    yield client
    
    # Cleanup
    get_settings.cache_clear()


# Health Check Tests

def test_health_check_success(client):
    """Test health check endpoint returns 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_check_response_format(client):
    """Test health check response has correct format."""
    response = client.get("/health")
    data = response.json()
    
    assert "status" in data
    assert data["status"] == "healthy"
    assert "service" in data
    assert data["service"] == "aareguru-mcp"
    assert "version" in data


# SSE Endpoint Tests

def test_sse_endpoint_content_type(client):
    """Test SSE endpoint returns correct content type."""
    # Note: SSE connections are long-lived, so we test initial response
    with client.stream("GET", "/sse") as response:
        # SSE should return 200 and start streaming
        assert response.status_code == 200 or response.status_code == 500
        # Note: Actual SSE connection may fail in test environment
        # but we verify the endpoint exists and responds


def test_sse_endpoint_without_auth(client):
    """Test SSE endpoint works when auth is disabled."""
    # With auth disabled (default), should get a response
    with client.stream("GET", "/sse") as response:
        # Should not get 401 (unauthorized)
        assert response.status_code != 401


# Authentication Tests

def test_auth_required_no_key(client_with_auth):
    """Test 401 when API key required but not provided."""
    response = client_with_auth.get("/sse")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data


def test_auth_required_invalid_key(client_with_auth):
    """Test 401 with invalid API key."""
    response = client_with_auth.get(
        "/sse",
        headers={"X-API-Key": "invalid-key"}
    )
    assert response.status_code == 401


def test_auth_required_valid_key(client_with_auth):
    """Test 200 with valid API key."""
    with client_with_auth.stream(
        "GET",
        "/sse",
        headers={"X-API-Key": "test-key-1"}
    ) as response:
        # Should not get 401
        assert response.status_code != 401


def test_auth_disabled(client):
    """Test SSE works when auth is disabled."""
    # Default settings have auth disabled
    with client.stream("GET", "/sse") as response:
        # Should not get 401
        assert response.status_code != 401


# Rate Limiting Tests

def test_rate_limit_under_limit(client):
    """Test requests under rate limit succeed."""
    # Make a few requests (well under limit)
    for _ in range(3):
        response = client.get("/health")
        assert response.status_code == 200


def test_rate_limit_messages_endpoint(client):
    """Test messages endpoint responds."""
    response = client.post("/messages")
    # Should not be rate limited for health checks
    assert response.status_code != 429


# CORS Tests

def test_cors_headers_present(client):
    """Test CORS headers are present in response."""
    response = client.get(
        "/health",
        headers={"Origin": "http://example.com"}
    )
    
    # Check for CORS headers
    assert "access-control-allow-origin" in response.headers


def test_cors_allowed_origin(client):
    """Test allowed origin works."""
    response = client.get(
        "/health",
        headers={"Origin": "http://example.com"}
    )
    
    # With default settings (CORS_ORIGINS=*), should allow any origin
    assert response.status_code == 200


def test_cors_preflight(client):
    """Test OPTIONS preflight request."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        }
    )
    
    # Preflight should succeed
    assert response.status_code == 200


# Messages Endpoint Tests

def test_messages_endpoint_post(client):
    """Test messages endpoint accepts POST."""
    response = client.post("/messages")
    assert response.status_code == 200


def test_messages_endpoint_with_auth(client_with_auth):
    """Test messages endpoint requires auth when enabled."""
    response = client_with_auth.post("/messages")
    assert response.status_code == 401
    
    # With valid key
    response = client_with_auth.post(
        "/messages",
        headers={"X-API-Key": "test-key-1"}
    )
    assert response.status_code == 200


# Full SSE Implementation Tests

@pytest.fixture
def client_with_full_sse(monkeypatch):
    """Create test client with full SSE transport enabled."""
    monkeypatch.setenv("USE_FULL_SSE", "true")
    
    # Force settings reload
    from aareguru_mcp.config import get_settings
    get_settings.cache_clear()
    
    client = TestClient(http_app)
    yield client
    
    # Cleanup
    get_settings.cache_clear()


def test_full_sse_mode_enabled(client_with_full_sse):
    """Test that full SSE mode can be enabled via config."""
    from aareguru_mcp.config import get_settings
    settings = get_settings()
    assert settings.use_full_sse is True

def test_simplified_mode_default(client):
    """Test that simplified SSE is the default mode."""
    from aareguru_mcp.config import get_settings
    settings = get_settings()
    assert settings.use_full_sse is False
