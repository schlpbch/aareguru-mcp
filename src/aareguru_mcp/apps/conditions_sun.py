"""Sun and sunshine app - displays sunshine hours and sunset times."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Badge,
    Card,
    CardContent,
    Column,
    Grid,
    Muted,
    Row,
    Text,
)

from ._constants import (
    _AG_BG_SUNNY,
    _AG_RADIUS,
    _AG_SUNNY,
    _AG_TXT_PRIMARY,
    _DK,
    _FONT_CSS,
)

logger = structlog.get_logger(__name__)

sun_app = FastMCPApp("conditions-sun")


@sun_app.tool()
async def refresh_sun(city: str) -> dict[str, Any]:
    """Refresh sun data for a city (called from UI)."""
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    return await service.get_current_conditions(city)


def render_sun_section(sun: dict[str, Any]) -> None:
    """Render sun section with sunshine hours and sunset times.

    Must be called inside an active Column/Row context.
    Displays total sunshine, sunset time, and location badges with time-left values.
    No-op if sun data is empty.
    """
    if not sun:
        return

    sun_today: dict[str, Any] = sun.get("today") or {}
    sun_locs: list[dict[str, Any]] = sun.get("sunlocations") or []
    suntotal_str: str | None = sun_today.get("suntotal")
    sunset_str: str | None = sun_locs[0].get("sunsetlocal") if sun_locs else None
    sun_rel = sun_today.get("sunrelative")

    with Card(
        cssClass=f"{_AG_RADIUS} border-t-[3px] border-t-[{_AG_SUNNY}] dark:border-t-[{_DK.SUNNY}] bg-[{_AG_BG_SUNNY}] dark:bg-[{_DK.BG_SUNNY}] overflow-hidden"
    ):
        with CardContent(cssClass="p-3"):
            with Grid(columns=2, gap=0, cssClass="mb-2"):
                with Card(
                    cssClass=f"{_AG_RADIUS} bg-[{_AG_SUNNY}]/20 dark:bg-[{_DK.BG_SUNNY}]/10"
                ):
                    with CardContent(cssClass="p-2 text-center"):
                        Text(
                            suntotal_str or "—",
                            cssClass=f"text-lg font-black tabular-nums text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                        )
                        Muted(
                            "Sonnenschein",
                            cssClass=f"text-[10px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                        )
                        if sun_rel is not None:
                            Muted(
                                f"{sun_rel:.0f}% des Tages",
                                cssClass=f"text-[10px] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                            )
                with Card(
                    cssClass=f"{_AG_RADIUS} bg-[{_AG_SUNNY}]/20 dark:bg-[{_DK.BG_SUNNY}]/10"
                ):
                    with CardContent(cssClass="p-2 text-center"):
                        Text(
                            sunset_str or "—",
                            cssClass=f"text-lg font-black tabular-nums text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]",
                        )
                        Muted(
                            "Sonnenuntergang",
                            cssClass=f"text-[10px] uppercase tracking-[0.1em] text-[{_AG_TXT_PRIMARY}]/50 dark:text-[{_DK.TXT_PRIMARY}]/50",
                        )

            if sun_locs:
                with Row(cssClass="gap-1.5 flex-wrap"):
                    for loc in sun_locs[:5]:
                        loc_name: str = loc.get("name") or "—"
                        timeleft: int | None = loc.get("timeleft")
                        timeleft_str = loc.get("timeleftstring") or (
                            f"{timeleft // 3600}h {(timeleft % 3600) // 60}m"
                            if timeleft is not None
                            else None
                        )
                        label = (
                            f"☀ {loc_name} · {timeleft_str}"
                            if timeleft_str
                            else f"☀ {loc_name}"
                        )
                        Badge(
                            label=label,
                            variant="secondary",
                            cssClass=f"bg-[{_AG_SUNNY}]/30 dark:bg-[{_DK.BG_SUNNY}]/15 text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] {_AG_RADIUS} text-xs",
                        )


@sun_app.ui()
async def sun_card(city: str = "Bern") -> PrefabApp:
    """Show an interactive Aare sun and sunshine card.

    Displays total sunshine hours for today, sunset time, and time-left-in-sun
    for nearby locations.

    Args:
        city: City identifier (e.g. 'Bern', 'Thun', 'Olten')
    """
    logger.info("app.sun_card", city=city)
    from aareguru_mcp.apps import AareguruService

    service = AareguruService()
    data = await service.get_current_conditions(city)
    location: str = (
        (data.get("aare") or {}).get("location_long")
        or (data.get("aare") or {}).get("location")
        or city
    )

    with Column(gap=0, cssClass="p-2 max-w-2xl mx-auto") as view:
        Text(
            f"Aare — {location}",
            cssClass=f"text-lg font-black tracking-tight text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}] text-center uppercase",
        )
        render_sun_section(data.get("sun") or {})

    return PrefabApp(
        view=view,
        state={"city": city, "sun": data.get("sun")},
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )
