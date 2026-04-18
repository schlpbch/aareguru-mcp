"""Current conditions dashboard - composes temperature, flow, weather, and sun sections."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Column,
    Muted,
    Text,
)

from ._constants import _AG_TXT_PRIMARY, _DK, _FONT_CSS, _FONT_INJECTION_ON_MOUNT
from ._helpers import _safety_badge
from .conditions_sun import render_sun_section
from .conditions_temperature import render_temperature_section
from .conditions_weather import render_weather_section

logger = structlog.get_logger(__name__)

conditions_app = FastMCPApp("conditions")


@conditions_app.tool()
async def refresh_conditions(city: str) -> dict[str, Any]:
    """Refresh current conditions for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


@conditions_app.ui()
async def conditions_dashboard(city: str = "Bern") -> PrefabApp:
    """Show an interactive aare.guru-style dashboard of current Aare conditions.

    Displays water temperature in the signature Aare cyan (#2be6ff) card,
    flow rate, BAFU safety level with the characteristic thick teal border,
    Swiss German description, and a danger alert when flow is elevated.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'Olten')
    """
    logger.info("app.conditions_dashboard", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    warning: str | None = aare.get("warning")
    flow: float | None = aare.get("flow")
    location: str = aare.get("location_long") or aare.get("location") or city

    safety_label, safety_variant, safety_color = _safety_badge(flow)

    with Column(gap=0, cssClass="p-2 max-w-2xl mx-auto") as view:
        # Page header
        Text(
            f"Aare — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center uppercase",
        )

        # Safety warning (only if dangerous)
        if warning:
            with Alert(variant="destructive", cssClass="rounded-lg"):
                AlertTitle("⚠ Sicherheitswarnung")
                AlertDescription(warning)

        # Composed sections from standalone apps
        render_temperature_section(aare)
        ## render_flow_section(aare)
        render_weather_section(data.get("weather") or {})
        render_sun_section(data.get("sun") or {})

        # Seasonal advice
        seasonal = data.get("seasonal_advice")
        if seasonal:
            Muted(
                seasonal,
                cssClass=f"text-center text-xs text-[{_AG_TXT_PRIMARY}]/60 dark:text-[{_DK.TXT_PRIMARY}]/60",
            )

    return PrefabApp(
        view=view,
        state={"city": city, "aare": aare, "safety": safety_label},
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )
