"""Design tokens and lookup tables for the aare.guru visual design system."""

import base64
from pathlib import Path

# ---------------------------------------------------------------------------
# Weather icons — embedded SVGs (base64 data URIs), keyed by MeteoSwiss sy-code
# ---------------------------------------------------------------------------
_WEATHER_ICON_DIR = Path(__file__).parent / "assets" / "img" / "weather"
_WEATHER_ICONS: dict[int, str] = {
    int(f.stem): "data:image/svg+xml;base64,"
    + base64.b64encode(f.read_bytes()).decode()
    for f in _WEATHER_ICON_DIR.glob("*.svg")
    if f.stem.isdigit()
}

# ---------------------------------------------------------------------------
# PT Sans Narrow — Injected via on_mount handler
# ---------------------------------------------------------------------------
_FONT_INJECTION_ON_MOUNT = (
    "if(!document.querySelector('style[data-font]')){"
    "const s=document.createElement('style');"
    "s.setAttribute('data-font','pt-sans-narrow');"
    "s.textContent="
    "'@font-face{font-family:\\\"PT Sans Narrow\\\";font-style:normal;font-weight:400;font-display:swap;src:url(https://fonts.gstatic.com/s/ptsansnarrow/v18/BcBkuQs5l2-g6qmSyCW_ahuMB7Vf7NxXIiUpXyWWuPI.woff2) format(\\\"woff2\\\")}'+"
    "'@font-face{font-family:\\\"PT Sans Narrow\\\";font-style:normal;font-weight:700;font-display:swap;src:url(https://fonts.gstatic.com/s/ptsansnarrow/v18/BcBIuQs5l2-g6qmSyCW_ahuMB7VfnpJuHh-84rqB_tY.woff2) format(\\\"woff2\\\")}'+"
    "'body,*{font-family:\\\"PT Sans Narrow\\\",ui-sans-serif,system-ui,sans-serif !important}';"
    "document.head.appendChild(s)"
    "}"
)

# Background pattern CSS (remains inline)
_BACKGROUND_PATTERN_CSS = (
    # Repeating diagonal stripe pattern — approximates aareguru-pattern-quer-2.svg
    "body{"
    "background-image:repeating-linear-gradient("
    "135deg,"
    "transparent,"
    "transparent 18px,"
    "rgba(15,64,95,0.04) 18px,"
    "rgba(15,64,95,0.04) 19px"
    ");"
    "}"
    "@media(prefers-color-scheme:dark){"
    "body{"
    "background-color:#1c3138 !important;"
    "background-image:repeating-linear-gradient("
    "135deg,"
    "transparent,"
    "transparent 18px,"
    "rgba(136,190,224,0.05) 18px,"
    "rgba(136,190,224,0.05) 19px"
    ");"
    "}}"
)

# Combined CSS for both fonts and background pattern
_FONT_CSS = (
    _BACKGROUND_PATTERN_CSS +
    "body,*{"
    "font-family:'PT Sans Narrow',ui-sans-serif,system-ui,sans-serif !important;"
    "}"
)

# ---------------------------------------------------------------------------
# aare.guru design tokens (light mode)
# ---------------------------------------------------------------------------
_AG_BG_WASSER = "#2be6ff"  # Aare cyan — water card background
_AG_BG_WETTER = "#aeffda"  # mint green — weather card background
_AG_BG_SUNNY = "#fff98e"  # sunny yellow — sun card background
_AG_TXT_PRIMARY = "#0f405f"  # dark blue — main labels
_AG_WASSER_TEMP = "#0877ab"  # water temperature values
_AG_WASSER_FLOW = "#357d9e"  # flow rate values
_AG_AIR_TEMP = "#0a96d7"  # air temperature values
_AG_BFU = "#00b2aa"  # BAFU safety accent
_AG_SUNNY = "#fffcca"  # sunny weather accent
_AG_RADIUS = "rounded-[0px]"  # angular Swiss border-radius


