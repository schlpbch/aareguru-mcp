"""Tests for the shop_catalog_view FastMCPApp (browsable merchandise grid)."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from prefab_ui.app import PrefabApp

from aareguru_mcp.apps.shop_catalog import shop_catalog_view

_PRODUCTS = [
    {
        "id": 147,
        "name": "Aare Guru Badetuch",
        "price_chf": 39.0,
        "permalink": "https://konsum.aare.guru/shop/badetuch/",
        "on_sale": True,
        "stock_status": "instock",
        "image_url": "https://konsum.aare.guru/img/towel.jpg",
    },
    {
        "id": 3552,
        "name": "Merino Gfrörli Chappe",
        "price_chf": 25.0,
        "permalink": "https://konsum.aare.guru/shop/chappe/",
        "on_sale": False,
        "stock_status": "outofstock",
        "image_url": None,
    },
]


class TestShopCatalogView:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.list_products = AsyncMock(
                return_value={"products": _PRODUCTS, "count": 2}
            )
            result = await shop_catalog_view("", "en")
        assert isinstance(result, PrefabApp)
        assert result.state["count"] == 2

    @pytest.mark.asyncio
    async def test_search_is_passed_through(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            mock_svc = MockService.return_value
            mock_svc.list_products = AsyncMock(
                return_value={"products": _PRODUCTS, "count": 2}
            )
            await shop_catalog_view("towel", "en")
        mock_svc.list_products.assert_called_once_with("towel")

    @pytest.mark.asyncio
    async def test_renders_thumbnails_and_links(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.list_products = AsyncMock(
                return_value={"products": _PRODUCTS, "count": 2}
            )
            result = await shop_catalog_view("", "en")
        rendered = json.dumps(result.to_json())
        assert '"type": "Image"' in rendered
        assert "https://konsum.aare.guru/img/towel.jpg" in rendered
        assert '"type": "Link"' in rendered
        assert '"href": "https://konsum.aare.guru/shop/badetuch/"' in rendered

    @pytest.mark.asyncio
    async def test_shows_sale_and_stock_badges(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.list_products = AsyncMock(
                return_value={"products": _PRODUCTS, "count": 2}
            )
            result = await shop_catalog_view("", "en")
        rendered = json.dumps(result.to_json())
        assert "On Sale" in rendered
        assert "Out of Stock" in rendered

    @pytest.mark.asyncio
    async def test_missing_image_does_not_raise(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.list_products = AsyncMock(
                return_value={"products": [_PRODUCTS[1]], "count": 1}
            )
            result = await shop_catalog_view("", "en")
        assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_empty_results_shows_alert(self):
        with patch("aareguru_mcp.shop_service.ShopService") as MockService:
            MockService.return_value.list_products = AsyncMock(
                return_value={"products": [], "count": 0}
            )
            result = await shop_catalog_view("nonexistent", "en")
        rendered = json.dumps(result.to_json())
        assert "No Products Found" in rendered
        assert result.state["count"] == 0
