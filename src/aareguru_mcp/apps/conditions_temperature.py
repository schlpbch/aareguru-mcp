"""Temperature card app - displays current Aare water temperature."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import Card, CardContent, Column, Muted, Text

from ._constants import (
    _AG_BG_WASSER,
    _AG_RADIUS,
    _AG_WASSER_TEMP,
    _DK,
    _FONT_CSS,
)
from ._helpers import _fmt_temp

logger = structlog.get_logger(__name__)

temperature_app = FastMCPApp("conditions-temperature")


@temperature_app.tool()
async def refresh_temperature(city: str) -> dict[str, Any]:
    """Refresh temperature data for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


def render_temperature_section(aare: dict[str, Any]) -> None:
    """Render water temperature card section.

    Must be called inside an active Column/Row context.
    Builds the cyan Aare water temperature card with trend and Swiss German explanation.
    """
    temp: float | None = aare.get("temperature")
    forecast_2h: float | None = aare.get("forecast2h")
    temp_text: str | None = aare.get("temperature_text")
    explanation: str | None = aare.get("swiss_german_explanation")

    # Temperature trend vs 2h forecast
    trend_text: str | None = None
    if temp is not None and forecast_2h is not None:
        diff = forecast_2h - temp
        if diff > 0.2:
            trend_text = f"↑ {forecast_2h:.1f}° in 2h"
        elif diff < -0.2:
            trend_text = f"↓ {forecast_2h:.1f}° in 2h"
        else:
            trend_text = f"→ {forecast_2h:.1f}° in 2h"

    with Card(
        cssClass=f"bg-[{_AG_BG_WASSER}] dark:bg-[{_DK.BG_WASSER}] {_AG_RADIUS} overflow-hidden"
    ):
        with CardContent(cssClass="p-4 text-center"):
            Text(
                _fmt_temp(temp),
                cssClass=f"text-6xl font-black leading-none tabular-nums text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
            )
            Text(
                "Wassertemperatur",
                cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}] mt-1 mb-0.5",
            )
            if trend_text:
                Muted(
                    trend_text,
                    cssClass=f"text-xs text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}] mt-0.5 font-semibold",
                )
            if temp_text:
                Text(
                    f"{temp_text}",
                    cssClass=f"text-lg text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}] font-semibold",
                )
                if explanation:
                    Muted(
                        explanation,
                        cssClass=f"text-xs text-[{_AG_WASSER_TEMP}]/70 dark:text-[{_DK.WASSER_TEMP}]/70 mt-0.5",
                    )


@temperature_app.ui()
async def temperature_card(city: str = "Bern") -> PrefabApp:
    """Show an interactive Aare water temperature card.

    Displays the current water temperature in the signature Aare cyan card
    with 2-hour forecast trend and Swiss German description.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'Olten')
    """
    logger.info("app.temperature_card", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)
    aare = data.get("aare") or {}
    location: str = aare.get("location_long") or aare.get("location") or city

    with Column(gap=0, cssClass="p-2 max-w-2xl mx-auto") as view:
        Text(
            f"Aare — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}] text-center uppercase",
        )
        render_temperature_section(aare)

    return PrefabApp(
        view=view,
        state={"city": city, "aare": aare},
        stylesheets=[_FONT_CSS],
    )
