"""Unit tests for MCP server handlers.

Tests all MCP protocol handlers including tool listing, tool calling,
resource listing, and resource reading.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch

from mcp.types import Tool, TextContent

from aareguru_mcp.server import (
    handle_list_tools,
    handle_call_tool,
    handle_list_resources,
    handle_read_resource,
)


# Tool Listing Tests (5 tests)


@pytest.mark.asyncio
async def test_handle_list_tools_returns_all_tools():
    """Test that handle_list_tools returns all 7 tools."""
    tools = await handle_list_tools()
    
    assert len(tools) == 7
    assert all(isinstance(tool, Tool) for tool in tools)


@pytest.mark.asyncio
async def test_handle_list_tools_has_correct_names():
    """Test that all tools have correct names."""
    tools = await handle_list_tools()
    tool_names = [tool.name for tool in tools]
    
    expected_names = [
        "get_current_temperature",
        "get_current_conditions",
        "get_historical_data",
        "list_cities",
        "get_flow_danger_level",
        "compare_cities",
        "get_forecast",
    ]
    
    assert tool_names == expected_names


@pytest.mark.asyncio
async def test_handle_list_tools_all_have_descriptions():
    """Test that all tools have descriptions."""
    tools = await handle_list_tools()
    
    for tool in tools:
        assert tool.description is not None
        assert len(tool.description) > 0
        assert isinstance(tool.description, str)


@pytest.mark.asyncio
async def test_handle_list_tools_all_have_schemas():
    """Test that all tools have input schemas."""
    tools = await handle_list_tools()
    
    for tool in tools:
        assert tool.inputSchema is not None
        assert isinstance(tool.inputSchema, dict)
        assert "type" in tool.inputSchema
        assert tool.inputSchema["type"] == "object"
        assert "properties" in tool.inputSchema


@pytest.mark.asyncio
async def test_handle_list_tools_historical_data_has_required_params():
    """Test that get_historical_data has required parameters."""
    tools = await handle_list_tools()
    historical_tool = next(t for t in tools if t.name == "get_historical_data")
    
    assert "required" in historical_tool.inputSchema
    assert set(historical_tool.inputSchema["required"]) == {"city", "start", "end"}


# Tool Calling Tests (10 tests)


@pytest.mark.asyncio
async def test_handle_call_tool_temperature_with_city():
    """Test calling get_current_temperature with city parameter."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_temperature = AsyncMock(
            return_value={
                "city": "bern",
                "temperature": 17.2,
                "temperature_text": "geil aber chli chalt",
            }
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={"city": "bern"}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        
        # Verify JSON content
        data = json.loads(result[0].text)
        assert data["city"] == "bern"
        assert data["temperature"] == 17.2
        
        mock_tools.get_current_temperature.assert_called_once_with("bern")


@pytest.mark.asyncio
async def test_handle_call_tool_temperature_default_city():
    """Test calling get_current_temperature without city uses default."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_temperature = AsyncMock(
            return_value={"city": "bern", "temperature": 17.2}
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={}
        )
        
        assert isinstance(result, list)
        mock_tools.get_current_temperature.assert_called_once_with("bern")


@pytest.mark.asyncio
async def test_handle_call_tool_current_conditions():
    """Test calling get_current_conditions."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_conditions = AsyncMock(
            return_value={
                "aare": {"temperature": 17.2, "flow": 85.3},
                "weather": {"temp": 22.0},
            }
        )
        
        result = await handle_call_tool(
            name="get_current_conditions",
            arguments={"city": "basel"}
        )
        
        assert isinstance(result, list)
        data = json.loads(result[0].text)
        assert "aare" in data
        assert "weather" in data
        
        mock_tools.get_current_conditions.assert_called_once_with("basel")


@pytest.mark.asyncio
async def test_handle_call_tool_historical_data():
    """Test calling get_historical_data with all required parameters."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_historical_data = AsyncMock(
            return_value={"timeseries": [{"timestamp": 123, "temp": 17.0}]}
        )
        
        result = await handle_call_tool(
            name="get_historical_data",
            arguments={"city": "bern", "start": "-7 days", "end": "now"}
        )
        
        assert isinstance(result, list)
        data = json.loads(result[0].text)
        assert "timeseries" in data
        
        mock_tools.get_historical_data.assert_called_once_with("bern", "-7 days", "now")


@pytest.mark.asyncio
async def test_handle_call_tool_list_cities():
    """Test calling list_cities with no parameters."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.list_cities = AsyncMock(
            return_value=[
                {"city": "bern", "name": "Bern", "temperature": 17.2},
                {"city": "thun", "name": "Thun", "temperature": 16.5},
            ]
        )
        
        result = await handle_call_tool(
            name="list_cities",
            arguments={}
        )
        
        assert isinstance(result, list)
        data = json.loads(result[0].text)
        assert len(data) == 2
        assert data[0]["city"] == "bern"
        
        mock_tools.list_cities.assert_called_once()


