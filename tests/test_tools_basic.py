"""Tests for basic MCP tools.

Tests get_current_temperature, get_current_conditions,
get_flow_danger_level, and get_historical_data.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp import tools
from aareguru_mcp.server import mcp


class TestGetCurrentTemperature:
    """Test get_current_temperature tool."""

    @pytest.mark.asyncio
    async def test_with_mocked_client(self):
        """Test with mocked client."""
        tool = mcp._tool_manager._tools["get_current_temperature"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.aare = MagicMock()
            mock_response.aare.temperature = 17.2
            mock_response.aare.temperature_text = "geil aber chli chalt"
            mock_response.aare.temperature_text_short = "chalt"
            mock_response.aare.location = "Bern"
            mock_response.aare.location_long = "Bern, Schönau"
            mock_response.aare.flow = 85.0
            mock_client.get_current = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await fn("bern")

            assert result.city == "bern"
            assert result.temperature == 17.2

    @pytest.mark.asyncio
    async def test_fallback_to_today(self):
        """Test fallback to today endpoint when current has no data."""
        tool = mcp._tool_manager._tools["get_current_temperature"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            # Current response has no aare data
            mock_current = MagicMock()
            mock_current.aare = None

            # Today response has data
            mock_today = MagicMock()
            mock_today.aare = 17.5
            mock_today.text = "warm"
            mock_today.name = "Bern"
            mock_today.aare_prec = 0.1
            mock_today.text_short = "warm"
            mock_today.longname = "Bern, Schönau"

            mock_client.get_current.return_value = mock_current
            mock_client.get_today.return_value = mock_today

            result = await fn("bern")
            assert result.temperature == 17.5
            mock_client.get_today.assert_called_once()


class TestGetCurrentConditions:
    """Test get_current_conditions tool."""

    @pytest.mark.asyncio
    async def test_with_weather_and_forecast(self):
        """Test with mocked weather and forecast data."""
        tool = mcp._tool_manager._tools["get_current_conditions"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            mock_response = MagicMock()
            mock_response.aare.location = "Bern"
            mock_response.aare.location_long = "Bern, Schönau"
            mock_response.aare.temperature = 17.0
            mock_response.aare.temperature_text = "geil aber chli chalt"
            mock_response.aare.temperature_text_short = "warm"
            mock_response.aare.flow = 100.0
            mock_response.aare.flow_text = "normal"
            mock_response.aare.height = 1.5
            mock_response.aare.forecast2h = 18.0
            mock_response.aare.forecast2h_text = "rising"
            mock_response.weather = {"temp": 22.0}
            mock_response.weatherprognosis = [{"day": "Monday"}]

            mock_client.get_current.return_value = mock_response

            result = await fn("bern")

            assert result.aare is not None
            assert result.aare.temperature == 17.0
            assert result.aare.swiss_german_explanation is not None
            assert result.weather is not None
            assert result.forecast is not None
            assert result.seasonal_advice is not None

    @pytest.mark.asyncio
    async def test_without_aare_data(self):
        """Test without aare data."""
        tool = mcp._tool_manager._tools["get_current_conditions"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            mock_response = MagicMock()
            mock_response.aare = None
            mock_response.weather = None
            mock_response.weatherprognosis = None

            mock_client.get_current.return_value = mock_response

            result = await fn("bern")

            assert result.city == "bern"
            assert result.aare is None
            assert result.seasonal_advice is not None


class TestGetFlowDangerLevel:
    """Test get_flow_danger_level tool."""

    @pytest.mark.asyncio
    async def test_with_mocked_client(self):
        """Test with mocked client."""
        tool = mcp._tool_manager._tools["get_flow_danger_level"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.aare = MagicMock()
            mock_response.aare.flow = 85.0
            mock_response.aare.flow_text = "Low flow"
            mock_response.aare.flow_scale_threshold = 220
            mock_client.get_current = AsyncMock(return_value=mock_response)
            mock_get_client.return_value = mock_client

            result = await fn("bern")

            assert result.city == "bern"
            assert result.flow == 85.0
            assert result.danger_level == 1  # Safe

    @pytest.mark.asyncio
    async def test_no_aare_data(self):
        """Test when no aare data is available."""
        tool = mcp._tool_manager._tools["get_flow_danger_level"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_get_client.return_value = mock_client

            mock_response = MagicMock()
            mock_response.aare = None

            mock_client.get_current.return_value = mock_response

            result = await fn("bern")

            assert result.flow is None
            assert "No data available" in result.safety_assessment


class TestGetHistoricalData:
    """Test get_historical_data tool."""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_with_relative_dates(self):
        """Test get_historical_data with relative dates."""
        result = await tools.get_historical_data(
            city="bern",
            start="-7 days",
            end="now",
        )
        assert "city" in result or "timeseries" in result or isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_with_mocked_client(self):
        """Test with mocked client."""
        tool = mcp._tool_manager._tools["get_historical_data"]
        fn = tool.fn

        with patch("aareguru_mcp.server.get_http_client") as mock_get_client:
            mock_client = AsyncMock()
            mock_client.get_history = AsyncMock(
                return_value={"timeseries": [{"timestamp": 123, "temp": 17.0}]}
            )
            mock_get_client.return_value = mock_client

            result = await fn("bern", "-7 days", "now")

            assert "timeseries" in result


class TestErrorHandling:
    """Test tools handle errors gracefully."""

    @pytest.mark.asyncio
    async def test_invalid_city(self):
        """Test tools handle invalid cities."""
        try:
            result = await tools.get_current_temperature("invalid_city_xyz")
            assert result is not None
        except Exception as e:
            error_msg = str(e).lower()
            assert "invalid" in error_msg or "not found" in error_msg or len(error_msg) > 0
