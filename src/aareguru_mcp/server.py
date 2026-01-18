"""MCP server implementation for Aareguru API using FastMCP.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio or HTTP transport.
"""

import json
from typing import Any

import structlog
from fastmcp import FastMCP
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from .client import AareguruClient
from .config import get_settings
from .helpers import (
    _check_safety_warning,
    _get_safety_assessment,
    _get_seasonal_advice,
    _get_suggestion,
    _get_swiss_german_explanation,
)
from .metrics import MetricsCollector
from .rate_limit import limiter, rate_limit_exceeded_handler

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
        - city (str): City identifier (e.g., 'bern', 'thun')
        - name (str): Display name
        - longname (str): Full location name
        - coordinates (object): Latitude and longitude
        - aare (float): Current water temperature in Celsius
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        return json.dumps([city.model_dump() for city in response], indent=2)


@mcp.resource("aareguru://current/{city}")
async def get_current_resource(city: str) -> str:
    """Retrieves complete current conditions for a specific city.
    
    Returns comprehensive real-time data including water temperature, flow rate,
    weather conditions, and forecasts for the specified location.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel')
    
    Returns:
        JSON string with complete current conditions including temperature,
        flow, weather, and forecast data for the specified city.
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        return response.model_dump_json(indent=2)


@mcp.resource("aareguru://today/{city}")
async def get_today_resource(city: str) -> str:
    """Retrieves minimal current data snapshot for a specific city.
    
    Returns a lightweight data structure with essential current information.
    Use this when you only need basic temperature data without full details.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel')
    
    Returns:
        JSON string with minimal current data including temperature and
        basic location information for the specified city.
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump_json(indent=2)


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt(name="daily-swimming-report")
async def daily_swimming_report(city: str = "bern") -> str:
    """Generates a comprehensive daily swimming report for a specific city.

    Creates a detailed report combining current conditions, safety assessment,
    weather, and personalized recommendations for a specific city.

    Args:
        city: City to generate the report for (default: bern)
    
    Returns:
        Prompt template string instructing the LLM to create a formatted report
        with current conditions, safety assessment, forecast, and recommendations.
        The report includes Swiss German descriptions and safety warnings.
    """
    return f"""Please provide a comprehensive daily swimming report for {city}.

Include:
1. **Current Conditions**: Use get_current_conditions to get temperature, flow rate, and weather
2. **Safety Assessment**: Use get_flow_danger_level to assess if swimming is safe
3. **Forecast**: Use get_forecast to see how conditions will change in the next few hours
4. **Recommendation**: Based on all data, give a clear swimming recommendation

Format the report in a friendly way with emojis. Include the Swiss German description if available.
If conditions are dangerous, make this very clear at the top of the report.
If there's a better location nearby, suggest it."""


@mcp.prompt(name="compare-swimming-spots")
async def compare_swimming_spots() -> str:
    """Generates a comparison of all available swimming locations.

    Creates a formatted comparison of all monitored cities to help users
    choose the best swimming spot.

    Returns:
        Prompt template string instructing the LLM to compare all cities,
        rank them by temperature and safety, and provide a recommendation
        for the best swimming location today.
    """
    return """Please compare all available Aare swimming locations.

Use the list_cities tool to get data for all cities, then use get_current_conditions
to get detailed information for each city to present:

1. **🏆 Best Choice Today**: The recommended city based on temperature and safety
2. **📊 Comparison Table**: All cities ranked by temperature with safety status
3. **⚠️ Safety Notes**: Any locations to avoid due to high flow

Format as a clear, scannable report. Use emojis for quick visual reference:
- 🟢 Safe (flow < 150 m³/s)
- 🟡 Caution (150-220 m³/s)
- 🔴 Dangerous (> 220 m³/s)

End with a personalized recommendation based on conditions."""