@pytest.mark.asyncio
async def test_handle_call_tool_flow_danger_level():
    """Test calling get_flow_danger_level."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_flow_danger_level = AsyncMock(
            return_value={
                "city": "bern",
                "flow": 85.3,
                "safety_assessment": "SAFE",
                "danger_level": "low",
            }
        )
        
        result = await handle_call_tool(
            name="get_flow_danger_level",
            arguments={"city": "bern"}
        )
        
        assert isinstance(result, list)
        data = json.loads(result[0].text)
        assert data["flow"] == 85.3
        assert data["danger_level"] == "low"
        
        mock_tools.get_flow_danger_level.assert_called_once_with("bern")


@pytest.mark.asyncio
async def test_handle_call_tool_unknown_tool():
    """Test calling unknown tool returns error."""
    result = await handle_call_tool(
        name="unknown_tool",
        arguments={}
    )
    
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], TextContent)
    assert "Error" in result[0].text
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_handle_call_tool_exception_handling():
    """Test that exceptions are caught and returned as error TextContent."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_temperature = AsyncMock(
            side_effect=Exception("API error")
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={"city": "bern"}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert "Error" in result[0].text
        assert "API error" in result[0].text


@pytest.mark.asyncio
async def test_handle_call_tool_returns_valid_json():
    """Test that tool results are formatted as valid JSON."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_temperature = AsyncMock(
            return_value={"city": "bern", "temperature": 17.2}
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={"city": "bern"}
        )
        
        # Should not raise JSONDecodeError
        data = json.loads(result[0].text)
        assert isinstance(data, dict)


@pytest.mark.asyncio
async def test_handle_call_tool_json_formatting():
    """Test that JSON is formatted with indentation and non-ASCII characters."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        # Include Swiss German text with special characters
        mock_tools.get_current_temperature = AsyncMock(
            return_value={
                "city": "bern",
                "temperature": 17.2,
                "temperature_text": "geil aber chli chält",  # ä character
            }
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={"city": "bern"}
        )
        
        # Verify Swiss German characters are preserved (ensure_ascii=False)
        assert "geil aber chli chält" in result[0].text
        
        # Verify indentation (indent=2)
        assert "\n" in result[0].text


# Resource Tests (6 tests)


@pytest.mark.asyncio
async def test_handle_list_resources_returns_all_resources():
    """Test that handle_list_resources returns all 4 resources."""
    with patch("aareguru_mcp.server.resources") as mock_resources:
        mock_resources.list_resources = AsyncMock(
            return_value=[
                {"uri": "aareguru://cities", "name": "Cities"},
                {"uri": "aareguru://current/{city}", "name": "Current"},
                {"uri": "aareguru://today/{city}", "name": "Today"},
                {"uri": "aareguru://widget", "name": "Widget"},
            ]
        )
        
        result = await handle_list_resources()
        
        assert isinstance(result, list)
        assert len(result) == 4
        mock_resources.list_resources.assert_called_once()


@pytest.mark.asyncio
async def test_handle_list_resources_has_uris():
    """Test that all resources have URIs."""
    with patch("aareguru_mcp.server.resources") as mock_resources:
        mock_resources.list_resources = AsyncMock(
            return_value=[
                {"uri": "aareguru://cities", "name": "Cities"},
                {"uri": "aareguru://widget", "name": "Widget"},
            ]
        )
        
        result = await handle_list_resources()
        
        for resource in result:
            assert "uri" in resource
            assert resource["uri"].startswith("aareguru://")


@pytest.mark.asyncio
async def test_handle_read_resource_valid_uri():
    """Test reading a resource with valid URI."""
    with patch("aareguru_mcp.server.resources") as mock_resources:
        mock_resources.read_resource = AsyncMock(
            return_value='{"cities": ["bern", "thun"]}'
        )
        
        result = await handle_read_resource("aareguru://cities")
        
        assert isinstance(result, str)
        assert "bern" in result
        mock_resources.read_resource.assert_called_once_with("aareguru://cities")


@pytest.mark.asyncio
async def test_handle_read_resource_with_city():
    """Test reading a resource with city parameter in URI."""
    with patch("aareguru_mcp.server.resources") as mock_resources:
        mock_resources.read_resource = AsyncMock(
            return_value='{"aare": {"temperature": 17.2}}'
        )
        
        result = await handle_read_resource("aareguru://today/bern")
        
        assert isinstance(result, str)
        assert "temperature" in result
        mock_resources.read_resource.assert_called_once_with("aareguru://today/bern")


@pytest.mark.asyncio
async def test_handle_read_resource_invalid_uri():
    """Test reading resource with invalid URI raises error."""
    with patch("aareguru_mcp.server.resources") as mock_resources:
        mock_resources.read_resource = AsyncMock(
            side_effect=ValueError("Invalid URI")
        )
        
        with pytest.raises(ValueError, match="Invalid URI"):
            await handle_read_resource("invalid://uri")


@pytest.mark.asyncio
async def test_handle_read_resource_returns_string():
    """Test that read_resource returns a string (JSON)."""
    with patch("aareguru_mcp.server.resources") as mock_resources:
        mock_resources.read_resource = AsyncMock(
            return_value='{"test": "data"}'
        )
        
        result = await handle_read_resource("aareguru://cities")
        
        assert isinstance(result, str)
        # Should be valid JSON
        data = json.loads(result)
        assert isinstance(data, dict)


# Error Handling Tests (4 tests)


@pytest.mark.asyncio
async def test_error_message_no_stack_trace():
    """Test that error messages don't expose stack traces."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_temperature = AsyncMock(
            side_effect=Exception("Internal error")
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={"city": "bern"}
        )
        
        # Should contain error message but not full stack trace
        assert "Error: Internal error" in result[0].text
        # Should not contain traceback details
        assert "Traceback" not in result[0].text


@pytest.mark.asyncio
async def test_missing_required_parameter():
    """Test calling tool with missing required parameter."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        # historical_data requires city, start, end
        mock_tools.get_historical_data = AsyncMock(
            side_effect=KeyError("city")
        )
        
        result = await handle_call_tool(
            name="get_historical_data",
            arguments={"start": "-7 days", "end": "now"}  # Missing city
        )
        
        assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_invalid_argument_type():
    """Test calling tool with invalid argument type."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_current_temperature = AsyncMock(
            side_effect=TypeError("Invalid type")
        )
        
        result = await handle_call_tool(
            name="get_current_temperature",
            arguments={"city": 123}  # Should be string
        )
        
        assert "Error" in result[0].text
        assert "Invalid type" in result[0].text


@pytest.mark.asyncio
async def test_graceful_error_formatting():
    """Test that errors are formatted gracefully as TextContent."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.list_cities = AsyncMock(
            side_effect=RuntimeError("Network timeout")
        )
        
        result = await handle_call_tool(
            name="list_cities",
            arguments={}
        )
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert result[0].type == "text"
        assert "Error" in result[0].text
        assert "Network timeout" in result[0].text


# New Tool Tests (4 tests)


@pytest.mark.asyncio
async def test_handle_call_tool_compare_cities():
    """Test calling compare_cities tool."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.compare_cities = AsyncMock(
            return_value={
                "cities": [
                    {"city": "bern", "name": "Bern", "temperature": 17.2},
                    {"city": "thun", "name": "Thun", "temperature": 16.5},
                ],
                "warmest": {"city": "bern", "name": "Bern", "temperature": 17.2},
                "coldest": {"city": "thun", "name": "Thun", "temperature": 16.5},
                "safest": {"city": "thun", "name": "Thun", "flow": 65.0},
                "comparison_summary": "Warmest: Bern (17.2°C) | Coldest: Thun (16.5°C)",
            }
        )
        
        result = await handle_call_tool(
            name="compare_cities",
            arguments={"cities": ["bern", "thun"]}
        )
        
        assert isinstance(result, list)
        data = json.loads(result[0].text)
        assert "warmest" in data
        assert data["warmest"]["name"] == "Bern"
        
        mock_tools.compare_cities.assert_called_once_with(["bern", "thun"])


@pytest.mark.asyncio
async def test_handle_call_tool_compare_cities_all():
    """Test calling compare_cities without cities parameter (all cities)."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.compare_cities = AsyncMock(
            return_value={
                "cities": [],
                "warmest": None,
                "coldest": None,
                "safest": None,
                "comparison_summary": "Comparison complete",
            }
        )
        
        result = await handle_call_tool(
            name="compare_cities",
            arguments={}
        )
        
        assert isinstance(result, list)
        mock_tools.compare_cities.assert_called_once_with(None)


@pytest.mark.asyncio
async def test_handle_call_tool_get_forecast():
    """Test calling get_forecast tool."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_forecast = AsyncMock(
            return_value={
                "city": "bern",
                "current": {"temperature": 17.2, "flow": 92.0},
                "forecast_2h": 17.8,
                "forecast_text": "slightly warmer",
                "trend": "rising",
                "temperature_change": 0.6,
                "recommendation": "Temperature rising by 0.6°C",
            }
        )
        
        result = await handle_call_tool(
            name="get_forecast",
            arguments={"city": "bern", "hours": 2}
        )
        
        assert isinstance(result, list)
        data = json.loads(result[0].text)
        assert data["trend"] == "rising"
        assert data["forecast_2h"] == 17.8
        
        mock_tools.get_forecast.assert_called_once_with("bern", 2)


@pytest.mark.asyncio
async def test_handle_call_tool_get_forecast_default_params():
    """Test calling get_forecast with default parameters."""
    with patch("aareguru_mcp.server.tools") as mock_tools:
        mock_tools.get_forecast = AsyncMock(
            return_value={
                "city": "bern",
                "current": {"temperature": 17.2},
                "forecast_2h": 17.5,
                "trend": "stable",
                "recommendation": "Temperature stable",
            }
        )
        
        result = await handle_call_tool(
            name="get_forecast",
            arguments={}
        )
        
        assert isinstance(result, list)
        mock_tools.get_forecast.assert_called_once_with("bern", 2)

