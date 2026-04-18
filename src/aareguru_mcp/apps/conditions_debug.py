"""Debug app - renders all condition app sections on one page for visual testing."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Grid, Text

from ._constants import _AG_TXT_PRIMARY, _DK, _FONT_CSS
from .conditions_flow import render_flow_section
from .conditions_sun import render_sun_section
from .conditions_temperature import render_temperature_section
from .conditions_weather import render_weather_section

logger = structlog.get_logger(__name__)

debug_app = FastMCPApp("conditions-debug")


@debug_app.ui()
async def conditions_debug_all(city: str = "Bern") -> PrefabApp:
    """Debug view: render all 4 condition app sections together.

    Displays temperature, flow/safety, weather, and sun sections side-by-side
    and stacked for visual debugging and component testing.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'olten')
    """
    logger.info("app.conditions_debug_all", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    location = aare.get("location_long") or aare.get("location") or city

    with Column(gap=0, cssClass="p-4 max-w-7xl mx-auto") as view:
        # Header
        Text(
            f"🔍 Debug: All Condition Apps — {location}",
            cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center mb-4",
        )

        # Row 1: Temperature + Flow side-by-side
        with Grid(columns=2, gap=2):
            # Temperature section
            with Column(
                cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded"
            ):
                Text(
                    "📊 Temperature App",
                    cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
                )
                render_temperature_section(aare)

            # Flow section
            with Column(
                cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded"
            ):
                Text(
                    "💧 Flow & Safety App",
                    cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
                )
                render_flow_section(aare)

        # Row 2: Weather (full width)
        with Column(
            cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded mt-4"
        ):
            Text(
                "🌤️ Weather App",
                cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
            )
            render_weather_section(data.get("weather") or {})

        # Row 3: Sun (full width)
        with Column(
            cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded mt-4"
        ):
            Text(
                "☀️ Sun App",
                cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
            )
            render_sun_section(data.get("sun") or {})

    return PrefabApp(
        view=view,
        state={"city": city, "all_data": data},
        stylesheets=[_FONT_CSS],
    )
