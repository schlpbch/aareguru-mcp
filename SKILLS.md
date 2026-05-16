# SKILLS.md — Aareguru MCP Capability Reference

<!-- cspell:ignore chli chalt intraday sparkline asyncio bern thun basel olten -->

This server gives AI assistants live access to Swiss Aare river data: water
temperature, flow rates, weather conditions, safety assessments, historical
trends, and interactive visualizations across multiple Swiss cities. It surfaces
BAFU (Federal Office for the Environment) safety data directly in conversation.

This document is a capability reference. For installation see [README.md](README.md),
for internals see [ARCHITECTURE.md](ARCHITECTURE.md), for governance see [CONSTITUTION.md](CONSTITUTION.md).

---

## Quick Reference

### Aare river tools

| Tool | What it does | Example question |
| --- | --- | --- |
| `get_current_temperature` | Water temp + Swiss German description + suitability | "How warm is the Aare in Bern?" |
| `get_current_conditions` | Full snapshot: temp, flow, height, weather, forecast | "Is it safe to swim today?" |
| `get_flow_danger_level` | BAFU 1–5 safety level with elicitation above threshold | "What's the current danger level?" |
| `get_historical_data` | Hourly time-series; relative or ISO dates | "Show temperature trends for the last 7 days" |
| `compare_cities` | Parallel multi-city comparison with warmest/safest ranking | "Which city has the warmest water?" |
| `get_forecasts` | Concurrent forecast fetch with 2-hour temperature trend | "What's the forecast for Thun and Basel?" |

### Shop tools (konsum.aare.guru — UCP checkout)

| Tool | What it does | Example question |
| --- | --- | --- |
| `list_shop_products` | Browse merchandise catalog with prices in CHF | "What merch is available?" |
| `get_shop_product` | Full details for a specific product | "Tell me more about the swim buoy" |
| `create_checkout_session` | Start a UCP checkout session, adds items to cart | "I want to buy the beach towel" |
| `update_checkout_session` | Attach billing/shipping address to a session | "My address is Bahnhofplatz 1, Bern" |
| `complete_checkout` | Submit the order and return the PostFinance payment URL | "Confirm my order" |
| `cancel_checkout_session` | Cancel a session and clear the cart | "Never mind, cancel my order" |

---

## Tool Selection Guide

```text
What does the user need?
│
├── Temperature only → get_current_temperature
│     "How warm is the water?" / "Is it warm enough?"
│
├── Safety or full conditions → get_current_conditions
│     "Is it safe?" / "How are conditions?" / "Should I go?"
│
├── Flow/danger level explicitly → get_flow_danger_level
│     "What's the BAFU level?" / "Is the current dangerous?"
│
├── Past data or trends → get_historical_data
│     "How has it changed?" / "Last week's temperatures?"
│
├── Compare locations → compare_cities
│     "Which city is warmest?" / "Best spot today?"
│
├── Forecast → get_forecasts
│     "What's the 2-hour forecast?" / "Will it warm up?"
│
└── Shopping / merchandise → shop tools
      Browse: list_shop_products / get_shop_product
      Buy:    create_checkout_session → update_checkout_session → complete_checkout
```

---

## Tools

Twelve tools for dynamic, parameterized queries. Aare tools default to Bern when no city is specified.

### Aare river tools

| Tool | Parameters | Returns | Notes |
| --- | --- | --- | --- |
| `get_current_temperature` | `city` | temp, Swiss German text, suitability | Fastest; use for simple temp checks |
| `get_current_conditions` | `city` | temp, flow, height, weather, forecast | Most complete; use for safety decisions |
| `get_flow_danger_level` | `city` | flow m³/s, BAFU level 1–5, description | Triggers elicitation when flow >220 m³/s |
| `get_historical_data` | `city`, `start`, `end` | hourly time-series array | Triggers elicitation for >90-day ranges |
| `compare_cities` | `cities?` (optional list) | all-city table + warmest/coldest/safest | Parallel fetch; omit `cities` for all |
| `get_forecasts` | `cities` (list) | per-city forecast + 2h trend | Parallel fetch; multiple cities at once |

### Shop tools (konsum.aare.guru — UCP checkout)

