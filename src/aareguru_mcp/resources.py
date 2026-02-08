"""MCP resources for Aareguru data.

Resources provide read-only access to Aareguru data that Claude can
proactively read without explicit tool calls.
"""

import json

import structlog

from .client import AareguruClient
from .config import get_settings

logger = structlog.get_logger(__name__)


async def get_cities() -> str:
    """Retrieves the complete list of cities with Aare monitoring stations.

    Returns JSON array containing city identifiers, full names, coordinates,
    and current temperature readings for all monitored locations. Use this
    resource for location discovery and initial data exploration.

    **Returns**:
        JSON string with array of city objects, each containing:
        - city (str): City identifier (e.g., 'Bern', 'Thun')
        - name (str): Display name
        - longname (str): Full location name
        - coordinates (object): Latitude and longitude
        - aare (float): Current water temperature in Celsius
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        return json.dumps([city.model_dump() for city in response], indent=2)


async def get_current(city: str) -> str:
    """Retrieves complete current conditions for a specific city.

    Returns comprehensive real-time data including water temperature, flow rate,
    weather conditions, and forecasts for the specified location.

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun')

    **Returns**:
        JSON string with complete current conditions including temperature,
        flow, weather, and forecast data for the specified city.
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        return response.model_dump_json(indent=2)


async def get_today(city: str) -> str:
    """Retrieves minimal current data snapshot for a specific city.

    Returns a lightweight data structure with essential current information.
    Use this when you only need basic temperature data without full details.

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun')

    **Returns**:
        JSON string with minimal current data including temperature and
        basic location information for the specified city.
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump_json(indent=2)
