"""Design tokens and lookup tables for the aare.guru visual design system."""

import base64
from pathlib import Path

# ---------------------------------------------------------------------------
# DIN Next LT Pro — embedded font (base64 woff2)
# ---------------------------------------------------------------------------
_FONT_FILE = Path(__file__).parent / "assets" / "webfonts" / "DIN-Next-LT-Pro.woff2"
_FONT_B64 = base64.b64encode(_FONT_FILE.read_bytes()).decode()
_FONT_CSS = (
    "@font-face {"
    "font-family:'DIN Next LT Pro';"
    "src:url('data:font/woff2;base64," + _FONT_B64 + "') format('woff2');"
    "font-weight:100 900;"
    "font-style:normal;"
    "font-display:swap;"
    "}"
    "body,*{font-family:'DIN Next LT Pro',ui-sans-serif,system-ui,sans-serif !important;}"
)

# ---------------------------------------------------------------------------
# aare.guru design tokens (light mode)
# ---------------------------------------------------------------------------
_AG_BG_WASSER = "#2be6ff"  # Aare cyan — water card background
_AG_BG_WETTER = "#aeffda"  # mint green — weather card background
_AG_TXT_PRIMARY = "#0f405f"  # dark blue — main labels
_AG_WASSER_TEMP = "#0877ab"  # water temperature values
_AG_WASSER_FLOW = "#357d9e"  # flow rate values
_AG_AIR_TEMP = "#0771a8"  # air temperature values  (darkened from #0a96d7 → 5.1:1 on white)
_AG_BFU = "#007d76"  # BAFU safety accent  (darkened from #00b2aa → 4.6:1 on white)
_AG_SUNNY = "#f2e500"  # sunny weather accent
_AG_RADIUS = "rounded-[3px]"  # angular Swiss border-radius


class _DK:
    """Dark mode equivalents for the aare.guru design tokens."""

    TXT_PRIMARY = "#c8e6f8"  # light sky blue — replaces dark navy
    BG_WASSER = "#0d4a5c"  # deep teal — dark cyan background
    BG_WETTER = "#0a3d24"  # dark forest green
    WASSER_TEMP = "#38bdf8"  # sky-400 — bright blue for dark bg
    WASSER_FLOW = "#7dd3fc"  # sky-300 — lighter flow color
    AIR_TEMP = "#38bdf8"  # sky-400
    BFU = "#2dd4bf"  # teal-400
    SUNNY = "#fde047"  # yellow-300
    CARD_BG = "#1a2e3d"  # dark navy card inner

# ---------------------------------------------------------------------------
# Safety helpers
# ---------------------------------------------------------------------------

# (max_flow_exclusive, label, badge_variant, hex_color)
# hex_color is used for text labels — chosen for WCAG AA on white (≥ 4.5:1).
_SAFETY_LEVELS: list[tuple[float, str, str, str]] = [
    (100, "Sicher",  "success",     "#007d76"),  # 4.6:1  (was #00b2aa → 2.6:1)
    (220, "Moderat", "info",        "#0877ab"),  # 5.0:1
    (300, "Erhöht",  "warning",     "#b45309"),  # 4.7:1  (was #f59e0b → 2.2:1)
    (430, "Hoch",    "destructive", "#dc2626"),  # 4.5:1  (was #ef4444 → 3.8:1)
]

# Flow scale bar zones — (lo, hi_or_None, label, hex_color, tailwind_width)
# Widths are proportional within a 600 m³/s display cap:
#   100/600=17%, 120/600=20%, 80/600=13%, 130/600=22%, 170/600=28%
# Colors match _SAFETY_LEVELS (WCAG AA on white).
_FLOW_ZONES: list[tuple[float, float | None, str, str, str]] = [
    (0, 100, "Sicher", "#007d76", "w-[17%]"),
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
        "#007d76",  # 4.6:1 on white
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
