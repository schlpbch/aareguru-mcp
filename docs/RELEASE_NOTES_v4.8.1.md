# Release Notes: v4.8.1

**Date**: 2026-09-11

## Shop UI Polish: Customer-Facing Cart & Product Views

**What changed**: The `shop_cart_view` and `product_view` FastMCPApp UIs
were built for a developer testing the tools, not a customer using them:
no product images in the cart, raw tool-call code shown as
"instructions" (e.g. `update_checkout_session("...", billing={...})`),
and the payment/product permalink URLs rendered as plain unclickable
text.

**Fix**:

- **Product thumbnails in the cart.** Each line item now shows a
  thumbnail image, name, quantity × unit price, and line total in a
  simple row layout, instead of a bare data table with no visuals.
  `UCPLineItem` gained an `image_url` field, populated from the
  product's first WooCommerce image in `create_checkout_session`.
- **Plain-language guidance instead of code.** The "next steps"
  (incomplete cart), "ready to complete" (billing attached), and
  "add to cart" (product view) sections no longer print raw Python
  tool-call syntax at the customer — they read as normal instructions.
- **Real clickable links.** The payment URL is now a styled,
  button-like `Link` component that opens in a new tab, instead of a
  raw URL string; the product permalink is a proper clickable link too.
- All strings reworded/added across all 4 supported locales
  (de/en/fr/it).

**Verified live** against a running `aareguru-mcp-http` server:
`product_view` renders the image carousel correctly, `shop_cart_view`
renders the thumbnail and a real payment `Link`, and no tool-call
syntax appears in either rendered view.

## Test Coverage

- 483 tests passing (12 new, in `tests/test_apps_shop.py`, covering all
  cart states — empty, incomplete, ready, completed — and `product_view`)
- 84% code coverage (up from 81%)
- `mypy`, `ruff`, and `black` all clean

## Files Changed

- `src/aareguru_mcp/shop_models.py` — added `image_url` to `UCPLineItem`
- `src/aareguru_mcp/shop_service.py` — populate `image_url` in
  `create_checkout_session`
- `src/aareguru_mcp/apps/shop.py` — thumbnail cart rows, plain-language
  hints, clickable payment `Link`
- `src/aareguru_mcp/apps/shop_product.py` — plain-language add-to-cart
  hint (shown only when in stock), clickable permalink `Link`
- `src/aareguru_mcp/apps/_i18n.py` — reworded/added strings for all 4
  locales
- `tests/test_apps_shop.py` — new regression tests
- `CLAUDE.md`, `README.md` — test count/coverage, version, release notes

---

**Summary**: Pure UI polish for the shop/checkout experience — no
service-layer or protocol changes, no breaking changes for consumers of
this MCP server.
