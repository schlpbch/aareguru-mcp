"""Weather section app - displays current weather and forecast."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Card,
    CardContent,
    Column,
    Grid,
    Muted,
    Row,
    Text,
)

from ._constants import (
    _AG_AIR_TEMP,
    _AG_BG_WETTER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _DK,
    _FONT_CSS,
)
from ._helpers import _fmt_pct, _fmt_temp, _sy_to_icon

logger = structlog.get_logger(__name__)

weather_app = FastMCPApp("conditions-weather")


@weather_app.tool()
async def refresh_weather(city: str) -> dict[str, Any]:
    """Refresh weather data for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


def render_weather_section(weather: dict[str, Any]) -> None:
    """Render weather section with current conditions and forecast.

    Must be called inside an active Column/Row context.
    Displays air temperature, precipitation risk, and daily forecast.
    No-op if weather data is empty.
    """
    if not weather:
        return

    weather_current: dict[str, Any] = weather.get("current") or {}
    weather_today_periods: dict[str, Any] = weather.get("today") or {}
    weather_period: dict[str, Any] = (
        weather_today_periods.get("n")
        or weather_today_periods.get("v")
        or weather_today_periods.get("a")
        or {}
    )
    forecast_list: list[dict[str, Any]] = weather.get("forecast") or []

    with Card(
        cssClass=f"bg-[{_AG_BG_WETTER}] dark:bg-[{_DK.BG_WETTER}] {_AG_RADIUS} overflow-hidden"
    ):
        with CardContent(cssClass="p-3"):
            sy: int | None = weather_period.get("symt")
            syt: str | None = weather_period.get("syt")
            with Row(cssClass="items-center gap-2 mb-2"):
                _sy_to_icon(sy, cssClass="w-8 h-8")
                if syt:
                    Text(
                        syt,
                        cssClass=f"text-sm font-semibold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                    )

            with Grid(columns=3, gap=0):
                # Air temp + min/max
                with Card(
                    cssClass=f"{_AG_RADIUS} bg-[{_AG_BG_WETTER}]/60 dark:bg-[{_DK.BG_WETTER}]/80"
                ):
                    with CardContent(cssClass="p-2 text-center"):
                        tn = forecast_list[0].get("tn") if forecast_list else None
                        tx = forecast_list[0].get("tx") if forecast_list else None
                        Text(
                            _fmt_temp(weather_current.get("tt")),
                            cssClass=f"text-xl font-black tabular-nums text-[{_AG_AIR_TEMP}] dark:text-[{_DK.AIR_TEMP}]",
                        )
                        Muted(
                            "Lufttemperatur",
                            cssClass=f"text-[10px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                        )
                        if tn is not None or tx is not None:
                            Muted(
                                f"{_fmt_temp(tn)} / {_fmt_temp(tx)}",
                                cssClass=f"text-[10px] text-[{_AG_AIR_TEMP}]/70 dark:text-[{_DK.AIR_TEMP}]/70",
                            )

                # Precipitation
                with Card(
                    cssClass=f"{_AG_RADIUS} bg-[{_AG_BG_WETTER}]/60 dark:bg-[{_DK.BG_WETTER}]/80"
                ):
                    with CardContent(cssClass="p-2 text-center"):
                        Text(
                            _fmt_pct(weather_period.get("rrisk")),
                            cssClass=f"text-xl font-black tabular-nums text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                        )
                        Muted(
                            "Niederschlag",
                            cssClass=f"text-[10px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                        )
                        rr = weather_period.get("rr")
                        if rr:
                            Muted(
                                f"{rr:.1f} mm",
                                cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                            )

                with Row(cssClass="gap-0 overflow-x-auto"):
                    for entry in forecast_list[:6]:
                        entry_sy: int | None = entry.get("symt")
                        entry_tt: float | None = entry.get("tx") or entry.get("tn")
                        time_label = entry.get("dayshort") or "—"
                        with Card(
                            cssClass=f"{_AG_RADIUS} bg-[{_AG_BG_WETTER}]/60 dark:bg-[{_DK.BG_WETTER}]/50 min-w-[52px] flex-shrink-0"
                        ):
                            with CardContent(cssClass="p-1.5 text-center"):
                                Muted(
                                    time_label,
                                    cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                )
                                _sy_to_icon(entry_sy, cssClass="w-5 h-5 my-0.5")
                                Text(
                                    _fmt_temp(entry_tt),
                                    cssClass=f"text-xs font-bold text-[{_AG_AIR_TEMP}] dark:text-[{_DK.AIR_TEMP}] tabular-nums",
                                )


@weather_app.ui()
async def weather_card(city: str = "Bern") -> PrefabApp:
    """Show an interactive Aare weather card.

    Displays current air temperature, precipitation risk, and a 6-day forecast strip.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'Olten')
    """
    logger.info("app.weather_card", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)
    location: str = (
        (data.get("aare") or {}).get("location_long")
        or (data.get("aare") or {}).get("location")
        or city
    )

    with Column(gap=0, cssClass="p-2 max-w-2xl mx-auto") as view:
        Text(
            f"Aare — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center uppercase",
        )
        render_weather_section(data.get("weather") or {})

    return PrefabApp(
        view=view,
        state={"city": city, "weather": data.get("weather")},
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )
