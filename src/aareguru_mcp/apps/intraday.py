"""App 5: Intraday sparkline."""

from datetime import datetime as _dt
from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Card,
    CardContent,
    Column,
    Grid,
    Muted,
    Text,
)
from prefab_ui.components.charts import AreaChart, ChartSeries

from ._constants import (
    _AG_BG_WASSER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_TEMP,
    _DK,
    _FONT_CSS,
)
from ._helpers import _fmt_temp

logger = structlog.get_logger(__name__)

intraday_app = FastMCPApp("intraday")


@intraday_app.tool()
async def refresh_intraday(city: str) -> dict[str, Any]:
    """Refresh intraday readings for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


@intraday_app.ui()
async def intraday_view(city: str = "Bern") -> PrefabApp:
    """Show today's water temperature as an intraday area chart.

    Uses the past readings from the current-conditions response to plot
    how the Aare temperature has evolved throughout the day — no extra
    API call required.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'olten')
    """
    logger.info("app.intraday_view", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    current_temp: float | None = aare.get("temperature")
    location: str = aare.get("location_long") or aare.get("location") or city

    # Normalise aarepast — API returns [{time: int|str, aare: float}, ...]
    raw_past: list[dict[str, Any]] = data.get("aarepast") or []
    points: list[dict[str, Any]] = []
    for entry in raw_past:
        t = entry.get("time")
        v = entry.get("aare") or entry.get("temperature")
        if v is None:
            continue
        if isinstance(t, int):
            label = _dt.fromtimestamp(t).strftime("%H:%M")
        elif isinstance(t, str) and len(t) >= 16:
            label = t[11:16]
        else:
            label = str(t)
        points.append({"Zeit": label, "Temperatur": round(float(v), 1)})

    # Delta: current vs first reading of the day
    delta: float | None = None
    if points and current_temp is not None:
        delta = current_temp - points[0]["Temperatur"]

    with Column(gap=2, cssClass="p-2 max-w-2xl mx-auto") as view:
        Text(
            f"Tagesverlauf — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            " text-center uppercase",
        )

        # Current + delta summary
        with Grid(columns=2, gap=2):
            with Card(cssClass=f"bg-[{_AG_BG_WASSER}] dark:bg-[{_DK.BG_WASSER}] {_AG_RADIUS}"):
                with CardContent(cssClass="p-3 text-center"):
                    Text(
                        _fmt_temp(current_temp),
                        cssClass=f"text-3xl font-black tabular-nums text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                    )
                    Muted(
                        "Aktuell",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )
            with Card(cssClass=f"{_AG_RADIUS}"):
                with CardContent(cssClass="p-3 text-center"):
                    delta_str = (
                        f"+{delta:.1f}°"
                        if delta is not None and delta > 0
                        else (f"{delta:.1f}°" if delta is not None else "—")
                    )
                    Text(
                        delta_str,
                        cssClass=f"text-3xl font-black tabular-nums"
                        f" text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                    )
                    Muted(
                        "Veränderung heute",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

        if points:
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}] dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="pt-3 pb-2 px-3"):
                    AreaChart(
                        data=points,
                        series=[
                            ChartSeries(
                                dataKey="Temperatur",
                                label="Wassertemperatur (°C)",
                                color=_AG_WASSER_TEMP,
                            )
                        ],
                        xAxis="Zeit",
                        curve="smooth",
                        showLegend=False,
                        height=160,
                    )
            Muted(
                f"{len(points)} Messungen heute",
                cssClass=f"text-center text-xs text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
            )
        else:
            with Alert(variant="warning", cssClass=f"{_AG_RADIUS}"):
                AlertTitle("Keine Tagesdaten")
                AlertDescription(
                    "Keine heutigen Messungen verfügbar. Bitte später erneut versuchen."
                )

    return PrefabApp(
        view=view,
        state={
            "city": city,
            "current_temp": current_temp,
            "delta": delta,
            "points": len(points),
        },
        stylesheets=[_FONT_CSS],
    )
