"""Business logic service for konsum.aare.guru shopping.

Maps UCP checkout-session semantics (create / update / complete / cancel)
onto the WooCommerce Store API via ShopClient.
"""

import uuid
from typing import Any

import structlog

from .shop_client import ShopClient
from .shop_models import UCPCheckoutSession, UCPLineItem

logger = structlog.get_logger(__name__)

# In-memory UCP checkout session store (keyed by session_id)
_checkout_sessions: dict[str, UCPCheckoutSession] = {}


def _parse_price(prices: dict[str, Any]) -> float:
    """Convert WooCommerce price string to CHF float.

    WooCommerce returns prices as strings in minor units (cents × 10),
    e.g. "4900" for CHF 49.00. Divide by 100 to get CHF.
    """
    raw = prices.get("price", prices.get("total_price", "0"))
    try:
        return int(str(raw)) / 100
    except (ValueError, TypeError):
        return 0.0


class ShopService:
    """Shopping service mapping UCP checkout semantics onto WooCommerce Store API.

    Usage:
        service = ShopService()
        result = await service.list_products()
    """

    def __init__(self) -> None:
        self.client = ShopClient.get_instance()

    async def list_products(self, search: str | None = None) -> dict[str, Any]:
        logger.info("shop_service.list_products", search=search)
        raw = await self.client.get_products(search=search)
        products = []
        for p in raw:
            images: list[dict[str, Any]] = p.get("images", [])
            products.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "price_chf": _parse_price(p.get("prices", {})),
                    "permalink": p.get("permalink", ""),
                    "short_description": p.get("short_description", ""),
                    "on_sale": p.get("on_sale", False),
                    "stock_status": p.get("stock_status", "instock"),
                    "image_url": images[0]["src"] if images else None,
                }
            )
        return {"products": products, "count": len(products)}

    async def get_product(self, product_id: int) -> dict[str, Any]:
        logger.info("shop_service.get_product", product_id=product_id)
        p = await self.client.get_product(product_id)
        images: list[dict[str, Any]] = p.get("images", [])
        return {
            "id": p["id"],
            "name": p["name"],
            "price_chf": _parse_price(p.get("prices", {})),
            "permalink": p.get("permalink", ""),
            "description": p.get("description", ""),
            "short_description": p.get("short_description", ""),
            "on_sale": p.get("on_sale", False),
            "stock_status": p.get("stock_status", "instock"),
            "images": [img["src"] for img in images],
        }

    async def create_checkout_session(
        self, items: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """UCP: create a new checkout session, adding items to the WooCommerce cart."""
        logger.info("shop_service.create_checkout_session", item_count=len(items))

        await self.client.clear_cart()

        line_items: list[UCPLineItem] = []
        for item in items:
            product_id = int(item["product_id"])
            quantity = int(item.get("quantity", 1))

            await self.client.add_to_cart(product_id, quantity)
            product = await self.client.get_product(product_id)
            price = _parse_price(product.get("prices", {}))

            line_items.append(
                UCPLineItem(
                    id=str(uuid.uuid4()),
                    product_id=product_id,
                    name=product.get("name", ""),
                    quantity=quantity,
                    unit_price_chf=price,
                    total_chf=round(price * quantity, 2),
                )
            )

        total = round(sum(li.total_chf for li in line_items), 2)
        session = UCPCheckoutSession(
            session_id=str(uuid.uuid4()),
            status="incomplete",
            currency="CHF",
            line_items=line_items,
            subtotal_chf=total,
            total_chf=total,
        )
        _checkout_sessions[session.session_id] = session
        logger.info("shop_service.session_created", session_id=session.session_id)
        return session.model_dump()

    async def update_checkout_session(
        self,
        session_id: str,
        billing: dict[str, Any],
        shipping: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """UCP: attach billing/shipping address to the session."""
        logger.info("shop_service.update_checkout_session", session_id=session_id)
        session = _checkout_sessions.get(session_id)
        if session is None:
            return {"error": f"Session '{session_id}' not found."}
        session.billing = billing
        session.shipping = shipping or billing
        session.status = "ready_for_complete"
        return session.model_dump()

    async def complete_checkout(self, session_id: str) -> dict[str, Any]:
        """UCP: submit order to WooCommerce, return payment URL."""
        logger.info("shop_service.complete_checkout", session_id=session_id)
        session = _checkout_sessions.get(session_id)
        if session is None:
            return {"error": f"Session '{session_id}' not found."}
        if not session.billing:
            return {
                "error": "Billing address required. Call update_checkout_session first."
            }

        order = await self.client.submit_checkout(
            billing=session.billing,
            shipping=session.shipping or session.billing,
        )
        session.status = "completed"
        session.order_id = order.get("id")
        session.continue_url = order.get("payment_url")
        return session.model_dump()

    async def cancel_checkout_session(self, session_id: str) -> dict[str, Any]:
        """UCP: cancel session and clear the WooCommerce cart."""
        logger.info("shop_service.cancel_checkout_session", session_id=session_id)
        session = _checkout_sessions.pop(session_id, None)
        if session is None:
            return {"error": f"Session '{session_id}' not found."}
        await self.client.clear_cart()
        return {"session_id": session_id, "status": "canceled"}
