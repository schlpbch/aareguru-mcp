"""MCP tools for querying Aareguru data.

Tools allow Claude to dynamically query the Aareguru API based on user requests.
"""

from typing import Any

import structlog

from .client import AareguruClient
from .config import get_settings
from .helpers import (
    _check_safety_warning,
    _get_seasonal_advice,
    _get_suggestion,
    _get_swiss_german_explanation,
)

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
    logger.info(f"Getting current temperature for {city}")

    async with AareguruClient(settings=get_settings()) as client:
        # Use get_current to get flow data for safety check
        response = await client.get_current(city)

        if not response.aare:
            # Fallback to get_today if no aare data (unlikely but safe)
            response = await client.get_today(city)
            temp = response.aare
            text = response.text
            flow = None
        else:
            temp = response.aare.temperature
            text = response.aare.temperature_text
            flow = response.aare.flow

        # UX Features
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

        # Add legacy fields for backward compatibility
        if response.aare and hasattr(response.aare, "temperature"):
            result["temperature_prec"] = response.aare.temperature  # Approximate
            result["temperature_text_short"] = response.aare.temperature_text_short
            result["longname"] = response.aare.location_long
        else:
            result["temperature_prec"] = response.aare_prec
            result["temperature_text_short"] = response.text_short
            result["longname"] = response.longname

        return result


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
    logger.info(f"Getting current conditions for {city}")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)

        # Build comprehensive response from nested structure
        result: dict[str, Any] = {
            "city": city,
        }

        # Aare data (nested in response.aare)
        if response.aare:
            # UX Features
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

        # Add seasonal advice at top level
        result["seasonal_advice"] = _get_seasonal_advice()

        # Weather data
        if response.weather:
            result["weather"] = response.weather

        # Forecast
        if response.weatherprognosis:
            result["forecast"] = response.weatherprognosis

        return result


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
    logger.info(f"Getting historical data for {city} from {start} to {end}")

    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_history(city, start, end)
        return response


async def compare_cities(
    cities: list[str] | None = None,
) -> dict[str, Any]:
    """Compare multiple cities

    This is the recommended tool for comparing cities.

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
    import asyncio

    async with AareguruClient(settings=get_settings()) as client:
        if cities is None:
            # Get all cities
            all_cities = await client.get_cities()
            cities = [city.city for city in all_cities]

        logger.info(f"Comparing {len(cities)} cities in parallel")

        # Fetch all city conditions concurrently
        async def fetch_conditions(city: str):
            try:
                return await client.get_current(city)
            except Exception as e:
                logger.warning(f"Failed to fetch {city}: {e}")
                return None

        results = await asyncio.gather(*[fetch_conditions(city) for city in cities])

        # Process results
        city_data = []
        for city, result in zip(cities, results):
            if result is None or not result.aare:
                continue

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

        # Determine safety based on flow threshold
        flow = response.aare.flow
        threshold = response.aare.flow_scale_threshold or 220

        if flow is None:
            safety = "Unknown - no flow data"
            danger_level = 0
        elif flow < 100:
            safety = "Safe - low flow"
            danger_level = 1
        elif flow < threshold:
            safety = "Moderate - safe for experienced swimmers"
            danger_level = 2
        elif flow < 300:
            safety = "Elevated - caution advised"
            danger_level = 3
        elif flow < 430:
            safety = "High - dangerous conditions"
            danger_level = 4
        else:
            safety = "Very high - extremely dangerous, avoid swimming"
            danger_level = 5

        return {
            "city": city,
            "flow": flow,
            "flow_text": response.aare.flow_text,
            "flow_threshold": threshold,
            "safety_assessment": safety,
            "danger_level": danger_level,
        }


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
    import asyncio

    async with AareguruClient(settings=get_settings()) as client:

        async def fetch_forecast(city: str):
            try:
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
            except Exception as e:
                logger.warning(f"Failed to fetch forecast for {city}: {e}")
                return None

        results = await asyncio.gather(*[fetch_forecast(city) for city in cities])

        forecasts = {}
        for city, result in zip(cities, results):
            if result is not None:
                forecasts[city] = result

        return {"forecasts": forecasts}
