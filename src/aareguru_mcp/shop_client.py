"""WooCommerce Store API client for konsum.aare.guru.

Singleton async HTTP client that maintains a nonce and Cart-Token so cart
state is preserved across consecutive tool calls within a server session.

The store no longer relies on cookies for cart identity (no Set-Cookie is
sent); instead the Store API issues a JWT `Cart-Token` response header that
must be echoed back as a request header on every subsequent call, or writes
(add-item, cart/items DELETE, checkout) are rejected with 401 Unauthorized
even with a valid nonce.
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
        self._cart_token: str | None = None
        self._init_lock: asyncio.Lock = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "ShopClient":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _capture_session_headers(self, resp: httpx.Response) -> None:
        """Capture the rolling Nonce and Cart-Token from any Store API response."""
        nonce = resp.headers.get("Nonce") or resp.headers.get("X-WC-Store-API-Nonce")
        if nonce:
            self._nonce = nonce
        cart_token = resp.headers.get("Cart-Token")
        if cart_token:
            self._cart_token = cart_token

    async def _ensure_nonce(self) -> None:
        """Fetch and cache the Nonce and Cart-Token required for write operations."""
        if self._nonce is not None and self._cart_token is not None:
            return
        async with self._init_lock:
            if self._nonce is not None and self._cart_token is not None:
                return
            resp = await self._http.get(f"{_STORE_API}/cart")
            resp.raise_for_status()
            self._capture_session_headers(resp)
            logger.info(
                "shop_client.session_initialized",
                nonce_present=self._nonce is not None,
                cart_token_present=self._cart_token is not None,
            )

    def _write_headers(self) -> dict[str, str]:
        headers = {"X-WC-Store-API-Nonce": self._nonce or ""}
        if self._cart_token:
            headers["Cart-Token"] = self._cart_token
        return headers

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
        resp = await self._http.get(f"{_STORE_API}/cart", headers=self._write_headers())
        resp.raise_for_status()
        self._capture_session_headers(resp)
        data: dict[str, Any] = resp.json()
        return data

    async def clear_cart(self) -> None:
        await self._ensure_nonce()
        resp = await self._http.delete(
            f"{_STORE_API}/cart/items",
            headers=self._write_headers(),
        )
        resp.raise_for_status()
        self._capture_session_headers(resp)

    async def add_to_cart(self, product_id: int, quantity: int = 1) -> dict[str, Any]:
        await self._ensure_nonce()
        resp = await self._http.post(
            f"{_STORE_API}/cart/add-item",
            json={"id": product_id, "quantity": quantity},
            headers=self._write_headers(),
        )
        resp.raise_for_status()
        self._capture_session_headers(resp)
        data: dict[str, Any] = resp.json()
        return data

    async def _default_payment_method(self) -> str:
        """Look up the store's current default payment gateway ID.

        PostFinance Checkout registers one WooCommerce gateway ID per payment
        method (e.g. "postfinancecheckout_6" for a specific card/wallet
        option), not a single "postfinance_checkout" ID — and the numbering
        is store-config-dependent. The checkout draft (GET /checkout)
        reports the store's current default, so that's used rather than a
        hardcoded value that can silently go stale.
        """
        resp = await self._http.get(
            f"{_STORE_API}/checkout", headers=self._write_headers()
        )
        resp.raise_for_status()
        self._capture_session_headers(resp)
        data: dict[str, Any] = resp.json()
        method = data.get("payment_method")
        return str(method) if method else ""

    async def submit_checkout(
        self,
        billing: dict[str, Any],
        shipping: dict[str, Any],
        payment_method: str | None = None,
    ) -> dict[str, Any]:
        await self._ensure_nonce()
        if payment_method is None:
            payment_method = await self._default_payment_method()
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
        self._capture_session_headers(resp)
        data: dict[str, Any] = resp.json()
        return data

    async def close(self) -> None:
        await self._http.aclose()
