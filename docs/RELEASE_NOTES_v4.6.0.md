# Release Notes: aareguru-mcp v4.6.0

**Release Date**: April 26, 2026
**Previous Version**: v4.5.0
**Status**: Stable, Production Ready

---

## Executive Summary

aareguru-mcp v4.6.0 adds full merchandise shopping and UCP checkout
functionality (6 new MCP tools, 1 new resource, 1 new FastMCPApp) plus
foundational governance documents (`CONSTITUTION.md`, `SKILLS.md`). The
`swiss-ai-mcp-commons` git dependency was removed. 376 tests pass at 76%
coverage.

---

## What's Changed

### Shop tools + UCP Checkout (ADR-019)

Six new MCP tools expose the [konsum.aare.guru](https://konsum.aare.guru)
merchandise store via a Universal Commerce Protocol-compatible checkout flow
over the WooCommerce Store API:

| Tool | Description |
| --- | --- |
| `list_shop_products` | Browse catalog with prices in CHF |
| `get_shop_product` | Full details for a specific product |
| `create_checkout_session` | Start a UCP session, add items to cart |
| `update_checkout_session` | Attach billing/shipping address |
| `complete_checkout` | Submit order, return PostFinance payment URL |
| `cancel_checkout_session` | Cancel session and clear cart |

New resource `aareguru://shop` provides a static catalog snapshot.

New modules: `shop_client.py` (singleton httpx client + WooCommerce cookie/nonce
management), `shop_models.py` (Pydantic models), `shop_service.py` (UCP session
state machine).

### Shop FastMCPApp

A 9th FastMCPApp (`apps/shop.py`) renders the cart and checkout UI at every
step of the purchase flow — empty state, items + total, billing summary, and
order confirmation with payment URL. Follows the aare.guru design system.

### CONSTITUTION.md — Project Governance

A new `CONSTITUTION.md` establishes the authoritative governance reference for
the project. It takes precedence over all other documents and defines:

- **11 Articles** covering mission, non-negotiable constraints, architecture,
  type safety, error handling, quality standards, UI apps, safety data handling,
  deployment, ADR governance, and dependency policy
- **RFC 2119 language** (MUST / SHOULD / MAY) throughout
- **Article X** (Governance): formalises the ADR process

### SKILLS.md — Capability Reference

A new `SKILLS.md` serves as the canonical "what can I ask this server to do?"
document for both end users and developers. Includes all 12 tools, 8 resources,
3 prompts, 13 app views, and use-case guidance.

### Dependency changes

- **Added**: `ucp-sdk>=0.3.0` for UCP Pydantic models
- **Removed**: `swiss-ai-mcp-commons` git dependency (provided only a marker
  mixin that was never needed)

---

## Metrics

| Metric | v4.5.0 | v4.6.0 |
| --- | --- | --- |
| Tests passing | 365 | 376 |
| Coverage | 80% | 76% |
| MCP tools | 6 | 12 |
| MCP resources | 7 | 8 |
| FastMCPApps | 8 | 9 |
| New documents | — | 2 |
| New ADRs | — | 1 (ADR-019) |

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
