"""MCP tools for querying Aareguru data.

Tools allow Claude to dynamically query the Aareguru API based on user requests.

This module provides thin MCP tool wrappers that delegate to AareguruService
for all business logic. Tools focus on MCP protocol requirements (docstrings,
type hints, parameter formatting) while the service handles data enrichment,
client lifecycle, and error handling.
"""

from typing import Any

import structlog

from .service import AareguruService

logger = structlog.get_logger(__name__)


async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature for a city.

    Use this for quick temperature checks and simple 'how warm is the water?' questions.
    Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'),
    and swimming suitability.

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun', 'olten').
              Use `list_cities()` to discover available locations.

    **Returns**:
        Dictionary with temperature data and Swiss German descriptions:
        - temperature: Water temperature in Celsius
        - temperature_prec: Temperature precision/decimal places
        - temperature_text: Swiss German description (e.g., "geil aber chli chalt")
        - temperature_text_short: Short Swiss German description
        - name: City short name
        - longname: City full name

    **Example**:
        >>> result = await get_current_temperature("Bern")
        >>> print(f"{result['temperature']}°C - {result['temperature_text']}")
        17.2°C - geil aber chli chalt
    """
    logger.info(f"Tool: get_current_temperature for {city}")
    try:
        service = AareguruService()
        return await service.get_current_temperature(city)
    except Exception as e:
        logger.error(f"Tool error: get_current_temperature for {city}", error=str(e))
        return {"error": str(e), "city": city}


async def get_current_conditions(city: str = "Bern") -> dict[str, Any]:
    """Get complete current conditions for a city.

    Use this for safety assessments, 'is it safe to swim?' questions, and when users
    need a complete picture before swimming. This is the most detailed tool - use it
    for contextual and safety-critical queries.

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun', 'olten').
              Use `list_cities()` to discover available locations.

    **Returns**:
        Dictionary with comprehensive swimming conditions:
        - aare: Nested dict with water data (temperature, flow, height, forecast)
        - weather: Current weather conditions (may be None)
        - forecast: Weather forecast data (may be None)

    **Example**:
        >>> result = await get_current_conditions("Bern")
        >>> print(f"Temp: {result['aare']['temperature']}°C")
        >>> print(f"Flow: {result['aare']['flow']} m³/s")
        >>> print(f"2h forecast: {result['aare']['forecast2h_text']}")
    """
    logger.info(f"Tool: get_current_conditions for {city}")
    try:
        service = AareguruService()
        return await service.get_current_conditions(city)
    except Exception as e:
        logger.error(f"Tool error: get_current_conditions for {city}", error=str(e))
        return {"error": str(e), "city": city}


async def get_historical_data(
    city: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Get historical time-series data.

    Use this for trend analysis, comparisons with past conditions, and statistical queries.
    Returns hourly data points for temperature and flow.

    **Args*:
        city: City identifier (e.g., 'Bern', 'Thun', 'olten')
        start: Start date/time. Accepts:
               - ISO format: "2024-11-01T00:00:00Z"
               - Unix timestamp: "1698796800"
               - Relative expressions: "-7 days", "-1 week", "-30 days"
               Relative times are calculated from now.
        end: End date/time. Accepts ISO format, Unix timestamp, or "now" for current time.
             Use "now" for most recent data.

    *Returns*:
        Dictionary with time series data containing hourly measurements

    **Example**:
        >>> # Get last week's data
        >>> result = await get_historical_data("Bern", "-7 days", "now")
        >>> print(f"Data points: {len(result['timeseries'])}")
        168  # 7 days × 24 hours

        >>> # Get specific date range
        >>> result = await get_historical_data(
        ...     "Bern",
        ...     "2024-11-01T00:00:00Z",
        ...     "2024-11-07T23:59:59Z"
        ... )
    """
    logger.info(f"Tool: get_historical_data for {city} from {start} to {end}")
    try:
        service = AareguruService()
        return await service.get_historical_data(city, start, end)
    except Exception as e:
        logger.error(f"Tool error: get_historical_data for {city}", error=str(e))
        return {"error": str(e), "city": city}


async def compare_cities(
    cities: list[str] | None = None,
) -> dict[str, Any]:
    """Compare multiple cities

    This is the recommended tool for comparing one to many cities.

    **Args:**
        cities: List of city identifiers (e.g., `['Bern', 'Thun']`).
                If None, compares all available cities.

    **Returns**:
        Dictionary with:
        - cities: List of city data with temperature, flow, safety
        - warmest: City with highest temperature
        - coldest: City with lowest temperature
        - safe_count: Number of cities with safe flow conditions
        - total_count: Total cities compared
    """
    logger.info(f"Tool: compare_cities for {cities or 'all cities'}")
    try:
        service = AareguruService()
        return await service.compare_cities(cities)
    except Exception as e:
        logger.error(f"Tool error: compare_cities", error=str(e))
        return {"error": str(e)}


async def get_flow_danger_level(city: str = "Bern") -> dict[str, Any]:
    """Get current flow rate and BAFU danger assessment.

    Use this for safety-critical questions about current strength and swimming danger.
    Returns flow rate in m³/s and safety assessment based on BAFU (Swiss Federal Office
    for the Environment) danger thresholds.

    Flow Safety Thresholds:
    - <100 m³/s: Safe - low flow
    - 100-220 m³/s: Moderate - safe for experienced swimmers
    - 220-300 m³/s: Elevated - caution advised
    - 300-430 m³/s: High - dangerous conditions
    - >430 m³/s: Very high - extremely dangerous, avoid swimming

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun', 'olten').
              Use `list_cities()` to discover available locations.

    **Returns**:
        Dictionary with flow data and safety assessment:
        - flow: Current flow rate in m³/s
        - flow_text: Human-readable flow description
        - flow_threshold: BAFU danger threshold for this location
        - safety_assessment: Safety recommendation based on current flow

    **Example**:
        >>> result = await get_flow_danger_level("Bern")
        >>> print(f"Flow: {result['flow']} m³/s")
        >>> print(f"Safety: {result['safety_assessment']}")
        Flow: 245 m³/s
        Safety: Moderate - safe for experienced swimmers
    """
    logger.info(f"Tool: get_flow_danger_level for {city}")
    try:
        service = AareguruService()
        return await service.get_flow_danger_level(city)
    except Exception as e:
        logger.error(f"Tool error: get_flow_danger_level for {city}", error=str(e))
        return {"error": str(e), "city": city}


async def get_forecasts(
    cities: list[str],
) -> dict[str, Any]:
    """Get forecasts for multiple cities.

    Fetches all forecasts concurrently.

    **Args:**
        cities: List of city identifiers (e.g., `['Bern', 'Thun']`)

    **Returns:**
        Dictionary mapping city names to forecast data:
        - forecasts (dict): Map of city to forecast data with current temp,
                           2-hour forecast, and trend
    """
    logger.info(f"Tool: get_forecasts for {len(cities)} cities: {cities}")
    try:
        service = AareguruService()
        return await service.get_forecasts(cities)
    except Exception as e:
        logger.error(f"Tool error: get_forecasts", error=str(e))
        return {"error": str(e)}
