"""Tests for the shop cart and product-detail FastMCPApp views.

Verifies the visual-polish pass: product thumbnails in the cart, plain-
language guidance instead of raw tool-call code snippets, and real
clickable links for the payment URL and product permalink.
"""

import json
from unittest.mock import AsyncMock, patch

import pytest
from prefab_ui.app import PrefabApp

from aareguru_mcp.apps.shop import shop_cart_view
from aareguru_mcp.apps.shop_product import product_view

_BILLING = {
    "first_name": "Hans",
    "last_name": "Muster",
    "email": "hans@example.ch",
    "address_1": "Bahnhofplatz 1",
    "postcode": "3011",
    "city": "Bern",
    "country": "CH",
}


def _session(**overrides):
    base = {
        "session_id": "s1",
        "status": "incomplete",
        "total_chf": 39.0,
        "line_items": [
            {
                "name": "Aare Guru Badetuch",
                "quantity": 1,
                "unit_price_chf": 39.0,
                "total_chf": 39.0,
                "image_url": "https://konsum.aare.guru/img/towel.jpg",
            }
        ],
        "billing": {},
        "order_id": None,
        "continue_url": None,
    }
    base.update(overrides)
    return base


class TestShopCartViewEmpty:
    @pytest.mark.asyncio
    async def test_empty_state_returns_prefab_app(self):
        result = await shop_cart_view("", "en")
        assert isinstance(result, PrefabApp)
        assert result.state["session_id"] == ""

    @pytest.mark.asyncio
    async def test_empty_state_has_no_tool_names(self):
        result = await shop_cart_view("", "en")
        rendered = json.dumps(result.to_json())
        assert "list_shop_products" not in rendered
        assert "create_checkout_session" not in rendered


class TestShopCartViewIncomplete:
    @pytest.mark.asyncio
    async def test_shows_item_thumbnail(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_session = AsyncMock(return_value=_session())
            result = await shop_cart_view("s1", "en")
        rendered = json.dumps(result.to_json())
        assert '"type": "Image"' in rendered
        assert "https://konsum.aare.guru/img/towel.jpg" in rendered

    @pytest.mark.asyncio
    async def test_missing_image_does_not_raise(self):
        session = _session()
        session["line_items"][0]["image_url"] = None
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_session = AsyncMock(return_value=session)
            result = await shop_cart_view("s1", "en")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_next_steps_use_plain_language_not_code(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_session = AsyncMock(return_value=_session())
            result = await shop_cart_view("s1", "en")
        rendered = json.dumps(result.to_json())
        assert "update_checkout_session" not in rendered
        assert "complete_checkout" not in rendered
        assert "Provide your delivery address" in rendered


class TestShopCartViewReadyForComplete:
    @pytest.mark.asyncio
    async def test_shows_billing_without_code_snippet(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_session = AsyncMock(
                return_value=_session(status="ready_for_complete", billing=_BILLING)
            )
            result = await shop_cart_view("s1", "en")
        rendered = json.dumps(result.to_json())
        assert "Hans Muster" in rendered
        assert "complete_checkout" not in rendered
        assert "Ready to order" in rendered


class TestShopCartViewCompleted:
    @pytest.mark.asyncio
    async def test_payment_link_is_a_real_clickable_link(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_session = AsyncMock(
                return_value=_session(
                    status="completed",
                    billing=_BILLING,
                    order_id=42,
                    continue_url="https://pay.example.com/42",
                )
            )
            result = await shop_cart_view("s1", "en")
        rendered = json.dumps(result.to_json())
        assert '"type": "Link"' in rendered
        assert '"href": "https://pay.example.com/42"' in rendered
        assert "Open Payment" in rendered

    @pytest.mark.asyncio
    async def test_no_continue_url_does_not_raise(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_session = AsyncMock(
                return_value=_session(status="completed", billing=_BILLING, order_id=42)
            )
            result = await shop_cart_view("s1", "en")
        assert isinstance(result, PrefabApp)


_PRODUCT = {
    "id": 147,
    "name": "Aare Guru Badetuch",
    "price_chf": 39.0,
    "permalink": "https://konsum.aare.guru/shop/badetuch/",
    "description": "Full description",
    "short_description": "Short description",
    "on_sale": False,
    "stock_status": "instock",
    "images": ["https://konsum.aare.guru/img/towel.jpg"],
}


class TestProductView:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_product = AsyncMock(return_value=_PRODUCT)
            result = await product_view(147, "en")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_permalink_is_a_real_clickable_link(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_product = AsyncMock(return_value=_PRODUCT)
            result = await product_view(147, "en")
        rendered = json.dumps(result.to_json())
        assert '"type": "Link"' in rendered
        assert '"href": "https://konsum.aare.guru/shop/badetuch/"' in rendered

    @pytest.mark.asyncio
    async def test_add_to_cart_hint_has_no_raw_code(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_product = AsyncMock(return_value=_PRODUCT)
            result = await product_view(147, "en")
        rendered = json.dumps(result.to_json())
        assert "create_checkout_session" not in rendered

    @pytest.mark.asyncio
    async def test_out_of_stock_hides_add_to_cart_hint(self):
        product = dict(_PRODUCT, stock_status="outofstock")
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.get_product = AsyncMock(return_value=product)
            result = await product_view(147, "en")
        rendered = json.dumps(result.to_json())
        assert "Ask me to add this product to your cart." not in rendered
