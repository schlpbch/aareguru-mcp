"""Tests for advanced tools: compare_cities and get_forecast.

Tests the new Week 4 tools for multi-city comparison and temperature forecasting.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from aareguru_mcp import tools


# Compare Cities Tests (6 tests)


@pytest.mark.asyncio
async def test_compare_cities_specific_cities():
    """Test comparing specific cities."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock responses for each city
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
async def test_compare_cities_all_cities():
    """Test comparing all cities (None parameter)."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock get_cities response
        mock_city1 = MagicMock()
        mock_city1.city = "bern"
        mock_city2 = MagicMock()
        mock_city2.city = "thun"
        
        mock_client.get_cities.return_value = [mock_city1, mock_city2]
        
        # Mock get_current responses
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


@pytest.mark.asyncio
async def test_compare_cities_finds_warmest():
    """Test that compare_cities correctly identifies warmest city."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Create cities with different temperatures
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
async def test_compare_cities_finds_safest():
    """Test that compare_cities correctly identifies safest city (lowest flow)."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Create cities with different flow rates
        cities_data = [
            ("bern", 92.0),
            ("thun", 65.0),  # Safest (lowest flow)
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


@pytest.mark.asyncio
async def test_compare_cities_handles_missing_data():
    """Test compare_cities handles cities with missing data gracefully."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # First city has data, second fails
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
        
        # Should only have one city (the successful one)
        assert len(result["cities"]) == 1
        assert result["cities"][0]["name"] == "Bern"


@pytest.mark.asyncio
async def test_compare_cities_empty_list():
    """Test compare_cities with empty cities list."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        result = await tools.compare_cities([])
        
        assert result["cities"] == []
        assert result["warmest"] is None
        assert result["coldest"] is None
        assert result["safest"] is None
        assert "No data available" in result["comparison_summary"]


# Forecast Tests (6 tests)


@pytest.mark.asyncio
async def test_get_forecast_basic():
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


@pytest.mark.asyncio
async def test_get_forecast_rising_trend():
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
async def test_get_forecast_falling_trend():
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
async def test_get_forecast_stable_trend():
    """Test forecast with stable temperature (minimal change)."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.aare.temperature = 17.5
        mock_resp.aare.temperature_text = "test"
        mock_resp.aare.flow = 90.0
        mock_resp.aare.forecast2h = 17.6  # +0.1°C (within threshold)
        mock_resp.aare.forecast2h_text = "stable"
        
        mock_client.get_current.return_value = mock_resp
        
        result = await tools.get_forecast("bern")
        
        assert result["trend"] == "stable"
        assert "stable" in result["recommendation"]


@pytest.mark.asyncio
async def test_get_forecast_missing_forecast_data():
    """Test forecast when forecast2h data is missing."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.aare.temperature = 17.2
        mock_resp.aare.temperature_text = "test"
        mock_resp.aare.flow = 90.0
        mock_resp.aare.forecast2h = None  # No forecast
        mock_resp.aare.forecast2h_text = None
        
        mock_client.get_current.return_value = mock_resp
        
        result = await tools.get_forecast("bern")
        
        assert result["trend"] == "unknown"
        assert "not available" in result["recommendation"]
        assert result["temperature_change"] is None


@pytest.mark.asyncio
async def test_get_forecast_no_aare_data():
    """Test forecast when no aare data is available."""
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


# Integration Tests (3 tests)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_compare_then_check_safety():
    """Test workflow: compare cities then check safety of warmest."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock compare_cities responses
        mock_bern = MagicMock()
        mock_bern.aare.location = "Bern"
        mock_bern.aare.location_long = "Bern"
        mock_bern.aare.temperature = 17.2
        mock_bern.aare.temperature_text = "test"
        mock_bern.aare.flow = 92.0
        mock_bern.aare.flow_text = "test"
        mock_bern.aare.flow_scale_threshold = 220
        
        mock_basel = MagicMock()
        mock_basel.aare.location = "Basel"
        mock_basel.aare.location_long = "Basel"
        mock_basel.aare.temperature = 18.9
        mock_basel.aare.temperature_text = "test"
        mock_basel.aare.flow = 105.0
        mock_basel.aare.flow_text = "test"
        mock_basel.aare.flow_scale_threshold = 220
        
        mock_client.get_current.side_effect = [mock_bern, mock_basel, mock_basel]
        
        # Step 1: Compare cities
        comparison = await tools.compare_cities(["bern", "basel"])
        warmest_city = comparison["warmest"]["city"]
        
        # Step 2: Check safety of warmest
        safety = await tools.get_flow_danger_level(warmest_city)
        
        assert warmest_city == "basel"
        assert safety["flow"] == 105.0
        assert "Moderate" in safety["safety_assessment"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_forecast_then_current_temp():
    """Test workflow: get forecast then current temperature."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock for forecast
        mock_forecast_resp = MagicMock()
        mock_forecast_resp.aare.temperature = 17.2
        mock_forecast_resp.aare.temperature_text = "geil aber chli chalt"
        mock_forecast_resp.aare.flow = 92.0
        mock_forecast_resp.aare.forecast2h = 17.8
        mock_forecast_resp.aare.forecast2h_text = "warmer"
        
        # Mock for current temp
        mock_today_resp = MagicMock()
        mock_today_resp.aare = 17.2
        mock_today_resp.aare_prec = 0.1
        mock_today_resp.text = "geil aber chli chalt"
        mock_today_resp.text_short = "chli chalt"
        mock_today_resp.name = "Bern"
        mock_today_resp.longname = "Bern, Schönau"
        
        mock_client.get_current.return_value = mock_forecast_resp
        mock_client.get_today.return_value = mock_today_resp
        
        # Step 1: Get forecast
        forecast = await tools.get_forecast("bern")
        
        # Step 2: Get current temperature
        temp = await tools.get_current_temperature("bern")
        
        assert forecast["trend"] == "rising"
        assert temp["temperature"] == 17.2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_city_comparison_with_safety():
    """Test comprehensive multi-city comparison with safety assessment."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Create mock responses for multiple cities with varying safety levels
        cities_data = [
            ("bern", 17.2, 92.0, "Safe"),
            ("thun", 16.5, 65.0, "Safe"),
            ("basel", 18.9, 250.0, "Elevated"),  # Higher flow
        ]
        
        responses = []
        for city, temp, flow, _ in cities_data:
            mock_resp = MagicMock()
            mock_resp.aare.location = city.capitalize()
            mock_resp.aare.location_long = city.capitalize()
            mock_resp.aare.temperature = temp
            mock_resp.aare.temperature_text = "test"
            mock_resp.aare.flow = flow
            mock_resp.aare.flow_text = "test"
            mock_resp.aare.flow_scale_threshold = 220
            responses.append(mock_resp)
        
        mock_client.get_current.side_effect = responses
        
        result = await tools.compare_cities(["bern", "thun", "basel"])
        
        # Verify warmest is Basel
        assert result["warmest"]["name"] == "Basel"
        
        # Verify safest is Thun (lowest flow)
        assert result["safest"]["name"] == "Thun"
        
        # Verify danger levels are calculated
        assert all("danger_level" in city for city in result["cities"])
        
        # Basel should have higher danger level due to elevated flow
        basel_data = next(c for c in result["cities"] if c["name"] == "Basel")
        assert basel_data["danger_level"] >= 3  # Elevated or higher
