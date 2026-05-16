"""Pydantic models for WooCommerce Store API responses and UCP checkout sessions.

WooCommerce response models parse the /wp-json/wc/store/v1/ API.
UCP checkout session models follow Universal Commerce Protocol semantics
(https://ucp.dev/specification/checkout-rest/) adapted for our WooCommerce transport.
"""

from typing import Any

from pydantic import BaseModel, Field


class ShopPrice(BaseModel):
    value: str
    currency_code: str = "CHF"


class ShopImage(BaseModel):
    src: str
    alt: str = ""


class ShopProduct(BaseModel):
    id: int
    name: str
    slug: str
    permalink: str
    short_description: str = ""
    prices: ShopPrice
    images: list[ShopImage] = Field(default_factory=list)
    on_sale: bool = False
    stock_status: str = "instock"


class ShopCartItem(BaseModel):
    key: str
    id: int
    name: str
    quantity: int
    prices: ShopPrice


class ShopCart(BaseModel):
    items: list[ShopCartItem] = Field(default_factory=list)
    totals: ShopPrice = Field(
        default_factory=lambda: ShopPrice(value="0", currency_code="CHF")
    )


class ShopOrder(BaseModel):
    id: int
    status: str
    payment_url: str = ""


# UCP-shaped checkout session
# Mirrors UCP Checkout fields (id, status, currency, line_items, totals, continue_url)
# without requiring full UCP protocol stack against this store.


class UCPLineItem(BaseModel):
    id: str
    product_id: int
    name: str
    quantity: int
    unit_price_chf: float
    total_chf: float


class UCPCheckoutSession(BaseModel):
    session_id: str
    status: str = "incomplete"
    currency: str = "CHF"
    line_items: list[UCPLineItem] = Field(default_factory=list)
    subtotal_chf: float = 0.0
    total_chf: float = 0.0
    billing: dict[str, Any] = Field(default_factory=dict)
    shipping: dict[str, Any] = Field(default_factory=dict)
    continue_url: str | None = None
    order_id: int | None = None
