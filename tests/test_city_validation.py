"""Tests for city-parameter validation.

The upstream /v2018/current and /v2018/today endpoints silently substitute
Bern's data for an unrecognised city instead of erroring (unlike
/v2018/history, which 400s) — see AareguruService._known_city_slugs /
_check_city in service.py. These tests confirm that get_current_temperature,
get_current_conditions, get_flow_danger_level, compare_cities, and
get_forecasts all reject an unknown city explicitly instead of silently
returning Bern's data, and that the server.py elicit-a-valid-city fallback
now actually fires (it previously never did, since nothing ever raised
ValueError for a bad city).
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from aareguru_mcp.server import (
    get_current_conditions_tool,
    get_current_temperature_tool,
    get_flow_danger_level_tool,
)
from aareguru_mcp.service import AareguruService

_KNOWN_CITIES = [
    SimpleNamespace(city="bern"),
    SimpleNamespace(city="thun"),
    SimpleNamespace(city="olten"),
]


def _mock_client(**overrides) -> AsyncMock:
    client = AsyncMock()
    client.get_cities = AsyncMock(return_value=_KNOWN_CITIES)
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)
    for key, value in overrides.items():
        setattr(client, key, value)
    return client


def _make_ctx(*, raises: bool) -> AsyncMock:
    """A ctx whose elicit() either works normally or raises ToolError,
    mirroring an MCP client that doesn't support server-initiated
    elicitation (see test_elicitation_fallback.py for the full story)."""
    ctx = AsyncMock()
    if raises:
        ctx.elicit = AsyncMock(side_effect=ToolError("elicitation unavailable"))
    return ctx


class TestCheckCityHelper:
    def test_known_city_passes(self):
        AareguruService._check_city("bern", {"bern", "thun"})  # no raise

    def test_unknown_city_raises(self):
        with pytest.raises(ValueError, match="Unknown city"):
            AareguruService._check_city("nichtexistentxyz", {"bern", "thun"})

    def test_case_and_whitespace_insensitive(self):
        AareguruService._check_city("  BERN  ", {"bern"})  # no raise

    @pytest.mark.asyncio
    async def test_known_city_slugs_normalises(self):
        client = AsyncMock()
        client.get_cities = AsyncMock(return_value=_KNOWN_CITIES)
        known = await AareguruService._known_city_slugs(client)
        assert known == {"bern", "thun", "olten"}


class TestServiceLevelValidation:
    """Each affected service method must raise ValueError for a bad city."""

    @pytest.mark.asyncio
    async def test_get_current_temperature_rejects_unknown_city(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client()
            with pytest.raises(ValueError, match="Unknown city"):
                await AareguruService().get_current_temperature("nichtexistentxyz")

    @pytest.mark.asyncio
    async def test_get_current_conditions_rejects_unknown_city(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client()
            with pytest.raises(ValueError, match="Unknown city"):
                await AareguruService().get_current_conditions("nichtexistentxyz")

    @pytest.mark.asyncio
    async def test_get_flow_danger_level_rejects_unknown_city(self):
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client()
            with pytest.raises(ValueError, match="Unknown city"):
                await AareguruService().get_flow_danger_level("nichtexistentxyz")

    @pytest.mark.asyncio
    async def test_valid_city_is_unaffected(self):
        response = MagicMock()
        response.aare = MagicMock()
        response.aare.flow = 85.0
        response.aare.flow_text = "Low flow"
        response.aare.flow_scale_threshold = 220
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client(
                get_current=AsyncMock(return_value=response)
            )
            result = await AareguruService().get_flow_danger_level("Bern")
        assert result["flow"] == 85.0


class TestMultiCityValidation:
    """compare_cities / get_forecasts must report a bad city per-item, not
    raise for the whole batch (consistent with their existing partial-
    failure design)."""

    @pytest.mark.asyncio
    async def test_compare_cities_reports_unknown_city_as_error(self):
        response = MagicMock()
        response.aare = MagicMock()
        response.aare.temperature = 18.0
        response.aare.flow = 100.0
        response.aare.temperature_text = "warm"
        response.aare.location = "Bern"

        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client(
                get_current=AsyncMock(return_value=response)
            )
            result = await AareguruService().compare_cities(
                ["Bern", "nichtexistentxyz"]
            )
        assert result["total_count"] == 1
        assert result["errors"]
        assert any(
            e["city"] == "nichtexistentxyz" and "Unknown city" in e["error"]
            for e in result["errors"]
        )

    @pytest.mark.asyncio
    async def test_get_forecasts_reports_unknown_city_as_error(self):
        response = MagicMock()
        response.aare = MagicMock()
        response.aare.temperature = 18.0
        response.aare.forecast2h = 18.5

        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client(
                get_current=AsyncMock(return_value=response)
            )
            result = await AareguruService().get_forecasts(["Bern", "nichtexistentxyz"])
        assert "Bern" in result["forecasts"]
        assert any(
            e["city"] == "nichtexistentxyz" and "Unknown city" in e["error"]
            for e in result["errors"]
        )

    @pytest.mark.asyncio
    async def test_compare_cities_empty_list_skips_validation_call(self):
        """An explicit empty list should short-circuit without calling
        get_cities() at all (no cities to validate)."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            client = _mock_client()
            MockClient.return_value = client
            result = await AareguruService().compare_cities([])
        assert result["cities"] == []
        client.get_cities.assert_not_called()


class TestToolLevelElicitFallback:
    """server.py's dead _elicit_city fallback now actually fires: it was
    only ever triggered on ValueError, which service.py never raised for
    a bad city before this fix."""

    @pytest.mark.asyncio
    async def test_unknown_city_triggers_elicit_when_supported(self):
        cities_response = MagicMock()
        cities_response.aare = MagicMock()
        cities_response.aare.temperature = 17.2
        cities_response.aare.temperature_text = "geil aber chli chalt"
        cities_response.aare.temperature_text_short = "chalt"
        cities_response.aare.location = "Bern"
        cities_response.aare.location_long = "Bern, Schönau"
        cities_response.aare.flow = 85.0

        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            MockClient.return_value = _mock_client(
                get_current=AsyncMock(return_value=cities_response)
            )
            with patch("aareguru_mcp.server.AareguruService") as MockAppService:
                instance = MockAppService.return_value
                instance.get_cities_list = AsyncMock(
                    return_value=[{"city": "bern"}, {"city": "thun"}]
                )
                instance.get_current_temperature = AsyncMock(
                    side_effect=[ValueError("Unknown city"), {"city": "bern"}]
                )
                from fastmcp.server.elicitation import AcceptedElicitation

                ctx = AsyncMock()
                ctx.elicit = AsyncMock(return_value=AcceptedElicitation(data="bern"))

                result = await get_current_temperature_tool("nichtexistentxyz", ctx)

        instance.get_current_temperature.assert_any_call("bern")
        assert result == {"city": "bern"}

    @pytest.mark.asyncio
    async def test_unknown_city_returns_clean_error_when_elicit_unavailable(self):
        with patch("aareguru_mcp.server.AareguruService") as MockAppService:
            instance = MockAppService.return_value
            instance.get_cities_list = AsyncMock(
                return_value=[{"city": "bern"}, {"city": "thun"}]
            )
            instance.get_current_temperature = AsyncMock(
                side_effect=ValueError("Unknown city")
            )
            ctx = _make_ctx(raises=True)
            result = await get_current_temperature_tool("nichtexistentxyz", ctx)

        assert result == {"error": "Stadt 'nichtexistentxyz' nicht gefunden."}

    @pytest.mark.asyncio
    async def test_current_conditions_elicit_unavailable_returns_clean_error(self):
        with patch("aareguru_mcp.server.AareguruService") as MockAppService:
            instance = MockAppService.return_value
            instance.get_cities_list = AsyncMock(
                return_value=[{"city": "bern"}, {"city": "thun"}]
            )
            instance.get_current_conditions = AsyncMock(
                side_effect=ValueError("Unknown city")
            )
            ctx = _make_ctx(raises=True)
            result = await get_current_conditions_tool("nichtexistentxyz", ctx)

        assert result == {"error": "Stadt 'nichtexistentxyz' nicht gefunden."}

    @pytest.mark.asyncio
    async def test_flow_danger_level_elicit_unavailable_returns_clean_error(self):
        with patch("aareguru_mcp.server.AareguruService") as MockAppService:
            instance = MockAppService.return_value
            instance.get_cities_list = AsyncMock(
                return_value=[{"city": "bern"}, {"city": "thun"}]
            )
            instance.get_flow_danger_level = AsyncMock(
                side_effect=ValueError("Unknown city")
            )
            ctx = _make_ctx(raises=True)
            result = await get_flow_danger_level_tool("nichtexistentxyz", ctx)

        assert result == {"error": "Stadt 'nichtexistentxyz' nicht gefunden."}
