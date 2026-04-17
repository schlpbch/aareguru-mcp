"""App 7: Safety briefing."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
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
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _BAFU_LEVELS,
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
    _, level_label, level_color, guidance, description = _BAFU_LEVELS[level - 1]

    with Column(gap=2, cssClass="p-2 max-w-xl mx-auto") as view:
        Text(
            f"Sicherheit — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}]"
            " text-center uppercase",
        )

        # Current level hero card
        with Card(cssClass=f"{_AG_RADIUS} border-[3px] border-[{level_color}]"):
            with CardContent(cssClass="p-3 text-center"):
                Text(
                    f"Stufe {level}",
                    cssClass=f"text-3xl font-black text-[{level_color}]",
                )
                Text(
                    level_label,
                    cssClass=f"text-sm font-bold text-[{_AG_TXT_PRIMARY}] mt-0.5",
                )
                Separator(cssClass="my-2")
                Text(
                    guidance,
                    cssClass=f"text-sm font-semibold text-[{_AG_TXT_PRIMARY}]",
                )
                Muted(
                    description,
                    cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/60 mt-0.5",
                )

        # Flow + height readings
        with Grid(columns=2, gap=2):
            with Card(cssClass=f"{_AG_RADIUS}"):
                with CardContent(cssClass="p-3 text-center"):
                    Text(
                        f"{_fmt_flow(flow)} m³/s",
                        cssClass=f"text-xl font-black tabular-nums"
                        f" text-[{_AG_WASSER_FLOW}]",
                    )
                    Muted(
                        "Abfluss",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 mt-0.5",
                    )
                    if threshold is not None:
                        Muted(
                            f"Schwelle: {threshold:.0f} m³/s",
                            cssClass=f"text-[9px] text-[{_AG_TXT_PRIMARY}]/40 mt-0.5",
                        )
            with Card(cssClass=f"{_AG_RADIUS}"):
                with CardContent(cssClass="p-3 text-center"):
                    Text(
                        f"{height:.2f} m" if height is not None else "—",
                        cssClass=f"text-xl font-black tabular-nums"
                        f" text-[{_AG_WASSER_FLOW}]",
                    )
                    Muted(
                        "Pegelstand",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 mt-0.5",
                    )

        # Full 5-level scale
        Separator(cssClass="my-1")
        Text(
            "BAFU Gefahrenstufen",
            cssClass=f"text-xs uppercase tracking-[0.2em]"
            f" text-[{_AG_TXT_PRIMARY}]/50 text-center",
        )
        with Column(gap=2):
            for lvl, lbl, color, swim_guidance, _desc in _BAFU_LEVELS:
                is_current = lvl == level
                with Card(
                    cssClass=(
                        f"{_AG_RADIUS} border-l-[4px] border-l-[{color}]"
                        + (" shadow-md" if is_current else " opacity-50")
                    )
                ):
                    with CardContent(cssClass="p-3"):
                        with Row(cssClass="items-center gap-3"):
                            Text(
                                str(lvl),
                                cssClass=f"text-xl font-black text-[{color}]"
                                " w-6 text-center flex-shrink-0",
                            )
                            with Column(cssClass="flex-1"):
                                Text(
                                    lbl + (" ← aktuell" if is_current else ""),
                                    cssClass=(
                                        f"text-sm font-bold text-[{color}]"
                                        if is_current
                                        else f"text-sm font-semibold"
                                        f" text-[{_AG_TXT_PRIMARY}]"
                                    ),
                                )
                                Muted(
                                    swim_guidance,
                                    cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/60",
                                )

    return PrefabApp(
        view=view,
        state={
            "city": city,
            "level": level,
            "flow": flow,
            "height": height,
        },
    )
