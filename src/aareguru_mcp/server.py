"""MCP server implementation for Aareguru API.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio transport.
"""

import asyncio
import logging
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from . import resources, tools
from .config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# Create MCP server instance
app = Server("aareguru-mcp")


@app.list_resources()
async def handle_list_resources() -> list:
    """Handle list_resources request."""
    logger.info("Listing resources")
    return await resources.list_resources()


@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Handle read_resource request."""
    logger.info(f"Reading resource: {uri}")
    return await resources.read_resource(uri)


@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """Handle list_tools request."""
    logger.info("Listing tools")
    
    return [
        Tool(
            name="get_current_temperature",
            description="Get current water temperature for a specific city. Use this for quick temperature checks and simple 'how warm is the water?' questions. Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'), and swimming suitability.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City identifier (e.g., 'bern', 'thun', 'basel', 'olten'). Use list_cities to discover available locations.",
                        "default": "bern",
                    }
                },
            },
        ),
        Tool(
            name="get_current_conditions",
            description="Get comprehensive swimming conditions report including water temperature, flow rate, water height, weather conditions, and 2-hour forecast. Use this for safety assessments, 'is it safe to swim?' questions, and when users need a complete picture before swimming. This is the most detailed tool - use it for contextual and safety-critical queries.",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City identifier (e.g., 'bern', 'thun', 'basel', 'olten'). Use list_cities to discover available locations.",
                        "default": "bern",
                    }
                },
            },
        ),
        Tool(
            name="get_historical_data",
            description="Get historical time-series data for trend analysis, comparisons with past conditions, and statistical queries. Returns hourly data points for temperature and flow. Use this for questions like 'how has temperature changed this week?' or 'what was the warmest day this month?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City identifier (e.g., 'bern', 'thun', 'basel', 'olten')",
                    },
                    "start": {
                        "type": "string",
                        "description": "Start date/time. Accepts ISO format (2024-11-01T00:00:00Z), Unix timestamp, or relative expressions like '-7 days', '-1 week', '-30 days'. Relative times are calculated from now.",
                    },
                    "end": {
                        "type": "string",
                        "description": "End date/time. Accepts ISO format, Unix timestamp, or 'now' for current time. Use 'now' for most recent data.",
                    },
                },
                "required": ["city", "start", "end"],
            },
        ),
        Tool(
            name="list_cities",
            description="Get all available cities with Aare monitoring stations. Returns city identifiers, full names, coordinates, and current temperature for each location. Use this for location discovery ('which cities are available?') and for comparing temperatures across all cities to find the warmest/coldest spot.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_flow_danger_level",
            description="Get current flow rate (m³/s) and safety assessment based on BAFU (Swiss Federal Office for the Environment) danger thresholds. Returns flow rate, danger level classification, and safety recommendations for swimmers. Use this for safety-critical questions about current strength and swimming danger. Flow thresholds: <100 (safe), 100-220 (moderate), 220-300 (elevated), 300-430 (high/dangerous), >430 (very high/extremely dangerous).",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "City identifier (e.g., 'bern', 'thun', 'basel', 'olten'). Use list_cities to discover available locations.",
                        "default": "bern",
                    }
                },
            },
        ),
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle call_tool request."""
    logger.info(f"Calling tool: {name} with arguments: {arguments}")
    
    try:
        # Route to appropriate tool
        if name == "get_current_temperature":
            city = arguments.get("city", "bern")
            result = await tools.get_current_temperature(city)
            
        elif name == "get_current_conditions":
            city = arguments.get("city", "bern")
            result = await tools.get_current_conditions(city)
            
        elif name == "get_historical_data":
            city = arguments["city"]
            start = arguments["start"]
            end = arguments["end"]
            result = await tools.get_historical_data(city, start, end)
            
        elif name == "list_cities":
            result = await tools.list_cities()
            
        elif name == "get_flow_danger_level":
            city = arguments.get("city", "bern")
            result = await tools.get_flow_danger_level(city)
            
        else:
            raise ValueError(f"Unknown tool: {name}")
        
        # Format result as TextContent
        import json
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2, ensure_ascii=False),
        )]
        
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=f"Error: {str(e)}",
        )]



async def main():
    """Main entry point for the MCP server."""
    settings = get_settings()
    logger.info(f"Starting Aareguru MCP Server v{settings.app_version}")
    logger.info(f"API base URL: {settings.aareguru_base_url}")
    
    # Run the server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options(),
        )


def entry_point():
    """Synchronous entry point for console script."""
    asyncio.run(main())


if __name__ == "__main__":
    entry_point()

