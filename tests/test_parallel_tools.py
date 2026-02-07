"""Tests for parallel fetch tools.

Tests compare_cities and get_forecasts.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp.server import mcp


class TestCompareCitiesFast:
    """Test compare_cities tool."""

    @pytest.mark.asyncio
    async def test_with_city_list(self):
        """Test with explicit city list."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()

            # Mock responses for multiple cities
            def make_response(city: str, temp: float, flow: float):
                response = MagicMock()
                response.aare = MagicMock()
                response.aare.temperature = temp
                response.aare.flow = flow
                response.aare.temperature_text = f"{temp}°C"
                response.aare.location = city.title()
                return response

            mock_client.get_current = AsyncMock(
                side_effect=lambda city: make_response(
                    city,
                    {"bern": 18.5, "thun": 19.2, "basel": 17.8}[city],
                    {"bern": 100, "thun": 120, "basel": 90}[city],
                )
            )
            mock_get_client.return_value = mock_client

            result = await fn(cities=["bern", "thun", "basel"])

            assert result["total_count"] == 3
            assert result["safe_count"] == 3
            assert result["warmest"]["city"] == "thun"
            assert result["warmest"]["temperature"] == 19.2
            assert result["coldest"]["city"] == "basel"
            assert result["coldest"]["temperature"] == 17.8

    @pytest.mark.asyncio
    async def test_without_city_list(self):
        """Test with automatic city discovery."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()

            # Mock get_cities
            mock_city_bern = MagicMock()
            mock_city_bern.city = "bern"
            mock_city_thun = MagicMock()
            mock_city_thun.city = "thun"

            mock_client.get_cities = AsyncMock(return_value=[mock_city_bern, mock_city_thun])

            # Mock get_current
            def make_response(city: str):
                response = MagicMock()
                response.aare = MagicMock()
                response.aare.temperature = 18.0 if city == "bern" else 19.0
                response.aare.flow = 100
                response.aare.temperature_text = "warm"
                response.aare.location = city.title()
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_get_client.return_value = mock_client

            result = await fn(cities=None)

            assert result["total_count"] == 2
            assert result["safe_count"] == 2

    @pytest.mark.asyncio
    async def test_with_unsafe_flow(self):
        """Test with unsafe flow levels."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()

            def make_response(city: str, flow: float):
                response = MagicMock()
                response.aare = MagicMock()
                response.aare.temperature = 18.0
                response.aare.flow = flow
                response.aare.temperature_text = "warm"
                response.aare.location = city.title()
                return response

            mock_client.get_current = AsyncMock(
                side_effect=lambda city: make_response(
                    city, {"bern": 100, "thun": 250}[city]  # thun is unsafe
                )
            )
            mock_get_client.return_value = mock_client

            result = await fn(cities=["bern", "thun"])

            assert result["total_count"] == 2
            assert result["safe_count"] == 1  # Only bern is safe
            assert result["cities"][0]["safe"] is True
            assert result["cities"][1]["safe"] is False


class TestGetForecastsBatch:
    """Test get_forecasts tool."""

    @pytest.mark.asyncio
    async def test_with_multiple_cities(self):
        """Test fetching forecasts for multiple cities."""
        tool = mcp._tool_manager._tools["get_forecasts"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()

            def make_response(city: str):
                response = MagicMock()
                response.aare = MagicMock()
                if city == "bern":
                    response.aare.temperature = 18.0
                    response.aare.forecast2h = 19.0
                elif city == "thun":
                    response.aare.temperature = 19.0
                    response.aare.forecast2h = 18.5
                else:
                    response.aare.temperature = 17.0
                    response.aare.forecast2h = 17.0
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_get_client.return_value = mock_client

            result = await fn(cities=["bern", "thun", "basel"])

            assert "forecasts" in result
            assert len(result["forecasts"]) == 3

            # Check bern (rising)
            assert result["forecasts"]["bern"]["current"] == 18.0
            assert result["forecasts"]["bern"]["forecast_2h"] == 19.0
            assert result["forecasts"]["bern"]["trend"] == "rising"
            assert result["forecasts"]["bern"]["change"] == 1.0

            # Check thun (falling)
            assert result["forecasts"]["thun"]["trend"] == "falling"

            # Check basel (stable)
            assert result["forecasts"]["basel"]["trend"] == "stable"

    @pytest.mark.asyncio
    async def test_with_missing_data(self):
        """Test handling cities with missing data."""
        tool = mcp._tool_manager._tools["get_forecasts"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()

            def make_response(city: str):
                response = MagicMock()
                if city == "bern":
                    response.aare = MagicMock()
                    response.aare.temperature = 18.0
                    response.aare.forecast2h = 19.0
                else:
                    response.aare = None  # No data for thun
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_get_client.return_value = mock_client

            result = await fn(cities=["bern", "thun"])

            assert "forecasts" in result
            assert len(result["forecasts"]) == 1  # Only bern has data
            assert "bern" in result["forecasts"]
            assert "thun" not in result["forecasts"]

    @pytest.mark.asyncio
    async def test_with_null_forecast(self):
        """Test handling null forecast values."""
        tool = mcp._tool_manager._tools["get_forecasts"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()

            response = MagicMock()
            response.aare = MagicMock()
            response.aare.temperature = None
            response.aare.forecast2h = None

            mock_client.get_current = AsyncMock(return_value=response)
            mock_get_client.return_value = mock_client

            result = await fn(cities=["bern"])

            assert "forecasts" in result
            assert len(result["forecasts"]) == 1
            assert result["forecasts"]["bern"]["trend"] == "unknown"
            assert result["forecasts"]["bern"]["change"] is None
