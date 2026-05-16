# Release Notes: aareguru-mcp v4.7.1

**Release Date**: May 16, 2026
**Previous Version**: v4.7.0
**Status**: Stable, Production Ready

---

## Executive Summary

aareguru-mcp v4.7.1 completes the shop experience. A new `product_view`
FastMCPApp renders product detail pages with a full image carousel. Two new MCP
prompts (`shop-browse`, `shop-checkout`) guide the AI through the full purchase
flow — from catalog browsing and product inspection to billing, confirmation,
and payment. 433 tests, 80% coverage. No breaking changes.

---

## What's Changed

### New FastMCPApp: `product_view`

A 10th FastMCPApp (`apps/shop_product.py`) shows a product detail page for any
item in the konsum.aare.guru catalog.

**Layout:**

| Section | Content |
| --- | --- |
| Header | Product name — uppercase, aare.guru primary color |
| Image(s) | Single image or looping Carousel with pagination dots |
| Price strip | CHF amount + On Sale badge + In Stock / Out of Stock badge |
| Description | Short description from WooCommerce |
| Add-to-cart hint | Exact `create_checkout_session(...)` call, teal left-border card |
| Link | Permalink to the product page on konsum.aare.guru |

**Image handling:**

- One image → `Image` component (full-width, `max-h-72`)
- Two or more images → `Carousel` (looping, pagination dots, height 288 px)
- No images → layout renders without image section

Supports `lang=` (de / en / fr / it). 9 new i18n keys added across all locales
(`page_product`, `label_price`, `label_in_stock`, `label_out_of_stock`,
`label_on_sale`, `label_add_to_cart_hint`, `label_view_online`,
`alert_product_not_found`, `alert_product_not_found_desc`).

**Invocation:** `product_view(product_id=<id>, lang?)`

### New MCP prompts: `shop-browse` and `shop-checkout`

Two new guided-workflow prompts complete the shopping experience.

#### `shop-browse`

| Parameter | Type | Description |
| --- | --- | --- |
| `search` | `str \| None` | Optional keyword filter (e.g. `"swim buoy"`) |

Instructs the AI to call `list_shop_products`, present results with prices and
stock status, call `product_view` to show images and full details for items the
user is interested in, and offer to start a purchase.

#### `shop-checkout`

| Parameter | Type | Description |
| --- | --- | --- |
| `items` | `str` | Optional description of what the user wants (e.g. `"swim buoy × 1"`) |

Walks the complete UCP purchase flow:

1. Browse catalog and inspect product via `product_view` (with images)
2. `create_checkout_session` + show cart with `shop_cart_view`
3. Collect billing details from the user
4. `update_checkout_session` + show updated cart
5. Explicit user confirmation before placing order
6. `complete_checkout` → display PostFinance payment link

---

## Metrics

| Metric | v4.7.0 | v4.7.1 |
| --- | --- | --- |
| Tests passing | 429 | 433 |
| Coverage | 80% | 80% |
| MCP tools | 12 | 12 |
| MCP resources | 8 | 8 |
| MCP prompts | 3 | 5 |
| FastMCPApps | 9 | 10 |
| App views | 13 | 14 |

---

## Document Inventory (post-release)

| Document | Purpose |
| --- | --- |
| `README.md` | Installation, quick start, configuration |
| `SKILLS.md` | Capability reference (tools, resources, prompts, apps) |
| `CONSTITUTION.md` | Project governance, principles, constraints |
| `ARCHITECTURE.md` | Layer design, data flow, patterns |
| `specs/ADR_COMPENDIUM.md` | 18 Architecture Decision Records |
| `docs/USER_QUESTIONS_SLIDES.md` | 130-question test suite |
| `docs/DEPLOYMENT.md` | FastMCP Cloud deployment guide |
| `docs/RELEASE_NOTES_v4.7.1.md` | This document |
