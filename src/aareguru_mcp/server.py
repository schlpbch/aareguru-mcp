"""MCP server implementation for Aareguru API using FastMCP.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio or HTTP transport.
"""

import json
from datetime import datetime
from typing import Any

import structlog
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from .client import AareguruClient
from .config import get_settings

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
# Helper Functions
# ============================================================================


def _get_seasonal_advice() -> str:
    """Get contextual advice based on the current season."""
    month = datetime.now().month

    if month in [11, 12, 1, 2, 3]:  # Winter
        return (
            "❄️ Winter Season: Water is freezing. "
            "Only for experienced ice swimmers. Keep swims very short."
        )
    elif month in [4, 5]:  # Spring
        return "🌱 Spring: Water is still very cold from snowmelt. Wetsuit recommended."
    elif month in [6, 7, 8]:  # Summer
        return "☀️ Summer: Perfect swimming season! Don't forget sunscreen."
    else:  # Autumn (9, 10)
        return "🍂 Autumn: Water is getting colder. Check daylight hours and bring warm clothes."


def _check_safety_warning(flow: float | None, threshold: float | None = 220) -> str | None:
    """Generate a warning if flow is dangerous."""
    if flow is None:
        return None

    threshold = threshold or 220

    if flow > 430:
        return "⛔ EXTREME DANGER: Flow is very high (>430 m³/s). Swimming is life-threatening."
    elif flow > 300:
        return "⚠️ DANGER: High flow rate (>300 m³/s). Swimming NOT recommended."
    elif flow > threshold:
        return "⚠️ CAUTION: Elevated flow rate. Only for experienced swimmers."

    return None


def _get_swiss_german_explanation(text: str | None) -> str | None:
    """Provide context for Swiss German phrases."""
    if not text:
        return None

    phrases = {
        "geil aber chli chalt": "Awesome but a bit cold (typical Bernese understatement)",
        "schön warm": "Nice and warm",
        "arschkalt": "Freezing cold",
        "perfekt": "Perfect conditions",
        "chli chalt": "A bit cold",
        "brrr": "Very cold",
    }

    for phrase, explanation in phrases.items():
        if phrase.lower() in text.lower():
            return explanation

    return None


async def _get_suggestion(current_city: str, current_temp: float | None) -> str | None:
    """Suggest a better city if current one is cold."""
    if current_temp is None or current_temp >= 18.0:
        return None

    try:
        async with AareguruClient(settings=get_settings()) as suggestion_client:
            all_cities = await suggestion_client.get_cities()

            warmest = None
            max_temp = -100.0

            for city in all_cities:
                if city.city != current_city and city.aare is not None:
                    if city.aare > max_temp:
                        max_temp = city.aare
                        warmest = city

            if warmest and max_temp > (current_temp + 1.0):
                return f"💡 Tip: {warmest.name} is warmer right now ({warmest.aare}°C)"

    except Exception:
        pass

    return None


def _get_safety_assessment(flow: float | None, threshold: float = 220) -> tuple[str, int]:
    """Get safety assessment and danger level from flow rate."""
    if flow is None:
        return "Unknown - no flow data", 0
    elif flow < 100:
        return "Safe - low flow", 1
    elif flow < threshold:
        return "Moderate - safe for experienced swimmers", 2
    elif flow < 300:
        return "Elevated - caution advised", 3
    elif flow < 430:
        return "High - dangerous conditions", 4
    else:
        return "Very high - extremely dangerous, avoid swimming", 5


# ============================================================================
# Resources
# ============================================================================


@mcp.resource("aareguru://cities")
async def get_cities_resource() -> str:
    """List of all cities with Aare data available."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        return json.dumps([city.model_dump() for city in response], indent=2)


@mcp.resource("aareguru://widget")
async def get_widget_resource() -> str:
    """Current data for all cities at once."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_widget()
        return json.dumps(response, indent=2)


@mcp.resource("aareguru://current/{city}")
async def get_current_resource(city: str) -> str:
    """Complete current conditions for a specific city."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        return response.model_dump_json(indent=2)


@mcp.resource("aareguru://today/{city}")
async def get_today_resource(city: str) -> str:
    """Minimal current data for a specific city."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump_json(indent=2)


# ============================================================================
# Tools
# ============================================================================


@mcp.tool()
async def get_current_temperature(city: str = "bern") -> dict[str, Any]:
    """Get current water temperature for a specific city.

    Use this for quick temperature checks and simple 'how warm is the water?' questions.
    Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'),
    and swimming suitability.

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.

    Returns:
        Dictionary with temperature data and Swiss German descriptions.
    """
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


