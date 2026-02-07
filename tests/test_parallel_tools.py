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

        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
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
                    {"Bern": 18.5, "Thun": 19.2, "basel": 17.8}[city],
                    {"Bern": 100, "Thun": 120, "basel": 90}[city],
                )
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await fn(cities=["Bern", "Thun", "basel"])

            assert result["total_count"] == 3
            assert result["safe_count"] == 3
            assert result["warmest"]["city"] == "Thun"
            assert result["warmest"]["temperature"] == 19.2
            assert result["coldest"]["city"] == "basel"
            assert result["coldest"]["temperature"] == 17.8

    @pytest.mark.asyncio
    async def test_without_city_list(self):
        """Test with automatic city discovery."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            # Mock get_cities
            mock_city_Bern = MagicMock()
            mock_city_Bern.city = "Bern"
            mock_city_Thun = MagicMock()
            mock_city_Thun.city = "Thun"

            mock_client.get_cities = AsyncMock(return_value=[mock_city_Bern, mock_city_Thun])

            # Mock get_current
            def make_response(city: str):
                response = MagicMock()
                response.aare = MagicMock()
                response.aare.temperature = 18.0 if city == "Bern" else 19.0
                response.aare.flow = 100
                response.aare.temperature_text = "warm"
                response.aare.location = city.title()
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await fn(cities=None)

            assert result["total_count"] == 2
            assert result["safe_count"] == 2

    @pytest.mark.asyncio
    async def test_with_unsafe_flow(self):
        """Test with unsafe flow levels."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
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
                    city, {"Bern": 100, "Thun": 250}[city]  # Thun is unsafe
                )
            )
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await fn(cities=["Bern", "Thun"])

            assert result["total_count"] == 2
            assert result["safe_count"] == 1  # Only Bern is safe
            assert result["cities"][0]["safe"] is True
            assert result["cities"][1]["safe"] is False


class TestGetForecastsBatch:
    """Test get_forecasts tool."""

    @pytest.mark.asyncio
    async def test_with_multiple_cities(self):
        """Test fetching forecasts for multiple cities."""
        tool = mcp._tool_manager._tools["get_forecasts"]
        fn = tool.fn

        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            def make_response(city: str):
                response = MagicMock()
                response.aare = MagicMock()
                if city == "Bern":
                    response.aare.temperature = 18.0
                    response.aare.forecast2h = 19.0
                elif city == "Thun":
                    response.aare.temperature = 19.0
                    response.aare.forecast2h = 18.5
                else:
                    response.aare.temperature = 17.0
                    response.aare.forecast2h = 17.0
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await fn(cities=["Bern", "Thun", "basel"])

            assert "forecasts" in result
            assert len(result["forecasts"]) == 3

            # Check Bern (rising)
            assert result["forecasts"]["Bern"]["current"] == 18.0
            assert result["forecasts"]["Bern"]["forecast_2h"] == 19.0
            assert result["forecasts"]["Bern"]["trend"] == "rising"
            assert result["forecasts"]["Bern"]["change"] == 1.0

            # Check Thun (falling)
            assert result["forecasts"]["Thun"]["trend"] == "falling"

            # Check basel (stable)
            assert result["forecasts"]["basel"]["trend"] == "stable"

    @pytest.mark.asyncio
    async def test_with_missing_data(self):
        """Test handling cities with missing data."""
        tool = mcp._tool_manager._tools["get_forecasts"]
        fn = tool.fn

        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            def make_response(city: str):
                response = MagicMock()
                if city == "Bern":
                    response.aare = MagicMock()
                    response.aare.temperature = 18.0
                    response.aare.forecast2h = 19.0
                else:
                    response.aare = None  # No data for Thun
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await fn(cities=["Bern", "Thun"])

            assert "forecasts" in result
            assert len(result["forecasts"]) == 1  # Only Bern has data
            assert "Bern" in result["forecasts"]
            assert "Thun" not in result["forecasts"]

    @pytest.mark.asyncio
    async def test_with_null_forecast(self):
        """Test handling null forecast values."""
        tool = mcp._tool_manager._tools["get_forecasts"]
        fn = tool.fn

        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            response = MagicMock()
            response.aare = MagicMock()
            response.aare.temperature = None
            response.aare.forecast2h = None

            mock_client.get_current = AsyncMock(return_value=response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await fn(cities=["Bern"])

            assert "forecasts" in result
            assert len(result["forecasts"]) == 1
            assert result["forecasts"]["Bern"]["trend"] == "unknown"
            assert result["forecasts"]["Bern"]["change"] is None
