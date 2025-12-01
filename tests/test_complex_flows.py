"""Tests for complex user flows and scenarios.

Tests end-to-end workflows that simulate real user interactions involving
multiple tools and decision making.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from aareguru_mcp import tools


@pytest.mark.integration
@pytest.mark.asyncio
async def test_cautious_swimmer_flow():
    """Scenario: User checks temp, sees warning, checks safety, finds safer spot.
    
    1. Check temp for Bern (High flow warning)
    2. Check detailed safety for Bern
    3. Compare cities to find safer option
    """
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # 1. Mock Bern high flow
        mock_bern_high = MagicMock()
        mock_bern_high.aare.location = "Bern"
        mock_bern_high.aare.temperature = 18.0
        mock_bern_high.aare.temperature_text = "warm"
        mock_bern_high.aare.flow = 350.0  # Dangerous
        mock_bern_high.aare.flow_scale_threshold = 220
        
        # 2. Mock Thun safe flow
        mock_thun_safe = MagicMock()
        mock_thun_safe.aare.location = "Thun"
        mock_thun_safe.aare.location_long = "Thun"
        mock_thun_safe.aare.temperature = 17.0
        mock_thun_safe.aare.temperature_text = "ok"
        mock_thun_safe.aare.flow = 80.0  # Safe
        mock_thun_safe.aare.flow_scale_threshold = 220
        
        # Setup side effects for sequence of calls
        # Call 1: get_current_temperature("bern")
        # Call 2: get_flow_danger_level("bern")
        # Call 3: compare_cities(["bern", "thun"]) -> calls get_current twice
        mock_client.get_current.side_effect = [
            mock_bern_high,  # 1
            mock_bern_high,  # 2
            mock_bern_high, mock_thun_safe  # 3
        ]
        
        # Step 1: Check temp
        temp_result = await tools.get_current_temperature("bern")
        assert temp_result["warning"] is not None
        assert "DANGER" in temp_result["warning"]
        
        # Step 2: Check safety details
        safety_result = await tools.get_flow_danger_level("bern")
        assert safety_result["danger_level"] >= 4  # High
        
        # Step 3: Compare to find safer spot
        compare_result = await tools.compare_cities(["bern", "thun"])
        assert compare_result["safest"]["name"] == "Thun"
        assert compare_result["safest"]["flow"] == 80.0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_group_planner_flow():
    """Scenario: Planner compares cities, checks forecast, makes decision.
    
    1. Compare all cities
    2. Pick warmest (Basel)
    3. Check forecast for Basel
    """
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock cities list
        mock_city1 = MagicMock()
        mock_city1.city = "bern"
        mock_city2 = MagicMock()
        mock_city2.city = "basel"
        mock_client.get_cities.return_value = [mock_city1, mock_city2]
        
        # Mock city data
        mock_bern = MagicMock()
        mock_bern.aare.location = "Bern"
        mock_bern.aare.location_long = "Bern"
        mock_bern.aare.temperature = 17.0
        mock_bern.aare.temperature_text = "ok"
        mock_bern.aare.flow = 90.0
        mock_bern.aare.flow_scale_threshold = 220
        
        mock_basel = MagicMock()
        mock_basel.aare.location = "Basel"
        mock_basel.aare.location_long = "Basel"
        mock_basel.aare.temperature = 19.0  # Warmest
        mock_basel.aare.temperature_text = "warm"
        mock_basel.aare.flow = 100.0
        mock_basel.aare.flow_scale_threshold = 220
        mock_basel.aare.forecast2h = 19.5
        mock_basel.aare.forecast2h_text = "rising"
        
        # Sequence: compare_cities(None) -> get_current(bern), get_current(basel)
        # Then: get_forecast("basel") -> get_current("basel")
        mock_client.get_current.side_effect = [
            mock_bern, mock_basel,  # compare loop
            mock_basel  # forecast
        ]
        
        # Step 1: Compare
        compare_result = await tools.compare_cities(None)
        warmest_city = compare_result["warmest"]["city"]
        assert warmest_city == "basel"
        
        # Step 2: Check forecast
        forecast_result = await tools.get_forecast(warmest_city)
        assert forecast_result["trend"] == "rising"
        assert "rising" in forecast_result["recommendation"]


@pytest.mark.integration
@pytest.mark.asyncio
async def test_winter_dipper_flow():
    """Scenario: User checks temp in winter, gets warning, checks history.
    
    1. Check temp (Winter advice)
    2. Check history (verify it's always cold)
    """
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock winter date
        with patch("aareguru_mcp.tools.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2024, 1, 15)
            
            # Mock current temp
            mock_resp = MagicMock()
            mock_resp.aare.temperature = 5.0
            mock_resp.aare.temperature_text = "brrr"
            mock_resp.aare.flow = 90.0
            mock_client.get_current.return_value = mock_resp
            
            # Mock history
            mock_client.get_history.return_value = {
                "timeseries": [{"temp": 5.1}, {"temp": 4.9}]
            }
            
            # Step 1: Check temp
            result = await tools.get_current_temperature("bern")
            assert "Winter" in result["seasonal_advice"]
            assert "freezing" in result["seasonal_advice"]
            
            # Step 2: Check history
            history = await tools.get_historical_data("bern", "-7 days", "now")
            assert len(history["timeseries"]) > 0