@mcp.tool()
async def get_current_conditions(city: str = "bern") -> dict[str, Any]:
    """Get comprehensive swimming conditions report including water temperature,
    flow rate, water height, weather conditions, and 2-hour forecast.

    Use this for safety assessments, 'is it safe to swim?' questions, and when users
    need a complete picture before swimming. This is the most detailed tool - use it
    for contextual and safety-critical queries.

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.

    Returns:
        Dictionary with comprehensive swimming conditions.
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


@mcp.tool()
async def get_historical_data(city: str, start: str, end: str) -> dict[str, Any]:
    """Get historical time-series data for trend analysis, comparisons with past
    conditions, and statistical queries.

    Returns hourly data points for temperature and flow. Use this for questions like
    'how has temperature changed this week?' or 'what was the warmest day this month?'

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten')
        start: Start date/time. Accepts ISO format (2024-11-01T00:00:00Z),
               Unix timestamp, or relative expressions like '-7 days', '-1 week'.
        end: End date/time. Accepts ISO format, Unix timestamp, or 'now' for current time.

    Returns:
        Dictionary with time series data containing hourly measurements.
    """
    logger.info(f"Getting historical data for {city} from {start} to {end}")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_history(city, start, end)
        return response


@mcp.tool()
async def list_cities() -> list[dict[str, Any]]:
    """Get all available cities with Aare monitoring stations.

    Returns city identifiers, full names, coordinates, and current temperature
    for each location. Use this for location discovery ('which cities are available?')
    and for comparing temperatures across all cities to find the warmest/coldest spot.

    Returns:
        List of city dictionaries with identifiers, names, coordinates, and temperatures.
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


@mcp.tool()
async def get_flow_danger_level(city: str = "bern") -> dict[str, Any]:
    """Get current flow rate (m³/s) and safety assessment based on BAFU
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
        Dictionary with flow data and safety assessment.
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


@mcp.tool()
async def compare_cities(cities: list[str] | None = None) -> dict[str, Any]:
    """Compare water conditions across multiple cities.

    Use this for comparative questions like 'which city has the warmest water?',
    'compare Bern and Thun', or 'where's the best place to swim today?'.

    Args:
        cities: List of city identifiers to compare (e.g., ['bern', 'thun', 'basel']).
                If not provided, compares all available cities.
                Use list_cities to discover available locations.

    Returns:
        Dictionary with comparison data including warmest, coldest, and safest cities.
    """
    logger.info(f"Comparing cities: {cities or 'all'}")

    async with AareguruClient(settings=get_settings()) as client:
        if cities is None:
            all_cities = await client.get_cities()
            cities = [city.city for city in all_cities]

        city_data = []
        for city in cities:
            try:
                response = await client.get_current(city)

                if response.aare:
                    flow = response.aare.flow
                    threshold = response.aare.flow_scale_threshold or 220

                    if flow is None:
                        safety = "Unknown"
                        danger_level = 0
                    elif flow < 100:
                        safety = "Safe"
                        danger_level = 1
                    elif flow < threshold:
                        safety = "Moderate"
                        danger_level = 2
                    elif flow < 300:
                        safety = "Elevated"
                        danger_level = 3
                    elif flow < 430:
                        safety = "High"
                        danger_level = 4
                    else:
                        safety = "Very High"
                        danger_level = 5

                    city_data.append(
                        {
                            "city": city,
                            "name": response.aare.location,
                            "longname": response.aare.location_long,
                            "temperature": response.aare.temperature,
                            "temperature_text": response.aare.temperature_text,
                            "flow": flow,
                            "flow_text": response.aare.flow_text,
                            "safety": safety,
                            "danger_level": danger_level,
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to get data for {city}: {e}")
                continue

        if not city_data:
            return {
                "cities": [],
                "warmest": None,
                "coldest": None,
                "safest": None,
                "comparison_summary": "No data available for comparison",
            }

        cities_with_temp = [c for c in city_data if c["temperature"] is not None]
        cities_with_flow = [c for c in city_data if c["flow"] is not None]

        warmest = (
            max(cities_with_temp, key=lambda c: c["temperature"]) if cities_with_temp else None
        )
        coldest = (
            min(cities_with_temp, key=lambda c: c["temperature"]) if cities_with_temp else None
        )
        safest = min(cities_with_flow, key=lambda c: c["flow"]) if cities_with_flow else None

        summary_parts = []
        if warmest:
            summary_parts.append(f"Warmest: {warmest['name']} ({warmest['temperature']}°C)")
        if coldest:
            summary_parts.append(f"Coldest: {coldest['name']} ({coldest['temperature']}°C)")
        if safest:
            summary_parts.append(f"Safest: {safest['name']} ({safest['flow']} m³/s)")

        recommendation = None
        if warmest and safest:
            if warmest == safest:
                recommendation = (
                    f"🏆 Best Choice: {warmest['name']} is both the warmest and safest option!"
                )
            elif warmest["danger_level"] <= 2:
                recommendation = (
                    f"🏆 Best Choice: {warmest['name']} is the warmest safe option "
                    f"({warmest['temperature']}°C)."
                )
            else:
                recommendation = (
                    f"⚠️ Trade-off: {warmest['name']} is warmest but has higher flow. "
                    f"{safest['name']} is safer."
                )

        return {
            "cities": city_data,
            "warmest": warmest,
            "coldest": coldest,
            "safest": safest,
            "comparison_summary": (
                " | ".join(summary_parts) if summary_parts else "Comparison complete"
            ),
            "recommendation": recommendation,
            "seasonal_advice": _get_seasonal_advice(),
        }


@mcp.tool()
async def get_forecast(city: str = "bern", hours: int = 2) -> dict[str, Any]:
    """Get temperature and flow forecast for a city.

    Use this for forecast questions like 'will the water be warmer tomorrow?',
    'what's the 2-hour forecast?', or 'when will it be warmest today?'.

    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities to discover available locations.
        hours: Forecast horizon in hours (typically 2). The API provides 2-hour forecasts.

    Returns:
        Dictionary with forecast data including trend analysis and timing recommendations.
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
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": "aareguru-mcp",
            "version": settings.app_version,
        }
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
