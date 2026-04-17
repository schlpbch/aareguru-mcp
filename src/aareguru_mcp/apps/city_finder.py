"""App 6: City finder."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Card,
    CardContent,
    Column,
    DataTable,
    DataTableColumn,
    Grid,
    Muted,
    Text,
)

from ._constants import (
    _AG_BFU,
    _AG_BG_WASSER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _AG_WASSER_TEMP,
    _DK,
    _FONT_CSS,
)
from ._helpers import _fmt_flow, _safety_badge

logger = structlog.get_logger(__name__)

city_finder_app = FastMCPApp("city-finder")


@city_finder_app.tool()
async def refresh_cities(cities: list[str] | None = None) -> dict[str, Any]:
    """Refresh city comparison data (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.compare_cities(cities)


@city_finder_app.ui()
async def city_finder_view(sort_by: str = "temperature") -> PrefabApp:
    """Show all cities ranked by water temperature or safety.

    Fetches live data for every available city and ranks them so swimmers
    can instantly find the warmest or safest spot.

    Args:
        sort_by: Ranking criterion — 'temperature' (warmest first, default)
                 or 'safety' (lowest flow / safest first)
    """
    logger.info("app.city_finder_view", sort_by=sort_by)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.compare_cities(None)

    cities_raw: list[dict[str, Any]] = data.get("cities") or []
    safe_count: int = data.get("safe_count", 0)
    total: int = data.get("total_count", 0)

    # Sort
    if sort_by == "safety":
        sorted_cities = sorted(
            cities_raw,
            key=lambda c: (c.get("flow") or 9999),
        )
    else:
        sorted_cities = sorted(
            cities_raw,
            key=lambda c: (c.get("temperature") or -99),
            reverse=True,
        )

    rows: list[dict[str, Any]] = []
    for rank, c in enumerate(sorted_cities, 1):
        flow = c.get("flow")
        safety_label, _, safety_color = _safety_badge(flow)
        rows.append(
            {
                "#": str(rank),
                "Stadt": c.get("location") or c.get("city") or "—",
                "Temp °C": (
                    f"{c['temperature']:.1f}"
                    if c.get("temperature") is not None
                    else "—"
                ),
                "m³/s": _fmt_flow(flow),
                "Sicherheit": safety_label,
            }
        )

    warmest = data.get("warmest") or {}

    with Column(gap=2, cssClass="p-2 max-w-3xl mx-auto") as view:
        Text(
            "Städtefinder",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            " text-center uppercase",
        )

        # Summary strip
        with Grid(columns=3, gap=2, cssClass="mb-1"):
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}] dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        warmest.get("location") or warmest.get("city") or "—",
                        cssClass=f"text-sm font-black text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                    )
                    if warmest.get("temperature") is not None:
                        Text(
                            f"{warmest['temperature']:.1f}°",
                            cssClass=f"text-xl font-black tabular-nums"
                            f" text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                        )
                    Muted(
                        "WÄRMSTE STADT",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

            with Card(cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BFU}] dark:border-t-[{_DK.BFU}]"):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        f"{safe_count} / {total}",
                        cssClass=f"text-xl font-black tabular-nums text-[{_AG_BFU}] dark:text-[{_DK.BFU}]",
                    )
                    Muted(
                        "SICHERE STÄDTE",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_WASSER_FLOW}] dark:border-t-[{_DK.WASSER_FLOW}]"
            ):
                with CardContent(cssClass="p-2 text-center"):
                    sort_label = (
                        "Nach Sicherheit" if sort_by == "safety" else "Nach Temperatur"
                    )
                    Text(
                        sort_label,
                        cssClass=f"text-xs font-semibold text-[{_AG_WASSER_FLOW}] dark:text-[{_DK.WASSER_FLOW}]",
                    )
                    Muted(
                        "SORTIERUNG",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em]"
                        f" text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

        with Card(cssClass=f"{_AG_RADIUS}"):
            with CardContent(cssClass="p-0"):
                DataTable(
                    columns=[
                        DataTableColumn(key="#", header="#", align="right"),
                        DataTableColumn(key="Stadt", header="Stadt", sortable=True),
                        DataTableColumn(
                            key="Temp °C",
                            header="Temp °C",
                            sortable=True,
                            align="right",
                        ),
                        DataTableColumn(
                            key="m³/s", header="m³/s", sortable=True, align="right"
                        ),
                        DataTableColumn(
                            key="Sicherheit", header="Sicherheit", sortable=True
                        ),
                    ],
                    rows=rows,  # type: ignore[arg-type]
                    search=True,
                    paginated=True,
                    pageSize=20,
                )

    return PrefabApp(
        view=view,
        state={"sort_by": sort_by, "total": total, "safe_count": safe_count},
        stylesheets=[_FONT_CSS],
    )
