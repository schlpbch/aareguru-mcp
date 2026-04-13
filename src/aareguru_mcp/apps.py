"""FastMCP Apps for interactive Aare river data UIs.

Provides three FastMCPApps that render interactive UIs directly in conversations,
using the aare.guru visual design system:

  --ag-c-bg-wasser  : #2be6ff  (Aare cyan — water section background)
  --ag-c-bg-wetter  : #aeffda  (mint green — weather section background)
  --ag-c-wasserTemp : #0877ab  (water temperature text)
  --ag-c-wasserFlow : #357d9e  (flow rate text)
  --ag-c-airTemp    : #0a96d7  (air temperature text)
  --ag-c-bfu        : #00b2aa  (BAFU safety border/accent)
  --ag-c-Sunny      : #f2e500  (sunny weather accent)
  --ag-c-txt-Primary: #0f405f  (primary text, labels)
  border-radius     : 3px      (angular Swiss style)

Apps:
- conditions_app: Dashboard for current water + weather conditions
- history_app:    Area chart for historical temperature and flow trends
- compare_app:    Sortable data table comparing conditions across cities

Each app delegates all data fetching to the existing AareguruService layer.
"""

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
    DataTable,
    DataTableColumn,
    Grid,
    Muted,
    Row,
    Separator,
    Text,
)
from prefab_ui.components.charts import AreaChart, ChartSeries

from .service import AareguruService

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# aare.guru design tokens (light mode)
# ---------------------------------------------------------------------------
_AG_BG_WASSER = "#2be6ff"  # Aare cyan — water card background
_AG_BG_WETTER = "#aeffda"  # mint green — weather card background
_AG_TXT_PRIMARY = "#0f405f"  # dark blue — main labels
_AG_WASSER_TEMP = "#0877ab"  # water temperature values
_AG_WASSER_FLOW = "#357d9e"  # flow rate values
_AG_AIR_TEMP = "#0a96d7"  # air temperature values
_AG_BFU = "#00b2aa"  # BAFU safety accent
_AG_SUNNY = "#f2e500"  # sunny weather accent
_AG_RADIUS = "rounded-[3px]"  # angular Swiss border-radius


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

# (max_flow_exclusive, label, badge_variant, hex_color)
_SAFETY_LEVELS: list[tuple[float, str, str, str]] = [
    (100, "Sicher", "success", "#00b2aa"),
    (220, "Moderat", "info", "#0877ab"),
    (300, "Erhöht", "warning", "#f59e0b"),
    (430, "Hoch", "destructive", "#ef4444"),
]

# Flow scale bar zones — (lo, hi_or_None, label, hex_color, tailwind_width)
# Widths are proportional within a 600 m³/s display cap:
#   100/600=17%, 120/600=20%, 80/600=13%, 130/600=22%, 170/600=28%
_FLOW_ZONES: list[tuple[float, float | None, str, str, str]] = [
    (0, 100, "Sicher", "#00b2aa", "w-[17%]"),
    (100, 220, "Moderat", "#0877ab", "w-[20%]"),
    (220, 300, "Erhöht", "#f59e0b", "w-[13%]"),
    (300, 430, "Hoch", "#ef4444", "w-[22%]"),
    (430, None, "Sehr hoch", "#7f1d1d", "w-[28%]"),
]


def _safety_badge(flow: float | None) -> tuple[str, str, str]:
    """Return (label, variant, hex_color) for a BAFU flow rate."""
    if flow is None:
        return "Unbekannt", "secondary", "#9ca3af"
    for threshold, label, variant, color in _SAFETY_LEVELS:
        if flow < threshold:
            return label, variant, color
    return "Sehr hoch", "destructive", "#7f1d1d"


def _fmt_temp(temp: float | None) -> str:
    return f"{temp:.1f}°" if temp is not None else "—"


def _fmt_flow(flow: float | None) -> str:
    return f"{flow:.0f}" if flow is not None else "—"


def _fmt_pct(val: float | None) -> str:
    return f"{val:.0f}%" if val is not None else "—"


def _fmt_wind(val: float | None) -> str:
    return f"{val:.0f} km/h" if val is not None else "—"


def _fmt_sun(minutes: int | float | None) -> str:
    """Format total sunshine minutes as Xh Ym."""
    if minutes is None:
        return "—"
    m = int(minutes)
    return f"{m // 60}h {m % 60:02d}m" if m >= 60 else f"{m}m"


# Beaufort scale in German (km/h thresholds, exclusive upper bound)
_BEAUFORT: list[tuple[float, int, str, str]] = [
    (1, 0, "Windstille", ""),
    (6, 1, "Leiser Zug", "🌬"),
    (12, 2, "Leichte Brise", "🌬"),
    (20, 3, "Schwache Brise", "🌬"),
    (29, 4, "Mäßige Brise", "💨"),
    (39, 5, "Frische Brise", "💨"),
    (50, 6, "Starker Wind", "💨"),
    (62, 7, "Steifer Wind", "💨"),
    (75, 8, "Stürmischer Wind", "🌪"),
    (89, 9, "Sturm", "🌪"),
    (103, 10, "Schwerer Sturm", "🌪"),
    (118, 11, "Orkanartig", "🌪"),
]