@mcp.prompt(name="weekly-trend-analysis")
async def weekly_trend_analysis(city: str = "bern") -> str:
    """Generates a weekly trend analysis for temperature and flow patterns.

    Creates a trend analysis to help users understand how conditions
    have been changing and what to expect.

    Args:
        city: City to analyze (default: bern)
    
    Returns:
        Prompt template string instructing the LLM to analyze historical data,
        identify temperature and flow trends, and provide outlook recommendations
        for optimal swimming times.
    """
    return f"""Please analyze the weekly trends for {city}.

Use get_historical_data with days=7 to get the past week's data, then provide:

1. **📈 Temperature Trend**: How has water temperature changed?
   - Highest and lowest temperatures
   - Current vs. weekly average
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
async def get_current_temperature(city: str = "bern") -> dict[str, Any]:
    """Retrieves current water temperature for a specific city.

    Use this for quick temperature checks and simple 'how warm is the water?' questions.
    Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'),
    and swimming suitability.

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.

    Returns:
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
        logger.info(f"Getting current temperature for {city}")

        async with AareguruClient(settings=get_settings()) as client:
            response = await client.get_current(city)

            if not response.aare:
                response = await client.get_today(city)
                temp = response.aare
                text = response.text
                flow = None
            else:
                temp = response.aare.temperature
                text = response.aare.temperature_text
                flow = response.aare.flow

            warning = _check_safety_warning(flow)
            explanation = _get_swiss_german_explanation(text)
            suggestion = await _get_suggestion(city, temp)
            season_advice = _get_seasonal_advice()

            result = {
                "city": city,
                "temperature": temp,
                "temperature_text": text,
                "swiss_german_explanation": explanation,
                "name": (
                    response.aare.location
                    if (response.aare and hasattr(response.aare, "location"))
                    else response.name
                ),
                "warning": warning,
                "suggestion": suggestion,
                "seasonal_advice": season_advice,
            }

            if response.aare and hasattr(response.aare, "temperature"):
                result["temperature_prec"] = response.aare.temperature
                result["temperature_text_short"] = response.aare.temperature_text_short
                result["longname"] = response.aare.location_long
            else:
                result["temperature_prec"] = response.aare_prec
                result["temperature_text_short"] = response.text_short
                result["longname"] = response.longname

            return result


