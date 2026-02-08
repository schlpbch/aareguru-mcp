"""MCP server implementation for Aareguru API using FastMCP.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio or HTTP transport.

Server responsibilities:
- Create FastMCP server instance
- Register resources (cities, current, today)
- Register prompts and tools (delegate to prompts.py and tools.py)
- Register custom HTTP routes (health, metrics)
- Provide entry points for stdio and HTTP transports
"""

import json
from typing import Any

import structlog
from fastmcp import FastMCP
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import prompts, tools
from .client import AareguruClient
from .config import get_settings
from .metrics import MetricsCollector
from .models import (
    AareConditionsData,
    ConditionsToolResponse,
    FlowDangerResponse,
    TemperatureToolResponse,
)
from .rate_limit import limiter

# Get structured logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastMCP server instance
mcp = FastMCP(
    name="aareguru-mcp",
    instructions="""You are an assistant that helps users with Swiss Aare river conditions.

You can provide:
- Current water temperatures for various Swiss cities
- Flow rates and safety assessments based on BAFU thresholds
- Weather conditions and forecasts
- Historical data for trend analysis
- Comparisons between different cities

Always consider safety when discussing swimming conditions. Flow rates above 220 m³/s
require caution, and rates above 300 m³/s are dangerous.

Swiss German phrases in the API responses add local flavor - feel free to explain them
to users (e.g., "geil aber chli chalt" means "awesome but a bit cold").
""",
)


# ============================================================================
# Resources
# ============================================================================


@mcp.resource("aareguru://cities")
async def get_cities_resource() -> str:
    """Retrieves the complete list of cities with Aare monitoring stations.

    Returns JSON array containing city identifiers, full names, coordinates,
    and current temperature readings for all monitored locations. Use this
    resource for location discovery and initial data exploration.

    Returns:
        JSON string with array of city objects, each containing:
        - city (str): City identifier (e.g., 'Bern', 'Thun')
        - name (str): Display name
        - longname (str): Full location name
        - coordinates (object): Latitude and longitude
        - aare (float): Current water temperature in Celsius
    """
    async with AareguruClient(settings=settings) as client:
        response = await client.get_cities()
        return json.dumps([city.model_dump() for city in response], indent=2)


@mcp.resource("aareguru://current/{city}")
async def get_current_resource(city: str) -> str:
    """Retrieves complete current conditions for a specific city.

    Returns comprehensive real-time data including water temperature, flow rate,
    weather conditions, and forecasts for the specified location.

    Args:
        city: City identifier (e.g., 'Bern', 'Thun')

    Returns:
        JSON string with complete current conditions including temperature,
        flow, weather, and forecast data for the specified city.
    """
    async with AareguruClient(settings=settings) as client:
        response = await client.get_current(city)
        return response.model_dump_json(indent=2)


@mcp.resource("aareguru://today/{city}")
async def get_today_resource(city: str) -> str:
    """Retrieves minimal current data snapshot for a specific city.

    Returns a lightweight data structure with essential current information.
    Use this when you only need basic temperature data without full details.

    Args:
        city: City identifier (e.g., 'Bern', 'Thun')

    Returns:
        JSON string with minimal current data including temperature and
        basic location information for the specified city.
    """
    async with AareguruClient(settings=settings) as client:
        response = await client.get_today(city)
        return response.model_dump_json(indent=2)


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt(name="daily-swimming-report")
async def daily_swimming_report_prompt(city: str = "Bern", include_forecast: bool = True) -> str:
    return await prompts.daily_swimming_report(city, include_forecast)

daily_swimming_report_prompt.__doc__ = prompts.daily_swimming_report.__doc__


@mcp.prompt(name="compare-swimming-spots")
async def compare_swimming_spots_prompt(
    min_temperature: float | None = None, safety_only: bool = False
) -> str:
    return await prompts.compare_swimming_spots(min_temperature, safety_only)

compare_swimming_spots_prompt.__doc__ = prompts.compare_swimming_spots.__doc__


@mcp.prompt(name="weekly-trend-analysis")
async def weekly_trend_analysis_prompt(city: str = "Bern", days: int = 7) -> str:
    return await prompts.weekly_trend_analysis(city, days)

weekly_trend_analysis_prompt.__doc__ = prompts.weekly_trend_analysis.__doc__


# ============================================================================
# Tools
# ============================================================================


@mcp.tool(name="get_current_temperature")
async def get_current_temperature_tool(city: str = "Bern") -> TemperatureToolResponse:
    with MetricsCollector.track_tool_call("get_current_temperature"):
        result = await tools.get_current_temperature(city)
        return TemperatureToolResponse(**result)

get_current_temperature_tool.__doc__ = tools.get_current_temperature.__doc__


@mcp.tool(name="get_current_conditions")
async def get_current_conditions_tool(city: str = "Bern") -> ConditionsToolResponse:
    result = await tools.get_current_conditions(city)
    if "aare" in result and result["aare"]:
        result["aare"] = AareConditionsData(**result["aare"])
    return ConditionsToolResponse(**result)

get_current_conditions_tool.__doc__ = tools.get_current_conditions.__doc__


@mcp.tool(name="get_historical_data")
async def get_historical_data_tool(city: str, start: str, end: str) -> dict[str, Any]:
    return await tools.get_historical_data(city, start, end)

get_historical_data_tool.__doc__ = tools.get_historical_data.__doc__


@mcp.tool(name="get_flow_danger_level")
async def get_flow_danger_level_tool(city: str = "Bern") -> FlowDangerResponse:
    result = await tools.get_flow_danger_level(city)
    return FlowDangerResponse(**result)

get_flow_danger_level_tool.__doc__ = tools.get_flow_danger_level.__doc__


@mcp.tool(name="compare_cities")
async def compare_cities_tool(cities: list[str] | None = None) -> dict[str, Any]:
    return await tools.compare_cities(cities)

compare_cities_tool.__doc__ = tools.compare_cities.__doc__


@mcp.tool(name="get_forecasts")
async def get_forecasts_tool(cities: list[str]) -> dict[str, Any]:
    return await tools.get_forecasts(cities)

get_forecasts_tool.__doc__ = tools.get_forecasts.__doc__


# ============================================================================
# Custom Routes (for HTTP transport)
# ============================================================================


@mcp.custom_route("/health", methods=["GET"])
@limiter.limit("60/minute")
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": mcp.name,
            "version": settings.app_version,
        }
    )


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ============================================================================
# Entry Points
# ============================================================================


def entry_point() -> None:
    """Synchronous entry point for stdio transport (console script)."""
    mcp.run()


def run_http() -> None:
    """Entry point for HTTP transport."""
    mcp.run(
        transport="http",
        host=settings.http_host,
        port=settings.http_port,
    )


# For backwards compatibility
app = mcp

if __name__ == "__main__":
    entry_point()
