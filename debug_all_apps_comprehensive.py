#!/usr/bin/env python3
"""Comprehensive debug page to render all 12 FastMCP apps for visual testing.

Shows all apps in a grid layout with sections for easy visual comparison.
"""

import asyncio

from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import Column, Grid, Text

from src.aareguru_mcp.apps._constants import _AG_TXT_PRIMARY, _DK, _FONT_CSS

# Import all app UI functions
from src.aareguru_mcp.apps.city_finder import city_finder_view
from src.aareguru_mcp.apps.compare import compare_cities_table
from src.aareguru_mcp.apps.conditions import conditions_dashboard
from src.aareguru_mcp.apps.conditions_flow import flow_card
from src.aareguru_mcp.apps.conditions_sun import sun_card
from src.aareguru_mcp.apps.conditions_temperature import temperature_card
from src.aareguru_mcp.apps.conditions_weather import weather_card
from src.aareguru_mcp.apps.forecast import forecast_view
from src.aareguru_mcp.apps.history import historical_chart
from src.aareguru_mcp.apps.intraday import intraday_view
from src.aareguru_mcp.apps.map import aare_map
from src.aareguru_mcp.apps.safety import safety_briefing

# Create a FastMCPApp instance for the debug app
debug_app = FastMCPApp("debug-all-apps")


def section_header(title: str, description: str = "") -> None:
    """Render a section header with title and optional description."""
    Text(
        title,
        cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mt-8 mb-2",
    )
    if description:
        Text(
            description,
            cssClass=f"text-sm text-gray-600 dark:text-gray-400 mb-4",
        )


def app_container(title: str, component) -> Column:
    """Wrap an app component in a labeled container."""
    with Column(
        cssClass="border-2 border-gray-300 dark:border-gray-700 p-4 rounded-lg bg-white dark:bg-gray-900"
    ) as container:
        Text(
            title,
            cssClass=f"text-lg font-bold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mb-3 border-b pb-2",
        )
        component
    return container


@debug_app.ui()
async def all_apps_debug_view(city: str = "Bern") -> PrefabApp:
    """Render ALL 12 FastMCP apps on one page for comprehensive visual debugging.

    This debug page shows:
    - 1. Conditions Dashboard (main dashboard with all sections)
    - 2. Temperature Card (standalone)
    - 3. Flow & Safety Card (standalone)
    - 4. Weather Card (standalone)
    - 5. Sun/Sunset Card (standalone)
    - 6. Historical Chart (7-day temperature & flow trends)
    - 7. Compare Cities Table (sortable comparison)
    - 8. Forecast View (24-hour air temperature forecast)
    - 9. Intraday View (today's water temperature sparkline)
    - 10. City Finder (all cities ranked by temperature)
    - 11. Safety Briefing (BAFU danger level assessment)
    - 12. Map (interactive Leaflet.js map of all stations)

    Args:
        city: Default city for single-city apps (default: "Bern")
    """
    with Column(
        gap=4, cssClass="p-6 max-w-[1600px] mx-auto bg-gray-50 dark:bg-gray-950"
    ) as view:
        # Main header
        Text(
            "🔍 Debug Dashboard: All 12 FastMCP Apps",
            cssClass=f"text-4xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center mb-2",
        )
        Text(
            f"Visual testing for city: {city}",
            cssClass="text-center text-gray-600 dark:text-gray-400 mb-6",
        )

        # ===== SECTION 1: MAIN DASHBOARD =====
        section_header(
            "Section 1: Complete Dashboard",
            "Main conditions app with temperature, flow, weather, and sun sections",
        )
        with Column(
            cssClass="border-4 border-blue-500 dark:border-blue-400 p-4 rounded-lg bg-blue-50 dark:bg-blue-950"
        ):
            await conditions_dashboard(city)

        # ===== SECTION 2: INDIVIDUAL CONDITION CARDS =====
        section_header(
            "Section 2: Individual Condition Cards",
            "Standalone temperature, flow, weather, and sun cards",
        )
        with Grid(columns=2, gap=4):
            app_container("2a. Temperature Card", await temperature_card(city))
            app_container("2b. Flow & Safety Card", await flow_card(city))
            app_container("2c. Weather Card", await weather_card(city))
            app_container("2d. Sun/Sunset Card", await sun_card(city))

        # ===== SECTION 3: TIME-SERIES APPS =====
        section_header(
            "Section 3: Time-Series Data",
            "Historical trends and intraday sparklines",
        )
        with Grid(columns=2, gap=4):
            app_container(
                "3a. Historical Chart (7 days)",
                await historical_chart(city, start="-7 days", end="now"),
            )
            app_container(
                "3b. Intraday Sparkline (today)",
                await intraday_view(city),
            )

        # ===== SECTION 4: FORECAST =====
        section_header(
            "Section 4: Weather Forecast",
            "24-hour air temperature forecast",
        )
        with Column(
            cssClass="border-2 border-purple-500 dark:border-purple-400 p-4 rounded-lg"
        ):
            await forecast_view([city])

        # ===== SECTION 5: COMPARISON & RANKING =====
        section_header(
            "Section 5: Multi-City Comparison & Ranking",
            "Compare cities side-by-side and find warmest/safest locations",
        )
        with Grid(columns=2, gap=4):
            app_container(
                "5a. Compare Cities Table",
                await compare_cities_table(["Bern", "Thun", "Brienz", "Muri"]),
            )
            app_container(
                "5b. City Finder (Ranked by Temperature)",
                await city_finder_view(sort_by="temperature"),
            )

        # ===== SECTION 6: SAFETY ASSESSMENT =====
        section_header(
            "Section 6: Safety Assessment",
            "BAFU danger level briefing with flow rate analysis",
        )
        with Column(
            cssClass="border-2 border-red-500 dark:border-red-400 p-4 rounded-lg"
        ):
            await safety_briefing(city)

        # ===== SECTION 7: GEOGRAPHIC MAP =====
        section_header(
            "Section 7: Interactive Map",
            "Leaflet.js map showing all monitoring stations",
        )
        with Column(
            cssClass="border-2 border-green-500 dark:border-green-400 p-4 rounded-lg"
        ):
            await aare_map()

        # Footer
        Text(
            "✅ All 12 apps rendered successfully",
            cssClass="text-center text-green-600 dark:text-green-400 font-bold mt-8 text-xl",
        )

    return PrefabApp(
        view=view,
        state={"city": city},
        stylesheets=[_FONT_CSS],
    )


if __name__ == "__main__":
    print("=" * 80)
    print("Debug All Apps - Comprehensive Visual Testing Page")
    print("=" * 80)
    print("\nThis script defines a FastMCP app that renders all 12 apps on one page.")
    print("\nUsage:")
    print("  1. Run as FastMCP server:")
    print("     uv run fastmcp dev debug_all_apps_comprehensive.py")
    print()
    print("  2. Or integrate into your main server:")
    print("     from debug_all_apps_comprehensive import all_apps_debug_view")
    print()
    print("Apps included:")
    print("  ✓ 1. Conditions Dashboard")
    print("  ✓ 2. Temperature Card")
    print("  ✓ 3. Flow & Safety Card")
    print("  ✓ 4. Weather Card")
    print("  ✓ 5. Sun/Sunset Card")
    print("  ✓ 6. Historical Chart")
    print("  ✓ 7. Compare Cities Table")
    print("  ✓ 8. Forecast View")
    print("  ✓ 9. Intraday Sparkline")
    print("  ✓ 10. City Finder")
    print("  ✓ 11. Safety Briefing")
    print("  ✓ 12. Interactive Map")
    print()
