"""App 4: Forecast view."""

from datetime import datetime as _dt
from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Badge,
    Card,
    CardContent,
    Column,
    Grid,
    Muted,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.charts import AreaChart, ChartSeries

from ._constants import (
    _AG_AIR_TEMP,
    _AG_BG_WASSER,
    _AG_BG_WETTER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _AG_WASSER_TEMP,
)
from ._helpers import _fmt_flow, _fmt_temp, _safety_badge, _sy_to_emoji

logger = structlog.get_logger(__name__)

forecast_app = FastMCPApp("forecast")


@forecast_app.tool()
async def refresh_forecast(city: str) -> dict[str, Any]:
    """Refresh forecast data for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


@forecast_app.ui()
async def forecast_view(city: str = "Bern") -> PrefabApp:
    """Show a 24-hour forecast with air-temperature chart and hourly card strip.

    Displays the 2-hour water temperature trend alongside an hourly weather
    prognosis (MeteoSwiss symbols, air temp, precipitation) for the full day.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'olten')
    """
    logger.info("app.forecast_view", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    temp: float | None = aare.get("temperature")
    flow: float | None = aare.get("flow")
    forecast_2h: float | None = aare.get("forecast2h")
    forecast_2h_text: str | None = aare.get("forecast2h_text")
    warning: str | None = aare.get("warning")
    location: str = aare.get("location_long") or aare.get("location") or city

    safety_label, safety_variant, _ = _safety_badge(flow)

    # Trend arrow + diff text
    trend_arrow = "→"
    trend_diff: str | None = None
    if temp is not None and forecast_2h is not None:
        diff = forecast_2h - temp
        if diff > 0.2:
            trend_arrow = "↑"
            trend_diff = f"+{diff:.1f}°"
        elif diff < -0.2:
            trend_arrow = "↓"
            trend_diff = f"{diff:.1f}°"
        else:
            trend_arrow = "→"
            trend_diff = "stabil"

    forecast_list: list[dict[str, Any]] = data.get("forecast") or []

    # Normalise forecast entries — extract time label once for both chart and strip
    normalised: list[dict[str, Any]] = []
    for entry in forecast_list:
        entry_time = entry.get("time")
        time_label = "—"
        if isinstance(entry_time, int):
            time_label = _dt.fromtimestamp(entry_time).strftime("%H:%M")
        elif isinstance(entry_time, str) and len(entry_time) >= 16:
            time_label = entry_time[11:16]
        normalised.append(
            {
                "time": time_label,
                "sy": entry.get("sy"),
                "tt": entry.get("tt") or entry.get("temperature"),
                "rr": entry.get("rr"),
            }
        )

    # Chart series — air temp + precipitation (drop entries missing air temp)
    chart_data: list[dict[str, Any]] = [
        {
            "Zeit": e["time"],
            "Lufttemp": round(float(e["tt"]), 1),
            "Niederschlag": round(float(e["rr"]), 1) if e["rr"] else 0,
        }
        for e in normalised
        if e["tt"] is not None
    ]

    with Column(gap=4, cssClass="p-4 max-w-2xl mx-auto") as view:

        # ── Header ──────────────────────────────────────────────────────────
        Text(
            f"Vorhersage — {location}",
            cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}]"
            " text-center uppercase",
        )

        # ── Safety warning ───────────────────────────────────────────────────
        if warning:
            with Alert(variant="destructive", cssClass=f"{_AG_RADIUS}"):
                AlertTitle("⚠ Sicherheitswarnung")
                AlertDescription(warning)

        # ── Current → 2h water temperature cards ────────────────────────────
        with Grid(columns=2, gap=4):
            with Card(cssClass=f"bg-[{_AG_BG_WASSER}] {_AG_RADIUS}"):
                with CardContent(cssClass="p-5 text-center"):
                    Text(
                        _fmt_temp(temp),
                        cssClass=f"text-5xl font-black tabular-nums text-[{_AG_WASSER_TEMP}]",
                    )
                    Muted(
                        "Jetzt",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                    )

            with Card(cssClass=f"bg-[{_AG_BG_WASSER}]/50 {_AG_RADIUS}"):
                with CardContent(cssClass="p-5 text-center"):
                    Text(
                        f"{trend_arrow} {_fmt_temp(forecast_2h)}",
                        cssClass=f"text-5xl font-black tabular-nums text-[{_AG_WASSER_TEMP}]",
                    )
                    Muted(
                        "in 2 Stunden",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                    )
                    if trend_diff:
                        Muted(
                            trend_diff,
                            cssClass=f"text-sm font-semibold text-[{_AG_WASSER_TEMP}] mt-1",
                        )
                    if forecast_2h_text:
                        Muted(
                            forecast_2h_text,
                            cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                        )

        # Safety + flow row
        with Row(cssClass="justify-center gap-3 items-center"):
            Badge(
                label=safety_label,
                variant=safety_variant,
                cssClass="text-sm px-3 py-1",
            )
            Muted(
                f"{_fmt_flow(flow)} m³/s",
                cssClass=f"text-sm text-[{_AG_WASSER_FLOW}] font-semibold",
            )

        # ── Air temperature chart ────────────────────────────────────────────
        if chart_data:
            Separator(cssClass="my-1")
            Text(
                "Wettervorhersage",
                cssClass=f"text-xs uppercase tracking-[0.2em]"
                f" text-[{_AG_TXT_PRIMARY}]/50 text-center",
            )
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WETTER}]"
            ):
                with CardContent(cssClass="pt-6 pb-4 px-4"):
                    AreaChart(
                        data=chart_data,
                        series=[
                            ChartSeries(
                                dataKey="Lufttemp",
                                label="Lufttemperatur (°C)",
                                color=_AG_AIR_TEMP,
                            ),
                            ChartSeries(
                                dataKey="Niederschlag",
                                label="Niederschlag (mm)",
                                color=_AG_WASSER_FLOW,
                            ),
                        ],
                        xAxis="Zeit",
                        curve="smooth",
                        showLegend=True,
                        height=200,
                    )

        # ── Hourly card strip ────────────────────────────────────────────────
        if normalised:
            Separator(cssClass="my-1")
            Text(
                "Stündliche Vorhersage",
                cssClass=f"text-xs uppercase tracking-[0.2em]"
                f" text-[{_AG_TXT_PRIMARY}]/50 text-center",
            )
            with Row(cssClass="gap-2 overflow-x-auto pb-2 flex-nowrap"):
                for entry in normalised[:24]:
                    with Card(
                        cssClass=f"{_AG_RADIUS} bg-[{_AG_BG_WETTER}]/50"
                        " min-w-[72px] flex-shrink-0"
                    ):
                        with CardContent(cssClass="p-2 text-center"):
                            Muted(
                                entry["time"],
                                cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/50",
                            )
                            Text(
                                _sy_to_emoji(entry["sy"]),
                                cssClass="text-2xl leading-none my-1",
                            )
                            Text(
                                _fmt_temp(entry["tt"]),
                                cssClass=f"text-sm font-bold tabular-nums"
                                f" text-[{_AG_AIR_TEMP}]",
                            )
                            if entry["rr"]:
                                Muted(
                                    f"{entry['rr']:.1f}mm",
                                    cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/50",
                                )

    return PrefabApp(
        view=view,
        state={
            "city": city,
            "current_temp": temp,
            "forecast_2h": forecast_2h,
            "trend": trend_arrow,
            "hours": len(normalised),
        },
    )
