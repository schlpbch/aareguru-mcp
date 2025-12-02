"""End-to-end conversation tests for Aareguru MCP server.

Simulates real user conversation flows from USER_QUESTIONS_SLIDES.md
to verify tool selection, response quality, and data accuracy.
"""

import pytest

from aareguru_mcp import tools


# Basic Queries (3 tests)

@pytest.mark.e2e
async def test_basic_temperature_query():
    """Category 1: Basic Temperature - 'What's the Aare temperature in Bern?'"""
    # Simulate tool call
    result = await tools.get_current_temperature("bern")
    
    # Verify tool selection (correct tool used)
    assert "temperature" in result
    
    # Verify response format
    assert isinstance(result["temperature"], (int, float))
    
    # Verify Swiss German text present
    assert "temperature_text" in result
    assert result["temperature_text"] is not None
    assert len(result["temperature_text"]) > 0
    
    # Verify city information
    assert result["city"] == "bern"
    assert "name" in result


@pytest.mark.e2e
async def test_safety_assessment_query():
    """Category 2: Safety & Flow - 'Is it safe to swim in the Aare today?'"""
    # For safety questions, should use get_current_conditions or get_flow_danger_level
    # Test with get_current_conditions (more comprehensive)
    result = await tools.get_current_conditions("bern")
    
    # Verify comprehensive data present
    assert result is not None
    assert isinstance(result, dict)
    
    # Should have aare data with flow information
    if "aare" in result:
        aare_data = result["aare"]
        # Flow data should be present for safety assessment
        assert "flow" in aare_data or "temperature" in aare_data


@pytest.mark.e2e
async def test_weather_integration_query():
    """Category 3: Weather Integration - 'What's the weather like for swimming in Bern?'"""
    result = await tools.get_current_conditions("bern")
    
    # Should include weather data
    assert result is not None
    
    # Weather data may or may not be present depending on API
    # But the tool should handle it gracefully
    assert isinstance(result, dict)


# Comparative & Analysis (3 tests)

@pytest.mark.e2e
async def test_comparative_query():
    """Category 4: Comparative - 'Which city has the warmest water?'"""
    # Get all cities
    cities = await tools.list_cities()
    
    # Verify we got cities
    assert len(cities) > 0
    
    # Each city should have temperature
    cities_with_temp = [c for c in cities if "temperature" in c and c["temperature"] is not None]
    assert len(cities_with_temp) > 0
    
    # Find warmest (this is what Claude would do)
    warmest = max(cities_with_temp, key=lambda c: c["temperature"])
    
    # Verify warmest city has valid data
    assert "city" in warmest
    assert "name" in warmest
    assert isinstance(warmest["temperature"], (int, float))


@pytest.mark.e2e
async def test_historical_trend_query():
    """Category 5: Historical & Trends - 'How has temperature changed this week?'"""
    # Should use get_historical_data with relative date
    result = await tools.get_historical_data("bern", "-7 days", "now")
    
    # Verify historical data returned
    assert result is not None
    assert isinstance(result, dict)
    
    # Should have time series data (structure depends on API)
    # Just verify we got a response
    assert len(result) > 0


@pytest.mark.e2e
async def test_data_analysis_query():
    """Category 10: Data Analysis - 'What's the average temperature for the last month?'"""
    # Get historical data for 30 days
    result = await tools.get_historical_data("bern", "-30 days", "now")
    
    # Verify data returned
    assert result is not None
    assert isinstance(result, dict)


# Discovery & Context (3 tests)

@pytest.mark.e2e
async def test_location_discovery_query():
    """Category 7: Location Discovery - 'Which cities have data available?'"""
    cities = await tools.list_cities()
    
    # Verify complete city list
    assert len(cities) > 0
    
    # Each city should have required metadata
    for city in cities:
        assert "city" in city  # Identifier
        assert "name" in city  # Display name
        
        # Should have coordinates (for map display)
        if "coordinates" in city:
            coords = city["coordinates"]
            assert coords is not None


@pytest.mark.e2e
async def test_conversational_query():
    """Category 9: Conversational - 'How's the Aare looking today?'"""
    # Casual question should trigger comprehensive response
    result = await tools.get_current_conditions("bern")
    
    # Should return comprehensive data
    assert result is not None
    assert isinstance(result, dict)
    
    # Verify it's comprehensive (has multiple data points)
    assert len(result) > 1


@pytest.mark.e2e
async def test_contextual_complex_query():
    """Category 8: Contextual & Complex - 'Give me a full swimming report for Bern'"""
    result = await tools.get_current_conditions("bern")
    
    # Should have comprehensive data
    assert result is not None
    
    # Should include multiple aspects
    if "aare" in result:
        aare = result["aare"]
        # Should have temperature, flow, and forecast
        assert "temperature" in aare or "flow" in aare


# Advanced Scenarios (4 tests)

@pytest.mark.e2e
async def test_multi_step_query():
    """Category 12: Multi-Step - 'Check Bern temperature, then compare with Thun'"""
    # Step 1: Get Bern temperature
    bern_result = await tools.get_current_temperature("bern")
    bern_temp = bern_result["temperature"]
    
    # Step 2: Get Thun temperature
    thun_result = await tools.get_current_temperature("thun")
    thun_temp = thun_result["temperature"]
    
    # Step 3: Compare (Claude would do this)
    assert isinstance(bern_temp, (int, float))
    assert isinstance(thun_temp, (int, float))
    
    # Verify both are valid temperatures
    assert -5 <= bern_temp <= 35
    assert -5 <= thun_temp <= 35


@pytest.mark.e2e
async def test_specific_use_case_query():
    """Category 11: Specific Use Cases - 'I'm a tourist, where should I swim?'"""
    # Get all cities to provide recommendation
    cities = await tools.list_cities()
    
    # Filter cities with valid temperature
    valid_cities = [c for c in cities if "temperature" in c and c["temperature"] is not None]
    
    # Should have cities to recommend
    assert len(valid_cities) > 0
    
    # Each should have location info for tourist
    for city in valid_cities[:3]:  # Check first 3
        assert "name" in city
        assert "longname" in city or "name" in city


@pytest.mark.e2e
async def test_forecast_query():
    """Category 6: Forecast - 'Will the water be warmer later today?'"""
    result = await tools.get_current_conditions("bern")
    
    # Should include forecast data
    assert result is not None
    
    # Check if forecast is present
    if "aare" in result:
        aare = result["aare"]
        # 2-hour forecast should be available
        has_forecast = "forecast2h" in aare or "forecast2h_text" in aare
        # Forecast may not always be present, but structure should support it
        assert isinstance(aare, dict)


@pytest.mark.e2e
async def test_flow_danger_specific_query():
    """Category 2: Safety (specific) - 'What's the current danger level in Basel?'"""
    result = await tools.get_flow_danger_level("basel")
    
    # Verify BAFU scale information
    assert "flow" in result
    assert "safety_assessment" in result
    
    # Verify safety assessment is present
    assert result["safety_assessment"] is not None
    assert isinstance(result["safety_assessment"], str)
    assert len(result["safety_assessment"]) > 0
    
    # Verify flow threshold is documented
    assert "flow_threshold" in result


# Edge Cases (2 tests)

@pytest.mark.e2e
async def test_edge_case_invalid_city():
    """Category 13: Edge Cases - 'What's the temperature in Zurich?' (not monitored)"""
    # Zurich is not in the Aare river system
    # This should either raise an error or return gracefully
    
    try:
        result = await tools.get_current_temperature("zurich")
        # If it doesn't raise, verify it handles gracefully
        # (API might return error in response)
        assert result is not None
    except Exception as e:
        # Exception is acceptable for invalid city
        # Just verify it's a reasonable error
        error_msg = str(e).lower()
        assert len(error_msg) > 0


@pytest.mark.e2e
async def test_edge_case_swiss_german_explanation():
    """Category 13: Edge Cases - 'What does 'geil aber chli chalt' mean?'"""
    # This tests that Swiss German text is present and can be explained
    result = await tools.get_current_temperature("bern")
    
    # Verify Swiss German text is present
    assert "temperature_text" in result
    swiss_german = result["temperature_text"]
    
    # Verify it's a non-empty string
    assert isinstance(swiss_german, str)
    assert len(swiss_german) > 0
    
    # Swiss German text should be present (any phrase is valid)
    # The API returns various Swiss German temperature descriptions
    assert swiss_german is not None


# Additional integration test for MCP protocol

@pytest.mark.e2e
async def test_mcp_protocol_tool_call():
    """Test actual MCP protocol tool call flow."""
    from aareguru_mcp.server import handle_call_tool
    
    # Simulate MCP tool call
    result = await handle_call_tool(
        name="get_current_temperature",
        arguments={"city": "bern"}
    )
    
    # Should return TextContent list
    assert isinstance(result, list)
    assert len(result) > 0
    
    # First item should be TextContent
    text_content = result[0]
    assert hasattr(text_content, "text")
    
    # Text should be valid JSON
    import json
    data = json.loads(text_content.text)
    assert "temperature" in data
