"""Tests for FastMCP App UIs.

Tests conditions_dashboard, historical_chart, and compare_cities_table.
All tests mock AareguruService to avoid real API calls.
"""

from unittest.mock import AsyncMock, patch

import pytest
from prefab_ui.app import PrefabApp

from aareguru_mcp.apps import (
    _safety_badge,
    compare_cities_table,
    conditions_dashboard,
    historical_chart,
)

# ---------------------------------------------------------------------------
# Helper tests
# ---------------------------------------------------------------------------


class TestSafetyBadge:
    def test_none_flow_is_unknown(self):
        label, variant, color = _safety_badge(None)
        assert label == "Unbekannt"
        assert variant == "secondary"

    def test_safe_below_100(self):
        label, variant, color = _safety_badge(50)
        assert label == "Sicher"
        assert variant == "success"
        assert color == "#00b2aa"

    def test_moderate_100_to_220(self):
        label, variant, color = _safety_badge(150)
        assert label == "Moderat"
        assert variant == "info"

    def test_elevated_220_to_300(self):
        label, variant, color = _safety_badge(250)
        assert label == "Erhöht"
        assert variant == "warning"

    def test_high_300_to_430(self):
        label, variant, color = _safety_badge(350)
        assert label == "Hoch"
        assert variant == "destructive"

    def test_very_high_above_430(self):
        label, variant, color = _safety_badge(500)
        assert label == "Sehr hoch"
        assert variant == "destructive"


# ---------------------------------------------------------------------------
# Shared mock data
# ---------------------------------------------------------------------------

MOCK_CONDITIONS = {
    "city": "Bern",
    "aare": {
        "location": "Bern",
        "location_long": "Bern, Schönau",
        "temperature": 17.2,
        "temperature_text": "geil aber chli chalt",
        "swiss_german_explanation": "awesome but a bit cold",
        "temperature_text_short": "chalt",
        "flow": 85.0,
        "flow_text": "normal",
        "height": 1.2,
        "forecast2h": 17.5,
        "forecast2h_text": "slightly warmer",
        "warning": None,
    },
    "seasonal_advice": "Great swimming weather in summer.",
}

MOCK_CONDITIONS_WITH_WARNING = {
    **MOCK_CONDITIONS,
    "aare": {
        **MOCK_CONDITIONS["aare"],
        "flow": 280.0,
        "warning": "Elevated flow — caution advised",
    },
}

MOCK_HISTORY = {
    "data": [
        {"time": "2026-04-06T10:00:00", "aare": 16.5, "flow": 80.0},
        {"time": "2026-04-06T11:00:00", "aare": 16.8, "flow": 82.0},
        {"time": "2026-04-06T12:00:00", "aare": 17.0, "flow": 85.0},
    ]
}

MOCK_COMPARE = {
    "cities": [
        {
            "city": "Bern",
            "location": "Bern",
            "temperature": 17.2,
            "flow": 85.0,
            "safe": True,
            "temperature_text": "geil",
        },
        {
            "city": "Thun",
            "location": "Thun",
            "temperature": 18.1,
            "flow": 65.0,
            "safe": True,
            "temperature_text": "warm",
        },
        {
            "city": "Olten",
            "location": "Olten",
            "temperature": 15.5,
            "flow": 120.0,
            "safe": False,
            "temperature_text": "chalt",
        },
    ],
    "warmest": {"city": "Thun", "location": "Thun", "temperature": 18.1},
    "coldest": {"city": "Olten", "location": "Olten", "temperature": 15.5},
    "safe_count": 2,
    "total_count": 3,
    "requested_count": 3,
    "errors": None,
}


# ---------------------------------------------------------------------------
# conditions_dashboard tests
# ---------------------------------------------------------------------------


