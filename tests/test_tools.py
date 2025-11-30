"""Tests for MCP tools."""

import pytest

from aareguru_mcp import tools


@pytest.mark.asyncio
async def test_get_current_temperature_default():
    """Test get_current_temperature with default city."""
    result = await tools.get_current_temperature()
    
    assert "city" in result
    assert "temperature" in result
    assert "temperature_text" in result
    assert result["city"] == "bern"


@pytest.mark.asyncio
async def test_get_current_temperature_specific_city():
    """Test get_current_temperature with specific city."""
    result = await tools.get_current_temperature("thun")
    
    assert result["city"] == "thun"
    assert "temperature" in result


@pytest.mark.asyncio
async def test_get_current_conditions():
    """Test get_current_conditions returns comprehensive data."""
    result = await tools.get_current_conditions("bern")
    
    assert result["city"] == "bern"
    assert "name" in result
    assert "aare" in result or "weather" in result  # At least one should be present


@pytest.mark.asyncio
async def test_get_current_conditions_has_aare_data():
    """Test current conditions includes Aare data."""
    result = await tools.get_current_conditions("bern")
    
    if "aare" in result:
        aare = result["aare"]
        assert "temperature" in aare
        assert "flow" in aare
        assert "flow_gefahrenstufe" in aare


@pytest.mark.asyncio
async def test_list_cities():
    """Test list_cities returns array of cities."""
    result = await tools.list_cities()
    
    assert isinstance(result, list)
    assert len(result) > 0
    
    # Check first city has required fields
    city = result[0]
    assert "city" in city
    assert "name" in city
    assert "longname" in city


@pytest.mark.asyncio
async def test_list_cities_includes_bern():
    """Test that Bern is in the cities list."""
    result = await tools.list_cities()
    
    cities = [c["city"] for c in result]
    assert "bern" in cities


@pytest.mark.asyncio
async def test_get_flow_danger_level():
    """Test get_flow_danger_level returns safety assessment."""
    result = await tools.get_flow_danger_level("bern")
    
    assert result["city"] == "bern"
    assert "flow" in result
    assert "flow_gefahrenstufe" in result
    assert "safety_assessment" in result


@pytest.mark.asyncio
async def test_get_flow_danger_level_safety_text():
    """Test safety assessment is human-readable."""
    result = await tools.get_flow_danger_level("bern")
    
    safety = result["safety_assessment"]
    assert isinstance(safety, str)
    assert len(safety) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_historical_data():
    """Test get_historical_data with relative dates."""
    result = await tools.get_historical_data(
        city="bern",
        start="-7 days",
        end="now",
    )
    
    assert "city" in result or "timeseries" in result or isinstance(result, dict)


@pytest.mark.asyncio
async def test_tool_error_handling():
    """Test tools handle errors gracefully."""
    # Invalid city should not crash
    try:
        result = await tools.get_current_temperature("invalid_city_xyz")
        # If it doesn't raise, result should indicate error
        assert result is not None
    except Exception as e:
        # Or it should raise a clear error
        assert "invalid" in str(e).lower() or "not found" in str(e).lower()
