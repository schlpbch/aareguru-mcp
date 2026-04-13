"""Tests for FastMCP App UIs.

Tests all apps and the _safety_badge helper.
All tests mock AareguruService to avoid real API calls.
"""

from unittest.mock import AsyncMock, patch

import pytest
from prefab_ui.app import PrefabApp

from aareguru_mcp.apps import (
    _safety_badge,
    city_finder_view,
    compare_cities_table,
    conditions_dashboard,
    forecast_view,
    historical_chart,
    intraday_view,
    safety_briefing,
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

MOCK_FORECAST_CONDITIONS = {
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
        "forecast2h": 17.8,
        "forecast2h_text": "slightly warmer",
        "warning": None,
    },
    "forecast": [
        {"time": "2026-04-06T10:00:00", "sy": 1, "tt": 18.0, "rr": 0.0},
        {"time": "2026-04-06T11:00:00", "sy": 2, "tt": 19.0, "rr": 0.2},
        {"time": "2026-04-06T12:00:00", "sy": 3, "tt": 20.0, "rr": 0.5},
    ],
    "seasonal_advice": "Great swimming weather in summer.",
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


# ---------------------------------------------------------------------------
# forecast_view tests
# ---------------------------------------------------------------------------


class TestForecastView:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_FORECAST_CONDITIONS
            )
            result = await forecast_view("Bern")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_default_city_is_bern(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            mock_svc = MockService.return_value
            mock_svc.get_current_conditions = AsyncMock(
                return_value=MOCK_FORECAST_CONDITIONS
            )
            await forecast_view()
            mock_svc.get_current_conditions.assert_called_once_with("Bern")

    @pytest.mark.asyncio
    async def test_state_has_current_temp(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_FORECAST_CONDITIONS
            )
            result = await forecast_view("Bern")
        assert result.state["current_temp"] == 17.2

    @pytest.mark.asyncio
    async def test_state_has_forecast_2h(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_FORECAST_CONDITIONS
            )
            result = await forecast_view("Bern")
        assert result.state["forecast_2h"] == 17.8

    @pytest.mark.asyncio
    async def test_rising_trend(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_FORECAST_CONDITIONS
            )
            result = await forecast_view("Bern")
        assert result.state["trend"] == "↑"

    @pytest.mark.asyncio
    async def test_state_has_hour_count(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_FORECAST_CONDITIONS
            )
            result = await forecast_view("Bern")
        assert result.state["hours"] == 3

    @pytest.mark.asyncio
    async def test_no_forecast_data_does_not_raise(self):
        empty = {**MOCK_FORECAST_CONDITIONS, "forecast": []}
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=empty
            )
            result = await forecast_view("Bern")
        assert result.state["hours"] == 0

    @pytest.mark.asyncio
    async def test_stable_trend(self):
        stable = {
            **MOCK_FORECAST_CONDITIONS,
            "aare": {**MOCK_FORECAST_CONDITIONS["aare"], "forecast2h": 17.2},
        }
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=stable
            )
            result = await forecast_view("Bern")
        assert result.state["trend"] == "→"


# ---------------------------------------------------------------------------
# intraday_view tests
# ---------------------------------------------------------------------------

MOCK_INTRADAY = {
    **MOCK_CONDITIONS,
    "aarepast": [
        {"time": "2026-04-06T08:00:00", "aare": 15.0},
        {"time": "2026-04-06T09:00:00", "aare": 16.0},
        {"time": "2026-04-06T10:00:00", "aare": 17.2},
    ],
}


class TestIntradayView:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_INTRADAY
            )
            result = await intraday_view("Bern")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_state_has_point_count(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_INTRADAY
            )
            result = await intraday_view("Bern")
        assert result.state["points"] == 3

    @pytest.mark.asyncio
    async def test_state_has_current_temp(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_INTRADAY
            )
            result = await intraday_view("Bern")
        assert result.state["current_temp"] == 17.2

    @pytest.mark.asyncio
    async def test_delta_computed(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_INTRADAY
            )
            result = await intraday_view("Bern")
        assert abs(result.state["delta"] - 2.2) < 0.01

    @pytest.mark.asyncio
    async def test_no_past_data_does_not_raise(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value={**MOCK_CONDITIONS, "aarepast": []}
            )
            result = await intraday_view("Bern")
        assert result.state["points"] == 0

    @pytest.mark.asyncio
    async def test_unix_timestamps_normalised(self):
        data = {
            **MOCK_CONDITIONS,
            "aarepast": [
                {"time": 1744000000, "aare": 16.0},
                {"time": 1744003600, "aare": 17.0},
            ],
        }
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=data
            )
            result = await intraday_view("Bern")
        assert result.state["points"] == 2


# ---------------------------------------------------------------------------
# city_finder_view tests
# ---------------------------------------------------------------------------


class TestCityFinderView:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await city_finder_view()
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_state_has_total(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await city_finder_view()
        assert result.state["total"] == 3

    @pytest.mark.asyncio
    async def test_default_sort_by_temperature(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await city_finder_view()
        assert result.state["sort_by"] == "temperature"

    @pytest.mark.asyncio
    async def test_sort_by_safety(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.compare_cities = AsyncMock(
                return_value=MOCK_COMPARE
            )
            result = await city_finder_view(sort_by="safety")
        assert result.state["sort_by"] == "safety"

    @pytest.mark.asyncio
    async def test_calls_compare_with_none(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            mock_svc = MockService.return_value
            mock_svc.compare_cities = AsyncMock(return_value=MOCK_COMPARE)
            await city_finder_view()
            mock_svc.compare_cities.assert_called_once_with(None)


# ---------------------------------------------------------------------------
# safety_briefing tests
# ---------------------------------------------------------------------------

MOCK_SAFETY_CONDITIONS = {
    **MOCK_CONDITIONS,
    "aare": {
        **MOCK_CONDITIONS["aare"],
        "flow": 85.0,
        "flow_gefahrenstufe": 1,
        "flow_scale_threshold": 220.0,
        "height": 1.2,
    },
}

MOCK_DANGER_CONDITIONS = {
    **MOCK_CONDITIONS,
    "aare": {
        **MOCK_CONDITIONS["aare"],
        "flow": 350.0,
        "flow_gefahrenstufe": 4,
        "flow_scale_threshold": 220.0,
        "height": 2.8,
    },
}


class TestSafetyBriefing:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_SAFETY_CONDITIONS
            )
            result = await safety_briefing("Bern")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_state_has_level(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_SAFETY_CONDITIONS
            )
            result = await safety_briefing("Bern")
        assert result.state["level"] == 1

    @pytest.mark.asyncio
    async def test_api_gefahrenstufe_takes_precedence(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_DANGER_CONDITIONS
            )
            result = await safety_briefing("Bern")
        assert result.state["level"] == 4

    @pytest.mark.asyncio
    async def test_state_has_flow(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=MOCK_SAFETY_CONDITIONS
            )
            result = await safety_briefing("Bern")
        assert result.state["flow"] == 85.0

    @pytest.mark.asyncio
    async def test_level_computed_from_flow_when_no_gefahrenstufe(self):
        no_gef = {
            **MOCK_CONDITIONS,
            "aare": {
                **MOCK_CONDITIONS["aare"],
                "flow": 260.0,
                "flow_gefahrenstufe": None,
                "flow_scale_threshold": None,
                "height": None,
            },
        }
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            MockService.return_value.get_current_conditions = AsyncMock(
                return_value=no_gef
            )
            result = await safety_briefing("Bern")
        assert result.state["level"] == 3  # 220–300 → Erhebliche Gefahr