@mcp.tool(name="get_current_conditions")
async def get_current_conditions(city: str = "bern") -> dict[str, Any]:
    """Retrieves comprehensive swimming conditions report including water temperature,
    flow rate, water height, weather conditions, and 2-hour forecast.

    Use this for safety assessments, 'is it safe to swim?' questions, and when users
    need a complete picture before swimming. This is the most detailed tool - use it
    for contextual and safety-critical queries.

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.

    Returns:
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
    logger.info(f"Getting current conditions for {city}")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)

        result: dict[str, Any] = {"city": city}

        if response.aare:
            warning = _check_safety_warning(response.aare.flow)
            explanation = _get_swiss_german_explanation(response.aare.temperature_text)

            result["aare"] = {
                "location": response.aare.location,
                "location_long": response.aare.location_long,
                "temperature": response.aare.temperature,
                "temperature_text": response.aare.temperature_text,
                "swiss_german_explanation": explanation,
                "temperature_text_short": response.aare.temperature_text_short,
                "flow": response.aare.flow,
                "flow_text": response.aare.flow_text,
                "height": response.aare.height,
                "forecast2h": response.aare.forecast2h,
                "forecast2h_text": response.aare.forecast2h_text,
                "warning": warning,
            }

        result["seasonal_advice"] = _get_seasonal_advice()

        if response.weather:
            result["weather"] = response.weather

        if response.weatherprognosis:
            result["forecast"] = response.weatherprognosis

        return result


@mcp.tool(name="get_historical_data")
async def get_historical_data(city: str, start: str, end: str) -> dict[str, Any]:
    """Retrieves historical time-series data for trend analysis, comparisons with past
    conditions, and statistical queries.

    Returns hourly data points for temperature and flow. Use this for questions like
    'how has temperature changed this week?' or 'what was the warmest day this month?'

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten')
        start: Start date/time. Accepts ISO format (2024-11-01T00:00:00Z),
               Unix timestamp, or relative expressions like '-7 days', '-1 week'.
        end: End date/time. Accepts ISO format, Unix timestamp, or 'now' for current time.

    Returns:
        Dictionary containing:
        - timestamps (list[str]): ISO 8601 timestamps for each data point
        - temperatures (list[float]): Water temperatures in Celsius
        - flows (list[float]): Flow rates in m³/s
        - city (str): City identifier
        - start (str): Start timestamp of data range
        - end (str): End timestamp of data range
    """
    logger.info(f"Getting historical data for {city} from {start} to {end}")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_history(city, start, end)
        return response


@mcp.tool(name="list_cities")
async def list_cities() -> list[dict[str, Any]]:
    """Retrieves all available cities with Aare monitoring stations.

    Returns city identifiers, full names, coordinates, and current temperature
    for each location. Use this for location discovery ('which cities are available?')
    and for comparing temperatures across all cities to find the warmest/coldest spot.

    Returns:
        List of dictionaries, each containing:
        - city (str): City identifier (e.g., 'bern', 'thun')
        - name (str): Display name
        - longname (str): Full location name
        - coordinates (dict): Location coordinates with lat/lon
        - temperature (float): Current water temperature in Celsius
    """
    logger.info("Listing all cities")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()

        return [
            {
                "city": city.city,
                "name": city.name,
                "longname": city.longname,
                "coordinates": city.coordinates,
                "temperature": city.aare,
            }
            for city in response
        ]


@mcp.tool(name="get_flow_danger_level")
async def get_flow_danger_level(city: str = "bern") -> dict[str, Any]:
    """Retrieves current flow rate (m³/s) and safety assessment based on BAFU
    (Swiss Federal Office for the Environment) danger thresholds.

    Returns flow rate, danger level classification, and safety recommendations.
    Use this for safety-critical questions about current strength and danger.

    Flow thresholds:
    - <100: safe
    - 100-220: moderate
    - 220-300: elevated
    - 300-430: high/dangerous
    - >430: very high/extremely dangerous

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.

    Returns:
        Dictionary containing:
        - city (str): City identifier
        - flow (float | None): Current flow rate in m³/s
        - flow_text (str | None): Flow description
        - flow_threshold (float): Danger threshold for this location
        - safety_assessment (str): Safety evaluation (e.g., 'Safe', 'Dangerous')
        - danger_level (int): Numeric danger level (1-5, higher is more dangerous)
    """
    logger.info(f"Getting flow danger level for {city}")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)

        if not response.aare:
            return {
                "city": city,
                "flow": None,
                "flow_text": None,
                "safety_assessment": "No data available",
            }

        flow = response.aare.flow
        threshold = response.aare.flow_scale_threshold or 220

        safety, danger_level = _get_safety_assessment(flow, threshold)

        return {
            "city": city,
            "flow": flow,
            "flow_text": response.aare.flow_text,
            "flow_threshold": threshold,
            "safety_assessment": safety,
            "danger_level": danger_level,
        }


@mcp.tool(name="get_forecast")
async def get_forecast(city: str = "bern", hours: int = 2) -> dict[str, Any]:
    """Retrieves temperature and flow forecast for a city.

    Use this for forecast questions like 'will the water be warmer tomorrow?',
    'what's the 2-hour forecast?', or 'when will it be warmest today?'.

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.
        hours: Forecast horizon in hours (typically 2). The API provides 2-hour forecasts.

    Returns:
        Dictionary containing:
        - city (str): City identifier
        - current (dict): Current conditions with temperature, text, and flow
        - forecast_2h (float | None): Forecasted temperature in 2 hours
        - forecast_text (str): Forecast description
        - trend (str): Temperature trend ('rising', 'falling', 'stable', 'unknown')
        - temperature_change (float | None): Expected temperature change in degrees
        - recommendation (str): Timing recommendation for swimming
        - seasonal_advice (str): Season-specific guidance
    """
    logger.info(f"Getting forecast for {city} ({hours}h)")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)

        if not response.aare:
            return {
                "city": city,
                "current": None,
                "forecast_2h": None,
                "forecast_text": "No data available",
                "trend": "unknown",
                "recommendation": "Unable to provide forecast - no data available",
            }

        current_temp = response.aare.temperature
        forecast_temp = response.aare.forecast2h
        forecast_text = response.aare.forecast2h_text

        if forecast_temp is None or current_temp is None:
            trend = "unknown"
            recommendation = "Forecast data not available"
        else:
            temp_diff = forecast_temp - current_temp

            if abs(temp_diff) < 0.3:
                trend = "stable"
                recommendation = "Temperature will remain stable - good time to swim anytime"
            elif temp_diff > 0:
                trend = "rising"
                recommendation = (
                    f"Temperature rising by {temp_diff:.1f}°C - water will be warmer in 2 hours"
                )
            else:
                trend = "falling"
                recommendation = (
                    f"Temperature falling by {abs(temp_diff):.1f}°C - "
                    "swim sooner rather than later"
                )

        return {
            "city": city,
            "current": {
                "temperature": current_temp,
                "temperature_text": response.aare.temperature_text,
                "flow": response.aare.flow,
            },
            "forecast_2h": forecast_temp,
            "forecast_text": forecast_text,
            "trend": trend,
            "temperature_change": (
                forecast_temp - current_temp if (forecast_temp and current_temp) else None
            ),
            "recommendation": recommendation,
            "seasonal_advice": _get_seasonal_advice(),
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
            "service": "aareguru-mcp",
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
