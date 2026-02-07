# MCP Elicitation Examples

## Overview

MCP elicitation allows prompts to have **arguments** that AI assistants can
interactively ask users for. This creates more flexible, guided workflows where
users don't need to provide all information upfront.

## Enhanced Prompts with Elicitation

### 1. Daily Swimming Report

**Arguments:**

- `city` (string, default: "Bern") - Which city to generate report for
- `include_forecast` (boolean, default: true) - Whether to include 2-hour
  forecast

**User Experience:**

```
User: "Give me a swimming report"
AI: "Would you like the report for Bern, or a different city?"
User: "Thun"
AI: [generates report for Thun with forecast]

OR

User: "Daily report for Basel, no forecast"
AI: [generates report for Basel without forecast section]
```

**Value:** Users can customize report depth based on their needs - quick current
conditions or full forecast analysis.

---

### 2. Compare Swimming Spots

**Arguments:**

- `min_temperature` (float | null, optional) - Only show cities above this
  temperature
- `safety_only` (boolean, default: false) - Filter to only safe locations

**User Experience:**

```
User: "Which spots are good for swimming?"
AI: [shows all cities ranked]

OR

User: "Compare spots with at least 18 degrees"
AI: [filters to only cities >= 18°C]

OR

User: "Show me only safe swimming spots"
AI: [filters to cities with flow < 150 m³/s]
```

**Value:** Users get targeted comparisons instead of overwhelming lists - find
warm spots quickly or prioritize safety.

---

### 3. Weekly Trend Analysis

**Arguments:**

- `city` (string, default: "Bern") - Which city to analyze
- `days` (int, default: 7) - Analysis period (3, 7, or 14 days)

**User Experience:**

```
User: "Show me the temperature trends"
AI: "For which city? And how many days back - 3, 7, or 14?"
User: "Bern, last 3 days"
AI: [analyzes 3-day trend for Bern]

OR

User: "2-week trend for Interlaken"
AI: [analyzes 14-day trend for Interlaken]
```

**Value:** Flexible time horizons for different use cases - quick weekend check
vs. seasonal pattern analysis.

---

## Implementation Details

### FastMCP 2.0 Decorator Pattern

```python
@mcp.prompt(name="daily-swimming-report")
async def daily_swimming_report(city: str = "Bern", include_forecast: bool = True) -> str:
    """Generates comprehensive daily swimming report.

    Args:
        city: City to generate the report for (default: Bern).
              Use list_cities to discover available locations.
        include_forecast: Whether to include 2-hour forecast (default: true)
    """
    # Implementation dynamically adjusts prompt based on arguments
```

### Argument Schema Generation

FastMCP automatically generates MCP-compliant argument schemas from Python type
hints:

- `str` → string type
- `int` → integer type
- `bool` → boolean type
- `float | None` → optional float (nullable)

Default values make all arguments optional, creating a smooth UX where:

1. Users can invoke prompt with no args → uses sensible defaults
2. Users can specify some args → combines user prefs with defaults
3. AI can ask for clarification → "Which city?" or "How many days?"

---

## Benefits of MCP Elicitation

### 1. Progressive Disclosure

Users don't need to know all options upfront. Start simple, add complexity as
needed.

### 2. Conversational Flexibility

AI assistants can ask clarifying questions naturally:

- "Would you like to include the forecast?"
- "How many days should I analyze?"
- "Any minimum temperature filter?"

### 3. Discovery Through Interaction

Users learn about available options through conversation, not documentation.

### 4. Smart Defaults

Sensible defaults (Bern, 7 days, true) work for 80% of use cases, with
customization available for power users.

---

## Testing Elicitation

The test suite validates:

- Prompt arguments are properly exposed via MCP protocol
- All arguments have correct types and optionality
- Prompts work with defaults, partial args, and full customization
- Dynamic content adjusts based on argument values

```python
# Test that arguments are properly defined
assert len(daily_swimming_report.arguments) == 2
assert "city" in [arg.name for arg in daily_swimming_report.arguments]
assert "include_forecast" in [arg.name for arg in daily_swimming_report.arguments]
```

---

## Future Enhancements

Potential additional elicitation parameters:

- `language` argument for Swiss German intensity preference
- `detail_level` for verbose vs. concise reports
- `units` for metric vs. imperial measurements
- `time_range` for custom forecast horizons
- `comparison_metric` for ranking criteria (temperature, safety, distance)

The MCP elicitation pattern scales naturally as new customization needs emerge.
