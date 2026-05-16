"""App: Shopping cart and UCP checkout view for konsum.aare.guru."""

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
    Muted,
    Row,
    Separator,
    Text,
)

from ._constants import (
    _AG_BFU,
    _AG_BG_WASSER,
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _AG_WASSER_FLOW,
    _DK,
    _FONT_CSS,
    _FONT_INJECTION_ON_MOUNT,
)
from ._i18n import t

logger = structlog.get_logger(__name__)

shop_app = FastMCPApp("shop")


@shop_app.tool()
async def refresh_shop_cart(session_id: str) -> dict[str, Any]:
    """Refresh cart and checkout state for a session (called from UI)."""
    from aareguru_mcp.shop_service import ShopService

    service = ShopService()
    return await service.get_session(session_id)


@shop_app.ui()
async def shop_cart_view(session_id: str = "", lang: str = "de") -> PrefabApp:
    """Show cart contents, billing details, and order status for a checkout session.

    Renders the full shopping cart UI including items, totals, billing address,
    and payment confirmation. Use after create_checkout_session to track your order.

    Args:
        session_id: From create_checkout_session result. Leave empty to see empty cart.
    """
    logger.info("app.shop_cart_view", session_id=session_id or "(empty)")
    from aareguru_mcp.shop_service import ShopService

    service = ShopService()
    session: dict[str, Any] = {}
    if session_id:
        session = await service.get_session(session_id)

    status = session.get("status", "")
    has_session = bool(session_id) and "error" not in session

    with Column(gap=0, cssClass="p-2 max-w-2xl mx-auto") as view:

        # ── Header ───────────────────────────────────────────────────────────
        Text(
            t("page_shop", lang),
            cssClass=(
                f"text-base font-black tracking-tight uppercase text-center"
                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            ),
        )

        # ── Empty state ───────────────────────────────────────────────────────
        if not has_session:
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
                f" dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="p-4 text-center"):
                    Text(
                        t("label_cart_empty", lang),
                        cssClass=(
                            f"text-lg font-black text-[{_AG_TXT_PRIMARY}]"
                            f" dark:text-[{_DK.TXT_PRIMARY}]"
                        ),
                    )
                    Muted(
                        t("label_cart_empty_hint1", lang),
                        cssClass="text-xs mt-1",
                    )
                    Muted(
                        t("label_cart_empty_hint2", lang),
                        cssClass="text-xs",
                    )

        # ── Session states (2 / 3 / 4) ───────────────────────────────────────
        else:
            line_items: list[dict[str, Any]] = session.get("line_items", [])
            total_chf: float = session.get("total_chf", 0.0)
            billing: dict[str, Any] = session.get("billing", {})
            order_id: int | None = session.get("order_id")
            continue_url: str | None = session.get("continue_url")

            # Cart items table
            rows = [
                {
                    "Artikel": item.get("name", "—"),
                    "Menge": str(item.get("quantity", 1)),
                    "Einzelpreis": f"CHF {item.get('unit_price_chf', 0):.2f}",
                    "Total": f"CHF {item.get('total_chf', 0):.2f}",
                }
                for item in line_items
            ]
            with Card(cssClass=f"{_AG_RADIUS}"):
                with CardContent(cssClass="p-0"):
                    DataTable(
                        columns=[
                            DataTableColumn(key="Artikel", header=t("col_item", lang)),
                            DataTableColumn(
                                key="Menge", header=t("col_qty", lang), align="right"
                            ),
                            DataTableColumn(
                                key="Einzelpreis",
                                header=t("col_unit_price", lang),
                                align="right",
                            ),
                            DataTableColumn(
                                key="Total", header=t("col_total", lang), align="right"
                            ),
                        ],
                        rows=rows,  # type: ignore[arg-type]
                        search=False,
                    )

            # Total card
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
                f" dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="px-4 py-2"):
                    with Row(cssClass="items-center justify-between"):
                        Muted(
                            t("label_total", lang),
                            cssClass=(
                                f"text-[10px] uppercase tracking-[0.2em]"
                                f" text-[{_AG_TXT_PRIMARY}]/60"
                                f" dark:text-[{_DK.TXT_PRIMARY}]/60"
                            ),
                        )
                        Text(
                            f"CHF {total_chf:.2f}",
                            cssClass=(
                                f"text-2xl font-black tabular-nums"
                                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                            ),
                        )

            # State 2 — next steps
            if status == "incomplete":
                with Card(
                    cssClass=f"{_AG_RADIUS} border-l-[4px] border-l-[{_AG_WASSER_FLOW}]"
                    f" dark:border-l-[{_DK.WASSER_FLOW}]"
                ):
                    with CardContent(cssClass="p-3"):
                        Text(
                            t("section_next_steps", lang),
                            cssClass=(
                                f"text-xs font-black uppercase tracking-[0.15em]"
                                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                            ),
                        )
                        Muted(
                            f'1.  update_checkout_session("{session_id}", billing={{...}})',
                            cssClass="text-xs font-mono mt-1",
                        )
                        Muted(
                            f'2.  complete_checkout("{session_id}")',
                            cssClass="text-xs font-mono",
                        )

            # State 3 — billing attached, ready to complete
            elif status == "ready_for_complete":
                _render_billing_card(billing, session_id, confirmed=False, lang=lang)

            # State 4 — order completed
            elif status == "completed":
                _render_billing_card(billing, session_id, confirmed=True, lang=lang)
                with Card(
                    cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BFU}]"
                    f" dark:border-t-[{_DK.BFU}]"
                ):
                    with CardContent(cssClass="p-3"):
                        Text(
                            t("label_ordered", lang),
                            cssClass=(
                                f"text-lg font-black text-[{_AG_BFU}]"
                                f" dark:text-[{_DK.BFU}]"
                            ),
                        )
                        if order_id:
                            Muted(
                                f"{t('label_order_number', lang)} #{order_id}",
                                cssClass="text-xs",
                            )
                        if continue_url:
                            Separator(cssClass="my-2")
                            Text(
                                t("label_payment_link", lang),
                                cssClass=(
                                    f"text-xs font-bold text-[{_AG_TXT_PRIMARY}]"
                                    f" dark:text-[{_DK.TXT_PRIMARY}]"
                                ),
                            )
                            Text(
                                continue_url,
                                cssClass="text-xs font-mono break-all text-blue-600 dark:text-blue-400",
                            )
                            Muted(
                                t("label_payment_desc", lang),
                                cssClass="text-[10px] mt-1",
                            )

    return PrefabApp(
        view=view,
        state={
            "session_id": session_id,
            "status": status,
            "total_chf": session.get("total_chf"),
            "order_id": session.get("order_id"),
        },
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )


