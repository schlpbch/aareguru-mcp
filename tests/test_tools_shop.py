"""Tests for shopping tools (konsum.aare.guru / UCP checkout).

Mocks ShopClient at the service layer boundary so no real HTTP requests are made.
"""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp import tools


def _make_wc_product(product_id: int = 1, name: str = "Test Product") -> dict[str, Any]:
    return {
        "id": product_id,
        "name": name,
        "slug": "test-product",
        "permalink": f"https://konsum.aare.guru/product/{product_id}",
        "prices": {"price": "4900", "currency_code": "CHF"},
        "images": [{"src": "https://example.com/img.jpg", "alt": ""}],
        "on_sale": False,
        "stock_status": "instock",
        "short_description": "A test product",
        "description": "Full description",
    }


def _make_mock_client(product: dict[str, Any] | None = None) -> MagicMock:
    p = product or _make_wc_product()
    client = MagicMock()
    client.get_products = AsyncMock(return_value=[p])
    client.get_product = AsyncMock(return_value=p)
    client.clear_cart = AsyncMock()
    client.add_to_cart = AsyncMock(return_value={"key": "abc123", "id": p["id"]})
    client.submit_checkout = AsyncMock(
        return_value={"id": 999, "status": "pending", "payment_url": "https://pay.example.com/999"}
    )
    client.close = AsyncMock()
    return client


class TestListShopProducts:
    @pytest.mark.asyncio
    async def test_returns_catalog(self) -> None:
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = _make_mock_client()
            result = await tools.list_shop_products()
        assert result["count"] == 1
        assert result["products"][0]["name"] == "Test Product"
        assert result["products"][0]["price_chf"] == 49.0

    @pytest.mark.asyncio
    async def test_search_passed_to_client(self) -> None:
        mock_client = _make_mock_client()
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = mock_client
            await tools.list_shop_products(search="towel")
        mock_client.get_products.assert_called_once_with(search="towel")

    @pytest.mark.asyncio
    async def test_error_returns_error_dict(self) -> None:
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            bad_client = MagicMock()
            bad_client.get_products = AsyncMock(side_effect=Exception("network error"))
            MockClient.get_instance.return_value = bad_client
            result = await tools.list_shop_products()
        assert "error" in result


class TestGetShopProduct:
    @pytest.mark.asyncio
    async def test_returns_product_details(self) -> None:
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = _make_mock_client()
            result = await tools.get_shop_product(1)
        assert result["id"] == 1
        assert result["price_chf"] == 49.0
        assert "description" in result


class TestCreateCheckoutSession:
    @pytest.mark.asyncio
    async def test_creates_session_with_session_id(self) -> None:
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = _make_mock_client()
            result = await tools.create_checkout_session(
                [{"product_id": 1, "quantity": 2}]
            )
        assert "session_id" in result
        assert result["status"] == "incomplete"
        assert result["currency"] == "CHF"
        assert len(result["line_items"]) == 1
        assert result["line_items"][0]["quantity"] == 2
        assert result["total_chf"] == 98.0

    @pytest.mark.asyncio
    async def test_clears_cart_before_adding(self) -> None:
        mock_client = _make_mock_client()
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = mock_client
            await tools.create_checkout_session([{"product_id": 1, "quantity": 1}])
        mock_client.clear_cart.assert_called_once()
        mock_client.add_to_cart.assert_called_once_with(1, 1)


class TestUpdateCheckoutSession:
    @pytest.mark.asyncio
    async def test_stores_billing_and_advances_status(self) -> None:
        mock_client = _make_mock_client()
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = mock_client
            create_result = await tools.create_checkout_session(
                [{"product_id": 1, "quantity": 1}]
            )
            session_id = create_result["session_id"]
            billing = {
                "first_name": "Hans",
                "last_name": "Muster",
                "email": "hans@example.ch",
                "address_1": "Musterstrasse 1",
                "city": "Bern",
                "postcode": "3000",
                "country": "CH",
            }
            update_result = await tools.update_checkout_session(session_id, billing)
        assert update_result["status"] == "ready_for_complete"
        assert update_result["billing"]["first_name"] == "Hans"

    @pytest.mark.asyncio
    async def test_unknown_session_returns_error(self) -> None:
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = _make_mock_client()
            result = await tools.update_checkout_session("nonexistent-id", {})
        assert "error" in result


class TestCompleteCheckout:
    @pytest.mark.asyncio
    async def test_returns_payment_url(self) -> None:
        mock_client = _make_mock_client()
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = mock_client
            create = await tools.create_checkout_session([{"product_id": 1, "quantity": 1}])
            session_id = create["session_id"]
            billing = {
                "first_name": "Hans",
                "last_name": "Muster",
                "email": "hans@example.ch",
                "address_1": "Bahnhofplatz 1",
                "city": "Bern",
                "postcode": "3011",
                "country": "CH",
            }
            await tools.update_checkout_session(session_id, billing)
            result = await tools.complete_checkout(session_id)
        assert result["status"] == "completed"
        assert result["continue_url"] == "https://pay.example.com/999"
        assert result["order_id"] == 999


class TestCancelCheckoutSession:
    @pytest.mark.asyncio
    async def test_cancels_and_clears_cart(self) -> None:
        mock_client = _make_mock_client()
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = mock_client
            create = await tools.create_checkout_session([{"product_id": 1, "quantity": 1}])
            session_id = create["session_id"]
            result = await tools.cancel_checkout_session(session_id)
        assert result["status"] == "canceled"
        assert result["session_id"] == session_id
        mock_client.clear_cart.assert_called()

    @pytest.mark.asyncio
    async def test_unknown_session_returns_error(self) -> None:
        with patch("aareguru_mcp.shop_service.ShopClient") as MockClient:
            MockClient.get_instance.return_value = _make_mock_client()
            result = await tools.cancel_checkout_session("bad-id")
        assert "error" in result
