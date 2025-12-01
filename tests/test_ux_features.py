"""Tests for UX features: safety checks, suggestions, and seasonal advice.

Tests the "Smart Logic" added in Week 5.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from aareguru_mcp import tools


# Safety Checks Tests


@pytest.mark.asyncio
async def test_safety_warning_high_flow():
    """Test that high flow triggers a warning."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock high flow
        mock_resp = MagicMock()
        mock_resp.aare.temperature = 17.0
        mock_resp.aare.temperature_text = "test"
        mock_resp.aare.flow = 350.0  # > 300
        mock_resp.aare.flow_scale_threshold = 220
        
        mock_client.get_current.return_value = mock_resp
        
        result = await tools.get_current_temperature("bern")
        
        assert result["warning"] is not None
        assert "DANGER" in result["warning"]
        assert "High flow rate" in result["warning"]


@pytest.mark.asyncio
async def test_safety_warning_extreme_flow():
    """Test that extreme flow triggers a severe warning."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock extreme flow
        mock_resp = MagicMock()
        mock_resp.aare.temperature = 17.0
        mock_resp.aare.temperature_text = "test"
        mock_resp.aare.flow = 500.0  # > 430
        
        mock_client.get_current.return_value = mock_resp
        
        result = await tools.get_current_temperature("bern")
        
        assert "EXTREME DANGER" in result["warning"]
        assert "life-threatening" in result["warning"]


@pytest.mark.asyncio
async def test_no_safety_warning_low_flow():
    """Test that low flow triggers no warning."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock low flow
        mock_resp = MagicMock()
        mock_resp.aare.temperature = 17.0
        mock_resp.aare.temperature_text = "test"
        mock_resp.aare.flow = 90.0
        
        mock_client.get_current.return_value = mock_resp
        
        result = await tools.get_current_temperature("bern")
        
        assert result["warning"] is None


# Smart Suggestions Tests


@pytest.mark.asyncio
async def test_suggestion_when_cold():
    """Test suggesting a warmer city when current is cold."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock current city (Bern) as cold
        mock_bern = MagicMock()
        mock_bern.aare.temperature = 15.0
        mock_bern.aare.temperature_text = "cold"
        mock_bern.aare.flow = 90.0
        
        mock_client.get_current.return_value = mock_bern
        
        # Mock all cities list with a warmer one (Basel)
        mock_city1 = MagicMock()
        mock_city1.city = "bern"
        mock_city1.aare = 15.0
        
        mock_city2 = MagicMock()
        mock_city2.city = "basel"
        mock_city2.name = "Basel"
        mock_city2.aare = 19.0  # Much warmer
        
        mock_client.get_cities.return_value = [mock_city1, mock_city2]
        
        result = await tools.get_current_temperature("bern")
        
        assert result["suggestion"] is not None
        assert "Basel" in result["suggestion"]
        assert "warmer" in result["suggestion"]


@pytest.mark.asyncio
async def test_no_suggestion_when_warm_enough():
    """Test no suggestion when current city is warm enough."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock current city as warm
        mock_bern = MagicMock()
        mock_bern.aare.temperature = 19.0
        mock_bern.aare.temperature_text = "warm"
        mock_bern.aare.flow = 90.0
        
        mock_client.get_current.return_value = mock_bern
        
        result = await tools.get_current_temperature("bern")
        
        assert result["suggestion"] is None


# Seasonal Advice Tests


@patch("aareguru_mcp.tools.datetime")
def test_seasonal_advice_winter(mock_datetime):
    """Test seasonal advice for winter."""
    mock_datetime.now.return_value = datetime(2024, 1, 15)  # January
    
    advice = tools._get_seasonal_advice()
    assert "Winter" in advice
    assert "freezing" in advice


@patch("aareguru_mcp.tools.datetime")
def test_seasonal_advice_summer(mock_datetime):
    """Test seasonal advice for summer."""
    mock_datetime.now.return_value = datetime(2024, 7, 15)  # July
    
    advice = tools._get_seasonal_advice()
    assert "Summer" in advice
    assert "Perfect" in advice


# Cultural Context Tests


def test_swiss_german_explanation():
    """Test Swiss German explanations."""
    assert "understatement" in tools._get_swiss_german_explanation("geil aber chli chalt")
    assert "Nice and warm" in tools._get_swiss_german_explanation("schön warm")
    assert tools._get_swiss_german_explanation("unknown phrase") is None


@pytest.mark.asyncio
async def test_explanation_in_response():
    """Test that explanation is included in tool response."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        mock_resp = MagicMock()
        mock_resp.aare.temperature = 17.0
        mock_resp.aare.temperature_text = "geil aber chli chalt"
        mock_resp.aare.flow = 90.0
        
        mock_client.get_current.return_value = mock_resp
        
        result = await tools.get_current_temperature("bern")
        
        assert result["swiss_german_explanation"] is not None
        assert "understatement" in result["swiss_german_explanation"]


# Compare Cities Recommendations


@pytest.mark.asyncio
async def test_compare_cities_recommendation():
    """Test smart recommendation in compare_cities."""
    with patch("aareguru_mcp.tools.AareguruClient") as MockClient:
        mock_client = AsyncMock()
        MockClient.return_value.__aenter__.return_value = mock_client
        
        # Mock cities: Bern (warm & safe), Thun (cold & safe)
        mock_bern = MagicMock()
        mock_bern.aare.location = "Bern"
        mock_bern.aare.location_long = "Bern"
        mock_bern.aare.temperature = 18.0
        mock_bern.aare.temperature_text = "test"
        mock_bern.aare.flow = 90.0
        mock_bern.aare.flow_scale_threshold = 220
        
        mock_thun = MagicMock()
        mock_thun.aare.location = "Thun"
        mock_thun.aare.location_long = "Thun"
        mock_thun.aare.temperature = 16.0
        mock_thun.aare.temperature_text = "test"
        mock_thun.aare.flow = 80.0
        mock_thun.aare.flow_scale_threshold = 220
        
        mock_client.get_current.side_effect = [mock_bern, mock_thun]
        
        result = await tools.compare_cities(["bern", "thun"])
        
        assert "Best Choice" in result["recommendation"]
        assert "Bern" in result["recommendation"]
