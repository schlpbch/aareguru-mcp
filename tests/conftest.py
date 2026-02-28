"""Pytest configuration and fixtures for Aareguru MCP tests.

This module provides reusable fixtures for:
- Configuration and settings management
- API client with proper lifecycle
- Mock responses and data fixtures
- Environment variable overrides
- Async test support
"""

import asyncio
import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from aareguru_mcp.client import AareguruClient
from aareguru_mcp.config import Settings

# ============================================================================
# EVENT LOOP FIXTURES
# ============================================================================


@pytest.fixture(scope="session")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create an event loop for the entire test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# CONFIGURATION FIXTURES
# ============================================================================


@pytest.fixture
def test_settings() -> Settings:
    """Create test settings with optimized values for testing."""
    return Settings(
        aareguru_base_url="https://aareguru.existenz.ch",
        app_name="aareguru-mcp-test",
        app_version="0.1.0-test",
        cache_ttl_seconds=60,
        min_request_interval_seconds=0,  # No rate limiting in tests
        log_level="DEBUG",
    )


@pytest.fixture(autouse=True)
def override_settings(monkeypatch: Any) -> None:
    """Override global settings for all tests.

    Automatically applied to every test to ensure consistent environment.
    Clears settings cache before and after to prevent cross-test contamination.
    """
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


# ============================================================================
# API CLIENT FIXTURES
# ============================================================================


@pytest.fixture
async def api_client(test_settings: Settings) -> AsyncMock:
    """Create API client for testing.

    Properly manages lifecycle with async context manager.
    """
    client = AareguruClient(settings=test_settings)
    yield client
    await client.close()


@pytest.fixture
def mock_api_client() -> AsyncMock:
    """Create a mock API client for unit testing.

    Useful for tests that need to mock HTTP responses without
    creating actual API client instances.
    """
    return AsyncMock(spec=AareguruClient)


# ============================================================================
# MOCK RESPONSE FIXTURES
# ============================================================================


@pytest.fixture
def sample_responses() -> dict[str, Any]:
    """Load sample API responses from fixtures.

    Returns empty dict if fixtures file doesn't exist,
    allowing tests to run without requiring fixture files.
    """
    fixture_path = Path(__file__).parent / "fixtures" / "sample_responses.json"
    if fixture_path.exists():
        with open(fixture_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


@pytest.fixture
def mock_aare_response() -> MagicMock:
    """Create a mock Aare current conditions response."""
    response = MagicMock()
    response.aare = MagicMock()
    response.aare.temperature = 17.2
    response.aare.temperature_text = "geil aber chli chalt"
    response.aare.temperature_text_short = "chalt"
    response.aare.temperature_prec = 0.1
    response.aare.location = "Bern"
    response.aare.location_long = "Bern, Schönau"
    response.aare.flow = 100.0
    response.aare.flow_text = "normal"
    response.aare.flow_scale_threshold = 220
    response.aare.height = 1.5
    response.aare.forecast2h = 18.0
    response.aare.forecast2h_text = "rising"
    return response


@pytest.fixture
def mock_weather_response() -> dict[str, Any]:
    """Create a mock weather API response."""
    return {
        "temp": 22.0,
        "humidity": 65,
        "description": "Partly cloudy",
    }


@pytest.fixture
def mock_forecast_response() -> list[dict[str, Any]]:
    """Create a mock forecast API response."""
    return [
        {"day": "Monday", "temp_max": 25, "temp_min": 15, "precipitation": 0},
        {"day": "Tuesday", "temp_max": 24, "temp_min": 14, "precipitation": 5},
        {"day": "Wednesday", "temp_max": 23, "temp_min": 13, "precipitation": 10},
    ]


# ============================================================================
# SERVICE LAYER FIXTURES
# ============================================================================


@pytest.fixture
def mock_service_response() -> dict[str, Any]:
    """Create a mock service layer response."""
    return {
        "city": "Bern",
        "temperature": 17.2,
        "temperature_text": "geil aber chli chalt",
        "flow": 100.0,
        "safety_assessment": "Safe - low flow",
    }


# ============================================================================
# TOOL FUNCTION FIXTURES
# ============================================================================


@pytest.fixture
def mock_tool_result() -> dict[str, Any]:
    """Create a mock tool function result."""
    return {
        "city": "Bern",
        "temperature": 17.2,
        "temperature_text": "geil aber chli chalt",
        "temperature_text_short": "chalt",
        "name": "Bern",
        "longname": "Bern, Schönau",
    }


@pytest.fixture
def mock_error_response() -> dict[str, str]:
    """Create a mock error response for failed tool calls."""
    return {
        "error": "Failed to fetch data from API"
    }
