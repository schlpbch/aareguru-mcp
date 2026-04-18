#!/usr/bin/env python3
"""Debug script to render all condition apps on one page for visual testing."""

import asyncio

from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Grid, Text

from src.aareguru_mcp.apps import (
    AareguruService,
)
from src.aareguru_mcp.apps._constants import _AG_TXT_PRIMARY, _DK, _FONT_CSS
from src.aareguru_mcp.apps.conditions_flow import render_flow_section
from src.aareguru_mcp.apps.conditions_sun import render_sun_section
from src.aareguru_mcp.apps.conditions_temperature import render_temperature_section
from src.aareguru_mcp.apps.conditions_weather import render_weather_section


async def render_all_apps_debug(city: str = "Bern") -> PrefabApp:
    """Render all 4 apps side-by-side for visual debugging.

    Shows:
    - Temperature card (left)
    - Flow/Safety card (right)
    - Weather section (full width)
    - Sun section (full width)
    """
    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    location = aare.get("location_long") or aare.get("location") or city

    with Column(gap=0, cssClass="p-4 max-w-7xl mx-auto") as view:
        # Header
        Text(
            f"🔍 Debug: All Apps — {location}",
            cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center mb-4",
        )

        # Row 1: Temperature + Flow side-by-side
        with Grid(columns=2, gap=2):
            # Temperature section
            with Column(cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded"):
                Text(
                    "Temperature App",
                    cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
                )
                render_temperature_section(aare)

            # Flow section
            with Column(cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded"):
                Text(
                    "Flow & Safety App",
                    cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
                )
                render_flow_section(aare)

        # Row 2: Weather (full width)
        with Column(cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded mt-4"):
            Text(
                "Weather App",
                cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
            )
            render_weather_section(data.get("weather") or {})

        # Row 3: Sun (full width)
        with Column(cssClass="border border-gray-300 dark:border-gray-700 p-3 rounded mt-4"):
            Text(
                "Sun App",
                cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-2",
            )
            render_sun_section(data.get("sun") or {})

    return PrefabApp(
        view=view,
        state={"city": city, "all_data": data},
        stylesheets=[_FONT_CSS],
    )


if __name__ == "__main__":
    # Test by printing the app structure
    print("Debug All Apps Page created. Use in FastMCP server or test harness.")
    print("\nExample usage:")
    print("  from debug_all_apps import render_all_apps_debug")
    print("  import asyncio")
    print("  app = asyncio.run(render_all_apps_debug('Bern'))")
