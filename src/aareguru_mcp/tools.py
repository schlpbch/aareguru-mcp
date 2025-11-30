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
            "city": response.city,
            "temperature": response.aare.temperature if response.aare else None,
            "temperature_text": response.aare.temperature_text if response.aare else None,
            "temperature_text_short": response.aare.temperature_text_short if response.aare else None,
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
        
        # Build comprehensive response
        result: dict[str, Any] = {
            "city": response.city,
            "name": response.name,
            "longname": response.longname,
        }
        
        # Aare data
        if response.aare:
            result["aare"] = {
                "temperature": response.aare.temperature,
                "temperature_text": response.aare.temperature_text,
                "temperature_text_short": response.aare.temperature_text_short,
                "flow": response.aare.flow,
                "flow_text": response.aare.flow_text,
                "flow_gefahrenstufe": response.aare.flow_gefahrenstufe,
                "height": response.aare.height,
            }
        
        # Weather data
        if response.weather:
            result["weather"] = {
                "air_temperature": response.weather.tt,
                "min_temperature": response.weather.tn,
                "max_temperature": response.weather.tx,
                "weather_symbol": response.weather.sy,
                "precipitation": response.weather.rr,
                "wind_speed": response.weather.v,
                "cloud_coverage": response.weather.n,
            }
        
        # Forecast
        if response.forecast2h:
            result["forecast_2h"] = {
                "time": response.forecast2h.time,
                "temperature": response.forecast2h.temperature,
                "weather_symbol": response.forecast2h.sy,
            }
        
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
        
        return [
            {
                "city": city.city,
                "name": city.name,
                "longname": city.longname,
                "url": city.url,
            }
            for city in response.cities
        ]


async def get_flow_danger_level(city: str = "bern") -> dict[str, Any]:
    """Get current flow rate and BAFU danger assessment.
    
    Args:
        city: City identifier (default: "bern")
        
    Returns:
        Dictionary with flow rate, danger level, and safety assessment
        
    Example:
        >>> result = await get_flow_danger_level("bern")
        >>> print(result["flow_gefahrenstufe"])
        2  # Moderate danger level
    """
    logger.info(f"Getting flow danger level for {city}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        
        if not response.aare:
            return {
                "city": city,
                "flow": None,
                "flow_gefahrenstufe": None,
                "flow_text": None,
                "safety_assessment": "No data available",
            }
        
        # Determine safety assessment based on danger level
        danger_level = response.aare.flow_gefahrenstufe
        if danger_level is None:
            safety = "Unknown - no danger level data"
        elif danger_level == 1:
            safety = "Safe - low danger level"
        elif danger_level == 2:
            safety = "Moderate - safe for experienced swimmers"
        elif danger_level == 3:
            safety = "Elevated - caution advised"
        elif danger_level == 4:
            safety = "High - dangerous conditions"
        else:  # 5
            safety = "Very high - extremely dangerous, avoid swimming"
        
        return {
            "city": city,
            "flow": response.aare.flow,
            "flow_gefahrenstufe": danger_level,
            "flow_text": response.aare.flow_text,
            "safety_assessment": safety,
        }
