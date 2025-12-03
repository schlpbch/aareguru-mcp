"""Tests for advanced MCP tools: compare_cities and get_forecast.

Tests multi-city comparison, temperature forecasting, trend calculations,
and recommendation logic.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp import tools
from aareguru_mcp.server import mcp


class TestCompareCitiesBasic:
    """Test basic compare_cities functionality."""

    @pytest.mark.asyncio
    async def test_specific_cities(self):
        """Test comparing specific cities."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_bern = MagicMock()
            mock_bern.aare.location = "Bern"
            mock_bern.aare.location_long = "Bern, Schönau"
            mock_bern.aare.temperature = 17.2
            mock_bern.aare.temperature_text = "geil aber chli chalt"
            mock_bern.aare.flow = 92.0
            mock_bern.aare.flow_text = "moderate"
            mock_bern.aare.flow_scale_threshold = 220

            mock_thun = MagicMock()
            mock_thun.aare.location = "Thun"
            mock_thun.aare.location_long = "Thun"
            mock_thun.aare.temperature = 16.5
            mock_thun.aare.temperature_text = "chli chalt"
            mock_thun.aare.flow = 78.0
            mock_thun.aare.flow_text = "low"
            mock_thun.aare.flow_scale_threshold = 220

            mock_client.get_current.side_effect = [mock_bern, mock_thun]

            result = await tools.compare_cities(["bern", "thun"])

            assert len(result["cities"]) == 2
            assert result["warmest"]["name"] == "Bern"
            assert result["warmest"]["temperature"] == 17.2
            assert result["coldest"]["name"] == "Thun"
            assert result["safest"]["name"] == "Thun"
            assert result["safest"]["flow"] == 78.0

    @pytest.mark.asyncio
    async def test_all_cities_none_param(self):
        """Test comparing all cities (None parameter)."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_city1 = MagicMock()
            mock_city1.city = "bern"
            mock_city2 = MagicMock()
            mock_city2.city = "thun"

            mock_client.get_cities.return_value = [mock_city1, mock_city2]

            mock_response = MagicMock()
            mock_response.aare.location = "Test"
            mock_response.aare.location_long = "Test City"
            mock_response.aare.temperature = 17.0
            mock_response.aare.temperature_text = "test"
            mock_response.aare.flow = 90.0
            mock_response.aare.flow_text = "test"
            mock_response.aare.flow_scale_threshold = 220

            mock_client.get_current.return_value = mock_response

            result = await tools.compare_cities(None)

            assert len(result["cities"]) == 2
            mock_client.get_cities.assert_called_once()


class TestCompareCitiesSelection:
    """Test warmest, coldest, safest selection."""

    @pytest.mark.asyncio
    async def test_finds_warmest(self):
        """Test correctly identifies warmest city."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            cities_data = [
                ("bern", 17.2),
                ("thun", 16.5),
                ("basel", 18.9),  # Warmest
            ]

            responses = []
            for city, temp in cities_data:
                mock_resp = MagicMock()
                mock_resp.aare.location = city.capitalize()
                mock_resp.aare.location_long = city.capitalize()
                mock_resp.aare.temperature = temp
                mock_resp.aare.temperature_text = "test"
                mock_resp.aare.flow = 90.0
                mock_resp.aare.flow_text = "test"
                mock_resp.aare.flow_scale_threshold = 220
                responses.append(mock_resp)

            mock_client.get_current.side_effect = responses

            result = await tools.compare_cities(["bern", "thun", "basel"])

            assert result["warmest"]["name"] == "Basel"
            assert result["warmest"]["temperature"] == 18.9

    @pytest.mark.asyncio
    async def test_finds_safest(self):
        """Test correctly identifies safest city (lowest flow)."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            cities_data = [
                ("bern", 92.0),
                ("thun", 65.0),  # Safest
                ("basel", 105.0),
            ]

            responses = []
            for city, flow in cities_data:
                mock_resp = MagicMock()
                mock_resp.aare.location = city.capitalize()
                mock_resp.aare.location_long = city.capitalize()
                mock_resp.aare.temperature = 17.0
                mock_resp.aare.temperature_text = "test"
                mock_resp.aare.flow = flow
                mock_resp.aare.flow_text = "test"
                mock_resp.aare.flow_scale_threshold = 220
                responses.append(mock_resp)

            mock_client.get_current.side_effect = responses

            result = await tools.compare_cities(["bern", "thun", "basel"])

            assert result["safest"]["name"] == "Thun"
            assert result["safest"]["flow"] == 65.0


class TestCompareCitiesEdgeCases:
    """Test compare_cities edge cases."""

    @pytest.mark.asyncio
    async def test_handles_missing_data(self):
        """Test handles cities with missing data gracefully."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare.location = "Bern"
            mock_resp.aare.location_long = "Bern"
            mock_resp.aare.temperature = 17.0
            mock_resp.aare.temperature_text = "test"
            mock_resp.aare.flow = 90.0
            mock_resp.aare.flow_text = "test"
            mock_resp.aare.flow_scale_threshold = 220

            mock_client.get_current.side_effect = [mock_resp, Exception("API error")]

            result = await tools.compare_cities(["bern", "invalid"])

            assert len(result["cities"]) == 1
            assert result["cities"][0]["name"] == "Bern"

    @pytest.mark.asyncio
    async def test_all_cities_fail(self):
        """Test when all cities fail."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_client.get_current.side_effect = Exception("API error")

            result = await fn(["bern", "thun"])

            assert result["cities"] == []
            assert result["warmest"] is None
            assert result["coldest"] is None
            assert result["safest"] is None
            assert "No data available" in result["comparison_summary"]

    @pytest.mark.asyncio
    async def test_empty_list(self):
        """Test with empty cities list."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            result = await tools.compare_cities([])

            assert result["cities"] == []
            assert result["warmest"] is None
            assert result["coldest"] is None
            assert result["safest"] is None
            assert "No data available" in result["comparison_summary"]

    @pytest.mark.asyncio
    async def test_flow_none(self):
        """Test with None flow."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_city = MagicMock()
            mock_city.aare.location = "Bern"
            mock_city.aare.location_long = "Bern"
            mock_city.aare.temperature = 17.0
            mock_city.aare.temperature_text = "ok"
            mock_city.aare.flow = None
            mock_city.aare.flow_text = None
            mock_city.aare.flow_scale_threshold = 220

            mock_client.get_current.return_value = mock_city

            result = await fn(["bern"])

            assert len(result["cities"]) == 1
            assert result["cities"][0]["safety"] == "Unknown"
            assert result["cities"][0]["danger_level"] == 0

    @pytest.mark.asyncio
    async def test_very_high_flow(self):
        """Test with very high flow (>430)."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_city = MagicMock()
            mock_city.aare.location = "Bern"
            mock_city.aare.location_long = "Bern"
            mock_city.aare.temperature = 17.0
            mock_city.aare.temperature_text = "ok"
            mock_city.aare.flow = 500.0
            mock_city.aare.flow_text = "very high"
            mock_city.aare.flow_scale_threshold = 220

            mock_client.get_current.return_value = mock_city

            result = await fn(["bern"])

            assert result["cities"][0]["safety"] == "Very High"
            assert result["cities"][0]["danger_level"] == 5


