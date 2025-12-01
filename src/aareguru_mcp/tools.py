"""MCP tools for querying Aareguru data.

Tools allow Claude to dynamically query the Aareguru API based on user requests.
"""

import logging
from typing import Any, Optional

from .client import AareguruClient
from .config import get_settings

logger = logging.getLogger(__name__)


async def get_current_temperature(city: str = "bern") -> dict[str, Any]:
    """Get current water temperature for a city.
    
    Use this for quick temperature checks and simple 'how warm is the water?' questions.
    Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'),
    and swimming suitability.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
         
    Returns:
        Dictionary with temperature data and Swiss German descriptions:
        - temperature: Water temperature in Celsius
        - temperature_prec: Temperature precision/decimal places
        - temperature_text: Swiss German description (e.g., "geil aber chli chalt")
        - temperature_text_short: Short Swiss German description
        - name: City short name
        - longname: City full name
         
    Example:
        >>> result = await get_current_temperature("bern")
        >>> print(f"{result['temperature']}°C - {result['temperature_text']}")
        17.2°C - geil aber chli chalt
    """
    logger.info(f"Getting current temperature for {city}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        
        return {
            "city": city,
            "temperature": response.aare,
            "temperature_prec": response.aare_prec,
            "temperature_text": response.text,
            "temperature_text_short": response.text_short,
            "name": response.name,
            "longname": response.longname,
        }


async def get_current_conditions(city: str = "bern") -> dict[str, Any]:
    """Get complete current conditions for a city.
    
    Use this for safety assessments, 'is it safe to swim?' questions, and when users
    need a complete picture before swimming. This is the most detailed tool - use it
    for contextual and safety-critical queries.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
         
    Returns:
        Dictionary with comprehensive swimming conditions:
        - aare: Nested dict with water data (temperature, flow, height, forecast)
        - weather: Current weather conditions (may be None)
        - forecast: Weather forecast data (may be None)
        
    Example:
        >>> result = await get_current_conditions("bern")
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
            result["aare"] = {
                "location": response.aare.location,
                "location_long": response.aare.location_long,
                "temperature": response.aare.temperature,
                "temperature_text": response.aare.temperature_text,
                "temperature_text_short": response.aare.temperature_text_short,
                "flow": response.aare.flow,
                "flow_text": response.aare.flow_text,
                "height": response.aare.height,
                "forecast2h": response.aare.forecast2h,
                "forecast2h_text": response.aare.forecast2h_text,
            }
        
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
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten')
        start: Start date/time. Accepts:
               - ISO format: "2024-11-01T00:00:00Z"
               - Unix timestamp: "1698796800"
               - Relative expressions: "-7 days", "-1 week", "-30 days"
               Relative times are calculated from now.
        end: End date/time. Accepts ISO format, Unix timestamp, or "now" for current time.
             Use "now" for most recent data.
         
    Returns:
        Dictionary with time series data containing hourly measurements
         
    Example:
        >>> # Get last week's data
        >>> result = await get_historical_data("bern", "-7 days", "now")
        >>> print(f"Data points: {len(result['timeseries'])}")
        168  # 7 days × 24 hours
        
        >>> # Get specific date range
        >>> result = await get_historical_data(
        ...     "bern",
        ...     "2024-11-01T00:00:00Z",
        ...     "2024-11-07T23:59:59Z"
        ... )
    """
    logger.info(f"Getting historical data for {city} from {start} to {end}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_history(city, start, end)
        return response


async def list_cities() -> list[dict[str, Any]]:
    """Get all available cities with metadata.
    
    Use this for location discovery ('which cities are available?') and for comparing
    temperatures across all cities to find the warmest/coldest spot.
    
    Returns:
        List of city dictionaries with:
        - city: City identifier (use this for other API calls)
        - name: Short city name
        - longname: Full city name
        - coordinates: Geographic coordinates
        - temperature: Current water temperature (useful for comparisons)
         
    Example:
        >>> cities = await list_cities()
        >>> print([c["city"] for c in cities])
        ['bern', 'thun', 'basel', 'olten', ...]
        
        >>> # Find warmest city
        >>> warmest = max(cities, key=lambda c: c['temperature'] or 0)
        >>> print(f"Warmest: {warmest['name']} at {warmest['temperature']}°C")
    """
    logger.info("Listing all cities")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        
        # Response is already a list
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


async def get_flow_danger_level(city: str = "bern") -> dict[str, Any]:
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
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
         
    Returns:
        Dictionary with flow data and safety assessment:
        - flow: Current flow rate in m³/s
        - flow_text: Human-readable flow description
        - flow_threshold: BAFU danger threshold for this location
        - safety_assessment: Safety recommendation based on current flow
         
    Example:
        >>> result = await get_flow_danger_level("bern")
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
        elif flow < 100:
            safety = "Safe - low flow"
        elif flow < threshold:
            safety = "Moderate - safe for experienced swimmers"
        elif flow < 300:
            safety = "Elevated - caution advised"
        elif flow < 430:
            safety = "High - dangerous conditions"
        else:
            safety = "Very high - extremely dangerous, avoid swimming"
        
        return {
            "city": city,
            "flow": flow,
            "flow_text": response.aare.flow_text,
            "flow_threshold": threshold,
            "safety_assessment": safety,
        }