def _render_billing_card(
    billing: dict[str, Any], session_id: str, confirmed: bool, lang: str = "de"
) -> None:
    """Render billing address summary card (state 3 and 4)."""
    border_color = _AG_BFU if confirmed else _AG_WASSER_FLOW
    border_color_dk = _DK.BFU if confirmed else _DK.WASSER_FLOW

    with Card(
        cssClass=f"{_AG_RADIUS} border-l-[4px] border-l-[{border_color}]"
        f" dark:border-l-[{border_color_dk}]"
    ):
        with CardContent(cssClass="p-3"):
            Text(
                t("section_delivery_address", lang),
                cssClass=(
                    f"text-xs font-black uppercase tracking-[0.15em]"
                    f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                ),
            )
            first = billing.get("first_name", "")
            last = billing.get("last_name", "")
            if first or last:
                Text(
                    f"{first} {last}".strip(),
                    cssClass=(
                        f"text-sm font-semibold text-[{_AG_TXT_PRIMARY}]"
                        f" dark:text-[{_DK.TXT_PRIMARY}] mt-1"
                    ),
                )
            if billing.get("email"):
                Muted(billing["email"], cssClass="text-xs")
            addr = billing.get("address_1", "")
            postcode = billing.get("postcode", "")
            city = billing.get("city", "")
            country = billing.get("country", "")
            if addr:
                Muted(
                    f"{addr}, {postcode} {city}, {country}".strip(", "),
                    cssClass="text-xs",
                )
            if not confirmed:
                Separator(cssClass="my-2")
                Muted(
                    f'complete_checkout("{session_id}")',
                    cssClass="text-xs font-mono",
                )
