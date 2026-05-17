# Release Notes: v4.7.3

**Date**: 2026-05-17

## Bugfix

### WooCommerce Checkout Nonce Header

**Issue**: `complete_checkout` was failing with HTTP 400 Bad Request when submitting orders to WooCommerce.

**Root Cause**: The WooCommerce Store API (`wc/store/v1/checkout`) requires the nonce header to be named `X-WC-Store-API-Nonce`, but the client was sending it as `Nonce`.

**Fix**: Updated [shop_client.py](../src/aareguru_mcp/shop_client.py) to use the correct header name in `_write_headers()`. The nonce bootstrap mechanism (`_ensure_nonce()`) already fetches the nonce correctly via the `/cart` endpoint; the issue was only in how it was being sent to the checkout endpoint.

**Impact**: UCP checkout workflows (create → update → complete) now complete successfully.

## Test Coverage

- All 464 tests passing
- 80% code coverage maintained
- shop tools tested with correct nonce behavior

## Files Changed

- `src/aareguru_mcp/shop_client.py` — Fixed nonce header name

---

**Summary**: Bug fix for WooCommerce Store API integration. No breaking changes.
