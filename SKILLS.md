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

| Tool | What it does | Example question |
| --- | --- | --- |
| `get_current_temperature` | Water temp + Swiss German description + suitability | "How warm is the Aare in Bern?" |
| `get_current_conditions` | Full snapshot: temp, flow, height, weather, forecast | "Is it safe to swim today?" |
| `get_flow_danger_level` | BAFU 1–5 safety level with elicitation above threshold | "What's the current danger level?" |
| `get_historical_data` | Hourly time-series; relative or ISO dates | "Show temperature trends for the last 7 days" |
| `compare_cities` | Parallel multi-city comparison with warmest/safest ranking | "Which city has the warmest water?" |
| `get_forecasts` | Concurrent forecast fetch with 2-hour temperature trend | "What's the forecast for Thun and Basel?" |

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
└── Forecast → get_forecasts
      "What's the 2-hour forecast?" / "Will it warm up?"
```

---

## Tools

Six tools for dynamic, parameterized queries. All tools default to Bern when no
city is specified.

| Tool | Parameters | Returns | Notes |
| --- | --- | --- | --- |
| `get_current_temperature` | `city` | temp, Swiss German text, suitability | Fastest; use for simple temp checks |
| `get_current_conditions` | `city` | temp, flow, height, weather, forecast | Most complete; use for safety decisions |
| `get_flow_danger_level` | `city` | flow m³/s, BAFU level 1–5, description | Triggers elicitation when flow >220 m³/s |
| `get_historical_data` | `city`, `start`, `end` | hourly time-series array | Triggers elicitation for >90-day ranges |
| `compare_cities` | `cities?` (optional list) | all-city table + warmest/coldest/safest | Parallel fetch; omit `cities` for all |
| `get_forecasts` | `cities` (list) | per-city forecast + 2h trend | Parallel fetch; multiple cities at once |

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

Seven URI-addressable resources for direct, read-only data access — useful when
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

Resources return JSON strings. `aareguru://current/{city}` uses a nested
structure (`aare.temperature`, `aare.flow`); `aareguru://today/{city}` uses a
flat structure (`aare` as a direct float). See [ARCHITECTURE.md](ARCHITECTURE.md)
for the full model breakdown.

---

## Prompts

Three guided workflows that compose multiple tool calls into a single structured
narrative. The AI assistant can use MCP elicitation to ask for missing parameter
values interactively.

| Prompt | Parameters | Output |
| --- | --- | --- |
| `daily-swimming-report` | `city` (default: Bern), `include_forecast` (bool) | Conditions + safety + forecast + recommendation |
| `compare-swimming-spots` | `min_temperature?` (float), `safety_only?` (bool) | Ranked city comparison filtered by criteria |
| `weekly-trend-analysis` | `city`, `days` (3 / 7 / 14) | Temperature and flow pattern analysis with observations |

**When to use prompts vs. tools:**

- Use **prompts** when the user wants a complete, structured narrative response.
- Use **tools** directly when you need a specific data field to answer a focused question.
- Prompts compose multiple tool calls internally; tools are atomic.

---

## Interactive Apps (FastMCPApps)

Twelve apps render rich HTML UIs directly inside AI conversations via FastMCP's
app rendering layer. Each app returns a self-contained visual component — no
external assets fetched at render time (fonts embedded as base64).

### Condition & Status Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `conditions_dashboard` | `conditions_dashboard(city)` | Full dashboard: temp, flow, weather, BAFU level |
| `temperature_card` | `temperature_card(city)` | Water temp with 2h trend arrow and Swiss German text |
| `flow_card` | `flow_card(city)` | Flow rate + BAFU level, color-coded by danger |
| `weather_card` | `weather_card(city)` | Air temperature + 6-day forecast strip |
| `sun_card` | `sun_card(city)` | Sunshine hours and sunset time |
| `safety_briefing` | `safety_briefing(city)` | BAFU 1–5 scale with current level highlighted |

### Historical & Trend Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `historical_chart` | `historical_chart(city, start, end)` | Area chart: water temperature and flow over time |
| `intraday_view` | `intraday_view(city)` | Today's intraday water temperature sparkline |
| `forecast_view` | `forecast_view(city)` | 24-hour forecast with hourly temperature cards |

### Discovery & Comparison Apps

| App | Invocation | What it shows |
| --- | --- | --- |
| `compare_cities_table` | `compare_cities_table(cities?)` | Sortable table across all cities (or a subset) |
| `city_finder_view` | `city_finder_view(sort_by)` | All cities ranked by temperature or safety |
| `aare_map` | `aare_map(city?)` | Leaflet.js interactive map, all stations, color-coded by BAFU level |

**When to use apps vs. tools:**

- Use **apps** when the user benefits from a visual layout (dashboard, chart, map, table).
- Use **tools** when you need structured data to reason over or combine with other information.
- `conditions_dashboard` covers most display scenarios without needing to call `get_current_conditions` manually.
- `historical_chart` avoids formatting raw `get_historical_data` output into prose.

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

## Developer Notes

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
