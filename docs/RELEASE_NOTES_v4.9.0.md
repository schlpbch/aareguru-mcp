# Release Notes: v4.9.0

**Date**: 2026-09-11

## New Feature: Browse the Full Merchandise Catalog

Added `shop_catalog_view`, a new FastMCPApp that renders the entire
`konsum.aare.guru` catalog as a browsable grid. Previously the only visual
shop UIs were `shop_cart_view` (a single checkout session) and
`product_view` (one product at a time) — there was no way to see the whole
catalog visually, only `list_shop_products`' raw JSON.

- Responsive grid of product tiles: thumbnail, name, price, on-sale/
  out-of-stock badge, and a clickable link to the product page
- Supports the same optional `search` filter as `list_shop_products`
- `shop_browse` prompt updated to point the assistant at this view as the
  visual alternative to the raw JSON listing
- New strings added across all 4 locales (de/en/fr/it)

## Bugfix: Unknown Cities No Longer Silently Return Bern's Data

**Issue**: `get_current_temperature`, `get_current_conditions`,
`get_flow_danger_level`, `get_forecasts`, and `compare_cities` all silently
substituted Bern's data for any unrecognized (or empty) city string — the
upstream `/v2018/current` and `/v2018/today` endpoints default to Bern
instead of erroring, unlike `/v2018/history`, which correctly 400s. A
typo'd city in a downstream integration would silently serve wrong data
with nothing to catch it in monitoring. This also meant `server.py`'s
`_elicit_city` fallback (prompting the user to pick a valid city) was dead
code — it only triggers on `ValueError`, and nothing ever raised one for a
bad city.

**Fix**: `AareguruService` now validates the requested city against the
live `/v2018/cities` list before trusting a response. The three
single-city methods raise `ValueError` for an unknown city, which now
correctly feeds the elicit-a-valid-city UX (previously unreachable); the
two multi-city methods (`compare_cities`, `get_forecasts`) report a bad
city as a per-item error, consistent with their existing partial-failure
design, rather than failing the whole batch. An explicit empty city list
short-circuits without an extra network call.

This also surfaced a latent bug in the test suite: `test_integration_workflows.py`'s
live-API tests used `"basel"` as a test city, but Basel was never a real
Aareguru monitoring station (the real list is brienz, interlaken, thun,
bern, hagneck, biel, olten, brugg) — those tests were unknowingly
exercising the exact silent-substitution bug and passing anyway, since the
assertions never checked the data was genuinely Basel's. Swapped to
`"Biel"`.

## Bugfix: Empty Checkout Requests No Longer Clear Your Cart

**Issue**: `create_checkout_session([])` cleared the caller's existing
WooCommerce cart and returned a "successful" CHF 0.00 session instead of
rejecting the empty request — a footgun for any client calling it
defensively or idempotently.

**Fix**: empty `items` is now rejected with a clear error before the cart
is touched.

## Test Coverage

- 505 tests passing (16 new: `tests/test_city_validation.py` and new cases
  in `tests/test_tools_shop.py`, plus 6 for `shop_catalog_view`)
- 85% code coverage
- `mypy`, `ruff`, and `black` all clean

## Verification

- Full test suite: `uv run pytest --cov=aareguru_mcp` — 505 passed
- Live against a running `aareguru-mcp-http` server:
  - `shop_catalog_view` appears in `list_tools`, renders images/links/grid,
    and search filtering returns the correct subset
  - All three single-city tools return a clean error for a bad city
    instead of silently returning Bern's data
  - `get_forecasts`/`compare_cities` isolate the bad city as a per-item
    error while a valid city in the same batch still succeeds
  - A valid city (Thun) is unaffected
  - The elicit-a-valid-city flow (previously unreachable) now genuinely
    prompts the client and retries with the chosen city
  - `create_checkout_session([])` is cleanly rejected

## Files Changed

- `src/aareguru_mcp/apps/shop_catalog.py` — new app
- `src/aareguru_mcp/apps/__init__.py`, `server.py`, `prompts.py`,
  `apps/_i18n.py` — wiring and strings for the new app
- `src/aareguru_mcp/service.py` — city validation helpers and call sites
- `src/aareguru_mcp/shop_service.py` — empty-items rejection
- `tests/test_apps_shop_catalog.py`, `tests/test_city_validation.py` — new
  tests
- `tests/test_city_and_history.py`, `test_coverage_gaps.py`,
  `test_integration_workflows.py`, `test_parallel_tools.py`,
  `test_service_error_paths.py`, `test_tools_basic.py`, `test_tools_shop.py`
  — updated mocks for the new city-validation call, and a fixed test city
- `CLAUDE.md`, `README.md` — app/tool/test counts, version, release notes

---

**Summary**: A new merchandise catalog view, plus two correctness fixes
for silent-failure patterns that could serve wrong data or destroy cart
state without any error surfacing. No breaking changes for consumers of
this MCP server — cities that were always valid keep working exactly as
before.
