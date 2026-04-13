"""App 1: Current conditions dashboard."""

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
    _FLOW_ZONES,
)
from ._helpers import (
    _beaufort,
    _fmt_flow,
    _fmt_pct,
    _fmt_sun,
    _fmt_temp,
    _fmt_wind,
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

    with Column(gap=4, cssClass="p-4 max-w-2xl mx-auto") as view:

        # ── Page header ────────────────────────────────────────────────────
        Text(
            f"Aare — {location}",
            cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] text-center uppercase",
        )

        # ── Safety warning (only if dangerous) ─────────────────────────────
        if warning:
            with Alert(variant="destructive", cssClass=f"{_AG_RADIUS}"):
                AlertTitle("⚠ Sicherheitswarnung")
                AlertDescription(warning)

        # ── Water temperature card (Aare cyan background) ──────────────────
        with Card(cssClass=f"bg-[{_AG_BG_WASSER}] {_AG_RADIUS} overflow-hidden"):
            with CardContent(cssClass="p-8 text-center"):
                # Giant temperature number — matches aare.guru XXL font size
                Text(
                    _fmt_temp(temp),
                    cssClass=f"text-[7rem] font-black leading-none tabular-nums text-[{_AG_WASSER_TEMP}]",
                )
                Text(
                    "Wassertemperatur",
                    cssClass=f"text-xs uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}] mt-1",
                )
                if trend_text:
                    Muted(
                        trend_text,
                        cssClass=f"text-sm text-[{_AG_WASSER_TEMP}] mt-1 font-semibold",
                    )

                # Swiss German phrase with English explanation
                if temp_text:
                    Separator(cssClass=f"my-5 border-[{_AG_WASSER_TEMP}]/30")
                    Text(
                        f"„{temp_text}\u201c",
                        cssClass=f"text-xl italic text-[{_AG_TXT_PRIMARY}] font-semibold",
                    )
                    if explanation:
                        Muted(
                            explanation,
                            cssClass=f"text-sm text-[{_AG_TXT_PRIMARY}]/70 mt-1",
                        )

        # ── Flow rate + BAFU safety (2-column) ─────────────────────────────
        with Grid(columns=2, gap=4):

            # Flow card
            with Card(cssClass=f"{_AG_RADIUS}"):
                with CardContent(cssClass="p-6 text-center"):
                    Text(
                        _fmt_flow(flow),
                        cssClass=f"text-5xl font-black tabular-nums text-[{_AG_WASSER_FLOW}]",
                    )
                    Text(
                        "m³/s",
                        cssClass=f"text-xs uppercase tracking-[0.2em] text-[{_AG_WASSER_FLOW}] mt-1",
                    )
                    Muted(
                        "Wasserstand",
                        cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/60 mt-1",
                    )

            # BAFU safety card — thick teal border matches aare.guru BFU panel
            with Card(cssClass=f"{_AG_RADIUS} border-[5px] border-[{_AG_BFU}]"):
                with CardContent(cssClass="p-6"):
                    # Badge + label centred
                    with Column(cssClass="items-center mb-4"):
                        Badge(
                            label=safety_label,
                            variant=safety_variant,
                            cssClass="text-base px-4 py-1",
                        )
                        Text(
                            "BAFU Sicherheit",
                            cssClass=f"text-xs uppercase tracking-[0.2em] text-[{_AG_BFU}] mt-2",
                        )

                    # ── Flow scale bar ──────────────────────────────────────
                    # Coloured track: 5 segments proportional to zone widths
                    with Row(cssClass="overflow-hidden rounded-full gap-0 h-2"):
                        for lo, hi, _lbl, color, width in _FLOW_ZONES:
                            is_active = (
                                flow is not None
                                and flow >= lo
                                and (hi is None or flow < hi)
                            )
                            Text(
                                " ",
                                cssClass=(
                                    f"block h-3 -mt-0.5 {width} bg-[{color}]"
                                    if is_active
                                    else f"block h-2 {width} bg-[{color}]/35"
                                ),
                            )

                    # Zone labels below the bar
                    with Row(cssClass="gap-0 mt-1"):
                        for lo, hi, lbl, color, width in _FLOW_ZONES:
                            is_active = (
                                flow is not None
                                and flow >= lo
                                and (hi is None or flow < hi)
                            )
                            Text(
                                f"▲ {lbl}" if is_active else lbl,
                                cssClass=(
                                    f"{width} text-center text-[9px] font-bold"
                                    f" text-[{color}]"
                                    if is_active
                                    else f"{width} text-center text-[9px]"
                                    f" text-[{_AG_TXT_PRIMARY}]/40"
                                ),
                            )

        # ── Weather section (--ag-c-bg-wetter mint green) ──────────────────
        weather: dict[str, Any] = data.get("weather") or {}
        forecast_list: list[dict[str, Any]] = data.get("forecast") or []

        if weather:
            Separator(cssClass="my-2")
            Text(
                "Wetter",
                cssClass=f"text-xs uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 text-center",
            )

            # Current weather card — mint green background
            with Card(cssClass=f"bg-[{_AG_BG_WETTER}] {_AG_RADIUS} overflow-hidden"):
                with CardContent(cssClass="p-6"):
                    # Header row: emoji + description
                    sy: int | None = weather.get("sy")
                    syt: str | None = weather.get("syt") or weather.get("symt")
                    with Row(cssClass="items-center gap-3 mb-4"):
                        Text(
                            _sy_to_emoji(sy),
                            cssClass="text-4xl leading-none",
                        )
                        if syt:
                            Text(
                                syt,
                                cssClass=f"text-lg font-semibold text-[{_AG_TXT_PRIMARY}]",
                            )

                    # Metrics grid: air temp / precipitation / wind
                    with Grid(columns=3, gap=3):
                        # Air temperature
                        with Card(cssClass=f"{_AG_RADIUS} bg-white/60"):
                            with CardContent(cssClass="p-3 text-center"):
                                Text(
                                    _fmt_temp(weather.get("tt")),
                                    cssClass=f"text-3xl font-black tabular-nums text-[{_AG_AIR_TEMP}]",
                                )
                                Muted(
                                    "Lufttemp.",
                                    cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_TXT_PRIMARY}]/50",
                                )
                                # Min/max on same card
                                tn = weather.get("tn")
                                tx = weather.get("tx")
                                if tn is not None or tx is not None:
                                    Muted(
                                        f"{_fmt_temp(tn)} / {_fmt_temp(tx)}",
                                        cssClass=f"text-xs text-[{_AG_AIR_TEMP}]/70 mt-1",
                                    )

                        # Precipitation risk
                        with Card(cssClass=f"{_AG_RADIUS} bg-white/60"):
                            with CardContent(cssClass="p-3 text-center"):
                                Text(
                                    _fmt_pct(weather.get("rrisk")),
                                    cssClass=f"text-3xl font-black tabular-nums text-[{_AG_TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Niederschlag",
                                    cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_TXT_PRIMARY}]/50",
                                )
                                rr = weather.get("rr")
                                if rr:
                                    Muted(
                                        f"{rr:.1f} mm",
                                        cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                                    )

                        # Wind speed + Beaufort
                        with Card(cssClass=f"{_AG_RADIUS} bg-white/60"):
                            with CardContent(cssClass="p-3 text-center"):
                                bft_num, bft_label, bft_emoji = _beaufort(
                                    weather.get("v")
                                )
                                Text(
                                    _fmt_wind(weather.get("v")),
                                    cssClass=f"text-2xl font-black tabular-nums text-[{_AG_TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Wind",
                                    cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_TXT_PRIMARY}]/50",
                                )
                                if weather.get("v") is not None:
                                    Muted(
                                        f"{bft_emoji} Bft {bft_num} · {bft_label}",
                                        cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/60 mt-1",
                                    )

            # Forecast row (up to 6 entries)
            if forecast_list:
                with Row(cssClass="gap-2 overflow-x-auto pb-1 mt-1"):
                    for entry in forecast_list[:6]:
                        entry_sy: int | None = entry.get("sy")
                        entry_tt: float | None = entry.get("tt") or entry.get(
                            "temperature"
                        )
                        entry_time: str | None = entry.get("time")
                        # Format timestamp to HH:MM if it's a unix int
                        time_label = "—"
                        if isinstance(entry_time, int):
                            time_label = _dt.fromtimestamp(entry_time).strftime("%H:%M")
                        elif isinstance(entry_time, str) and len(entry_time) >= 16:
                            time_label = entry_time[11:16]

                        with Card(
                            cssClass=f"{_AG_RADIUS} bg-[{_AG_BG_WETTER}]/60 min-w-[64px] flex-shrink-0"
                        ):
                            with CardContent(cssClass="p-2 text-center"):
                                Muted(
                                    time_label,
                                    cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/50",
                                )
                                Text(
                                    _sy_to_emoji(entry_sy),
                                    cssClass="text-xl leading-none my-1",
                                )
                                Text(
                                    _fmt_temp(entry_tt),
                                    cssClass=f"text-sm font-bold text-[{_AG_AIR_TEMP}] tabular-nums",
                                )

        # ── Sun section ────────────────────────────────────────────────────
        sun: dict[str, Any] = data.get("sun") or {}
        if sun:
            Separator(cssClass="my-2")
            Text(
                "Sonne",
                cssClass=f"text-xs uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 text-center",
            )
            with Card(cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_SUNNY}]"):
                with CardContent(cssClass="p-4"):
                    # Top row: sunshine hours + sunset time
                    with Grid(columns=2, gap=3, cssClass="mb-3"):
                        with Card(cssClass=f"{_AG_RADIUS} bg-[{_AG_SUNNY}]/20"):
                            with CardContent(cssClass="p-3 text-center"):
                                Text(
                                    _fmt_sun(sun.get("suntotal")),
                                    cssClass=f"text-2xl font-black tabular-nums text-[{_AG_TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Sonnenschein",
                                    cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_TXT_PRIMARY}]/50",
                                )
                                sun_rel = sun.get("suntotalrelative")
                                if sun_rel is not None:
                                    Muted(
                                        f"{sun_rel:.0f}% des Tages",
                                        cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                                    )
                        with Card(cssClass=f"{_AG_RADIUS} bg-[{_AG_SUNNY}]/20"):
                            with CardContent(cssClass="p-3 text-center"):
                                Text(
                                    sun.get("ss") or "—",
                                    cssClass=f"text-2xl font-black tabular-nums text-[{_AG_TXT_PRIMARY}]",
                                )
                                Muted(
                                    "Sonnenuntergang",
                                    cssClass=f"text-[10px] uppercase tracking-[0.15em] text-[{_AG_TXT_PRIMARY}]/50",
                                )

                    # Nearby sunny locations
                    sun_locs: list[dict[str, Any]] = sun.get("sunlocations") or []
                    if sun_locs:
                        Text(
                            "Sonnige Orte in der Nähe",
                            cssClass=f"text-xs uppercase tracking-[0.15em] text-[{_AG_TXT_PRIMARY}]/50 mb-2",
                        )
                        with Row(cssClass="gap-2 flex-wrap"):
                            for loc in sun_locs[:5]:
                                loc_name: str = loc.get("name") or "—"
                                timeleft: int | None = loc.get("timeleft")
                                label = (
                                    f"☀ {loc_name} · {timeleft}min"
                                    if timeleft is not None
                                    else f"☀ {loc_name}"
                                )
                                Badge(
                                    label=label,
                                    variant="secondary",
                                    cssClass=f"bg-[{_AG_SUNNY}]/30 text-[{_AG_TXT_PRIMARY}] {_AG_RADIUS}",
                                )

        # ── Seasonal advice ─────────────────────────────────────────────────
        seasonal = data.get("seasonal_advice")
        if seasonal:
            Muted(
                seasonal,
                cssClass=f"text-center text-sm text-[{_AG_TXT_PRIMARY}]/60 mt-2",
            )

    return PrefabApp(
        view=view,
        state={"city": city, "aare": aare, "safety": safety_label},
    )
