"""Shared helper functions for the aare.guru FastMCP Apps."""

from ._constants import _BEAUFORT, _SAFETY_LEVELS, _SY_EMOJI, _WEATHER_ICONS


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


def _beaufort(v: float | None) -> tuple[int, str, str]:
    """Return (beaufort_number, german_label, emoji) for a wind speed in km/h."""
    if v is None:
        return 0, "—", ""
    for threshold, bft, label, emoji in _BEAUFORT:
        if v < threshold:
            return bft, label, emoji
    return 12, "Orkan", "🌪"


def _sy_to_emoji(sy: int | None) -> str:
    """Map a MeteoSwiss weather symbol code to an emoji."""
    if sy is None:
        return "🌡"
    return _SY_EMOJI.get(sy, "🌡")


def _sy_to_icon(sy: int | None, cssClass: str = "leading-none") -> None:
    """Render a MeteoSwiss weather icon (SVG Image) or emoji fallback (Text)."""
    from prefab_ui.components import Image, Text

    if sy is not None and sy in _WEATHER_ICONS:
        Image(src=_WEATHER_ICONS[sy], alt=str(sy), cssClass=cssClass)
    else:
        Text(_sy_to_emoji(sy), cssClass=cssClass)


def _bafu_level(flow: float | None, gefahrenstufe: int | None) -> int:
    """Return BAFU danger level 1–5 from API value or computed from flow."""
    if gefahrenstufe is not None and 1 <= gefahrenstufe <= 5:
        return gefahrenstufe
    if flow is None:
        return 1
    if flow < 100:
        return 1
    if flow < 220:
        return 2
    if flow < 300:
        return 3
    if flow < 430:
        return 4
    return 5


__all__ = [
    "_safety_badge",
    "_fmt_temp",
    "_fmt_flow",
    "_fmt_pct",
    "_fmt_wind",
    "_fmt_sun",
    "_beaufort",
    "_sy_to_emoji",
    "_sy_to_icon",
    "_bafu_level",
]
