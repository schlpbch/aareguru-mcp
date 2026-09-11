"""App: Full merchandise catalog view for konsum.aare.guru."""

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
    Grid,
    Image,
    Link,
    Muted,
    Text,
)

from ._constants import (
    _AG_RADIUS,
    _AG_TXT_PRIMARY,
    _DK,
    _FONT_CSS,
    _FONT_INJECTION_ON_MOUNT,
)
from ._i18n import t

logger = structlog.get_logger(__name__)

shop_catalog_app = FastMCPApp("shop-catalog")


@shop_catalog_app.tool()
async def refresh_shop_catalog(search: str | None = None) -> dict[str, Any]:
    """Refresh the merchandise catalog, optionally filtered by search term (called from UI)."""
    from aareguru_mcp.shop_service import ShopService

    service = ShopService()
    return await service.list_products(search)


@shop_catalog_app.ui()
async def shop_catalog_view(search: str = "", lang: str = "de") -> PrefabApp:
    """Show the full konsum.aare.guru merchandise catalog as a browsable grid.

    Displays every available product with thumbnail, name, price, and stock/
    sale status. Use this for "what merch is there?" or "show me the shop"
    questions. Use get_shop_product / product_view for details on one item,
    and create_checkout_session to start a purchase.

    Args:
        search: Optional search term to filter products (e.g. 'towel', 'cap').
                Leave empty to show the full catalog.
    """
    logger.info("app.shop_catalog_view", search=search or "(all)")
    from aareguru_mcp.shop_service import ShopService

    service = ShopService()
    result = await service.list_products(search or None)
    products: list[dict[str, Any]] = result.get("products", [])

    with Column(gap=0, css_class="p-2 max-w-3xl mx-auto") as view:

        # ── Header ───────────────────────────────────────────────────────────
        Text(
            t("page_shop_catalog", lang),
            css_class=(
                f"text-base font-black tracking-tight uppercase text-center"
                f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
            ),
        )

        if not products:
            with Alert(variant="warning", css_class=f"{_AG_RADIUS} mt-2"):
                AlertTitle(t("alert_no_products", lang))
                AlertDescription(t("alert_no_products_desc", lang))
        else:
            with Grid(columns={"default": 2, "md": 3}, gap=3, css_class="mt-2"):
                for product in products:
                    _render_product_card(product, lang)

    return PrefabApp(
        view=view,
        state={
            "search": search,
            "count": len(products),
        },
        stylesheets=[_FONT_CSS],
        on_mount=_FONT_INJECTION_ON_MOUNT,
    )


def _render_product_card(product: dict[str, Any], lang: str) -> None:
    """Render a single product tile: thumbnail, name, price, badges, view link."""
    name: str = product.get("name", "")
    price_chf: float = product.get("price_chf", 0.0)
    on_sale: bool = product.get("on_sale", False)
    stock_status: str = product.get("stock_status", "instock")
    image_url: str | None = product.get("image_url")
    permalink: str = product.get("permalink", "")
    in_stock = stock_status == "instock"

    with Card(css_class=f"{_AG_RADIUS} overflow-hidden flex flex-col"):
        if image_url:
            Image(
                src=image_url,
                alt=name,
                css_class="w-full object-cover h-32",
            )
        with CardContent(css_class="p-2 flex-1 flex flex-col gap-1"):
            Text(
                name,
                css_class=(
                    f"text-xs font-bold leading-tight line-clamp-2"
                    f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                ),
            )
            Text(
                f"CHF {price_chf:.2f}",
                css_class=(
                    f"text-sm font-black tabular-nums"
                    f" text-[{_AG_TXT_PRIMARY}] dark:text-[{_DK.TXT_PRIMARY}]"
                ),
            )
            if on_sale or not in_stock:
                Muted(
                    (
                        t("label_on_sale", lang)
                        if on_sale
                        else t("label_out_of_stock", lang)
                    ),
                    css_class=(
                        f"text-[10px] font-bold uppercase"
                        f" {'text-red-600 dark:text-red-400' if on_sale else ''}"
                    ),
                )
            if permalink:
                Link(
                    t("label_view_online", lang),
                    href=permalink,
                    target="_blank",
                    css_class="text-[10px] mt-auto pt-1",
                )
