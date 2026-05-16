"""MCP server implementation for Aareguru API using FastMCP.

This module implements the Model Context Protocol server that exposes
Aareguru data to AI assistants via stdio or HTTP transport.

Server responsibilities:
- Create FastMCP server instance
- Register resources (cities, current, today)
- Register prompts and tools (delegate to prompts.py and tools.py)
- Register custom HTTP routes (health, metrics)
- Provide entry points for stdio and HTTP transports
"""

import functools
import json
import re
from datetime import UTC, datetime
from typing import Any

import structlog
from fastmcp import Context, FastMCP
from fastmcp.server.elicitation import AcceptedElicitation
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from . import apps, prompts, resources, tools
from .config import get_settings
from .metrics import MetricsCollector
from .service import AareguruService
from .shop_service import ShopService

# Get structured logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create FastMCP server instance
mcp = FastMCP(
    name="aareguru-mcp",
    providers=[
        apps.conditions_app,
        apps.temperature_app,
        apps.flow_app,
        apps.weather_app,
        apps.sun_app,
        apps.history_app,
        apps.compare_app,
        apps.forecast_app,
        apps.intraday_app,
        apps.city_finder_app,
        apps.safety_app,
        apps.map_app,
        apps.shop_app,
        apps.shop_product_app,
    ],
    instructions="""You are an assistant that helps users with Swiss Aare river conditions.

You can provide:
- Current water temperatures for various Swiss cities
- Flow rates and safety assessments based on BAFU thresholds
- Weather conditions and forecasts
- Historical data for trend analysis
- Comparisons between different cities

Always consider safety when discussing swimming conditions. Flow rates above 220 m³/s
require caution, and rates above 300 m³/s are dangerous.

Swiss German phrases in the API responses add local flavor - feel free to explain them
to users (e.g., "geil aber chli chalt" means "awesome but a bit cold").
""",
)


# ============================================================================
# Resources
# ============================================================================


@mcp.resource("aareguru://cities")
@functools.wraps(resources.get_cities)
async def get_cities_resource() -> str:
    return await resources.get_cities()


@mcp.resource("aareguru://current/{city}")
@functools.wraps(resources.get_current)
async def get_current_resource(city: str) -> str:
    return await resources.get_current(city)


@mcp.resource("aareguru://today/{city}")
@functools.wraps(resources.get_today)
async def get_today_resource(city: str) -> str:
    return await resources.get_today(city)


@mcp.resource("aareguru://forecast/{city}")
@functools.wraps(resources.get_forecast)
async def get_forecast_resource(city: str) -> str:
    return await resources.get_forecast(city)


@mcp.resource("aareguru://history/{city}/{start}/{end}")
@functools.wraps(resources.get_history)
async def get_history_resource(city: str, start: str, end: str) -> str:
    return await resources.get_history(city, start, end)


@mcp.resource("aareguru://safety-levels")
def get_safety_levels_resource() -> str:
    return resources.get_safety_levels()


@mcp.resource("aareguru://thresholds")
def get_thresholds_resource() -> str:
    return resources.get_thresholds()


# ============================================================================
# Prompts
# ============================================================================


@mcp.prompt(name="daily-swimming-report")
@functools.wraps(prompts.daily_swimming_report)
async def daily_swimming_report_prompt(
    city: str = "Bern", include_forecast: bool = True
) -> str:
    return await prompts.daily_swimming_report(city, include_forecast)


@mcp.prompt(name="compare-swimming-spots")
@functools.wraps(prompts.compare_swimming_spots)
async def compare_swimming_spots_prompt(
    min_temperature: float | None = None, safety_only: bool = False
) -> str:
    return await prompts.compare_swimming_spots(min_temperature, safety_only)


@mcp.prompt(name="weekly-trend-analysis")
@functools.wraps(prompts.weekly_trend_analysis)
async def weekly_trend_analysis_prompt(city: str = "Bern", days: int = 7) -> str:
    return await prompts.weekly_trend_analysis(city, days)


@mcp.prompt(name="shop-browse")
@functools.wraps(prompts.shop_browse)
async def shop_browse_prompt(search: str | None = None) -> str:
    return await prompts.shop_browse(search)


@mcp.prompt(name="shop-checkout")
@functools.wraps(prompts.shop_checkout)
async def shop_checkout_prompt(items: str = "") -> str:
    return await prompts.shop_checkout(items)


# ============================================================================
# Elicitation helpers
# ============================================================================


async def _elicit_city(ctx: Context, bad_city: str) -> str | None:
    """Ask the user to pick a valid city when bad_city is not recognised."""
    try:
        service = AareguruService()
        cities = await service.get_cities_list()
        names: list[str] = sorted(str(c["city"]) for c in cities)
    except Exception:
        return None
    result = await ctx.elicit(
        f"Stadt '{bad_city}' nicht gefunden. Bitte eine Stadt wählen:",
        names,  # type: ignore[arg-type]
    )
    if isinstance(result, AcceptedElicitation):
        return str(result.data)
    return None


def _estimate_days(start: str) -> float:
    """Return approximate number of days covered by a start expression."""
    s = start.strip().lstrip("-")
    m = re.match(r"(\d+(?:\.\d+)?)\s*(day|week|month|year)s?", s, re.I)
    if m:
        n, unit = float(m.group(1)), m.group(2).lower()
        return n * {"day": 1, "week": 7, "month": 30, "year": 365}[unit]
    try:
        ts = float(start)
        return (datetime.now(UTC).timestamp() - ts) / 86400
    except ValueError:
        pass
    try:
        dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
        return (datetime.now(UTC) - dt).total_seconds() / 86400
    except ValueError:
        pass
    return 0.0


# ============================================================================
# Tools
# ============================================================================


@mcp.tool(name="get_current_temperature")
async def get_current_temperature_tool(
    city: str = "Bern", ctx: Context = None  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get current water temperature for a city.

    Use this for quick temperature checks and simple 'how warm is the water?' questions.
    Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'),
    and swimming suitability.

    Args:
        city: City identifier (e.g., 'Bern', 'Thun', 'Olten').
              Use `list_cities()` to discover available locations.
    """
    with MetricsCollector.track_tool_call("get_current_temperature"):
        service = AareguruService()
        try:
            return await service.get_current_temperature(city)
        except ValueError:
            chosen = await _elicit_city(ctx, city)
            if chosen is None:
                return {"error": f"Stadt '{city}' nicht gefunden."}
            return await service.get_current_temperature(chosen)
        except Exception as e:
            return {"error": str(e), "city": city}


@mcp.tool(name="get_current_conditions")
async def get_current_conditions_tool(
    city: str = "Bern", ctx: Context = None  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get complete current conditions for a city.

    Use this for safety assessments, 'is it safe to swim?' questions, and when users
    need a complete picture before swimming. This is the most detailed tool.

    Args:
        city: City identifier (e.g., 'Bern', 'Thun', 'Olten').
              Use `list_cities()` to discover available locations.
    """
    service = AareguruService()
    try:
        return await service.get_current_conditions(city)
    except ValueError:
        chosen = await _elicit_city(ctx, city)
        if chosen is None:
            return {"error": f"Stadt '{city}' nicht gefunden."}
        return await service.get_current_conditions(chosen)
    except Exception as e:
        return {"error": str(e), "city": city}


@mcp.tool(name="get_historical_data")
async def get_historical_data_tool(
    city: str, start: str, end: str, ctx: Context = None  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get historical time-series data.

    Use this for trend analysis, comparisons with past conditions, and statistical queries.
    Returns hourly data points for temperature and flow.

    Args:
        city: City identifier (e.g., 'Bern', 'Thun', 'Olten')
        start: Start date/time — ISO, Unix timestamp, or relative ('-7 days', '-1 month')
        end:   End date/time — ISO, Unix timestamp, or 'now'
    """
    days = _estimate_days(start)
    if days > 90:
        result = await ctx.elicit(
            f"Der Zeitraum umfasst ca. {int(days)} Tage (~{int(days) * 24} Datenpunkte). "
            "Das kann einen Moment dauern. Fortfahren?",
            {"ja": {"title": "Ja, fortfahren"}, "nein": {"title": "Nein, abbrechen"}},  # type: ignore[arg-type]
        )
        if not isinstance(result, AcceptedElicitation) or str(result.data) == "nein":
            return {
                "error": "Abgebrochen",
                "tip": "Wähle '-7 days' bis '-90 days' für schnellere Ergebnisse.",
            }
    return await tools.get_historical_data(city, start, end)


@mcp.tool(name="get_flow_danger_level")
async def get_flow_danger_level_tool(
    city: str = "Bern", ctx: Context = None  # type: ignore[assignment]
) -> dict[str, Any]:
    """Get current flow rate and BAFU danger assessment.

    Use this for safety-critical questions about current strength and swimming danger.

    Flow Safety Thresholds:
    - <100 m³/s: Safe · 100-220: Moderate · 220-300: Elevated
    - 300-430 m³/s: High — dangerous · >430: Very high — extremely dangerous

    Args:
        city: City identifier (e.g., 'Bern', 'Thun', 'Olten').
              Use `list_cities()` to discover available locations.
    """
    service = AareguruService()
    try:
        result = await service.get_flow_danger_level(city)
    except ValueError:
        chosen = await _elicit_city(ctx, city)
        if chosen is None:
            return {"error": f"Stadt '{city}' nicht gefunden."}
        result = await service.get_flow_danger_level(chosen)
    except Exception as e:
        return {"error": str(e), "city": city}

    level: int = result.get("danger_level") or 1
    if level >= 4:
        flow = result.get("flow", "?")
        label: str = result.get("safety_assessment", "Gefährlich")
        elicit_result = await ctx.elicit(
            f"⚠️ Durchfluss {flow} m³/s — Stufe {level} ({label}). "
            "Schwimmen ist gefährlich. Details trotzdem anzeigen?",
            {"show": {"title": "Ja, anzeigen"}, "cancel": {"title": "Nein, abbrechen"}},  # type: ignore[arg-type]
        )
        if (
            not isinstance(elicit_result, AcceptedElicitation)
            or str(elicit_result.data) == "cancel"
        ):
            return {
                "city": result.get("city", city),
                "flow": result.get("flow"),
                "danger_level": level,
                "safety_assessment": label,
                "warning": "Auf Wunsch des Benutzers abgebrochen.",
            }

    return result


@mcp.tool(name="compare_cities")
@functools.wraps(tools.compare_cities)
async def compare_cities_tool(cities: list[str] | None = None) -> dict[str, Any]:
    return await tools.compare_cities(cities)


@mcp.tool(name="get_forecasts")
@functools.wraps(tools.get_forecasts)
async def get_forecasts_tool(cities: list[str]) -> dict[str, Any]:
    return await tools.get_forecasts(cities)


# ============================================================================
# Shop resource + tools (konsum.aare.guru / UCP checkout)
# ============================================================================


@mcp.resource("aareguru://shop")
async def shop_catalog_resource() -> str:
    """Product catalog from the Aareguru merchandise shop (konsum.aare.guru).

    Returns JSON list of all available products with name, price in CHF,
    permalink, and stock status.
    """
    service = ShopService()
    try:
        result = await service.list_products()
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


@mcp.tool(name="list_shop_products")
@functools.wraps(tools.list_shop_products)
async def list_shop_products_tool(search: str | None = None) -> dict[str, Any]:
    return await tools.list_shop_products(search)


@mcp.tool(name="get_shop_product")
@functools.wraps(tools.get_shop_product)
async def get_shop_product_tool(product_id: int) -> dict[str, Any]:
    return await tools.get_shop_product(product_id)


@mcp.tool(name="create_checkout_session")
@functools.wraps(tools.create_checkout_session)
async def create_checkout_session_tool(
    items: list[dict[str, Any]],
) -> dict[str, Any]:
    return await tools.create_checkout_session(items)


@mcp.tool(name="update_checkout_session")
@functools.wraps(tools.update_checkout_session)
async def update_checkout_session_tool(
    session_id: str,
    billing: dict[str, Any],
    shipping: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return await tools.update_checkout_session(session_id, billing, shipping)


@mcp.tool(name="complete_checkout")
async def complete_checkout_tool(
    session_id: str,
    ctx: Context = None,  # type: ignore[assignment]
) -> dict[str, Any]:
    """Submit the order and return the payment URL.

    Use this after update_checkout_session to finalise the purchase.
    Returns a payment_url the user must open in their browser to pay
    via PostFinance Checkout.

    Args:
        session_id: From create_checkout_session result.
    """
    service = ShopService()
    result = await service.complete_checkout(session_id)
    if "error" in result and "Billing address" in str(result["error"]):
        elicit_result = await ctx.elicit(
            "Bitte Lieferadresse angeben (Vorname Nachname, E-Mail, Strasse, PLZ Ort):",
            str,  # type: ignore[arg-type]
        )
        if isinstance(elicit_result, AcceptedElicitation):
            return {
                **result,
                "hint": "Call update_checkout_session with billing details first.",
            }
    return result


@mcp.tool(name="cancel_checkout_session")
@functools.wraps(tools.cancel_checkout_session)
async def cancel_checkout_session_tool(session_id: str) -> dict[str, Any]:
    return await tools.cancel_checkout_session(session_id)


# ============================================================================
# Custom Routes (for HTTP transport)
# ============================================================================


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse(
        {
            "status": "healthy",
            "service": mcp.name,
            "version": settings.app_version,
        }
    )


@mcp.custom_route("/metrics", methods=["GET"])
async def metrics_endpoint(request: Request) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


# ============================================================================
# Entry Points
# ============================================================================


def entry_point() -> None:
    """Synchronous entry point for stdio transport (console script)."""
    mcp.run()


def run_http() -> None:
    """Entry point for HTTP transport."""
    mcp.run(
        transport="http",
        host=settings.http_host,
        port=settings.http_port,
    )


# For backwards compatibility
app = mcp

if __name__ == "__main__":
    entry_point()
