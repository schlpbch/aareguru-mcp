"""Pytest configuration and fixtures for Aareguru MCP tests."""

import json
from pathlib import Path
from typing import Any

import pytest

from aareguru_mcp.client import AareguruClient
from aareguru_mcp.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with overrides."""
    return Settings(
        aareguru_base_url="https://aareguru.existenz.ch",
        app_name="aareguru-mcp-test",
        app_version="0.1.0-test",
        cache_ttl_seconds=60,
        min_request_interval_seconds=0,  # No rate limiting in tests
        log_level="DEBUG",
    )


@pytest.fixture
def sample_responses() -> dict[str, Any]:
    """Load sample API responses from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_responses.json"
    if fixture_path.exists():
        with open(fixture_path) as f:
            return json.load(f)
    return {}


@pytest.fixture
async def api_client(test_settings: Settings) -> AareguruClient:
    """Create API client for testing."""
    client = AareguruClient(settings=test_settings)
    yield client
    await client.close()


@pytest.fixture(autouse=True)
def override_settings(monkeypatch):
    """Override global settings for all tests."""
    from aareguru_mcp.config import get_settings

    # Set environment variables for testing
    monkeypatch.setenv("MIN_REQUEST_INTERVAL_SECONDS", "0")
    monkeypatch.setenv("CACHE_TTL_SECONDS", "60")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    # Clear cache to force reload with new env vars
    get_settings.cache_clear()

    yield

    # Clear cache again
    get_settings.cache_clear()
