"""Tests for city normalization, multi-city differentiation, and historical date formats."""

from unittest.mock import AsyncMock, patch

import pytest

from aareguru_mcp import tools
from aareguru_mcp.client import AareguruClient

# ---------------------------------------------------------------------------
# City normalization
# ---------------------------------------------------------------------------

_CITY_NORM_CASES = [
    ("Bern", "bern"),
    ("BERN", "bern"),
    ("bern", "bern"),
    ("  Thun  ", "thun"),
    ("OLTEN", "olten"),
    ("Basel", "basel"),
]


@pytest.mark.parametrize("raw,expected", _CITY_NORM_CASES)
def test_normalize_city(raw: str, expected: str) -> None:
    assert AareguruClient._normalize_city(raw) == expected


def _make_mock_client(city_responses: dict) -> AsyncMock:
    """Build a mock AareguruClient that returns different data per city."""

    async def _get_current(city: str):
        key = city.strip().lower()
        data = city_responses.get(key, city_responses.get("bern"))
        mock = AsyncMock()
        mock.aare = AsyncMock()
        mock.aare.temperature = data["temperature"]
        mock.aare.flow = data["flow"]
        mock.aare.location = data["location"]
        mock.aare.location_long = data["location"]
        mock.aare.height = 1.0
        mock.aare.temperature_text = data.get("text", "geil")
        mock.aare.forecast2h = data["temperature"] + 0.2
        mock.aare.forecast2h_text = None
        mock.aare.warning = None
        mock.aare.flow_gefahrenstufe = 1
        mock.weather = None
        mock.sun = None
        mock.forecast = []
        mock.aarepast = []
        mock.seasonal_advice = None
        return mock

    client = AsyncMock()
    client.get_current = _get_current
    client.get_today = AsyncMock(side_effect=Exception("fallback"))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


_CITY_DATA = {
    "bern": {"temperature": 18.5, "flow": 95.0, "location": "Bern"},
    "thun": {"temperature": 20.1, "flow": 110.0, "location": "Thun"},
    "olten": {"temperature": 16.3, "flow": 80.0, "location": "Olten"},
    "basel": {"temperature": 17.8, "flow": 140.0, "location": "Basel"},
}


@pytest.mark.asyncio
@pytest.mark.parametrize("city,expected_temp", [
    ("Bern", 18.5),
    ("Thun", 20.1),
    ("Olten", 16.3),
    ("Basel", 17.8),
])
async def test_different_cities_return_different_temperatures(
    city: str, expected_temp: float
) -> None:
    """Each city identifier must resolve to its own distinct data."""
    with patch("aareguru_mcp.service.AareguruClient") as MockClient:
        MockClient.return_value = _make_mock_client(_CITY_DATA)
        result = await tools.get_current_temperature(city)
    assert result.get("temperature") == expected_temp, (
        f"Expected {expected_temp}°C for {city}, got {result.get('temperature')}"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("city_a,city_b", [
    ("Bern", "Thun"),
    ("Olten", "Basel"),
])
async def test_two_cities_differ(city_a: str, city_b: str) -> None:
    """Two distinct cities must not return identical temperatures."""
    with patch("aareguru_mcp.service.AareguruClient") as MockClient:
        MockClient.return_value = _make_mock_client(_CITY_DATA)
        result_a = await tools.get_current_temperature(city_a)
        result_b = await tools.get_current_temperature(city_b)
    assert result_a.get("temperature") != result_b.get("temperature"), (
        f"{city_a} and {city_b} should return different temperatures"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("variant", ["Bern", "BERN", "bern", " Bern "])
async def test_city_case_insensitive(variant: str) -> None:
    """City lookup is case-insensitive — all variants resolve to the same result."""
    with patch("aareguru_mcp.service.AareguruClient") as MockClient:
        MockClient.return_value = _make_mock_client(_CITY_DATA)
        result = await tools.get_current_temperature(variant)
    assert result.get("temperature") == 18.5


# ---------------------------------------------------------------------------
# Historical data — date format coverage
# ---------------------------------------------------------------------------

_MOCK_HISTORY = [
    {"time": 1700000000, "aare": 15.0, "flow": 80.0},
    {"time": 1700003600, "aare": 15.2, "flow": 81.0},
]


def _history_mock():
    client = AsyncMock()
    client.get_history = AsyncMock(return_value=_MOCK_HISTORY)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    return client


@pytest.mark.asyncio
@pytest.mark.parametrize("start,end", [
    ("-7 days", "now"),
    ("-1 week", "now"),
    ("-30 days", "now"),
    ("-1 month", "now"),
    ("2025-01-01", "2025-01-07"),
    ("2025-01-01T00:00:00Z", "2025-01-07T23:59:59Z"),
    ("1700000000", "1700090000"),
])
async def test_historical_data_date_formats(start: str, end: str) -> None:
    """get_historical_data accepts all documented date formats."""
    with patch("aareguru_mcp.service.AareguruClient") as MockClient:
        MockClient.return_value = _history_mock()
        result = await tools.get_historical_data("Bern", start, end)
    assert isinstance(result, (dict, list)), f"Unexpected result type for {start!r}"


@pytest.mark.asyncio
async def test_historical_data_invalid_range_returns_error() -> None:
    """End before start must return an error dict, not raise."""
    with patch("aareguru_mcp.service.AareguruClient") as MockClient:
        MockClient.return_value = _history_mock()
        result = await tools.get_historical_data("Bern", "now", "-7 days")
    assert "error" in result, "Expected error key for inverted date range"


@pytest.mark.asyncio
@pytest.mark.parametrize("city", ["Bern", "Thun", "Olten"])
async def test_historical_data_different_cities(city: str) -> None:
    """Historical data tool accepts any valid city without falling back to Bern."""
    captured: list[str] = []

    async def _get_history(c: str, s: str, e: str):
        captured.append(c)
        return _MOCK_HISTORY

    client = AsyncMock()
    client.get_history = _get_history
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch("aareguru_mcp.service.AareguruClient") as MockClient:
        MockClient.return_value = client
        await tools.get_historical_data(city, "-7 days", "now")

    assert captured, "get_history was never called"
    assert captured[0] == city.strip().lower(), (
        f"Expected city '{city.strip().lower()}', client received '{captured[0]}'"
    )


# ---------------------------------------------------------------------------
# _estimate_days in server (uses _resolve_timestamp internally)
# ---------------------------------------------------------------------------

def test_estimate_days_relative() -> None:
    from aareguru_mcp.server import _estimate_days
    assert abs(_estimate_days("-7 days") - 7) < 1


def test_estimate_days_weeks() -> None:
    from aareguru_mcp.server import _estimate_days
    assert abs(_estimate_days("-2 weeks") - 14) < 1


def test_estimate_days_unix_timestamp_recent() -> None:
    from datetime import UTC, datetime

    from aareguru_mcp.server import _estimate_days

    # A timestamp 10 days ago should give ~10
    ts = int(datetime.now(UTC).timestamp()) - 10 * 86400
    days = _estimate_days(str(ts))
    assert 9 < days < 11


def test_estimate_days_unix_timestamp_does_not_overflow() -> None:
    """A very recent Unix timestamp must not report thousands of days."""
    from datetime import UTC, datetime

    from aareguru_mcp.server import _estimate_days

    ts = int(datetime.now(UTC).timestamp()) - 3600  # 1 hour ago
    assert _estimate_days(str(ts)) < 1
