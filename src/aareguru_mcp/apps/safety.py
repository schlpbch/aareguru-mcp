"""App 7: Safety briefing."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Card,
    CardContent,
    Column,
    Muted,
    Row,
    Separator,
    Text,
)

from ._constants import (
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _BAFU_LEVELS,
    _DK,
    _FONT_CSS,
)
from ._helpers import _bafu_level, _fmt_flow

logger = structlog.get_logger(__name__)

safety_app = FastMCPApp("safety")


@safety_app.tool()
async def refresh_safety(city: str) -> dict[str, Any]:
    """Refresh safety data for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


@safety_app.ui()
async def safety_briefing(city: str = "Bern") -> PrefabApp:
    """Show the official BAFU 1–5 danger level scale with the current reading highlighted.

    Translates the hydrological danger level into plain swimmer guidance,
    using the actual flow_gefahrenstufe from the API where available.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'olten')
    """
    logger.info("app.safety_briefing", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)

    aare = data.get("aare") or {}
    flow: float | None = aare.get("flow")
    height: float | None = aare.get("height")
    gefahrenstufe: int | None = aare.get("flow_gefahrenstufe")
    threshold: float | None = aare.get("flow_scale_threshold")
    location: str = aare.get("location_long") or aare.get("location") or city

    level = _bafu_level(flow, gefahrenstufe)
    _, level_label, level_color, level_color_dk, guidance, description = _BAFU_LEVELS[level - 1]

    with Column(gap=2, cssClass="p-2 max-w-xl mx-auto") as view:
        Text(
            f"Sicherheit — {location}",
            cssClass=f"text-base font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            " text-center uppercase",
        )

        # Current level hero card
        with Card(cssClass=f"{_AG_RADIUS} border-l-[4px] border-l-[{level_color}] dark:border-l-[{level_color_dk}]"):
            with CardContent(cssClass="p-2"):
                with Row(cssClass="items-center gap-3"):
                    Text(
                        str(level),
                        cssClass=f"text-3xl font-black w-8 text-center flex-shrink-0"
                        f" text-[{level_color}] dark:text-[{level_color_dk}]",
                    )
                    with Column(cssClass="flex-1"):
                        Text(
                            level_label,
                            cssClass=f"text-sm font-black text-[{level_color}] dark:text-[{level_color_dk}]",
                        )
                        Text(
                            guidance,
                            cssClass=f"text-xs font-semibold text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                        )
                        Muted(
                            description,
                            cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/60 dark:text-[{_DK.TXT_PRIMARY}]/60",
                        )
                    with Column(cssClass="items-end flex-shrink-0 gap-0.5"):
                        Text(
                            f"{_fmt_flow(flow)} m³/s",
                            cssClass=f"text-base font-black tabular-nums"
                            f" text-[{_AG_WASSER_FLOW}] dark:text-[{_DK.WASSER_FLOW}]",
                        )
                        Muted(
                            "Abfluss",
                            cssClass=f"text-[9px] uppercase tracking-[0.15em]"
                            f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                        )
                        Text(
                            f"{height:.2f} m" if height is not None else "—",
                            cssClass=f"text-base font-black tabular-nums"
                            f" text-[{_AG_WASSER_FLOW}] dark:text-[{_DK.WASSER_FLOW}]",
                        )
                        Muted(
                            "Pegelstand",
                            cssClass=f"text-[9px] uppercase tracking-[0.15em]"
                            f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                        )
                        if threshold is not None:
                            Muted(
                                f"Schwelle {threshold:.0f} m³/s",
                                cssClass=f"text-[9px] text-[{_AG_TXT_PRIMARY}]/40 dark:text-[{_DK.TXT_PRIMARY}]/40",
                            )

        # Full 5-level scale
        Separator(cssClass="my-0.5")
        Text(
            "BAFU Gefahrenstufen",
            cssClass=f"text-[9px] uppercase tracking-[0.2em]"
            f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 text-center",
        )
        with Column(gap=1):
            for lvl, lbl, color, color_dk, swim_guidance, _desc in _BAFU_LEVELS:
                is_current = lvl == level
                with Card(
                    cssClass=(
                        f"{_AG_RADIUS} border-l-[3px] border-l-[{color}] dark:border-l-[{color_dk}]"
                        + (" shadow-sm" if is_current else " opacity-40")
                    )
                ):
                    with CardContent(cssClass="py-1.5 px-2"):
                        with Row(cssClass="items-center gap-2"):
                            Text(
                                str(lvl),
                                cssClass=f"text-sm font-black text-[{color}] dark:text-[{color_dk}]"
                                " w-4 text-center flex-shrink-0",
                            )
                            Text(
                                lbl + (" ← aktuell" if is_current else ""),
                                cssClass=(
                                    f"text-xs font-bold text-[{color}] dark:text-[{color_dk}]"
                                    if is_current
                                    else f"text-xs font-semibold"
                                    f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                                ),
                            )
                            Muted(
                                swim_guidance,
                                cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/60 dark:text-[{_DK.TXT_PRIMARY}]/60 ml-auto text-right",
                            )

    return PrefabApp(
        view=view,
        state={
            "city": city,
            "level": level,
            "flow": flow,
            "height": height,
        },
        stylesheets=[_FONT_CSS],
    )
