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


async def get_forecast(city: str) -> str:
    """Retrieves weather and temperature forecast for a specific city.

    Returns the next-day weather forecast including predicted temperatures,
    weather conditions, and MeteoSwiss symbol codes. Use this to passively
    read forecast data without calling a tool.

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun')

    **Returns**:
        JSON string with forecast entries, each containing:
        - time (str): Forecast time
        - tt (float): Air temperature in Celsius
        - sy (int): MeteoSwiss weather symbol code
        - rr (float): Precipitation in mm
        - fff (float): Wind speed in km/h
    """
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        forecast = response.weatherprognosis or []
        return json.dumps(
            [entry.model_dump() if hasattr(entry, "model_dump") else entry for entry in forecast],
            indent=2,
        )


async def get_history(city: str, start: str, end: str) -> str:
    """Retrieves historical time-series data for a specific city.

    Returns hourly temperature and flow readings for trend analysis,
    comparisons with past conditions, and statistical queries.

    **Args**:
        city: City identifier (e.g., 'Bern', 'Thun')
        start: Start date/time — ISO, Unix timestamp, or relative ('-7 days', '-1 month')
        end: End date/time — ISO, Unix timestamp, or 'now'

    **Returns**:
        JSON string with time-series data containing hourly readings of
        temperature (°C) and flow rate (m³/s).
    """
    async with AareguruClient(settings=get_settings()) as client:
        data = await client.get_history(city, start, end)
        return json.dumps(data, indent=2)


def get_safety_levels() -> str:
    """Returns the official BAFU 1–5 hydrological danger level reference table.

    This is static reference data describing what each danger level means for
    swimmers. Use this to interpret flow_gefahrenstufe values from other resources.

    **Returns**:
        JSON array with 5 entries, each containing:
        - level (int): 1–5 danger level
        - label (str): German label (e.g., 'Keine Gefahr')
        - guidance (str): Swimmer-specific guidance in German
        - description (str): Hydrological description
        - flow_range (str): Approximate flow range this level corresponds to
    """
    levels = [
        {
            "level": 1,
            "label": "Keine Gefahr",
            "guidance": "Normales Schwimmen möglich",
            "description": "Normale Abflussverhältnisse. Keine erhöhte Gefahr.",
            "flow_range": "< 100 m³/s",
        },
        {
            "level": 2,
            "label": "Mässige Gefahr",
            "guidance": "Vorsicht für schwache Schwimmer und Kinder",
            "description": "Leicht erhöhter Abfluss. Ufer teilweise überschwemmt.",
            "flow_range": "100–220 m³/s",
        },
        {
            "level": 3,
            "label": "Erhebliche Gefahr",
            "guidance": "Nur geübte Schwimmer · keine Kinder",
            "description": "Stark erhöhter Abfluss. Überflutungen an Uferbereichen.",
            "flow_range": "220–300 m³/s",
        },
        {
            "level": 4,
            "label": "Grosse Gefahr",
            "guidance": "Schwimmen nicht empfohlen",
            "description": "Sehr hoher Abfluss. Grosse Überschwemmungen möglich.",
            "flow_range": "300–430 m³/s",
        },
        {
            "level": 5,
            "label": "Sehr grosse Gefahr",
            "guidance": "Lebensgefahr — Wasser meiden",
            "description": "Ausserordentlich hoher Abfluss. Lebensgefahr im Wasser.",
            "flow_range": "> 430 m³/s",
        },
    ]
    return json.dumps(levels, indent=2, ensure_ascii=False)


def get_thresholds() -> str:
    """Returns flow rate thresholds and safety zone boundaries used by this server.

    Machine-readable reference for interpreting flow values across all tools
    and resources. Thresholds are based on BAFU hydrological guidelines.

    **Returns**:
        JSON object with threshold definitions:
        - flow_zones: List of flow ranges with safety labels and hex colors
        - safety_thresholds: Key breakpoints in m³/s with plain-text meaning
        - source: Attribution information
    """
    thresholds = {
        "flow_zones": [
            {"lo": 0, "hi": 100, "label": "Sicher", "color": "#00b2aa"},
            {"lo": 100, "hi": 220, "label": "Moderat", "color": "#0877ab"},
            {"lo": 220, "hi": 300, "label": "Erhöht", "color": "#b45309"},
            {"lo": 300, "hi": 430, "label": "Hoch", "color": "#dc2626"},
            {"lo": 430, "hi": None, "label": "Sehr hoch", "color": "#7f1d1d"},
        ],
        "safety_thresholds": {
            "100": "Below this flow rate: safe for all swimmers",
            "220": "Above this: caution, experienced swimmers only",
            "300": "Above this: swimming not recommended",
            "430": "Above this: life-threatening, avoid water entirely",
        },
        "default_elicitation_threshold_days": 90,
        "source": "BAFU (Swiss Federal Office for the Environment) hydrological guidelines",
        "attribution": "Data from aare.guru — non-commercial use only",
    }
    return json.dumps(thresholds, indent=2, ensure_ascii=False)
