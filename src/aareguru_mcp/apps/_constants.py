"""Design tokens and lookup tables for the aare.guru visual design system."""

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

# Official BAFU danger levels with German descriptions and swimmer guidance
_BAFU_LEVELS: list[tuple[int, str, str, str, str]] = [
    (
        1,
        "Keine Gefahr",
        "#00b2aa",
        "Normales Schwimmen möglich",
        "Normale Abflussverhältnisse. Keine erhöhte Gefahr.",
    ),
    (
        2,
        "Mässige Gefahr",
        "#0877ab",
        "Vorsicht für schwache Schwimmer und Kinder",
        "Leicht erhöhter Abfluss. Ufer teilweise überschwemmt.",
    ),
    (
        3,
        "Erhebliche Gefahr",
        "#f59e0b",
        "Nur geübte Schwimmer · keine Kinder",
        "Stark erhöhter Abfluss. Überflutungen an Uferbereichen.",
    ),
    (
        4,
        "Grosse Gefahr",
        "#ef4444",
        "Schwimmen nicht empfohlen",
        "Sehr hoher Abfluss. Grosse Überschwemmungen möglich.",
    ),
    (
        5,
        "Sehr grosse Gefahr",
        "#7f1d1d",
        "Lebensgefahr — Wasser meiden",
        "Ausserordentlich hoher Abfluss. Lebensgefahr im Wasser.",
    ),
]