class TestCompareCitiesRecommendations:
    """Test compare_cities recommendation logic."""

    @pytest.mark.asyncio
    async def test_warmest_is_safest(self):
        """Test recommendation when warmest city is also safest."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_city = MagicMock()
            mock_city.aare.location = "Bern"
            mock_city.aare.location_long = "Bern"
            mock_city.aare.temperature = 20.0
            mock_city.aare.temperature_text = "warm"
            mock_city.aare.flow = 50.0  # Low flow = safe
            mock_city.aare.flow_text = "low"
            mock_city.aare.flow_scale_threshold = 220

            mock_client.get_current.return_value = mock_city

            result = await fn(["bern"])

            assert "Best Choice" in result["recommendation"]
            assert "warmest and safest" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_warmest_safe_but_not_safest(self):
        """Test recommendation when warmest is safe but not safest."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_warm = MagicMock()
            mock_warm.aare.location = "Basel"
            mock_warm.aare.location_long = "Basel"
            mock_warm.aare.temperature = 20.0
            mock_warm.aare.temperature_text = "warm"
            mock_warm.aare.flow = 150.0  # Moderate
            mock_warm.aare.flow_text = "moderate"
            mock_warm.aare.flow_scale_threshold = 220

            mock_safe = MagicMock()
            mock_safe.aare.location = "Thun"
            mock_safe.aare.location_long = "Thun"
            mock_safe.aare.temperature = 16.0
            mock_safe.aare.temperature_text = "cold"
            mock_safe.aare.flow = 50.0  # Very safe
            mock_safe.aare.flow_text = "low"
            mock_safe.aare.flow_scale_threshold = 220

            mock_client.get_current.side_effect = [mock_warm, mock_safe]

            result = await fn(["basel", "thun"])

            assert result["warmest"]["name"] == "Basel"
            assert result["safest"]["name"] == "Thun"
            assert "Best Choice" in result["recommendation"]
            assert "warmest safe option" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_warmest_dangerous(self):
        """Test recommendation when warmest city has dangerous flow."""
        tool = mcp._tool_manager._tools["compare_cities"]
        fn = tool.fn

        with patch("aareguru_mcp.server.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_warm = MagicMock()
            mock_warm.aare.location = "Basel"
            mock_warm.aare.location_long = "Basel"
            mock_warm.aare.temperature = 20.0
            mock_warm.aare.temperature_text = "warm"
            mock_warm.aare.flow = 350.0  # Dangerous
            mock_warm.aare.flow_text = "high"
            mock_warm.aare.flow_scale_threshold = 220

            mock_safe = MagicMock()
            mock_safe.aare.location = "Thun"
            mock_safe.aare.location_long = "Thun"
            mock_safe.aare.temperature = 16.0
            mock_safe.aare.temperature_text = "cold"
            mock_safe.aare.flow = 50.0
            mock_safe.aare.flow_text = "low"
            mock_safe.aare.flow_scale_threshold = 220

            mock_client.get_current.side_effect = [mock_warm, mock_safe]

            result = await fn(["basel", "thun"])

            assert "Trade-off" in result["recommendation"]


class TestGetForecastBasic:
    """Test basic get_forecast functionality."""

    @pytest.mark.asyncio
    async def test_basic_forecast(self):
        """Test basic forecast retrieval."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare.temperature = 17.2
            mock_resp.aare.temperature_text = "geil aber chli chalt"
            mock_resp.aare.flow = 92.0
            mock_resp.aare.forecast2h = 17.8
            mock_resp.aare.forecast2h_text = "slightly warmer"

            mock_client.get_current.return_value = mock_resp

            result = await tools.get_forecast("bern")

            assert result["city"] == "bern"
            assert result["current"]["temperature"] == 17.2
            assert result["forecast_2h"] == 17.8
            assert result["trend"] == "rising"
            assert result["temperature_change"] == pytest.approx(0.6)


class TestGetForecastTrends:
    """Test forecast trend calculations."""

    @pytest.mark.asyncio
    async def test_rising_trend(self):
        """Test forecast with rising temperature trend."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare.temperature = 17.0
            mock_resp.aare.temperature_text = "test"
            mock_resp.aare.flow = 90.0
            mock_resp.aare.forecast2h = 18.0  # +1.0°C
            mock_resp.aare.forecast2h_text = "warmer"

            mock_client.get_current.return_value = mock_resp

            result = await tools.get_forecast("bern")

            assert result["trend"] == "rising"
            assert "rising" in result["recommendation"]
            assert "1.0°C" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_falling_trend(self):
        """Test forecast with falling temperature trend."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare.temperature = 18.0
            mock_resp.aare.temperature_text = "test"
            mock_resp.aare.flow = 90.0
            mock_resp.aare.forecast2h = 17.2  # -0.8°C
            mock_resp.aare.forecast2h_text = "cooler"

            mock_client.get_current.return_value = mock_resp

            result = await tools.get_forecast("bern")

            assert result["trend"] == "falling"
            assert "falling" in result["recommendation"]
            assert "0.8°C" in result["recommendation"]

    @pytest.mark.asyncio
    async def test_stable_trend(self):
        """Test forecast with stable temperature (minimal change)."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare.temperature = 17.5
            mock_resp.aare.temperature_text = "test"
            mock_resp.aare.flow = 90.0
            mock_resp.aare.forecast2h = 17.6  # +0.1°C
            mock_resp.aare.forecast2h_text = "stable"

            mock_client.get_current.return_value = mock_resp

            result = await tools.get_forecast("bern")

            assert result["trend"] == "stable"
            assert "stable" in result["recommendation"]


class TestGetForecastEdgeCases:
    """Test get_forecast edge cases."""

    @pytest.mark.asyncio
    async def test_missing_forecast_data(self):
        """Test when forecast2h data is missing."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare.temperature = 17.2
            mock_resp.aare.temperature_text = "test"
            mock_resp.aare.flow = 90.0
            mock_resp.aare.forecast2h = None
            mock_resp.aare.forecast2h_text = None

            mock_client.get_current.return_value = mock_resp

            result = await tools.get_forecast("bern")

            assert result["trend"] == "unknown"
            assert "not available" in result["recommendation"]
            assert result["temperature_change"] is None

    @pytest.mark.asyncio
    async def test_no_aare_data(self):
        """Test when no aare data is available."""
        with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            MockClient.return_value.__aenter__.return_value = mock_client

            mock_resp = MagicMock()
            mock_resp.aare = None

            mock_client.get_current.return_value = mock_resp

            result = await tools.get_forecast("bern")

            assert result["current"] is None
            assert result["forecast_2h"] is None
            assert result["trend"] == "unknown"
            assert "no data available" in result["forecast_text"].lower()
