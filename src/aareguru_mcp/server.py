"""MCP server implementation for Aareguru API using FastMCP.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio or HTTP transport.
"""

import asyncio
import json
from typing import Any

import structlog
from fastmcp import FastMCP
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
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
from .models import (
    AareConditionsData,
    CityListResponse,
    ConditionsToolResponse,
    CurrentConditionsData,
    FlowDangerResponse,
    ForecastToolResponse,
    TemperatureToolResponse,
)
from .rate_limit import limiter

# Get structured logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# ============================================================================
# Singleton HTTP Client for connection pooling
# ============================================================================

_http_client: AareguruClient | None = None
_client_lock = asyncio.Lock()


async def get_http_client() -> AareguruClient:
    """Get or create singleton HTTP client with connection reuse.

    This client is shared across all tool calls to enable:
    - Connection pooling and keep-alive
    - Reduced connection setup overhead
    - Better resource utilization

    **Returns:**
        Singleton AareguruClient instance
    """
    global _http_client

    async with _client_lock:
        if _http_client is None:
            settings_instance = get_settings()
            _http_client = AareguruClient(settings=settings_instance)
            logger.info("Created singleton HTTP client with connection pooling")

        return _http_client


async def close_http_client():
    """Close singleton HTTP client on shutdown."""
    global _http_client

    if _http_client is not None:
        await _http_client.close()
        _http_client = None
        logger.info("Closed singleton HTTP client")


def _reset_http_client():
    """Reset singleton client for testing purposes."""
    global _http_client
    _http_client = None


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
# Parallel Fetch Utilities
# ============================================================================


async def fetch_multiple_cities(
    cities: list[str],
    fetch_func: callable,
    max_concurrency: int = 10,
) -> list[tuple[str, Any]]:
    """Fetch data for multiple cities in parallel with concurrency limit.

    **Args:**
        cities: List of city identifiers
        fetch_func: Async function to call for each city (takes city: str)
        max_concurrency: Maximum concurrent requests (default: 10)

    **Returns:**
        List of tuples: (city, result or exception)
    """
    semaphore = asyncio.Semaphore(max_concurrency)

    async def fetch_with_limit(city: str):
        async with semaphore:
            try:
                result = await fetch_func(city)
                return (city, result)
            except Exception as e:
                logger.warning(f"Failed to fetch {city}: {e}")
                return (city, e)

    tasks = [fetch_with_limit(city) for city in cities]
    results = await asyncio.gather(*tasks)

    return results


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
    client = await get_http_client()
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
    client = await get_http_client()
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
    client = await get_http_client()
    response = await client.get_today(city)
    return response.model_dump_json(indent=2)


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt(name="daily-swimming-report")
async def daily_swimming_report(city: str = "bern", include_forecast: bool = True) -> str:
    """Generates comprehensive daily swimming report combining conditions, safety.

    **Args:**
        city: City to generate the report for (default: `bern`).
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
async def weekly_trend_analysis(city: str = "bern", days: int = 7) -> str:
    """Generates trend analysis showing temperature and flow patterns with outlook.

    **Args:**
        city: City to analyze (default: `bern`). Use `compare_cities` to discover available locations.
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
async def get_current_temperature(city: str = "bern") -> TemperatureToolResponse:
    """Retrieves current water temperature for a single city.

    Takes `city` parameter (optional, default: `bern`).

    Use this for quick temperature checks and simple "how warm is the water?" questions.
    Returns temperature in Celsius, Swiss German description (e.g., `geil aber chli chalt`),
    and swimming suitability.

    **For multiple cities:** Use `compare_cities` instead - it's 8-13x faster.

    **Args:****
        city: City identifier (e.g., `'bern'`, `'thun'`, `'basel'`, `'olten'`).
              Use `compare_cities` to discover available locations.

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
        logger.info(f"Getting current temperature for {city}")

        client = await get_http_client()
        current_response = await client.get_current(city)

        if not current_response.aare:
            today_response = await client.get_today(city)
            temp = today_response.aare
            text = today_response.text
            flow = None
            temp_prec = today_response.aare_prec
            text_short = today_response.text_short
            longname = today_response.longname
            location_name = today_response.name
        else:
            temp = current_response.aare.temperature
            text = current_response.aare.temperature_text
            flow = current_response.aare.flow
            temp_prec = current_response.aare.temperature
            text_short = current_response.aare.temperature_text_short
            longname = current_response.aare.location_long
            location_name = current_response.aare.location

        warning = _check_safety_warning(flow)
        explanation = _get_swiss_german_explanation(text)
        suggestion = await _get_suggestion(city, temp)
        season_advice = _get_seasonal_advice()

        return TemperatureToolResponse(
            city=city,
            temperature=temp,
            temperature_text=text,
            swiss_german_explanation=explanation,
            name=location_name,
            warning=warning,
            suggestion=suggestion,
            seasonal_advice=season_advice,
            temperature_prec=temp_prec,
            temperature_text_short=text_short,
            longname=longname,
        )


@mcp.tool(name="get_current_conditions")
async def get_current_conditions(city: str = "bern") -> ConditionsToolResponse:
    """Retrieves comprehensive swimming conditions for a single city.

    Takes `city` parameter (optional, default: `bern`). Returns water temperature,
    flow rate, water height, weather conditions, and 2-hour forecast.

    Use this for safety assessments, "is it safe to swim?" questions, and when users
    need a complete picture before swimming. This is the most detailed single-city tool.

    **For comparing multiple cities:** Use `compare_cities` instead - it's 8-13x faster.

    **Args:****
        city: City identifier (e.g., `'bern'`, `'thun'`, `'basel'`, `'olten'`).
              Use `compare_cities` to discover available locations.

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
    logger.info(f"Getting current conditions for {city}")

    client = await get_http_client()
    response = await client.get_current(city)

    result: dict[str, Any] = {"city": city}

    if response.aare:
        warning = _check_safety_warning(response.aare.flow)
        explanation = _get_swiss_german_explanation(response.aare.temperature_text)

        result["aare"] = AareConditionsData(
            location=response.aare.location,
            location_long=response.aare.location_long,
            temperature=response.aare.temperature,
            temperature_text=response.aare.temperature_text,
            swiss_german_explanation=explanation,
            temperature_text_short=response.aare.temperature_text_short,
            flow=response.aare.flow,
            flow_text=response.aare.flow_text,
            height=response.aare.height,
            forecast2h=response.aare.forecast2h,
            forecast2h_text=response.aare.forecast2h_text,
            warning=warning,
        )

    result["seasonal_advice"] = _get_seasonal_advice()

    if response.weather:
        result["weather"] = response.weather

    if response.weatherprognosis:
        result["forecast"] = response.weatherprognosis

    return ConditionsToolResponse(**result)


