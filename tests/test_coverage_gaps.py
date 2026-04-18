"""Tests targeting coverage gaps in tools.py, service.py, and apps/_helpers.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp import tools
from aareguru_mcp.apps._helpers import (
    _bafu_level,
    _beaufort,
    _fmt_flow,
    _fmt_pct,
    _fmt_sun,
    _fmt_temp,
    _fmt_wind,
    _safety_badge,
    _sy_to_emoji,
)

# =============================================================================
# tools.py — exception handler branches
# =============================================================================


class TestToolsExceptionHandlers:
    """Verify every tool returns {"error": ...} on unexpected exceptions."""

    @pytest.mark.asyncio
    async def test_get_current_conditions_exception(self):
        with patch("aareguru_mcp.tools.AareguruService") as MockSvc:
            MockSvc.return_value.get_current_conditions = AsyncMock(
                side_effect=RuntimeError("API down")
            )
            result = await tools.get_current_conditions("BadCity")
            assert "error" in result
            assert "API down" in result["error"]
            assert result["city"] == "BadCity"

    @pytest.mark.asyncio
    async def test_get_historical_data_exception(self):
        with patch("aareguru_mcp.tools.AareguruService") as MockSvc:
            MockSvc.return_value.get_historical_data = AsyncMock(
                side_effect=ValueError("bad dates")
            )
            result = await tools.get_historical_data("Bern", "invalid", "now")
            assert "error" in result
            assert "bad dates" in result["error"]
            assert result["city"] == "Bern"

    @pytest.mark.asyncio
    async def test_compare_cities_exception(self):
        with patch("aareguru_mcp.tools.AareguruService") as MockSvc:
            MockSvc.return_value.compare_cities = AsyncMock(
                side_effect=TimeoutError("timeout")
            )
            result = await tools.compare_cities(["Bern", "Thun"])
            assert "error" in result
            assert "timeout" in result["error"]

    @pytest.mark.asyncio
    async def test_get_flow_danger_level_exception(self):
        with patch("aareguru_mcp.tools.AareguruService") as MockSvc:
            MockSvc.return_value.get_flow_danger_level = AsyncMock(
                side_effect=Exception("connection refused")
            )
            result = await tools.get_flow_danger_level("Bern")
            assert "error" in result
            assert "connection refused" in result["error"]
            assert result["city"] == "Bern"

    @pytest.mark.asyncio
    async def test_get_forecasts_exception(self):
        with patch("aareguru_mcp.tools.AareguruService") as MockSvc:
            MockSvc.return_value.get_forecasts = AsyncMock(
                side_effect=RuntimeError("forecasts failed")
            )
            result = await tools.get_forecasts(["Bern", "Thun"])
            assert "error" in result
            assert "forecasts failed" in result["error"]

    @pytest.mark.asyncio
    async def test_get_current_temperature_exception(self):
        with patch("aareguru_mcp.tools.AareguruService") as MockSvc:
            MockSvc.return_value.get_current_temperature = AsyncMock(
                side_effect=ConnectionError("unreachable")
            )
            result = await tools.get_current_temperature("Bern")
            assert "error" in result
            assert "unreachable" in result["error"]
            assert result["city"] == "Bern"


# =============================================================================
# service.py — fallback path when current endpoint has no aare data
# =============================================================================


class TestServiceFallbackPath:
    """Test fallback from /current to /today when aare is None."""

    @pytest.mark.asyncio
    async def test_get_current_temperature_falls_back_to_today(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_current = MagicMock()
            mock_current.aare = None
            mock_today = MagicMock()
            mock_today.aare = 17.5
            mock_today.text = "warm"
            mock_client.get_current = AsyncMock(return_value=mock_current)
            mock_client.get_today = AsyncMock(return_value=mock_today)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            result = await AareguruService().get_current_temperature("Bern")

            assert result["temperature"] == 17.5
            assert result["temperature_text"] == "warm"
            mock_client.get_today.assert_called_once_with("Bern")

    @pytest.mark.asyncio
    async def test_get_current_temperature_legacy_fields_when_no_aare(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_current = MagicMock()
            mock_current.aare = None
            mock_current.aare_prec = 0.1
            mock_current.text_short = "chalt"
            mock_current.longname = "Bern, Schönau"
            mock_today = MagicMock()
            mock_today.aare = 17.5
            mock_today.text = "chli chalt"
            mock_client.get_current = AsyncMock(return_value=mock_current)
            mock_client.get_today = AsyncMock(return_value=mock_today)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            result = await AareguruService().get_current_temperature("Bern")

            assert result["temperature_prec"] == 0.1
            assert result["temperature_text_short"] == "chalt"
            assert result["longname"] == "Bern, Schönau"


# =============================================================================
# service.py — parallel fetch error paths
# =============================================================================


class TestServiceParallelFetchErrors:

    @pytest.mark.asyncio
    async def test_compare_cities_partial_failure_returns_partial_results(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            good = MagicMock()
            good.aare = MagicMock()
            good.aare.temperature = 18.0
            good.aare.flow = 100.0
            good.aare.temperature_text = "warm"
            good.aare.location = "Bern"

            def _side(city):
                if city == "Bern":
                    return good
                raise RuntimeError(f"fail {city}")

            mock_client.get_current = AsyncMock(side_effect=_side)
            mock_client.get_cities = AsyncMock(return_value=[MagicMock(city="Bern"), MagicMock(city="Thun")])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            result = await AareguruService().compare_cities(["Bern", "Thun"])

            assert "cities" in result
            assert len(result["cities"]) >= 1
            assert result.get("errors") or result.get("error_count", 0) > 0

    @pytest.mark.asyncio
    async def test_compare_cities_all_fail_raises(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get_current = AsyncMock(side_effect=RuntimeError("API unavailable"))
            mock_client.get_cities = AsyncMock(return_value=[MagicMock(city="Bern"), MagicMock(city="Thun")])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            with pytest.raises(RuntimeError, match="Failed to fetch data for all"):
                await AareguruService().compare_cities(["Bern", "Thun"])

    @pytest.mark.asyncio
    async def test_get_forecasts_partial_failure_returns_partial_results(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            good = MagicMock()
            good.aare = MagicMock()
            good.aare.temperature = 17.0
            good.aare.forecast2h = 18.0

            def _side(city):
                if city == "Bern":
                    return good
                raise RuntimeError(f"fail {city}")

            mock_client.get_current = AsyncMock(side_effect=_side)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            result = await AareguruService().get_forecasts(["Bern", "Thun"])

            assert "forecasts" in result
            assert "Bern" in result["forecasts"]
            assert result.get("errors") or result.get("success_count", 0) < 2

    @pytest.mark.asyncio
    async def test_get_forecasts_all_fail_raises(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get_current = AsyncMock(side_effect=RuntimeError("API unavailable"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            with pytest.raises(RuntimeError, match="Failed to fetch forecasts for all"):
                await AareguruService().get_forecasts(["Bern", "Thun"])


# =============================================================================
# apps/_helpers.py
# =============================================================================


class TestSafetyBadge:

    def test_none_flow(self):
        label, variant, color = _safety_badge(None)
        assert label == "Unbekannt"
        assert variant == "secondary"

    def test_safe(self):
        label, variant, color = _safety_badge(50.0)
        assert label == "Sicher"
        assert variant == "success"

    def test_moderate(self):
        label, variant, color = _safety_badge(150.0)
        assert label == "Moderat"

    def test_elevated(self):
        label, variant, color = _safety_badge(250.0)
        assert label == "Erhöht"

    def test_high(self):
        label, variant, color = _safety_badge(350.0)
        assert label == "Hoch"

    def test_very_high(self):
        label, variant, color = _safety_badge(500.0)
        assert label == "Sehr hoch"
        assert color == "#7f1d1d"

    def test_boundary_at_100(self):
        # 100.0 >= 100 threshold → Moderat
        assert _safety_badge(100.0)[0] == "Moderat"

    def test_just_below_100(self):
        assert _safety_badge(99.9)[0] == "Sicher"


class TestFmtFlow:

    def test_none(self):
        assert _fmt_flow(None) == "—"

    def test_integer_value(self):
        assert _fmt_flow(95.0) == "95"

    def test_rounds(self):
        assert _fmt_flow(95.6) == "96"

    def test_zero(self):
        assert _fmt_flow(0.0) == "0"

    def test_large(self):
        assert _fmt_flow(1234.0) == "1234"


class TestBeaufort:

    def test_none(self):
        bft, label, emoji = _beaufort(None)
        assert bft == 0
        assert label == "—"
        assert emoji == ""

    def test_calm(self):
        bft, label, emoji = _beaufort(0.5)
        assert bft == 0
        assert "Windstille" in label

    def test_light_pull(self):
        bft, label, emoji = _beaufort(3.0)
        assert bft == 1

    def test_moderate_breeze(self):
        bft, label, emoji = _beaufort(25.0)
        assert bft == 4
        assert emoji == "💨"

    def test_storm(self):
        bft, label, emoji = _beaufort(95.0)
        assert bft == 10
        assert emoji == "🌪"

    def test_hurricane(self):
        bft, label, emoji = _beaufort(150.0)
        assert bft == 12
        assert label == "Orkan"
        assert emoji == "🌪"


class TestSyToEmoji:

    def test_none(self):
        assert _sy_to_emoji(None) == "🌡"

    def test_sunny(self):
        assert _sy_to_emoji(1) == "☀️"

    def test_cloudy(self):
        assert _sy_to_emoji(5) == "☁️"

    def test_rainy(self):
        assert _sy_to_emoji(8) == "🌧"

    def test_thunderstorm(self):
        assert _sy_to_emoji(11) == "⛈"

    def test_unknown_code(self):
        assert _sy_to_emoji(999) == "🌡"


class TestBafuLevel:

    def test_explicit_gefahrenstufe(self):
        assert _bafu_level(250.0, 3) == 3

    def test_invalid_gefahrenstufe_0_falls_back_to_flow(self):
        assert _bafu_level(150.0, 0) == 2

    def test_invalid_gefahrenstufe_6_falls_back_to_flow(self):
        assert _bafu_level(150.0, 6) == 2

    def test_none_flow_returns_1(self):
        assert _bafu_level(None, None) == 1

    def test_safe(self):
        assert _bafu_level(50.0, None) == 1

    def test_moderate(self):
        assert _bafu_level(150.0, None) == 2

    def test_elevated(self):
        assert _bafu_level(250.0, None) == 3

    def test_high(self):
        assert _bafu_level(350.0, None) == 4

    def test_very_high(self):
        assert _bafu_level(500.0, None) == 5

    def test_boundaries(self):
        assert _bafu_level(99.9, None) == 1
        assert _bafu_level(100.0, None) == 2
        assert _bafu_level(219.9, None) == 2
        assert _bafu_level(220.0, None) == 3
        assert _bafu_level(299.9, None) == 3
        assert _bafu_level(300.0, None) == 4
        assert _bafu_level(429.9, None) == 4
        assert _bafu_level(430.0, None) == 5


class TestFmtHelpers:
    """Test remaining _fmt_* helper functions."""

    def test_fmt_temp_value(self):
        assert _fmt_temp(17.2) == "17.2°"

    def test_fmt_temp_none(self):
        assert _fmt_temp(None) == "—"

    def test_fmt_pct_value(self):
        assert _fmt_pct(65.0) == "65%"

    def test_fmt_pct_none(self):
        assert _fmt_pct(None) == "—"

    def test_fmt_wind_value(self):
        assert _fmt_wind(25.0) == "25 km/h"

    def test_fmt_wind_none(self):
        assert _fmt_wind(None) == "—"

    def test_fmt_sun_under_60(self):
        assert _fmt_sun(45) == "45m"

    def test_fmt_sun_over_60(self):
        assert _fmt_sun(90) == "1h 30m"

    def test_fmt_sun_none(self):
        assert _fmt_sun(None) == "—"

    def test_fmt_sun_exactly_60(self):
        assert _fmt_sun(60) == "1h 00m"


# =============================================================================
# service.py — get_cities_list
# =============================================================================


class TestServiceGetCitiesList:
    """Test get_cities_list service method."""

    @pytest.mark.asyncio
    async def test_get_cities_list_returns_list_of_dicts(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            city1 = MagicMock()
            city1.model_dump.return_value = {"city": "Bern", "name": "Bern", "aare": 17.0}
            city2 = MagicMock()
            city2.model_dump.return_value = {"city": "Thun", "name": "Thun", "aare": 16.5}
            mock_client.get_cities = AsyncMock(return_value=[city1, city2])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            result = await AareguruService().get_cities_list()

            assert isinstance(result, list)
            assert len(result) == 2
            assert result[0]["city"] == "Bern"
            assert result[1]["city"] == "Thun"

    @pytest.mark.asyncio
    async def test_get_cities_list_empty(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get_cities = AsyncMock(return_value=[])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            result = await AareguruService().get_cities_list()

            assert result == []


# =============================================================================
# service.py — compare_cities processing: no-aare-data path
# =============================================================================


class TestServiceCompareCitiesProcessing:
    """Test compare_cities result-processing edge cases."""

    @pytest.mark.asyncio
    async def test_compare_cities_response_without_aare(self):
        """Responses that have no aare attribute are skipped as errors."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            no_aare = MagicMock()
            no_aare.aare = None  # triggers "No aare data available" branch

            mock_client.get_current = AsyncMock(return_value=no_aare)
            mock_client.get_cities = AsyncMock(return_value=[MagicMock(city="Bern")])
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            from aareguru_mcp.service import AareguruService

            with pytest.raises((RuntimeError, Exception)):
                await AareguruService().compare_cities(["Bern"])
