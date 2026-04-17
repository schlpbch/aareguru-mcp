"""App 3: City comparison table."""

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

compare_app = FastMCPApp("compare")


@compare_app.tool()
async def fetch_comparison(cities: list[str] | None = None) -> dict[str, Any]:
    """Fetch comparison data for cities (called from UI)."""
    from aareguru_mcp.apps import AareguruService

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
    from aareguru_mcp.apps import AareguruService

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

    with Column(gap=2, cssClass="p-2 max-w-4xl mx-auto") as view:

        # Header
        Text(
            "Städtevergleich",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] uppercase text-center",
        )

        # Summary strip — cyan accent top-border cards
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
                            cssClass=f"text-xl font-black tabular-nums text-[{_AG_WASSER_TEMP}] dark:text-[{_DK.WASSER_TEMP}]",
                        )
                    Muted(
                        "WÄRMSTE STADT",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )

            with Card(cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BFU}] dark:border-t-[{_DK.BFU}]"):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        f"{safe_count} / {total}",
                        cssClass=f"text-xl font-black tabular-nums text-[{_AG_BFU}] dark:text-[{_DK.BFU}]",
                    )
                    Muted(
                        "SICHERE STÄDTE",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
                    )
                    Muted(
                        "Durchfluss < 150 m³/s",
                        cssClass=f"text-[9px] text-[{_AG_TXT_PRIMARY}]/40 dark:text-[{_DK.TXT_PRIMARY}]/40",
                    )

            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_WASSER_FLOW}] dark:border-t-[{_DK.WASSER_FLOW}]"
            ):
                with CardContent(cssClass="p-2 text-center"):
                    Text(
                        str(total),
                        cssClass=f"text-xl font-black tabular-nums text-[{_AG_WASSER_FLOW}] dark:text-[{_DK.WASSER_FLOW}]",
                    )
                    Muted(
                        "STÄDTE VERGLICHEN",
                        cssClass=f"text-[10px] uppercase tracking-[0.2em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
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
        stylesheets=[_FONT_CSS],
    )