class _DK:
    """Dark mode equivalents — matched to aare.guru CSS custom properties."""

    TXT_PRIMARY = "#88bee0"  # --ag-c-txt-Primary dark
    BG_WASSER = "#0c4257"  # --ag-c-bg-wasser dark
    BG_WETTER = "#2e4239"  # --ag-c-bg-wetter dark
    BG_SUNNY = "#fde047"  # --ag-c-bg-sunny dark
    WASSER_TEMP = "#47aad7"  # --ag-c-wasserTemp dark
    WASSER_FLOW = "#62ddd3"  # --ag-c-wasserFlow dark
    AIR_TEMP = "#46b5e9"  # --ag-c-airTemp dark
    BFU = "#2dd4bf"  # teal-400 (readable on dark)
    SUNNY = "#ffe97c"  # yellow-300
    CARD_BG = "#1c3138"  # page background dark


# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

# (max_flow_exclusive, label, badge_variant, hex_color)
# hex_color used for text — WCAG AA on white (≥ 4.5:1) required.
_SAFETY_LEVELS: list[tuple[float, str, str, str]] = [
    (100, "Sicher", "success", "#007d76"),  # 4.6:1 on white
    (220, "Moderat", "info", "#0877ab"),  # 5.0:1
    (300, "Erhöht", "warning", "#b45309"),  # 4.7:1
    (430, "Hoch", "destructive", "#dc2626"),  # 4.5:1
]

# Flow scale bar zones — (lo, hi_or_None, label, hex_color, tailwind_width)
# Widths are proportional within a 600 m³/s display cap:
#   100/600=17%, 120/600=20%, 80/600=13%, 130/600=22%, 170/600=28%
_FLOW_ZONES: list[tuple[float, float | None, str, str, str]] = [
    (0, 100, "Sicher", "#00b2aa", "w-[17%]"),  # original BFU teal (bar only)
    (100, 220, "Moderat", "#0877ab", "w-[20%]"),
    (220, 300, "Erhöht", "#b45309", "w-[13%]"),
    (300, 430, "Hoch", "#dc2626", "w-[22%]"),
    (430, None, "Sehr hoch", "#7f1d1d", "w-[28%]"),
]

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

# Official BAFU danger levels with German descriptions and swimmer guidance.
# Tuple: (level, label, light_color, dark_color, guidance, description)
# dark_color ensures WCAG AA contrast on dark card backgrounds (#1c1c1e).
_BAFU_LEVELS: list[tuple[int, str, str, str, str, str]] = [
    (
        1,
        "Keine Gefahr",
        "#00b2aa",  # original BFU teal (border/accent); text uses _SAFETY_LEVELS for white bg
        "#2dd4bf",  # 9.1:1 on dark card
        "Normales Schwimmen möglich",
        "Normale Abflussverhältnisse. Keine erhöhte Gefahr.",
    ),
    (
        2,
        "Mässige Gefahr",
        "#0877ab",  # 5.0:1 on white
        "#38bdf8",  # 7.9:1 on dark card
        "Vorsicht für schwache Schwimmer und Kinder",
        "Leicht erhöhter Abfluss. Ufer teilweise überschwemmt.",
    ),
    (
        3,
        "Erhebliche Gefahr",
        "#b45309",  # amber-700 — 4.7:1 on white (replaces #f59e0b which was 2.2:1)
        "#fbbf24",  # amber-400 — 9.4:1 on dark card
        "Nur geübte Schwimmer · keine Kinder",
        "Stark erhöhter Abfluss. Überflutungen an Uferbereichen.",
    ),
    (
        4,
        "Grosse Gefahr",
        "#dc2626",  # red-600 — 4.5:1 on white (replaces #ef4444 which was 3.8:1)
        "#f87171",  # red-400 — 5.9:1 on dark card
        "Schwimmen nicht empfohlen",
        "Sehr hoher Abfluss. Grosse Überschwemmungen möglich.",
    ),
    (
        5,
        "Sehr grosse Gefahr",
        "#7f1d1d",  # red-900 — 10.0:1 on white
        "#fca5a5",  # red-300 — 8.3:1 on dark card (replaces #7f1d1d which was 1.7:1)
        "Lebensgefahr — Wasser meiden",
        "Ausserordentlich hoher Abfluss. Lebensgefahr im Wasser.",
    ),
]