class TestConditionsDashboard:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_CONDITIONS
            )
            result = await conditions_dashboard("Bern")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_default_city_is_bern(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            mock_svc = MockService.return_value
            mock_svc.get_current_conditions = AsyncMock(return_value=MOCK_CONDITIONS)
            await conditions_dashboard()
            mock_svc.get_current_conditions.assert_called_once_with("Bern")

    @pytest.mark.asyncio
    async def test_state_contains_city(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_CONDITIONS
            )
            result = await conditions_dashboard("Thun")
        assert result.state["city"] == "Thun"

    @pytest.mark.asyncio
    async def test_state_contains_safety(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_CONDITIONS
            )
            result = await conditions_dashboard("Bern")
        assert result.state["safety"] == "Sicher"

    @pytest.mark.asyncio
    async def test_elevated_flow_gives_warning_state(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_CONDITIONS_WITH_WARNING
            )
            result = await conditions_dashboard("Bern")
        assert result.state["safety"] == "Erhöht"

    @pytest.mark.asyncio
    async def test_missing_aare_data_does_not_raise(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value={"city": "Bern", "aare": None}
            )
            result = await conditions_dashboard("Bern")
        assert isinstance(result, PrefabApp)


# ---------------------------------------------------------------------------
# historical_chart tests
# ---------------------------------------------------------------------------


class TestHistoricalChart:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_historical_data = AsyncMock(
                return_value=MOCK_HISTORY
            )
            result = await historical_chart("Bern", "-7 days", "now")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_state_has_point_count(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_historical_data = AsyncMock(
                return_value=MOCK_HISTORY
            )
            result = await historical_chart("Bern", "-7 days", "now")
        assert result.state["points"] == 3

    @pytest.mark.asyncio
    async def test_empty_data_does_not_raise(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_historical_data = AsyncMock(
                return_value={"data": []}
            )
            result = await historical_chart("Bern", "-7 days", "now")
        assert result.state["points"] == 0

    @pytest.mark.asyncio
    async def test_handles_list_response(self):
        raw_list = [
            {"time": "2026-04-06T10:00:00", "aare": 16.5},
            {"time": "2026-04-06T11:00:00", "aare": 17.0},
        ]
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_historical_data = AsyncMock(
                return_value=raw_list
            )
            result = await historical_chart("Bern", "-2 days", "now")
        assert result.state["points"] == 2

    @pytest.mark.asyncio
    async def test_state_contains_city_and_range(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_historical_data = AsyncMock(
                return_value=MOCK_HISTORY
            )
            result = await historical_chart("Thun", "-3 days", "now")
        assert result.state["city"] == "Thun"
        assert result.state["start"] == "-3 days"
        assert result.state["end"] == "now"


# ---------------------------------------------------------------------------
# compare_cities_table tests
# ---------------------------------------------------------------------------


class TestCompareCitiesTable:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await compare_cities_table()
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_state_has_safe_count(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await compare_cities_table()
        assert result.state["safe_count"] == 2

    @pytest.mark.asyncio
    async def test_state_has_total(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await compare_cities_table()
        assert result.state["total"] == 3

    @pytest.mark.asyncio
    async def test_rows_include_all_cities(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await compare_cities_table()
        assert len(result.state["rows"]) == 3

    @pytest.mark.asyncio
    async def test_rows_have_safety_column(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await compare_cities_table()
        rows = result.state["rows"]
        assert all("Sicherheit" in row for row in rows)

    @pytest.mark.asyncio
    async def test_passes_cities_to_service(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            mock_svc = MockService.return_value
            mock_svc.compare_cities = AsyncMock(return_value=MOCK_COMPARE)
            await compare_cities_table(["Bern", "Thun"])
            mock_svc.compare_cities.assert_called_once_with(["Bern", "Thun"])

    @pytest.mark.asyncio
    async def test_empty_cities_does_not_raise(self):
        empty = {
            **MOCK_COMPARE,
            "cities": [],
            "warmest": None,
            "safe_count": 0,
            "total_count": 0,
        }
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(return_value=empty)
            result = await compare_cities_table()
        assert isinstance(result, PrefabApp)
        assert result.state["rows"] == []
