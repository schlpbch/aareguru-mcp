"""App: Shopping cart and UCP checkout view for konsum.aare.guru."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Card,
    CardContent,
    Column,
    Image,
    Link,
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

    with Column(gap=0, css_class="p-2 max-w-2xl mx-auto") as view:

        # ── Header ───────────────────────────────────────────────────────────
        Text(
            t("page_shop", lang),
            css_class=(
                f"text-base font-black tracking-tight uppercase text-center"
                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            ),
        )

        # ── Empty state ───────────────────────────────────────────────────────
        if not has_session:
            with Card(
                css_class=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
                f" dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(css_class="p-4 text-center"):
                    Text(
                        t("label_cart_empty", lang),
                        css_class=(
                            f"text-lg font-black text-[{_AG_TXT_PRIMARY}]"
                            f" dark:text-[{_DK.TXT_PRIMARY}]"
                        ),
                    )
                    Muted(
                        t("label_cart_empty_hint1", lang),
                        css_class="text-xs mt-1",
                    )
                    Muted(
                        t("label_cart_empty_hint2", lang),
                        css_class="text-xs",
                    )

        # ── Session states (2 / 3 / 4) ───────────────────────────────────────
        else:
            line_items: list[dict[str, Any]] = session.get("line_items", [])
            total_chf: float = session.get("total_chf", 0.0)
            billing: dict[str, Any] = session.get("billing", {})
            order_id: int | None = session.get("order_id")
            continue_url: str | None = session.get("continue_url")

            # Cart items — thumbnail, name, quantity × unit price, line total
            with Card(css_class=f"{_AG_RADIUS}"):
                with CardContent(
                    css_class="p-0 divide-y divide-black/5 dark:divide-white/10"
                ):
                    for item in line_items:
                        with Row(css_class="items-center gap-3 p-3"):
                            image_url = item.get("image_url")
                            if image_url:
                                Image(
                                    src=image_url,
                                    alt=item.get("name", ""),
                                    css_class=(
                                        f"{_AG_RADIUS} w-12 h-12 object-cover shrink-0"
                                        " border border-black/10 dark:border-white/10"
                                    ),
                                )
                            with Column(gap=0, css_class="flex-1 min-w-0"):
                                Text(
                                    item.get("name", "—"),
                                    css_class=(
                                        f"text-sm font-bold truncate"
                                        f" text-[{_AG_TXT_PRIMARY}]"
                                        f" dark:text-[{_DK.TXT_PRIMARY}]"
                                    ),
                                )
                                Muted(
                                    f"{item.get('quantity', 1)} × "
                                    f"CHF {item.get('unit_price_chf', 0):.2f}",
                                    css_class="text-xs",
                                )
                            Text(
                                f"CHF {item.get('total_chf', 0):.2f}",
                                css_class=(
                                    f"text-sm font-black tabular-nums shrink-0"
                                    f" text-[{_AG_TXT_PRIMARY}]"
                                    f" dark:text-[{_DK.TXT_PRIMARY}]"
                                ),
                            )

            # Total card
            with Card(
                css_class=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
                f" dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(css_class="px-4 py-2"):
                    with Row(css_class="items-center justify-between"):
                        Muted(
                            t("label_total", lang),
                            css_class=(
                                f"text-[10px] uppercase tracking-[0.2em]"
                                f" text-[{_AG_TXT_PRIMARY}]/60"
                                f" dark:text-[{_DK.TXT_PRIMARY}]/60"
                            ),
                        )
                        Text(
                            f"CHF {total_chf:.2f}",
                            css_class=(
                                f"text-2xl font-black tabular-nums"
                                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                            ),
                        )

            # State 2 — next steps
            if status == "incomplete":
                with Card(
                    css_class=f"{_AG_RADIUS} border-l-[4px] border-l-[{_AG_WASSER_FLOW}]"
                    f" dark:border-l-[{_DK.WASSER_FLOW}]"
                ):
                    with CardContent(css_class="p-3"):
                        Text(
                            t("section_next_steps", lang),
                            css_class=(
                                f"text-xs font-black uppercase tracking-[0.15em]"
                                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                            ),
                        )
                        Muted(
                            t("label_next_step_hint", lang),
                            css_class="text-xs mt-1",
                        )

            # State 3 — billing attached, ready to complete
            elif status == "ready_for_complete":
                _render_billing_card(billing, confirmed=False, lang=lang)

            # State 4 — order completed
            elif status == "completed":
                _render_billing_card(billing, confirmed=True, lang=lang)
                with Card(
                    css_class=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BFU}]"
                    f" dark:border-t-[{_DK.BFU}]"
                ):
                    with CardContent(css_class="p-3"):
                        Text(
                            t("label_ordered", lang),
                            css_class=(
                                f"text-lg font-black text-[{_AG_BFU}]"
                                f" dark:text-[{_DK.BFU}]"
                            ),
                        )
                        if order_id:
                            Muted(
                                f"{t('label_order_number', lang)} #{order_id}",
                                css_class="text-xs",
                            )
                        if continue_url:
                            Separator(css_class="my-2")
                            Link(
                                t("label_open_payment", lang),
                                href=continue_url,
                                target="_blank",
                                css_class=(
                                    f"{_AG_RADIUS} block w-full text-center py-2"
                                    " font-black uppercase tracking-wide no-underline"
                                    f" text-white bg-[{_AG_BFU}] dark:bg-[{_DK.BFU}]"
                                    f" dark:text-[{_DK.CARD_BG}]"
                                ),
                            )
                            Muted(
                                t("label_payment_desc", lang),
                                css_class="text-[10px] mt-2 text-center",
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
    billing: dict[str, Any], confirmed: bool, lang: str = "de"
) -> None:
    """Render billing address summary card (state 3 and 4)."""
    border_color = _AG_BFU if confirmed else _AG_WASSER_FLOW
    border_color_dk = _DK.BFU if confirmed else _DK.WASSER_FLOW

    with Card(
        css_class=f"{_AG_RADIUS} border-l-[4px] border-l-[{border_color}]"
        f" dark:border-l-[{border_color_dk}]"
    ):
        with CardContent(css_class="p-3"):
            Text(
                t("section_delivery_address", lang),
                css_class=(
                    f"text-xs font-black uppercase tracking-[0.15em]"
                    f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                ),
            )
            first = billing.get("first_name", "")
            last = billing.get("last_name", "")
            if first or last:
                Text(
                    f"{first} {last}".strip(),
                    css_class=(
                        f"text-sm font-semibold text-[{_AG_TXT_PRIMARY}]"
                        f" dark:text-[{_DK.TXT_PRIMARY}] mt-1"
                    ),
                )
            if billing.get("email"):
                Muted(billing["email"], css_class="text-xs")
            addr = billing.get("address_1", "")
            postcode = billing.get("postcode", "")
            city = billing.get("city", "")
            country = billing.get("country", "")
            if addr:
                Muted(
                    f"{addr}, {postcode} {city}, {country}".strip(", "),
                    css_class="text-xs",
                )
            if not confirmed:
                Separator(css_class="my-2")
                Muted(
                    t("label_ready_hint", lang),
                    css_class="text-xs",
                )
