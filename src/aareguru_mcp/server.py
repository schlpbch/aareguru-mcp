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

import functools
from typing import Any

import structlog
from fastmcp import FastMCP
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import prompts, resources, tools
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
@functools.wraps(resources.get_cities)
async def get_cities_resource() -> str:
    return await resources.get_cities()


@mcp.resource("aareguru://current/{city}")
@functools.wraps(resources.get_current)
async def get_current_resource(city: str) -> str:
    return await resources.get_current(city)


@mcp.resource("aareguru://today/{city}")
@functools.wraps(resources.get_today)
async def get_today_resource(city: str) -> str:
    return await resources.get_today(city)


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt(name="daily-swimming-report")
@functools.wraps(prompts.daily_swimming_report)
async def daily_swimming_report_prompt(city: str = "Bern", include_forecast: bool = True) -> str:
    return await prompts.daily_swimming_report(city, include_forecast)


@mcp.prompt(name="compare-swimming-spots")
@functools.wraps(prompts.compare_swimming_spots)
async def compare_swimming_spots_prompt(
    min_temperature: float | None = None, safety_only: bool = False
) -> str:
    return await prompts.compare_swimming_spots(min_temperature, safety_only)


@mcp.prompt(name="weekly-trend-analysis")
@functools.wraps(prompts.weekly_trend_analysis)
async def weekly_trend_analysis_prompt(city: str = "Bern", days: int = 7) -> str:
    return await prompts.weekly_trend_analysis(city, days)


# ============================================================================
# Tools
# ============================================================================


@mcp.tool(name="get_current_temperature")
@functools.wraps(tools.get_current_temperature)
async def get_current_temperature_tool(city: str = "Bern") -> TemperatureToolResponse:
    with MetricsCollector.track_tool_call("get_current_temperature"):
        result = await tools.get_current_temperature(city)
        return TemperatureToolResponse(**result)


@mcp.tool(name="get_current_conditions")
@functools.wraps(tools.get_current_conditions)
async def get_current_conditions_tool(city: str = "Bern") -> ConditionsToolResponse:
    result = await tools.get_current_conditions(city)
    if "aare" in result and result["aare"]:
        result["aare"] = AareConditionsData(**result["aare"])
    return ConditionsToolResponse(**result)


@mcp.tool(name="get_historical_data")
@functools.wraps(tools.get_historical_data)
async def get_historical_data_tool(city: str, start: str, end: str) -> dict[str, Any]:
    return await tools.get_historical_data(city, start, end)


@mcp.tool(name="get_flow_danger_level")
@functools.wraps(tools.get_flow_danger_level)
async def get_flow_danger_level_tool(city: str = "Bern") -> FlowDangerResponse:
    result = await tools.get_flow_danger_level(city)
    return FlowDangerResponse(**result)


@mcp.tool(name="compare_cities")
@functools.wraps(tools.compare_cities)
async def compare_cities_tool(cities: list[str] | None = None) -> dict[str, Any]:
    return await tools.compare_cities(cities)


@mcp.tool(name="get_forecasts")
@functools.wraps(tools.get_forecasts)
async def get_forecasts_tool(cities: list[str]) -> dict[str, Any]:
    return await tools.get_forecasts(cities)


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