@mcp.tool(name="get_historical_data")
async def get_historical_data(city: str, start: str, end: str) -> dict[str, Any]:
    """Retrieves historical time-series data for trend analysis.

    Takes `city`, `start`, and `end` parameters (all required).
    Returns hourly data points for temperature and flow.

    Use this for questions like "how has temperature changed this week?"
    or "what was the warmest day this month?"

    **Args:**
        city: City identifier (e.g., `'bern'`, `'thun'`, `'basel'`, `'olten'`)
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
    logger.info(f"Getting historical data for {city} from {start} to {end}")

    client = await get_http_client()
    response = await client.get_history(city, start, end)
    return response


@mcp.tool(name="get_flow_danger_level")
async def get_flow_danger_level(city: str = "bern") -> FlowDangerResponse:
    """Retrieves current flow rate and safety assessment.

    Takes `city` parameter (optional, default: `bern`).
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
        city: City identifier (e.g., `'bern'`, `'thun'`, `'basel'`, `'olten'`).
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
    logger.info(f"Getting flow danger level for {city}")

    client = await get_http_client()
    response = await client.get_current(city)

    if not response.aare:
        return FlowDangerResponse(
            city=city,
            flow=None,
            flow_text=None,
            flow_threshold=None,
            safety_assessment="No data available",
            danger_level=None,
        )

    flow = response.aare.flow
    threshold = response.aare.flow_scale_threshold or 220

    safety, danger_level = _get_safety_assessment(flow, threshold)

    return FlowDangerResponse(
        city=city,
        flow=flow,
        flow_text=response.aare.flow_text,
        flow_threshold=threshold,
        safety_assessment=safety,
        danger_level=danger_level,
    )


@mcp.tool(name="compare_cities")
async def compare_cities(
    cities: list[str] | None = None,
) -> dict[str, Any]:
    """⚡ FAST: Compare multiple cities with parallel fetching (8-13x faster).

    This is the recommended tool for comparing cities. Fetches all city data
    concurrently instead of sequentially.

    **Performance:** 10 cities in ~60-100ms vs ~800ms sequential

    **Args:**
        cities: List of city identifiers (e.g., `['bern', 'thun', 'basel']`).
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
    client = await get_http_client()

    # Get city list if not provided
    if cities is None:
        cities_response = await client.get_cities()
        cities = [city.city for city in cities_response]

    logger.info(f"Comparing {len(cities)} cities in parallel")

    # Fetch all city conditions concurrently
    async def fetch_conditions(city: str):
        return await client.get_current(city)

    results = await fetch_multiple_cities(cities, fetch_conditions)

    # Process results
    city_data = []
    for city, result in results:
        if isinstance(result, Exception):
            continue

        if result.aare:
            city_data.append(
                {
                    "city": city,
                    "temperature": result.aare.temperature,
                    "flow": result.aare.flow,
                    "safe": result.aare.flow < 150 if result.aare.flow else True,
                    "temperature_text": result.aare.temperature_text,
                    "location": result.aare.location,
                }
            )

    # Sort by temperature
    city_data.sort(key=lambda x: x["temperature"] or 0, reverse=True)

    return {
        "cities": city_data,
        "warmest": city_data[0] if city_data else None,
        "coldest": city_data[-1] if city_data else None,
        "safe_count": sum(1 for c in city_data if c["safe"]),
        "total_count": len(city_data),
    }


@mcp.tool(name="get_forecasts")
async def get_forecasts(
    cities: list[str],
) -> dict[str, Any]:
    """⚡ FAST: Get forecasts for multiple cities in parallel (2-5x faster).

    This is the recommended tool for batch forecast operations.
    Fetches all forecasts concurrently.

    **Args:**
        cities: List of city identifiers (e.g., `['bern', 'thun', 'basel']`)

    **Returns:**
        Dictionary mapping city names to forecast data:
        - forecasts (dict): Map of city to forecast data with current temp,
                           2-hour forecast, and trend
    """
    client = await get_http_client()

    async def fetch_forecast(city: str):
        response = await client.get_current(city)
        if not response.aare:
            return None

        current = response.aare.temperature
        forecast_2h = response.aare.forecast2h

        if current is None or forecast_2h is None:
            trend = "unknown"
        elif forecast_2h > current:
            trend = "rising"
        elif forecast_2h < current:
            trend = "falling"
        else:
            trend = "stable"

        return {
            "current": current,
            "forecast_2h": forecast_2h,
            "trend": trend,
            "change": forecast_2h - current if (forecast_2h and current) else None,
        }

    results = await fetch_multiple_cities(cities, fetch_forecast)

    forecasts = {}
    for city, result in results:
        if not isinstance(result, Exception) and result is not None:
            forecasts[city] = result

    return {"forecasts": forecasts}


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
