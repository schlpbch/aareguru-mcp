# Release Notes: v4.8.0

**Date**: 2026-09-11

## Dependency Upgrade

### FastMCP 3.x → 4.x

**What changed**: Upgraded `fastmcp[apps]` from 3.3.1 to 4.0.3, pulling in
MCP SDK v2 (`mcp` 1.27.1 → 2.2.0) and `prefab-ui` 0.19.1 → 0.20.2.

**Code changes required**:

- `prefab-ui` 0.20.x renamed the `cssClass` keyword argument to `css_class`
  on all UI components (`Card`, `CardContent`, `Column`, `Row`, `Alert`,
  `Separator`, `Image`, `Text`, …). Updated all ~270 call sites across the
  9 FastMCPApps in `src/aareguru_mcp/apps/`.
- Removed four now-unused `# type: ignore[arg-type]` comments in
  `server.py` around `ctx.elicit()` calls — fastmcp 4.x's updated type
  signature for `elicit()` no longer produces the type mismatch they were
  suppressing.

### Other Updates

- `structlog` 23.3.0 → 26.1.0
- `ucp-sdk` 0.3.0 → 0.5.0 (declared dependency, not directly imported by
  this codebase)
- ~50 additional transitive dependencies refreshed via `uv lock --upgrade`
  (`starlette`, `uvicorn`, `pydantic`, `cryptography`, `rich`, dev tools
  `pytest`, `mypy`, `black`, `ruff`, `playwright`, etc.)

## Bugfix: Elicitation Regression on the Modern MCP Protocol

**Issue**: MCP protocol era `2026-07-28` (SEP-2322/SEP-2575), which MCP SDK
v2 clients negotiate by default, removed server-initiated elicitation from
the protocol entirely. Under the fastmcp 4.x upgrade, any tool call that
reached `ctx.elicit()` — the unknown-city fallback, the >90-day history
confirmation, the dangerous-flow-level warning, and the checkout
billing-address prompt — started raising a hard `ToolError` for any client
connecting with the modern protocol, instead of the intended graceful UX.
This was found via live extensive testing against a running
`aareguru-mcp-http` server (see Verification below), not by the unit test
suite, since no existing tests exercised the elicitation call sites through
a real client-protocol handshake.

**Fix**: Added `_elicit_safe()` in `server.py`, a wrapper around
`ctx.elicit()` that catches the protocol-unsupported `ToolError` and
returns a sentinel (`_ELICIT_UNAVAILABLE`) instead of propagating it. Each
of the four call sites now degrades to a sensible default when it can't
ask the client:

- **Unknown city** (`_elicit_city`): falls back to the existing
  "not found" error, same as if the user had declined.
- **>90-day history range**: proceeds with the fetch automatically instead
  of permanently blocking large-range queries for modern-protocol clients.
- **Dangerous flow level warning**: returns the full safety data the
  caller explicitly asked for, rather than withholding it because the
  confirmation gate can't be shown.
- **Checkout billing-address prompt**: returns the existing error dict
  unchanged rather than crashing.

An explicit decline/cancel from a client that *does* support elicitation
is unaffected — only the "can't ask at all" case changed behavior.

## Bugfix: UCP Checkout Broken Against the Live WooCommerce Store

**Issue**: Found by walking the actual shop/checkout tools end-to-end
against the live `konsum.aare.guru` store (`create_checkout_session` →
`update_checkout_session` → `complete_checkout`), not by the unit test
suite — the existing mocks had drifted from the real Store API shape and
masked all three of the following:

1. **Every cart write failed with 401 Unauthorized.** The store no longer
   uses cookies for cart identity; the WooCommerce Store API instead
   issues a JWT `Cart-Token` response header that must be echoed back on
   every subsequent write (`add-item`, `cart/items` DELETE, `checkout`),
   or the request is rejected even with a valid nonce. `shop_client.py`
   never captured or resent it.
2. **`complete_checkout` failed with 400 Bad Request.** The hardcoded
   `payment_method="postfinance_checkout"` default didn't match any
   registered gateway ID — PostFinance Checkout registers one ID per
   payment method (e.g. `postfinancecheckout_6`), not a single fixed
   string.
3. **`order_id` and `continue_url` always came back `null`.** The code
   read `order.get("id")` / `order.get("payment_url")`, but the Store
   API's checkout response nests these under `order_id` and
   `payment_result.redirect_url`. The unit test's mock had used the same
   wrong (aspirational) field names, so this passed tests while failing
   on every real order.

**Fix**: `shop_client.py` now captures and forwards the `Cart-Token`
header alongside the nonce on every request; `submit_checkout` looks up
the store's current default payment gateway from the checkout draft
instead of a hardcoded string; `shop_service.py` reads `order_id` and
`payment_result.redirect_url` from the real response shape. The test
mock in `tests/test_tools_shop.py` was corrected to match.

**Verified live**: walked the full flow against `konsum.aare.guru` with
test billing data — `create_checkout_session` and `update_checkout_session`
now succeed (previously 401), and `complete_checkout` returned a real
order (`order_id: 4127`) with a populated `continue_url` payment link
(previously both `null`).

## Test Coverage

- 471 tests passing (7 new, in `tests/test_elicitation_fallback.py`,
  covering `_elicit_safe` and all four degraded call sites)
- 81% code coverage maintained
- `mypy`, `ruff`, and `black` all clean

## Verification

- Full test suite: `uv run pytest --cov=aareguru_mcp` — 471 passed
- Live extensive testing against a running `aareguru-mcp-http` server using
  `fastmcp.Client`: all 12 core tools, 9 FastMCPApp tools, 8 resources, 5
  prompts, checkout session lifecycle, and edge cases (unicode/empty city,
  malformed dates, invalid sessions, parallel calls) — this is what
  surfaced the elicitation regression above.
- After the elicitation fix: reproduced the exact failing scenario
  (`get_historical_data` with a 400-day range under `Client(mode="auto")`)
  and confirmed it now succeeds; confirmed a `mode="legacy"` client's
  elicitation handler is still invoked and an explicit decline still
  aborts as before.
- After the checkout fix: completed a real order against the live store
  (see above) confirming the Cart-Token, payment-method, and response
  field-name fixes all work together end-to-end.

## Files Changed

- `pyproject.toml` — dependency floors and version bump
- `uv.lock` — full dependency re-resolution
- `src/aareguru_mcp/apps/*.py` (9 apps + `_helpers.py`) — `cssClass` →
  `css_class`
- `src/aareguru_mcp/server.py` — removed stale `type: ignore` comments;
  added `_elicit_safe()` and updated all four `ctx.elicit()` call sites
- `tests/test_elicitation_fallback.py` — new regression tests
- `src/aareguru_mcp/shop_client.py` — Cart-Token capture/forwarding,
  dynamic payment-method lookup
- `src/aareguru_mcp/shop_service.py` — corrected `order_id` /
  `continue_url` field mapping
- `tests/test_tools_shop.py` — corrected mock to match the real Store API
  response shape
- `CLAUDE.md`, `README.md` — FastMCP 3.x → 4.x references, test count/coverage

---

**Summary**: Dependency upgrade to FastMCP 4.x / MCP SDK v2, a fix for an
elicitation regression the upgrade introduced for clients on the modern
MCP protocol, and a fix for three checkout bugs that broke UCP purchases
against the live WooCommerce store. No breaking changes for consumers of
this MCP server.
