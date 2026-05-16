"""App: Product detail view for konsum.aare.guru."""

from typing import Any

import structlog
from fastmcp import FastMCPApp
from prefab_ui.app import PrefabApp
from prefab_ui.components import (
    Alert,
    AlertDescription,
    AlertTitle,
    Badge,
    Card,
    CardContent,
    Column,
    Image,
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
    _DK,
    _FONT_CSS,
    _FONT_INJECTION_ON_MOUNT,
)
from ._i18n import t

logger = structlog.get_logger(__name__)

shop_product_app = FastMCPApp("shop_product")


@shop_product_app.tool()
async def refresh_product(product_id: int) -> dict[str, Any]:
    """Refresh product details (called from UI)."""
    from aareguru_mcp.shop_service import ShopService

    service = ShopService()
    return await service.get_product(product_id)


@shop_product_app.ui()
async def product_view(product_id: int = 0, lang: str = "de") -> PrefabApp:
    """Show a product detail page for a konsum.aare.guru merchandise item.

    Displays the product image, name, price, stock status, and description.
    Use after list_shop_products to let the user inspect a specific item before
    adding it to their cart.

    Args:
        product_id: WooCommerce product ID (from list_shop_products)
    """
    logger.info("app.product_view", product_id=product_id)
    from aareguru_mcp.shop_service import ShopService

    product: dict[str, Any] = {}
    if product_id:
        service = ShopService()
        product = await service.get_product(product_id)

    with Column(gap=0, cssClass="p-2 max-w-xl mx-auto") as view:

        # ── Header ───────────────────────────────────────────────────────────
        Text(
            t("page_product", lang),
            cssClass=(
                f"text-base font-black tracking-tight uppercase text-center"
                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            ),
        )

        if not product or "error" in product:
            with Alert(variant="warning", cssClass=f"{_AG_RADIUS}"):
                AlertTitle(t("alert_product_not_found", lang))
                AlertDescription(t("alert_product_not_found_desc", lang))
        else:
            name: str = product.get("name", "")
            price_chf: float = product.get("price_chf", 0.0)
            on_sale: bool = product.get("on_sale", False)
            stock_status: str = product.get("stock_status", "instock")
            short_desc: str = product.get("short_description", "")
            images: list[str] = product.get("images", [])
            permalink: str = product.get("permalink", "")
            in_stock = stock_status == "instock"

            # ── Product name ─────────────────────────────────────────────────
            Text(
                name,
                cssClass=(
                    f"text-xl font-black tracking-tight uppercase text-center mt-1"
                    f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                ),
            )

            # ── Product image ─────────────────────────────────────────────────
            if images:
                with Card(cssClass=f"{_AG_RADIUS} overflow-hidden"):
                    with CardContent(cssClass="p-0"):
                        Image(
                            src=images[0],
                            alt=name,
                            cssClass="w-full object-cover max-h-72",
                        )

            # ── Price + badges ────────────────────────────────────────────────
            with Card(
                cssClass=f"{_AG_RADIUS} border-t-[4px] border-t-[{_AG_BG_WASSER}]"
                f" dark:border-t-[{_DK.BG_WASSER}]"
            ):
                with CardContent(cssClass="px-4 py-3"):
                    with Row(cssClass="items-center justify-between flex-wrap gap-2"):
                        Text(
                            f"CHF {price_chf:.2f}",
                            cssClass=(
                                f"text-3xl font-black tabular-nums"
                                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                            ),
                        )
                        with Row(cssClass="gap-1 flex-wrap"):
                            if on_sale:
                                Badge(
                                    label=t("label_on_sale", lang),
                                    variant="destructive",
                                )
                            Badge(
                                label=(
                                    t("label_in_stock", lang)
                                    if in_stock
                                    else t("label_out_of_stock", lang)
                                ),
                                variant="success" if in_stock else "secondary",
                            )

            # ── Description ───────────────────────────────────────────────────
            if short_desc:
                with Card(cssClass=f"{_AG_RADIUS}"):
                    with CardContent(cssClass="px-4 py-3"):
                        Muted(
                            short_desc,
                            cssClass="text-sm leading-relaxed",
                        )

            # ── Add to cart hint ──────────────────────────────────────────────
            with Card(
                cssClass=f"{_AG_RADIUS} border-l-[4px] border-l-[{_AG_BFU}]"
                f" dark:border-l-[{_DK.BFU}]"
            ):
                with CardContent(cssClass="p-3"):
                    Muted(
                        t("label_add_to_cart_hint", lang),
                        cssClass="text-xs uppercase tracking-[0.15em]",
                    )
                    Muted(
                        f'create_checkout_session(items=[{{"product_id": {product_id}, "quantity": 1}}])',
                        cssClass="text-xs font-mono mt-1",
                    )

            # ── Online link ───────────────────────────────────────────────────
            if permalink:
                Separator(cssClass="my-1")
                Muted(
                    f"{t('label_view_online', lang)}: {permalink}",
                    cssClass="text-[10px] text-center break-all",
                )

    return PrefabApp(
        view=view,
        state={
            "product_id": product_id,
            "name": product.get("name"),
            "price_chf": product.get("price_chf"),
            "in_stock": product.get("stock_status") == "instock",
        },
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )
