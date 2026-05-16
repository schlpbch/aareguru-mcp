# Release Notes: aareguru-mcp v4.7.0

**Release Date**: May 16, 2026
**Previous Version**: v4.6.0
**Status**: Stable, Production Ready

---

## Executive Summary

aareguru-mcp v4.7.0 adds full internationalisation (de / en / fr / it) to all 9
FastMCPApps. Every user-visible label, section header, chart legend, alert, and
BAFU safety description can now be rendered in German (default), English, French,
or Italian via a `lang: str = "de"` parameter on every app UI function. Also
fixes a 400 Bad Request on the historical chart caused by the upstream API
dropping support for relative date expressions. 429 tests pass at 80% coverage.
No MCP API surface changes.

---

## What's Changed

### i18n for all FastMCPApps (`lang=` parameter)

A new `lang: str = "de"` parameter has been added to every FastMCPApp UI
function. The AI assistant detects the conversation language and passes it
automatically — no user-visible toggle is required.

**Supported locales**:

| Code | Language | Notes |
| --- | --- | --- |
| `de` | German | Default; fallback for unknown locales |
| `en` | English | Swiss tourism and international users |
| `fr` | French | National language; BAFU translations official |
| `it` | Italian | National language; BAFU translations official |

**Affected app views** (13 total across 9 apps):

| App | UI function |
| --- | --- |
| `conditions` | `conditions_dashboard(city, lang)` |
| `conditions_temperature` | `temperature_card(city, lang)` |
| `conditions_flow` | `flow_card(city, lang)` |
| `conditions_weather` | `weather_card(city, lang)` |
| `conditions_sun` | `sun_card(city, lang)` |
| `forecast` | `forecast_view(city, lang)` |
| `history` | `historical_chart(city, start, end, lang)` |
| `intraday` | `intraday_view(city, lang)` |
| `safety` | `safety_briefing(city, lang)` |
| `city_finder` | `city_finder_view(sort_by, lang)` |
| `compare` | `compare_cities_table(cities, lang)` |
| `map` | `aare_map(city, lang)` |
| `shop` | `shop_cart_view(session_id, lang)` |

### New module: `apps/_i18n.py`

Single source of truth for all translated UI strings. ~85 string keys × 4
locales = ~340 translation entries. The `t(key, lang="de")` helper returns the
requested locale's string and falls back gracefully to German for any unknown
locale or missing key.

Key categories:

| Prefix | Scope |
| --- | --- |
| `safety_*` | Safety badge labels (safe / moderate / elevated / high / very_high) |
| `bafu_N_label/desc/guidance` | All 5 BAFU danger levels × 3 text fields |
| `card_*` | Card and section titles |
| `col_*` | DataTable column headers |
| `alert_*` | Alert titles and descriptions |
| `label_*` | Inline labels (current, change today, now, in 2h, …) |
| `chart_*` | Chart series legends |
| `page_*` | Page/view header titles |
| `badge_*` | Summary badge labels |
| `sort_*` | Sort button labels |
| `section_*` | Section headers |

BAFU official multilingual terminology is used verbatim (OFEV for French, UFAM
for Italian) as required by CONSTITUTION Art. VIII.

### `_helpers.py` update

`_safety_badge(flow, lang="de")` now accepts a `lang` parameter and returns the
localised safety label string via `t()`.

### `_constants.py` unchanged

`_BAFU_LEVELS`, `_SAFETY_LEVELS`, `_FLOW_ZONES`, and `_BEAUFORT` data structures
are not modified. Apps translate their display strings through `t()` lookups
keyed by `FLOW_LABEL_KEY` mapping. Authoritative German safety data remains the
primary source.

---

## Bug Fixes

### Historical chart: 400 Bad Request on relative date expressions

`historical_chart` and `get_historical_data` were returning a 400 Bad Request
when called with relative start/end expressions such as `"-7 days"` or `"now"`.

**Root cause**: The upstream `/v2018/history` endpoint stopped accepting
human-readable relative date strings and now requires Unix timestamps.

**Fix**: `AareguruClient._resolve_timestamp(expr)` is called on both `start` and
`end` before the request is sent. It converts:

| Input | Example | Output |
| --- | --- | --- |
| `"now"` | — | current Unix timestamp |
| Relative | `"-7 days"`, `"-2 weeks"`, `"-1 month"` | computed Unix timestamp |
| ISO 8601 | `"2025-06-15"`, `"2025-06-15T12:00:00Z"` | Unix timestamp |
| Unix timestamp | `"1700000000"` | passed through unchanged |
| Unknown | anything else | passed through unchanged |

No caller changes required — all existing invocations continue to work.

9 new unit tests added to `tests/test_unit_client.py`.

---

### New tests: `tests/test_i18n.py`

44 new tests covering:

- All German keys present in every locale (completeness check)
- Fallback to German for unknown locale
- Fallback to raw key when missing from all locales
- German default when `lang` argument is omitted
- English, French, Italian spot-checks for critical strings
- All 5 BAFU levels × 3 fields × 4 locales (60 assertions)
- Parametrized async smoke tests for every app UI function with all 4 locales

---

## Metrics

| Metric | v4.6.0 | v4.7.0 |
| --- | --- | --- |
| Tests passing | 376 | 429 |
| Coverage | 76% | 80% |
| MCP tools | 12 | 12 |
| MCP resources | 8 | 8 |
| FastMCPApps | 9 | 9 |
| Supported UI languages | 1 (de) | 4 (de, en, fr, it) |
| i18n string keys | — | ~85 |
| New i18n tests | — | 44 |
| New client tests | — | 9 |
| New ADRs | — | — |

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
| `docs/RELEASE_NOTES_v4.7.0.md` | This document |
