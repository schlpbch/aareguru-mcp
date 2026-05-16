"""WooCommerce Store API client for konsum.aare.guru.

Singleton async HTTP client that maintains a persistent cookie jar and nonce
so cart state is preserved across consecutive tool calls within a server session.
"""

import asyncio
from typing import Any

import httpx
import structlog

logger = structlog.get_logger(__name__)

_STORE_API = "https://konsum.aare.guru/wp-json/wc/store/v1"


class ShopClient:
    """Singleton async client for the WooCommerce Store API.

    Usage:
        client = ShopClient.get_instance()
        products = await client.get_products()
    """

    _instance: "ShopClient | None" = None

    def __init__(self) -> None:
        self._http: httpx.AsyncClient = httpx.AsyncClient(
            follow_redirects=True,
            timeout=10.0,
            headers={"Content-Type": "application/json"},
        )
        self._nonce: str | None = None
        self._init_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "ShopClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def _ensure_nonce(self) -> None:
        """Fetch and cache the Nonce required for write operations."""
        if self._nonce is not None:
            return
        async with self._init_lock:
            if self._nonce is not None:
                return
            resp = await self._http.get(f"{_STORE_API}/cart")
            resp.raise_for_status()
            self._nonce = resp.headers.get("Nonce") or resp.headers.get(
                "X-WC-Store-API-Nonce"
            )
            logger.info(
                "shop_client.nonce_fetched", nonce_present=self._nonce is not None
            )

    def _write_headers(self) -> dict[str, str]:
        return {"Nonce": self._nonce or ""}

    async def get_products(
        self, search: str | None = None, per_page: int = 20
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"per_page": per_page}
        if search:
            params["search"] = search
        resp = await self._http.get(f"{_STORE_API}/products", params=params)
        resp.raise_for_status()
        data: list[dict[str, Any]] = resp.json()
        return data

    async def get_product(self, product_id: int) -> dict[str, Any]:
        resp = await self._http.get(f"{_STORE_API}/products/{product_id}")
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    async def get_cart(self) -> dict[str, Any]:
        resp = await self._http.get(f"{_STORE_API}/cart")
        resp.raise_for_status()
        nonce = resp.headers.get("Nonce") or resp.headers.get("X-WC-Store-API-Nonce")
        if nonce:
            self._nonce = nonce
        data: dict[str, Any] = resp.json()
        return data

    async def clear_cart(self) -> None:
        await self._ensure_nonce()
        resp = await self._http.delete(
            f"{_STORE_API}/cart/items",
            headers=self._write_headers(),
        )
        resp.raise_for_status()

    async def add_to_cart(self, product_id: int, quantity: int = 1) -> dict[str, Any]:
        await self._ensure_nonce()
        resp = await self._http.post(
            f"{_STORE_API}/cart/add-item",
            json={"id": product_id, "quantity": quantity},
            headers=self._write_headers(),
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    async def submit_checkout(
        self,
        billing: dict[str, Any],
        shipping: dict[str, Any],
        payment_method: str = "postfinance_checkout",
    ) -> dict[str, Any]:
        await self._ensure_nonce()
        resp = await self._http.post(
            f"{_STORE_API}/checkout",
            json={
                "billing_address": billing,
                "shipping_address": shipping,
                "payment_method": payment_method,
                "customer_note": "",
            },
            headers=self._write_headers(),
        )
        resp.raise_for_status()
        data: dict[str, Any] = resp.json()
        return data

    async def close(self) -> None:
        await self._http.aclose()
