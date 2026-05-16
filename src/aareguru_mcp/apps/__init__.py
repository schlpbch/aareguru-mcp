"""FastMCP Apps for interactive Aare river data UIs.

Provides eight FastMCPApps that render interactive UIs directly in conversations,
using the aare.guru visual design system.

Apps:
- conditions_app: Dashboard for current water + weather conditions
- history_app:    Area chart for historical temperature and flow trends
- compare_app:    Sortable data table comparing conditions across cities
- forecast_app:   24-hour forecast with air-temperature chart
- intraday_app:   Today's intraday water temperature sparkline
- city_finder_app: All cities ranked by temperature or safety
- safety_app:     BAFU 1-5 danger level briefing
- map_app:        Interactive Leaflet.js map of all monitoring stations
"""

from ..service import AareguruService
from ._helpers import _safety_badge
from ._i18n import t
from .city_finder import city_finder_app, city_finder_view, refresh_cities
from .compare import compare_app, compare_cities_table, fetch_comparison
from .conditions import conditions_app, conditions_dashboard, refresh_conditions
from .conditions_flow import flow_app, flow_card, render_flow_section
from .conditions_sun import render_sun_section, sun_app, sun_card
from .conditions_temperature import (
    render_temperature_section,
    temperature_app,
    temperature_card,
)
from .conditions_weather import render_weather_section, weather_app, weather_card
from .forecast import forecast_app, forecast_view, refresh_forecast
from .history import fetch_history, historical_chart, history_app
from .intraday import intraday_app, intraday_view, refresh_intraday
from .map import aare_map, map_app, refresh_map
from .safety import refresh_safety, safety_app, safety_briefing
from .shop import refresh_shop_cart, shop_app, shop_cart_view

__all__ = [
    # App instances (used by server.py)
    "conditions_app",
    "temperature_app",
    "flow_app",
    "weather_app",
    "sun_app",
    "history_app",
    "compare_app",
    "forecast_app",
    "intraday_app",
    "city_finder_app",
    "safety_app",
    "map_app",
    "shop_app",
    # UI functions (used by tests)
    "conditions_dashboard",
    "temperature_card",
    "flow_card",
    "weather_card",
    "sun_card",
    "historical_chart",
    "compare_cities_table",
    "forecast_view",
    "intraday_view",
    "city_finder_view",
    "safety_briefing",
    "aare_map",
    "shop_cart_view",
    # Render functions (used by conditions_dashboard and tests)
    "render_temperature_section",
    "render_flow_section",
    "render_weather_section",
    "render_sun_section",
    # Tool functions
    "refresh_conditions",
    "fetch_history",
    "fetch_comparison",
    "refresh_forecast",
    "refresh_intraday",
    "refresh_cities",
    "refresh_safety",
    "refresh_map",
    "refresh_shop_cart",
    # Helper (used by tests)
    "_safety_badge",
    # i18n
    "t",
    # Service class (re-exported so patch("aareguru_mcp.apps.AareguruService") works)
    "AareguruService",
]
