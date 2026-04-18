"""Flow and safety level app - displays water flow and BAFU safety assessment."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import Badge, Card, CardContent, Column, Grid, Row, Text

from ._constants import (
    _AG_BFU,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _DK,
    _FLOW_ZONES,
    _FONT_CSS,
    _FONT_INJECTION_ON_MOUNT,
)
from ._helpers import _fmt_flow, _safety_badge
from ._skeletons import skeleton_flow_card

logger = structlog.get_logger(__name__)

flow_app = FastMCPApp("conditions-flow")


@flow_app.tool()
async def refresh_flow(city: str) -> dict[str, Any]:
    """Refresh flow and safety data for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


def render_flow_section(aare: dict[str, Any] | None = None) -> None:
    """Render flow rate and BAFU safety grid section.

    Must be called inside an active Column/Row context.
    Displays flow in m³/s and BAFU safety level with colored flow zones.
    Shows skeleton loader if data is unavailable.
    """
    if not aare:
        skeleton_flow_card()
        return

    flow: float | None = aare.get("flow")
    safety_label, safety_variant, safety_color = _safety_badge(flow)

    with Grid(columns=2, gap=0):
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
        with Card(
            cssClass=f"{_AG_RADIUS} border-[4px] border-[{_AG_BFU}] dark:border-[{_DK.BFU}]"
        ):
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


@flow_app.ui()
async def flow_card(city: str = "Bern") -> PrefabApp:
    """Show an interactive Aare flow and safety level card.

    Displays water flow in m³/s with BAFU safety level assessment
    and color-coded flow zones.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'Olten')
    """
    logger.info("app.flow_card", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)
    aare = data.get("aare") or {}
    location: str = aare.get("location_long") or aare.get("location") or city

    with Column(gap=0, cssClass="p-2 max-w-2xl mx-auto") as view:
        Text(
            f"Aare — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center uppercase",
        )
        render_flow_section(aare)

    return PrefabApp(
        view=view,
        state={"city": city, "aare": aare},
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )
