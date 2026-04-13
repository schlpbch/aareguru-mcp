"""FastMCP Apps for interactive Aare river data UIs.

Provides seven FastMCPApps that render interactive UIs directly in conversations,
using the aare.guru visual design system.

Apps:
- conditions_app: Dashboard for current water + weather conditions
- history_app:    Area chart for historical temperature and flow trends
- compare_app:    Sortable data table comparing conditions across cities
- forecast_app:   24-hour forecast with air-temperature chart
- intraday_app:   Today's intraday water temperature sparkline
- city_finder_app: All cities ranked by temperature or safety
- safety_app:     BAFU 1-5 danger level briefing
"""

from ..service import AareguruService
from ._helpers import _safety_badge
from .city_finder import city_finder_app, city_finder_view, refresh_cities
from .compare import compare_app, compare_cities_table, fetch_comparison
from .conditions import conditions_app, conditions_dashboard, refresh_conditions
from .forecast import forecast_app, forecast_view, refresh_forecast
from .history import fetch_history, historical_chart, history_app
from .intraday import intraday_app, intraday_view, refresh_intraday
from .safety import refresh_safety, safety_app, safety_briefing

__all__ = [
    # App instances (used by server.py)
    "conditions_app",
    "history_app",
    "compare_app",
    "forecast_app",
    "intraday_app",
    "city_finder_app",
    "safety_app",
    # UI functions (used by tests)
    "conditions_dashboard",
    "historical_chart",
    "compare_cities_table",
    "forecast_view",
    "intraday_view",
    "city_finder_view",
    "safety_briefing",
    # Tool functions
    "refresh_conditions",
    "fetch_history",
    "fetch_comparison",
    "refresh_forecast",
    "refresh_intraday",
    "refresh_cities",
    "refresh_safety",
    # Helper (used by tests)
    "_safety_badge",
    # Service class (re-exported so patch("aareguru_mcp.apps.AareguruService") works)
    "AareguruService",
]
