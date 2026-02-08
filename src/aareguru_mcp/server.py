"""MCP server implementation for Aareguru API using FastMCP.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio or HTTP transport.
"""

import json
from typing import Any

import structlog
from fastmcp import FastMCP
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import tools
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
async def daily_swimming_report(city: str = "Bern", include_forecast: bool = True) -> str:
    """Generates comprehensive daily swimming report combining conditions, safety.

    **Args:**
        city: City to generate the report for (default: `Bern`).
              Use `compare_cities` to discover available locations.
        include_forecast: Whether to include 2-hour forecast in the report (default: `true`)

    **Returns:**
        Prompt template string instructing the LLM to create a formatted report
        with current conditions, safety assessment, forecast, and recommendations.
        The report includes Swiss German descriptions and safety warnings.
    """
    forecast_instruction = (
        "\n3. **Forecast**: Use `get_forecasts` to see how conditions "
        "will change in the next few hours"
        if include_forecast
        else ""
    )

    return f"""Please provide a comprehensive daily swimming report for {city}.

Include:
1. **Current Conditions**: Use `get_current_conditions` to get temperature, \
flow rate, and weather
2. **Safety Assessment**: Use `get_flow_danger_level` to assess if \
swimming is safe{forecast_instruction}
{'4' if include_forecast else '3'}. **Recommendation**: Based on all data, \
give a clear swimming recommendation

Format the report in a friendly way with emojis. Include the Swiss German description if available.
If conditions are dangerous, make this very clear at the top of the report.
If there's a better location nearby, suggest it."""


@mcp.prompt(name="compare-swimming-spots")
async def compare_swimming_spots(
    min_temperature: float | None = None, safety_only: bool = False
) -> str:
    """Generates comparison of all swimming locations ranked by temperature and safety.

    **Args:**
        min_temperature: Optional minimum temperature threshold in Celsius (e.g., `18.0`).
                        Filter out cities below this temperature.
        safety_only: Whether to show only safe locations (flow < 150 m³/s). Default: `false`.

    **Returns:**
        Prompt template string instructing the LLM to compare all cities,
        rank them by temperature and safety, and provide a recommendation
        for the best swimming location today.
    """
    filter_instructions = ""
    if min_temperature is not None:
        filter_instructions += f"\n- Only include cities with temperature >= {min_temperature}°C"
    if safety_only:
        filter_instructions += "\n- Only include cities with safe flow levels (< 150 m³/s)"

    # Use fast parallel comparison tool
    return f"""Please compare all available Aare swimming locations.

**Use `compare_cities` tool** - it fetches all city data concurrently for maximum speed.
This is 8-13x faster than sequential requests.

Present:
1. **🏆 Best Choice Today**: The recommended city based on temperature and safety
2. **📊 Comparison Table**: All cities ranked by temperature with safety status
3. **⚠️ Safety Notes**: Any locations to avoid due to high flow{filter_instructions}

Format as a clear, scannable report. Use emojis for quick visual reference:
- 🟢 Safe (flow < 150 m³/s)
- 🟡 Caution (150-220 m³/s)
- 🔴 Dangerous (> 220 m³/s)

End with a personalized recommendation based on conditions."""


@mcp.prompt(name="weekly-trend-analysis")
async def weekly_trend_analysis(city: str = "Bern", days: int = 7) -> str:
    """Generates trend analysis showing temperature and flow patterns with outlook.

    **Args:**
        city: City to analyze (default: `Bern`). Use `compare_cities` to discover locations.
        days: Number of days to analyze (`3`, `7`, or `14`). Default: `7` days (one week).

    **Returns:**
        Prompt template string instructing the LLM to analyze historical data,
        identify temperature and flow trends, and provide outlook recommendations
        for optimal swimming times.
    """
    period_name = "3-day" if days == 3 else "weekly" if days == 7 else f"{days}-day"

    return f"""Please analyze the {period_name} trends for {city}.

Use `get_historical_data` with days={days} to get the past {days} days of data, then provide:

1. **📈 Temperature Trend**: How has water temperature changed?
   - Highest and lowest temperatures
   - Current vs. {period_name} average
   - Is it warming or cooling?

2. **🌊 Flow Trend**: How has the flow rate varied?
   - Any dangerous periods?
   - Current conditions vs. average

3. **🔮 Outlook**: Based on trends and current forecast, what should swimmers expect?

Include specific numbers and dates. Make recommendations for the best swimming times."""


# ============================================================================
# Tools
# ============================================================================


@mcp.tool(name="get_current_temperature")
async def get_current_temperature(city: str = "Bern") -> TemperatureToolResponse:
    """Retrieves current water temperature for a single city.

    Takes `city` parameter (optional, default: `Bern`).

    Use this for quick temperature checks and simple "how warm is the water?" questions.
    Returns temperature in Celsius, Swiss German description (e.g., `geil aber chli chalt`),
    and swimming suitability.

    **For multiple cities:** Use `compare_cities` instead - it's 8-13x faster.

    **Args:**
        city: City identifier (e.g., `'Bern'`, `'Thun'`, `'basel'`, `'olten'`).
              Use `compare_cities` to discover locations.

    **Returns:**
        Dictionary containing:
        - city (str): City identifier
        - temperature (float): Water temperature in Celsius
        - temperature_text (str): Swiss German description
        - swiss_german_explanation (str): English translation of Swiss German phrase
        - name (str): Location name
        - warning (str | None): Safety warning if flow is dangerous
        - suggestion (str): Swimming recommendation based on temperature
        - seasonal_advice (str): Season-specific swimming guidance
        - temperature_prec (float): Precise temperature value
        - temperature_text_short (str): Short temperature description
        - longname (str): Full location name
    """
    with MetricsCollector.track_tool_call("get_current_temperature"):
        result = await tools.get_current_temperature(city)
        return TemperatureToolResponse(**result)


@mcp.tool(name="get_current_conditions")
async def get_current_conditions(city: str = "Bern") -> ConditionsToolResponse:
    """Retrieves comprehensive swimming conditions for a single city.

    Takes `city` parameter (optional, default: `Bern`). Returns water temperature,
    flow rate, water height, weather conditions, and 2-hour forecast.

    Use this for safety assessments, "is it safe to swim?" questions, and when users
    need a complete picture before swimming. This is the most detailed single-city tool.

    **For comparing multiple cities:** Use `compare_cities` instead - it's 8-13x faster.

    **Args:**
        city: City identifier (e.g., `'Bern'`, `'Thun'`, `'basel'`,
              `'olten'`). Use `compare_cities` to discover locations.

    **Returns:**
        Dictionary containing:
        - city (str): City identifier
        - aare (dict): Aare river data with temperature, flow, height, and forecast
          - location (str): Location name
          - location_long (str): Full location name
          - temperature (float): Water temperature in Celsius
          - temperature_text (str): Swiss German temperature description
          - swiss_german_explanation (str): English translation
          - temperature_text_short (str): Short description
          - flow (float): Flow rate in m³/s
          - flow_text (str): Flow description
          - height (float): Water height in meters
          - forecast2h (float): Temperature forecast for 2 hours
          - forecast2h_text (str): Forecast description
          - warning (str | None): Safety warning if applicable
        - seasonal_advice (str): Season-specific guidance
        - weather (dict | None): Current weather conditions
        - forecast (dict | None): Weather forecast
    """
    result = await tools.get_current_conditions(city)

    # Convert aare dict to typed model if present
    if "aare" in result and result["aare"]:
        result["aare"] = AareConditionsData(**result["aare"])

    return ConditionsToolResponse(**result)


@mcp.tool(name="get_historical_data")
async def get_historical_data(city: str, start: str, end: str) -> dict[str, Any]:
    """Retrieves historical time-series data for trend analysis.

    Takes `city`, `start`, and `end` parameters (all required).
    Returns hourly data points for temperature and flow.

    Use this for questions like "how has temperature changed this week?"
    or "what was the warmest day this month?"

    **Args:**
        city: City identifier (e.g., `'Bern'`, `'Thun'`, `'basel'`, `'olten'`)
        start: Start date/time. Accepts ISO format (`2024-11-01T00:00:00Z`),
               Unix timestamp, or relative expressions like `'-7 days'`, `'-1 week'`.
        end: End date/time. Accepts ISO format, Unix timestamp, or `'now'` for current time.

    **Returns:**
        Dictionary containing:
        - timestamps (list[str]): ISO 8601 timestamps for each data point
        - temperatures (list[float]): Water temperatures in Celsius
        - flows (list[float]): Flow rates in m³/s
        - city (str): City identifier
        - start (str): Start timestamp of data range
        - end (str): End timestamp of data range
    """
    return await tools.get_historical_data(city, start, end)


@mcp.tool(name="get_flow_danger_level")
async def get_flow_danger_level(city: str = "Bern") -> FlowDangerResponse:
    """Retrieves current flow rate and safety assessment.

    Takes `city` parameter (optional, default: `Bern`).
    Returns flow rate (m³/s), danger level, and safety recommendations
    based on BAFU thresholds.

    Use this for safety-critical questions about current strength and danger.

    **Flow thresholds:**
    - `<100`: safe
    - `100-220`: moderate
    - `220-300`: elevated
    - `300-430`: high/dangerous
    - `>430`: very high/extremely dangerous

    **Args:**
        city: City identifier (e.g., `'Bern'`, `'Thun'`, `'basel'`, `'olten'`).
              Use `compare_cities` to discover available locations.

    **Returns:**
        Dictionary containing:
        - city (str): City identifier
        - flow (float | None): Current flow rate in m³/s
        - flow_text (str | None): Flow description
        - flow_threshold (float): Danger threshold for this location
        - safety_assessment (str): Safety evaluation (e.g., 'Safe', 'Dangerous')
        - danger_level (int): Numeric danger level (1-5, higher is more dangerous)
    """
    result = await tools.get_flow_danger_level(city)
    return FlowDangerResponse(**result)


@mcp.tool(name="compare_cities")
async def compare_cities(
    cities: list[str] | None = None,
) -> dict[str, Any]:
    """⚡ FAST: Compare multiple cities with parallel fetching (8-13x faster).

    This is the recommended tool for comparing cities. Fetches all city data
    concurrently instead of sequentially.

    **Performance:** 10 cities in ~60-100ms vs ~800ms sequential

    **Args:**
        cities: List of city identifiers (e.g., `['Bern', 'Thun']`).
                If None, compares all available cities.

    **Returns:**
        Dictionary with comparison results including temperature ranking,
        safety status, and recommendations:
        - cities (list): List of city data with temperature, flow, safety
        - warmest (dict): City with highest temperature
        - coldest (dict): City with lowest temperature
        - safe_count (int): Number of cities with safe flow levels
        - total_count (int): Total number of cities compared
    """
    try:
        return await tools.compare_cities(cities)
    except Exception as e:
        logger.error(f"Error comparing cities: {e}", exc_info=True)
        return {
            "error": str(e),
            "cities": [],
            "warmest": None,
            "coldest": None,
            "safe_count": 0,
            "total_count": 0
        }


@mcp.tool(name="get_forecasts")
async def get_forecasts(
    cities: list[str],
) -> dict[str, Any]:
    """⚡ FAST: Get forecasts for multiple cities in parallel (2-5x faster).

    This is the recommended tool for batch forecast operations.
    Fetches all forecasts concurrently.

    **Args:**
        cities: List of city identifiers (e.g., `['Bern', 'Thun']`)

    **Returns:**
        Dictionary mapping city names to forecast data:
        - forecasts (dict): Map of city to forecast data with current temp,
                           2-hour forecast, and trend
    """
    try:
        return await tools.get_forecasts(cities)
    except Exception as e:
        logger.error(f"Error getting forecasts: {e}", exc_info=True)
        return {
            "error": str(e),
            "forecasts": {}
        }


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
