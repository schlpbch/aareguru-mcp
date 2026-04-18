"""Skeleton loaders for Aareguru FastMCP apps — display while loading data."""

from prefab_ui.components import Card, CardContent, Column, Div, Row, Text

from ._constants import _AG_RADIUS


def _skeleton_pulse() -> str:
    """Return CSS animation for skeleton pulse effect."""
    return (
        "animate-pulse "
        "bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 "
        "dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 "
        "bg-[length:200%_100%] "
        "animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite"
    )


def _skeleton_line(height: str = "h-4", width: str = "w-full") -> None:
    """Render a skeleton line placeholder."""
    Div(
        cssClass=f"{height} {width} {_skeleton_pulse()} rounded-md",
    )


def skeleton_temperature_card() -> None:
    """Render skeleton loader for temperature card."""
    with Card(
        cssClass=f"bg-gray-100 dark:bg-gray-800 {_AG_RADIUS} overflow-hidden"
    ):
        with CardContent(cssClass="p-4 text-center space-y-2"):
            _skeleton_line("h-16", "w-32 mx-auto")
            _skeleton_line("h-3", "w-24 mx-auto")
            _skeleton_line("h-2", "w-20 mx-auto")


def skeleton_flow_card() -> None:
    """Render skeleton loader for flow/safety card."""
    with Card(
        cssClass=f"bg-gray-100 dark:bg-gray-800 {_AG_RADIUS} overflow-hidden border-4 border-gray-200 dark:border-gray-700"
    ):
        with CardContent(cssClass="p-4 space-y-3"):
            with Row(gap=4):
                _skeleton_line("h-12", "w-32")
                _skeleton_line("h-8", "w-20 ml-auto")
            _skeleton_line("h-2", "w-full")
            _skeleton_line("h-3", "w-40")


def skeleton_weather_card() -> None:
    """Render skeleton loader for weather card."""
    with Card(
        cssClass=f"bg-gray-100 dark:bg-gray-800 {_AG_RADIUS} overflow-hidden"
    ):
        with CardContent(cssClass="p-4 space-y-4"):
            with Row(gap=4):
                _skeleton_line("h-10", "w-10")
                with Column(gap=1):
                    _skeleton_line("h-4", "w-32")
                    _skeleton_line("h-3", "w-24")
            _skeleton_line("h-2", "w-full mt-2")
            with Row(gap=2):
                for _ in range(6):
                    _skeleton_line("h-16", "w-20")


def skeleton_sun_card() -> None:
    """Render skeleton loader for sun/hours card."""
    with Card(
        cssClass=f"bg-gray-100 dark:bg-gray-800 {_AG_RADIUS} overflow-hidden"
    ):
        with CardContent(cssClass="p-4 space-y-2"):
            _skeleton_line("h-6", "w-24")
            _skeleton_line("h-4", "w-32")
            _skeleton_line("h-3", "w-28")


def skeleton_map() -> None:
    """Render skeleton loader for map."""
    with Column(gap=0, cssClass="p-2 max-w-6xl mx-auto"):
        Text(
            "Aare — Loading map...",
            cssClass="text-lg font-black text-center mb-4 text-gray-400 dark:text-gray-600",
        )
        Div(
            cssClass=f"w-full h-96 {_skeleton_pulse()} {_AG_RADIUS} overflow-hidden"
        )


def skeleton_forecast() -> None:
    """Render skeleton loader for forecast."""
    with Column(gap=2, cssClass="p-2 max-w-2xl mx-auto"):
        Text(
            "Aare — Loading forecast...",
            cssClass="text-lg font-black text-center mb-2 text-gray-400 dark:text-gray-600",
        )
        # Header
        _skeleton_line("h-4", "w-48 mx-auto mb-4")
        # Forecast cards
        with Row(gap=2):
            for _ in range(6):
                with Card(cssClass=f"bg-gray-100 dark:bg-gray-800 {_AG_RADIUS} p-3 flex-1"):
                    _skeleton_line("h-6", "w-16 mx-auto")
                    _skeleton_line("h-4", "w-12 mx-auto mt-2")
                    _skeleton_line("h-3", "w-10 mx-auto mt-1")


def skeleton_history() -> None:
    """Render skeleton loader for historical data chart."""
    with Column(gap=0, cssClass="p-2 max-w-4xl mx-auto"):
        Text(
            "Aare — Loading history...",
            cssClass="text-lg font-black text-center mb-4 text-gray-400 dark:text-gray-600",
        )
        Div(
            cssClass=f"w-full h-64 {_skeleton_pulse()} {_AG_RADIUS} overflow-hidden"
        )


def skeleton_compare() -> None:
    """Render skeleton loader for city comparison table."""
    with Column(gap=2, cssClass="p-2 max-w-4xl mx-auto"):
        Text(
            "Loading city data...",
            cssClass="text-lg font-black text-center mb-4 text-gray-400 dark:text-gray-600",
        )
        for _ in range(5):
            with Row(gap=2):
                _skeleton_line("h-8", "w-24")
                _skeleton_line("h-8", "w-16")
                _skeleton_line("h-8", "w-16")
                _skeleton_line("h-8", "w-20")


def skeleton_conditions_dashboard() -> None:
    """Render skeleton loader for conditions dashboard."""
    with Column(gap=2, cssClass="p-2 max-w-2xl mx-auto"):
        Text(
            "Aare — Loading conditions...",
            cssClass="text-lg font-black text-center mb-2 text-gray-400 dark:text-gray-600",
        )
        skeleton_temperature_card()
        skeleton_flow_card()
        skeleton_weather_card()
        skeleton_sun_card()


__all__ = [
    "skeleton_temperature_card",
    "skeleton_flow_card",
    "skeleton_weather_card",
    "skeleton_sun_card",
    "skeleton_map",
    "skeleton_forecast",
    "skeleton_history",
    "skeleton_compare",
    "skeleton_conditions_dashboard",
]