def _beaufort(v: float | None) -> tuple[int, str, str]:
    """Return (beaufort_number, german_label, emoji) for a wind speed in km/h."""
    if v is None:
        return 0, "—", ""
    for threshold, bft, label, emoji in _BEAUFORT:
        if v < threshold:
            return bft, label, emoji
    return 12, "Orkan", "🌪"


# MeteoSwiss sy-code → emoji (codes 1-100, subset of common ones)
_SY_EMOJI: dict[int, str] = {
    1: "☀️",
    2: "🌤",
    3: "⛅",
    4: "🌥",
    5: "☁️",
    6: "🌫",
    7: "🌦",
    8: "🌧",
    9: "🌧",
    10: "🌧",
    11: "⛈",
    12: "⛈",
    13: "⛈",
    14: "🌩",
    15: "🌩",
    16: "🌨",
    17: "❄️",
    18: "🌨",
    19: "🌨",
    20: "🌨",
    26: "🌦",
    27: "🌦",
    28: "🌦",
    29: "🌦",
    30: "🌦",
}


def _sy_to_emoji(sy: int | None) -> str:
    """Map a MeteoSwiss weather symbol code to an emoji."""
    if sy is None:
        return "🌡"
    return _SY_EMOJI.get(sy, "🌡")


# ---------------------------------------------------------------------------
# App 1: Current conditions dashboard
# ---------------------------------------------------------------------------

conditions_app = FastMCPApp("conditions")


@conditions_app.tool()
async def refresh_conditions(city: str) -> dict[str, Any]:
    """Refresh current conditions for a city (called from UI)."""
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


# ---------------------------------------------------------------------------
# App 2: Historical data area chart
# ---------------------------------------------------------------------------

history_app = FastMCPApp("history")


@history_app.tool()
async def fetch_history(city: str, start: str, end: str) -> dict[str, Any]:
    """Fetch historical time-series data (called from UI)."""
    service = AareguruService()
    return await service.get_historical_data(city, start, end)


@history_app.ui()
async def historical_chart(
    city: str = "Bern",
    start: str = "-7 days",
    end: str = "now",
) -> PrefabApp:
    """Show an aare.guru-style area chart of historical Aare temperature and flow.

    Uses the Aare color palette: #0877ab for temperature, #357d9e for flow.

    Args:
        city:  City identifier (e.g. 'Bern', 'Thun', 'olten')
        start: Start of period (e.g. '-7 days', '-1 month', ISO timestamp)
        end:   End of period ('now' or ISO timestamp)
    """
    logger.info("app.historical_chart", city=city, start=start, end=end)
    service = AareguruService()
    raw = await service.get_historical_data(city, start, end)

    # The API returns a list of hourly dicts under various keys
    points: list[dict[str, Any]] = []
    if isinstance(raw, list):
        points = raw
    elif isinstance(raw, dict):
        for key in ("data", "timeseries", "values", "result"):
            if isinstance(raw.get(key), list):
                points = raw[key]
                break

    # Normalise to {time, temperature, flow}
    chart_data: list[dict[str, Any]] = []
    for p in points:
        temp_val = p.get("aare") or p.get("temperature")
        flow_val = p.get("flow")
        time_val = p.get("time") or p.get("timestamp") or p.get("datetime")
        if temp_val is not None and time_val is not None:
            chart_data.append(
                {
                    "time": str(time_val),
                    "temperature": round(float(temp_val), 1),
                    "flow": (
                        round(float(flow_val), 0) if flow_val is not None else None
                    ),
                }
            )

    has_flow = any(p.get("flow") is not None for p in chart_data)
    series = [
        ChartSeries(
            dataKey="temperature", label="Wassertemperatur (°C)", color=_AG_WASSER_TEMP
        ),
    ]
    if has_flow:
        series.append(
            ChartSeries(
                dataKey="flow", label="Wasserstand (m³/s)", color=_AG_WASSER_FLOW
            )
        )

    with Column(gap=4, cssClass="p-4 max-w-3xl mx-auto") as view:

        # Header — matches aare.guru section title style
        with Row(cssClass="justify-between items-end mb-2"):
            Text(
                f"Aare — {city}",
                cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] uppercase",
            )
            Muted(
                f"{start} → {end}",
                cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/50",
            )

        if chart_data:
            # Chart card with subtle Aare cyan border-top
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
            ):
                with CardContent(cssClass="pt-6 pb-4 px-4"):
                    AreaChart(
                        data=chart_data,
                        series=series,
                        xAxis="time",
                        curve="smooth",
                        showLegend=True,
                        height=300,
                    )
            Muted(
                f"{len(chart_data)} Datenpunkte",
                cssClass=f"text-center text-xs text-[{_AG_TXT_PRIMARY}]/50 mt-1",
            )
        else:
            with Alert(variant="warning", cssClass=f"{_AG_RADIUS}"):
                AlertTitle("Keine Daten")
                AlertDescription(
                    "Keine historischen Daten für den gewählten Zeitraum gefunden."
                )

    return PrefabApp(
        view=view,
        state={"city": city, "start": start, "end": end, "points": len(chart_data)},
    )


# ---------------------------------------------------------------------------
# App 3: City comparison table
# ---------------------------------------------------------------------------

compare_app = FastMCPApp("compare")


@compare_app.tool()
async def fetch_comparison(cities: list[str] | None = None) -> dict[str, Any]:
    """Fetch comparison data for cities (called from UI)."""
    service = AareguruService()
    return await service.compare_cities(cities)


@compare_app.ui()
async def compare_cities_table(cities: list[str] | None = None) -> PrefabApp:
    """Show a sortable, searchable table comparing Aare conditions across cities.

    Header summary cards use the aare.guru cyan (#2be6ff) accent.
    Safety column uses BAFU color coding.

    Args:
        cities: City identifiers to compare. If omitted, compares all available cities.
    """
    logger.info("app.compare_cities_table", cities=cities or "all")
    service = AareguruService()
    data = await service.compare_cities(cities)

    city_rows: list[dict[str, Any]] = []
    for c in data.get("cities", []):
        flow = c.get("flow")
        safety_label, _, _ = _safety_badge(flow)
        city_rows.append(
            {
                "Stadt": c.get("location") or c.get("city", "—"),
                "Temp °C": (
                    f"{c['temperature']:.1f}"
                    if c.get("temperature") is not None
                    else "—"
                ),
                "m³/s": _fmt_flow(flow),
                "Sicherheit": safety_label,
                "Beschreibung": c.get("temperature_text") or "—",
            }
        )

    warmest = data.get("warmest") or {}
    safe_count = data.get("safe_count", 0)
    total = data.get("total_count", 0)

    with Column(gap=4, cssClass="p-4 max-w-4xl mx-auto") as view:

        # Header
        Text(
            "Städtevergleich",
            cssClass=f"text-2xl font-black tracking-tight text-[{_AG_TXT_PRIMARY}] uppercase text-center",
        )

        # Summary strip — cyan accent top-border cards
        with Grid(columns=3, gap=3, cssClass="mb-4"):
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
            ):
                with CardContent(cssClass="p-4 text-center"):
                    Text(
                        warmest.get("location") or warmest.get("city") or "—",
                        cssClass=f"text-lg font-black text-[{_AG_WASSER_TEMP}]",
                    )
                    if warmest.get("temperature") is not None:
                        Text(
                            f"{warmest['temperature']:.1f}°",
                            cssClass=f"text-3xl font-black tabular-nums text-[{_AG_WASSER_TEMP}]",
                        )
                    Muted(
                        "WÄRMSTE STADT",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                    )

            with Card(cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BFU}]"):
                with CardContent(cssClass="p-4 text-center"):
                    Text(
                        f"{safe_count} / {total}",
                        cssClass=f"text-3xl font-black tabular-nums text-[{_AG_BFU}]",
                    )
                    Muted(
                        "SICHERE STÄDTE",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                    )
                    Muted(
                        "Durchfluss < 150 m³/s",
                        cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/40",
                    )

            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_WASSER_FLOW}]"
            ):
                with CardContent(cssClass="p-4 text-center"):
                    Text(
                        str(total),
                        cssClass=f"text-3xl font-black tabular-nums text-[{_AG_WASSER_FLOW}]",
                    )
                    Muted(
                        "STÄDTE VERGLICHEN",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 mt-1",
                    )

        # Main comparison table
        with Card(cssClass=f"{_AG_RADIUS}"):
            with CardContent(cssClass="p-0"):
                DataTable(
                    columns=[
                        DataTableColumn(key="Stadt", header="Stadt", sortable=True),
                        DataTableColumn(
                            key="Temp °C",
                            header="Temp °C",
                            sortable=True,
                            align="right",
                        ),
                        DataTableColumn(
                            key="m³/s",
                            header="m³/s",
                            sortable=True,
                            align="right",
                        ),
                        DataTableColumn(
                            key="Sicherheit", header="Sicherheit", sortable=True
                        ),
                        DataTableColumn(key="Beschreibung", header="Beschreibung"),
                    ],
                    rows=city_rows,  # type: ignore[arg-type]
                    search=True,
                    paginated=True,
                    pageSize=15,
                )

    return PrefabApp(
        view=view,
        state={"rows": city_rows, "safe_count": safe_count, "total": total},
    )
