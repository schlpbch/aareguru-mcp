"""App 2: Historical data area chart."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Card,
    CardContent,
    Column,
    Muted,
    Row,
    Text,
)
from prefab_ui.components.charts import AreaChart, ChartSeries

from ._constants import (
    _AG_BG_WASSER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _AG_WASSER_TEMP,
    _DK,
    _FONT_CSS,
    _FONT_INJECTION_ON_MOUNT,
)
from ._skeletons import skeleton_history

logger = structlog.get_logger(__name__)

history_app = FastMCPApp("history")


@history_app.tool()
async def fetch_history(city: str, start: str, end: str) -> dict[str, Any]:
    """Fetch historical time-series data (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_historical_data(city, start, end)


@history_app.ui()
async def historical_chart(
    city: str = "Bern",
    start: str = "-7 days",
    end: str = "now",
) -> PrefabApp:
    """Show an aare.guru-style area chart of historical Aare temperature and flow.

    Uses the Aare color palette: #0877ab for temperature, #357d9e for flow.

    Args:
        city:  City identifier (e.g. 'Bern', 'Thun', 'Olten')
        start: Start of period (e.g. '-7 days', '-1 month', ISO timestamp)
        end:   End of period ('now' or ISO timestamp)
    """
    logger.info("app.historical_chart", city=city, start=start, end=end)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    raw = await service.get_historical_data(city, start, end)

    # The API returns a list of hourly dicts under various keys
    points: list[dict[str, Any]] = []
    if isinstance(raw, list):
        points = raw
    elif isinstance(raw, dict):
        for key in ("data", "timeseries", "values", "result"):
            if isinstance(raw.get(key), list):
                points = raw[key]
                break

    # Normalise to {time, temperature, flow}
    chart_data: list[dict[str, Any]] = []
    for p in points:
        temp_val = p.get("aare") or p.get("temperature")
        flow_val = p.get("flow")
        time_val = p.get("time") or p.get("timestamp") or p.get("datetime")
        if temp_val is not None and time_val is not None:
            chart_data.append(
                {
                    "time": str(time_val),
                    "temperature": round(float(temp_val), 1),
                    "flow": (
                        round(float(flow_val), 0) if flow_val is not None else None
                    ),
                }
            )

    has_flow = any(p.get("flow") is not None for p in chart_data)
    series = [
        ChartSeries(
            dataKey="temperature", label="Wassertemperatur (°C)", color=_AG_WASSER_TEMP
        ),
    ]
    if has_flow:
        series.append(
            ChartSeries(
                dataKey="flow", label="Wasserstand (m³/s)", color=_AG_WASSER_FLOW
            )
        )

    with Column(gap=0, cssClass="p-2 max-w-3xl mx-auto") as view:

        # Header — matches aare.guru section title style
        with Row(cssClass="justify-between items-end mb-0"):
            Text(
                f"Aare — {city}",
                cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] uppercase",
            )
            Muted(
                f"{start} → {end}",
                cssClass=f"text-xs text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
            )

        if chart_data:
            # Chart card with subtle Aare cyan border-top
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}] dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="pt-3 pb-2 px-3"):
                    AreaChart(
                        data=chart_data,
                        series=series,
                        xAxis="time",
                        curve="smooth",
                        showLegend=True,
                        height=220,
                    )
            Muted(
                f"{len(chart_data)} Datenpunkte",
                cssClass=f"text-center text-xs text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50 mt-0.5",
            )
        else:
            with Alert(variant="warning", cssClass=f"{_AG_RADIUS}"):
                AlertTitle("Keine Daten")
                AlertDescription(
                    "Keine historischen Daten für den gewählten Zeitraum gefunden."
                )

    return PrefabApp(
        view=view,
        state={"city": city, "start": start, "end": end, "points": len(chart_data)},
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )
