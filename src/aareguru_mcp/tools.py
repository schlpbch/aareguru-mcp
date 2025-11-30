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
    
    Args:
        city: City identifier (default: "bern")
        
    Returns:
        Dictionary with temperature, text, and short text
        
    Example:
        >>> result = await get_current_temperature("bern")
        >>> print(result["temperature"])
        17.2
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
    
    Args:
        city: City identifier (default: "bern")
        
    Returns:
        Dictionary with water data, weather, forecasts, and safety info
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
    
    Args:
        city: City identifier (required)
        start: Start date/time (ISO, timestamp, or relative like "-7 days")
        end: End date/time (ISO, timestamp, or "now")
        
    Returns:
        Dictionary with time series data
        
    Example:
        >>> result = await get_historical_data("bern", "-7 days", "now")
        >>> print(len(result["timeseries"]))
        168  # 7 days of hourly data
    """
    logger.info(f"Getting historical data for {city} from {start} to {end}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_history(city, start, end)
        return response


async def list_cities() -> list[dict[str, Any]]:
    """Get all available cities with metadata.
    
    Returns:
        List of city dictionaries with identifiers and names
        
    Example:
        >>> cities = await list_cities()
        >>> print([c["city"] for c in cities])
        ['bern', 'thun', 'basel', ...]
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
    
    Args:
        city: City identifier (default: "bern")
        
    Returns:
        Dictionary with flow rate, danger level, and safety assessment
        
    Example:
        >>> result = await get_flow_danger_level("bern")
        >>> print(result["flow"])
        65  # m³/s
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
