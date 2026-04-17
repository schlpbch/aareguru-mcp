"""App 1: Current conditions dashboard."""

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

from ._constants import (
    _AG_AIR_TEMP,
    _AG_BFU,
    _AG_BG_WASSER,
    _AG_BG_WETTER,
    _AG_RADIUS,
    _AG_SUNNY,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _AG_WASSER_TEMP,
    _DK,
    _FLOW_ZONES,
)
from ._helpers import (
    _fmt_flow,
    _fmt_pct,
    _fmt_temp,
    _safety_badge,
    _sy_to_emoji,
)

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
        city: City identifier (e.g. 'Bern', 'Thun', 'olten')
    """
    logger.info("app.conditions_dashboard", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    temp: float | None = aare.get("temperature")
    flow: float | None = aare.get("flow")
    temp_text: str | None = aare.get("temperature_text")
    explanation: str | None = aare.get("swiss_german_explanation")
    warning: str | None = aare.get("warning")
    forecast_2h: float | None = aare.get("forecast2h")
    location: str = aare.get("location_long") or aare.get("location") or city

    safety_label, safety_variant, safety_color = _safety_badge(flow)

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

    with Column(gap=2, cssClass="p-2 max-w-2xl mx-auto") as view:

        # ── Page header ────────────────────────────────────────────────────
        Text(
            f"Aare — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center uppercase",
        )

        # ── Safety warning (only if dangerous) ─────────────────────────────
        if warning:
            with Alert(variant="destructive", cssClass=f"{_AG_RADIUS}"):
                AlertTitle("⚠ Sicherheitswarnung")
                AlertDescription(warning)

        # ── Water temperature card (Aare cyan background) ──────────────────
        with Card(cssClass=f"bg-[{_AG_BG_WASSER}] dark:bg-[{_DK.BG_WASSER}] {_AG_RADIUS} overflow-hidden"):
            with CardContent(cssClass="p-4 text-center"):
                Text(
                    _fmt_temp(temp),
                    cssClass=f"text-5xl font-black leading-none tabular-nums text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                )
                Text(
                    "Wassertemperatur",
                    cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] mt-1",
                )
                if trend_text:
                    Muted(
                        trend_text,
                        cssClass=f"text-xs text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}] mt-0.5 font-semibold",
                    )
                if temp_text:
                    Separator(cssClass=f"my-2 border-[{_AG_WASSER_TEMP}]/30")
                    Text(
                        f"„{temp_text}\u201c",
                        cssClass=f"text-base italic text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] font-semibold",
                    )
                    if explanation:
                        Muted(
                            explanation,
                            cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/70 dark:text-[{_DK.TXT_PRIMARY}]/70 mt-0.5",
                        )

        # ── Flow rate + BAFU safety (2-column) ─────────────────────────────
        with Grid(columns=2, gap=2):

            # Flow card
            with Card(cssClass=f"{_AG_RADIUS}"):
                with CardContent(cssClass="p-3 text-center"):
                    Text(
                        _fmt_flow(flow),
                        cssClass=f"text-3xl font-black tabular-nums text-[{_AG_WASSER_FLOW}] dark:text-[{_DK.WASSER_FLOW}]",
                    )
                    Text(
                        "m³/s · Wasserstand",
                        cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_WASSER_FLOW}] dark:text-[{_DK.WASSER_FLOW}] mt-0.5",
                    )

            # BAFU safety card — thick teal border matches aare.guru BFU panel
            with Card(cssClass=f"{_AG_RADIUS} border-[4px] border-[{_AG_BFU}] dark:border-[{_DK.BFU}]"):
                with CardContent(cssClass="p-3"):
                    with Column(cssClass="items-center mb-2"):
                        Badge(
                            label=safety_label,
                            variant=safety_variant,
                            cssClass="text-sm px-3 py-0.5",
                        )
                        Text(
                            "BAFU Sicherheit",
                            cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_BFU}] dark:text-[{_DK.BFU}] mt-1",
                        )

                    # Flow scale bar
                    with Row(cssClass="overflow-hidden rounded-full gap-0 h-1.5"):
                        for lo, hi, _lbl, color, width in _FLOW_ZONES:
                            is_active = (
                                flow is not None
                                and flow >= lo
                                and (hi is None or flow < hi)
                            )
                            Text(
                                " ",
                                cssClass=(
                                    f"block h-2 -mt-0.5 {width} bg-[{color}]"
                                    if is_active
                                    else f"block h-1.5 {width} bg-[{color}]/35"
                                ),
                            )

                    with Row(cssClass="gap-0 mt-0.5"):
                        for lo, hi, lbl, color, width in _FLOW_ZONES:
                            is_active = (
                                flow is not None
                                and flow >= lo
                                and (hi is None or flow < hi)
                            )
                            Text(
                                f"▲ {lbl}" if is_active else lbl,
                                cssClass=(
                                    f"{width} text-center text-[8px] font-bold text-[{color}]"
                                    if is_active
                                    else f"{width} text-center text-[8px] text-[{_AG_TXT_PRIMARY}]/40 dark:text-[{_DK.TXT_PRIMARY}]/40"
 ),
                            )

        # ── Weather section ─────────────────────────────────────────────────
        # API: weather.current={tt,rr}, weather.today={v,n,a}, weather.forecast=[]
        weather: dict[str, Any] = data.get("weather") or {}
        weather_current: dict[str, Any] = weather.get("current") or {}
        weather_today_periods: dict[str, Any] = weather.get("today") or {}
        weather_period: dict[str, Any] = (
            weather_today_periods.get("n")
            or weather_today_periods.get("v")
            or weather_today_periods.get("a")
            or {}
        )
        forecast_list: list[dict[str, Any]] = weather.get("forecast") or []

        if weather:
            Separator(cssClass="my-0")
            Text(
                "Wetter",
                cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 text-center",
            )

            with Card(cssClass=f"bg-[{_AG_BG_WETTER}] dark:bg-[{_DK.BG_WETTER}] {_AG_RADIUS} overflow-hidden"):
                with CardContent(cssClass="p-3"):
                    sy: int | None = weather_period.get("symt")
                    syt: str | None = weather_period.get("syt")
                    with Row(cssClass="items-center gap-2 mb-2"):
                        Text(_sy_to_emoji(sy), cssClass="text-2xl leading-none")
                        if syt:
                            Text(
                                syt,
                                cssClass=f"text-sm font-semibold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                            )

                    with Grid(columns=2, gap=2):
                        # Air temp + min/max
                        with Card(cssClass=f"{_AG_RADIUS} bg-white/60 dark:bg-[{_DK.CARD_BG}]/80"):
                            with CardContent(cssClass="p-2 text-center"):
                                tn = forecast_list[0].get("tn") if forecast_list else None
                                tx = forecast_list[0].get("tx") if forecast_list else None
                                Text(
                                    _fmt_temp(weather_current.get("tt")),
                                    cssClass=f"text-xl font-black tabular-nums text-[{_AG_AIR_TEMP}] dark:text-[{_DK.AIR_TEMP}]",
                                )
                                Muted(
                                    "Lufttemp.",
                                    cssClass=f"text-[9px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                )
                                if tn is not None or tx is not None:
                                    Muted(
                                        f"{_fmt_temp(tn)} / {_fmt_temp(tx)}",
                                        cssClass=f"text-[9px] text-[{_AG_AIR_TEMP}]/70 dark:text-[{_DK.AIR_TEMP}]/70",
                                    )

                        # Precipitation
                        with Card(cssClass=f"{_AG_RADIUS} bg-white/60 dark:bg-[{_DK.CARD_BG}]/80"):
                            with CardContent(cssClass="p-2 text-center"):
                                Text(
                                    _fmt_pct(weather_period.get("rrisk")),
                                    cssClass=f"text-xl font-black tabular-nums text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Niederschlag",
                                    cssClass=f"text-[9px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                )
                                rr = weather_period.get("rr")
                                if rr:
                                    Muted(
                                        f"{rr:.1f} mm",
                                        cssClass=f"text-[9px] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                    )

            # Daily forecast strip
            if forecast_list:
                with Row(cssClass="gap-1.5 overflow-x-auto pb-0.5"):
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
                                    cssClass=f"text-[9px] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                )
                                Text(_sy_to_emoji(entry_sy), cssClass="text-base leading-none my-0.5")
                                Text(
                                    _fmt_temp(entry_tt),
                                    cssClass=f"text-xs font-bold text-[{_AG_AIR_TEMP}] dark:text-[{_DK.AIR_TEMP}] tabular-nums",
                                )

        # ── Sun section ─────────────────────────────────────────────────────
        # API: sun.today={suntotal:"9:46",sunrelative:72},
        # sun.sunlocations=[{name,sunsetlocal,timeleft,...}]
        sun: dict[str, Any] = data.get("sun") or {}
        sun_today: dict[str, Any] = sun.get("today") or {}
        if sun:
            Separator(cssClass="my-0")
            Text(
                "Sonne",
                cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 text-center",
            )
            suntotal_str: str | None = sun_today.get("suntotal")
            sun_locs: list[dict[str, Any]] = sun.get("sunlocations") or []
            sunset_str: str | None = sun_locs[0].get("sunsetlocal") if sun_locs else None
            sun_rel = sun_today.get("sunrelative")

            with Card(cssClass=f"{_AG_RADIUS} border-t-[3px] border-t-[{_AG_SUNNY}] dark:border-t-[{_DK.SUNNY}]"):
                with CardContent(cssClass="p-3"):
                    with Grid(columns=2, gap=2, cssClass="mb-2"):
                        with Card(cssClass=f"{_AG_RADIUS} bg-[{_AG_SUNNY}]/20 dark:bg-[{_DK.SUNNY}]/10"):
                            with CardContent(cssClass="p-2 text-center"):
                                Text(
                                    suntotal_str or "—",
                                    cssClass=f"text-lg font-black tabular-nums text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Sonnenschein",
                                    cssClass=f"text-[9px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                )
                                if sun_rel is not None:
                                    Muted(
                                        f"{sun_rel:.0f}% des Tages",
                                        cssClass=f"text-[9px] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                    )
                        with Card(cssClass=f"{_AG_RADIUS} bg-[{_AG_SUNNY}]/20 dark:bg-[{_DK.SUNNY}]/10"):
                            with CardContent(cssClass="p-2 text-center"):
                                Text(
                                    sunset_str or "—",
                                    cssClass=f"text-lg font-black tabular-nums text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Sonnenuntergang",
                                    cssClass=f"text-[9px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                                )

                    if sun_locs:
                        with Row(cssClass="gap-1.5 flex-wrap"):
                            for loc in sun_locs[:5]:
                                loc_name: str = loc.get("name") or "—"
                                timeleft: int | None = loc.get("timeleft")
                                timeleft_str = loc.get("timeleftstring") or (
                                    f"{timeleft // 3600}h {(timeleft % 3600) // 60}m"
                                    if timeleft is not None
                                    else None
                                )
                                label = (
                                    f"☀ {loc_name} · {timeleft_str}"
                                    if timeleft_str
                                    else f"☀ {loc_name}"
                                )
                                Badge(
                                    label=label,
                                    variant="secondary",
                                    cssClass=f"bg-[{_AG_SUNNY}]/30 dark:bg-[{_DK.SUNNY}]/15 text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] {_AG_RADIUS} text-xs",
                                )

        # ── Seasonal advice ─────────────────────────────────────────────────
        seasonal = data.get("seasonal_advice")
        if seasonal:
            Muted(
                seasonal,
                cssClass=f"text-center text-xs text-[{_AG_TXT_PRIMARY}]/60 dark:text-[{_DK.TXT_PRIMARY}]/60",
            )

    return PrefabApp(
        view=view,
        state={"city": city, "aare": aare, "safety": safety_label},
    )