| Tool | Parameters | Returns | Notes |
| --- | --- | --- | --- |
| `list_shop_products` | `search?` | list of products with name, price CHF, stock | Optional keyword filter |
| `get_shop_product` | `product_id` | full product details | Use `list_shop_products` to find IDs |
| `create_checkout_session` | `items` (list of `{id, quantity}`) | UCP session with total and status | Clears cart; starts fresh session |
| `update_checkout_session` | `session_id`, `billing`, `shipping?` | updated session (ready_for_complete) | Required before `complete_checkout` |
| `complete_checkout` | `session_id` | order ID + PostFinance payment URL | Triggers elicitation if billing missing |
| `cancel_checkout_session` | `session_id` | confirmation | Clears cart and removes session |

### Date formats for `get_historical_data`

`start` and `end` accept:

- ISO 8601: `"2025-06-15T00:00:00Z"`
- Unix timestamp: `"1750000000"`
- Relative expressions: `"-7 days"`, `"-1 week"`, `"-30 days"`, `"now"`

### BAFU Flow Danger Levels

| Flow (m³/s) | Level | Label | Meaning |
| --- | --- | --- | --- |
| < 100 | 1 | Safe | Swimming OK |
| 100–220 | 2 | Moderate | Experienced swimmers only |
| 220–300 | 3 | Elevated | Caution advised |
| 300–430 | 4 | High | Dangerous |
| > 430 | 5 | Very High | Extremely dangerous |

When flow exceeds 220 m³/s, `get_flow_danger_level` uses MCP elicitation to
request acknowledgement before continuing.

### Swiss German Descriptions

Temperature responses include authentic local phrases, e.g.:

- `"geil aber chli chalt"` — awesome but a bit cold
- `"geil und warm"` — awesome and warm
- `"chli chalt"` — a bit cold

---

## Resources

Eight URI-addressable resources for direct, read-only data access — useful when
building integrations or when you need raw data without tool invocation overhead.

| URI | Returns | When to use |
| --- | --- | --- |
| `aareguru://cities` | All monitored cities with coordinates | Discover available locations |
| `aareguru://current/{city}` | Full current conditions (nested) | Complete data snapshot |
| `aareguru://today/{city}` | Lightweight current snapshot (flat) | Minimal temp + text only |
| `aareguru://forecast/{city}` | Weather forecast entries | Forward-looking data |
| `aareguru://history/{city}/{start}/{end}` | Hourly time-series | Historical analysis |
| `aareguru://safety-levels` | Static BAFU 1–5 reference table | Display or interpret the scale |
| `aareguru://thresholds` | Flow thresholds with hex color codes | Build safety visualizations |
| `aareguru://shop` | Merchandise catalog from konsum.aare.guru | Browse products without tool call |

Resources return JSON strings. `aareguru://current/{city}` uses a nested
structure (`aare.temperature`, `aare.flow`); `aareguru://today/{city}` uses a
flat structure (`aare` as a direct float). See [ARCHITECTURE.md](ARCHITECTURE.md)
for the full model breakdown.

---

## Prompts

Three guided workflows that compose multiple tool calls into a single structured
narrative. The AI assistant can use MCP elicitation to ask for missing parameter
values interactively.

### Swimming prompts

| Prompt | Parameters | Output |
| --- | --- | --- |
| `daily-swimming-report` | `city` (default: Bern), `include_forecast` (bool) | Conditions + safety + forecast + recommendation |
| `compare-swimming-spots` | `min_temperature?` (float), `safety_only?` (bool) | Ranked city comparison filtered by criteria |
| `weekly-trend-analysis` | `city`, `days` (3 / 7 / 14) | Temperature and flow pattern analysis with observations |

### Shop prompts

| Prompt | Parameters | Output |
| --- | --- | --- |
| `shop-browse` | `search?` (keyword filter) | Catalog listing with prices, stock, and offer to inspect or buy |
| `shop-checkout` | `items?` (description of desired items) | Full guided flow: browse → product detail → cart → billing → confirm → payment |

**When to use prompts vs. tools:**

- Use **prompts** when the user wants a complete, structured narrative response.
- Use **tools** directly when you need a specific data field to answer a focused question.
- Prompts compose multiple tool calls internally; tools are atomic.
- Use `shop-browse` when the user is exploring; use `shop-checkout` when they're ready to buy.

---

## Interactive Apps (FastMCPApps)

Fourteen app views across ten FastMCPApps render rich HTML UIs directly inside
AI conversations via FastMCP's app rendering layer. Each app returns a
self-contained visual component — no external assets fetched at render time
(fonts embedded as base64).

All app views accept an optional `lang` parameter (`"de"` / `"en"` / `"fr"` /
`"it"`, default `"de"`). Pass `lang` to render every label, header, chart
legend, and BAFU description in the user's language.

### Condition & Status Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `conditions_dashboard` | `conditions_dashboard(city, lang?)` | Full dashboard: temp, flow, weather, BAFU level |
| `temperature_card` | `temperature_card(city, lang?)` | Water temp with 2h trend arrow and Swiss German text |
| `flow_card` | `flow_card(city, lang?)` | Flow rate + BAFU level, color-coded by danger |
| `weather_card` | `weather_card(city, lang?)` | Air temperature + 6-day forecast strip |
| `sun_card` | `sun_card(city, lang?)` | Sunshine hours and sunset time |
| `safety_briefing` | `safety_briefing(city, lang?)` | BAFU 1–5 scale with current level highlighted |

### Historical & Trend Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `historical_chart` | `historical_chart(city, start, end, lang?)` | Area chart: water temperature and flow over time |
| `intraday_view` | `intraday_view(city, lang?)` | Today's intraday water temperature sparkline |
| `forecast_view` | `forecast_view(city, lang?)` | 24-hour forecast with hourly temperature cards |

### Discovery & Comparison Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `compare_cities_table` | `compare_cities_table(cities?, lang?)` | Sortable table across all cities (or a subset) |
| `city_finder_view` | `city_finder_view(sort_by, lang?)` | All cities ranked by temperature or safety |
| `aare_map` | `aare_map(city?, lang?)` | Leaflet.js interactive map, all stations, color-coded by BAFU level |

### Shop & Checkout Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `product_view` | `product_view(product_id, lang?)` | Product detail: image carousel, price, stock badges, description, add-to-cart hint |
| `shop_cart_view` | `shop_cart_view(session_id?, lang?)` | Cart items, total, billing summary, payment URL |

**When to use apps vs. tools:**

- Use **apps** when the user benefits from a visual layout (dashboard, chart, map, table, cart).
- Use **tools** when you need structured data to reason over or combine with other information.
- `conditions_dashboard` covers most display scenarios without needing to call `get_current_conditions` manually.
- `historical_chart` avoids formatting raw `get_historical_data` output into prose.
- `product_view` shows product images via a Carousel before the user commits to buying.
- `shop_cart_view` gives the user a visual cart/checkout summary at each step of the purchase flow.

---

## Use Cases by Topic

### Basic temperature queries
>
> "How warm is the Aare?" / "Is it warm enough to swim?" / "Temperature in Thun?"

Primary: `get_current_temperature`  
Visual: `temperature_card`

---

### Safety and flow assessment
>
> "Is it safe?" / "What's the danger level?" / "Can beginners swim?"

Primary: `get_flow_danger_level` or `get_current_conditions`  
Visual: `safety_briefing`, `flow_card`  
Note: flows above 220 m³/s trigger an elicitation confirmation step.

---

### Full conditions report
>
> "How are conditions today?" / "Should I go to the Aare?" / "Give me a swimming report"

Primary: `get_current_conditions` or prompt `daily-swimming-report`  
Visual: `conditions_dashboard`

---

### Weather integration
>
> "What's the air temperature?" / "Will it rain?" / "Is it sunny?"

Primary: `get_current_conditions` (includes weather sub-object)  
Visual: `weather_card`, `sun_card`

---

### City comparison
>
> "Which city is warmest?" / "Compare Bern and Basel" / "Best spot today?"

Primary: `compare_cities` or prompt `compare-swimming-spots`  
Visual: `compare_cities_table`, `city_finder_view`, `aare_map`

---

### Historical trends
>
> "How has the temperature changed this week?" / "Was it warmer last month?"

Primary: `get_historical_data`  
Visual: `historical_chart`  
Note: requests exceeding 90 days trigger an elicitation confirmation step.

---

### Forecasts
>
> "What's the 2-hour forecast?" / "Will it warm up this afternoon?"

Primary: `get_forecasts`  
Visual: `forecast_view`  
Resource: `aareguru://forecast/{city}`

---

### Location discovery
>
> "Which cities are monitored?" / "Where can I check Aare data?"

Primary: resource `aareguru://cities`  
Visual: `aare_map`, `city_finder_view`

---

### Activity-specific queries
>
> "Is it good for Aare floating?" / "Can I kayak today?" / "Safe for wild swimming?"

Primary: `get_flow_danger_level` + `get_current_conditions`  
Visual: `conditions_dashboard` + `safety_briefing`  
Logic: flow >220 m³/s → caution; flow >300 m³/s → dangerous for all activities.

---

### Intraday temperature evolution
>
> "Has it warmed up since this morning?" / "Show me today's temperature curve"

Primary: `get_current_conditions` (includes 2h forecast trend)  
Visual: `intraday_view`

---

### Weekly trend analysis
>
> "Show me temperature patterns over 7 days" / "Has it been cooling down?"

Primary: prompt `weekly-trend-analysis` or `get_historical_data`  
Visual: `historical_chart`

---

### Multi-step queries
>
> "Compare all cities, then show me the warmest one in detail"

Step 1: `compare_cities` or `compare_cities_table`  
Step 2: `get_current_conditions(warmest_city)` or `conditions_dashboard(warmest_city)`

---

### Shopping & merchandise
>
> "What merch is available?" / "I want to buy the swim buoy" / "Show my cart"

Prompt (browse): `shop-browse` — lists catalog, shows product detail with images, offers to buy  
Prompt (buy):    `shop-checkout` — full guided flow from browse to payment link  
Browse: `list_shop_products` → `product_view(product_id)` (images + detail)  
Buy:    `create_checkout_session` → `update_checkout_session` → `complete_checkout`  
Visual: `product_view` — product images carousel before purchase  
Visual: `shop_cart_view(session_id)` — cart at every checkout step  
Cancel: `cancel_checkout_session`  
Resource: `aareguru://shop` — static catalog snapshot  
Note: checkout uses UCP over WooCommerce Store API; payment via PostFinance.

---

## Developer Notes

### Language / i18n

All FastMCPApp UI functions accept a `lang` parameter:

| Value | Language | Notes |
| --- | --- | --- |
| `"de"` | German | Default; fallback for any unknown locale |
| `"en"` | English | Swiss tourism and international users |
| `"fr"` | French | National language; BAFU translations official |
| `"it"` | Italian | National language; BAFU translations official |

The AI assistant should detect the conversation language and pass it
automatically. Users do not need an explicit toggle. Every user-visible label,
section header, chart legend, alert, badge, and BAFU safety description is
translated. Swiss German temperature phrases (`"geil und warm"` etc.) are
returned from the upstream API unchanged regardless of `lang`.

Translations live in `apps/_i18n.py` (`STRINGS` dict + `t(key, lang)` helper).
BAFU danger level text uses official OFEV (French) and UFAM (Italian)
terminology verbatim.

### Elicitation behavior

Two tools use MCP elicitation to confirm user intent before proceeding:

- `get_flow_danger_level`: prompts when flow >220 m³/s (elevated or above)
- `get_historical_data`: prompts when the requested range exceeds 90 days

Elicitation requires an MCP client that supports `elicitation/create`. Claude
Desktop supports this natively. Clients that do not support elicitation will
receive an error or skip the confirmation step depending on server configuration.

### Parallel fetching

`compare_cities` and `get_forecasts` use `asyncio.gather()` internally. Passing
a list of cities returns results for all cities in a single tool call — no need
to call per-city tools in a loop.

### Caching

Current-condition responses are cached for 120 seconds (configurable via
`CACHE_TTL_SECONDS`). Historical data bypasses the cache. Back-to-back calls
within the cache window return the same snapshot; this is intentional and
respects the upstream API rate limit.

### City identifiers

City names are lowercase ASCII strings, e.g. `"bern"`, `"thun"`, `"basel"`,
`"olten"`. Tools accept any capitalization; the client normalizes. Use
`aareguru://cities` to retrieve the authoritative list.

### Data attribution

All data originates from [Aare.guru](https://aare.guru) and
[BAFU](https://www.hydrodaten.admin.ch). This server is for non-commercial use
only. Tool responses include attribution fields; do not suppress them.

---

## Related Documents

| Document | Scope |
| --- | --- |
| [README.md](README.md) | Installation, quick start, configuration |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Layer design, data flow, patterns |
| [CONSTITUTION.md](CONSTITUTION.md) | Project principles, safety constraints, ADR governance |
| [specs/ADR_COMPENDIUM.md](specs/ADR_COMPENDIUM.md) | 18 Architecture Decision Records |
| [docs/USER_QUESTIONS_SLIDES.md](docs/USER_QUESTIONS_SLIDES.md) | 130-question test suite by category |
