# Prompt Arguments Investigation - Issue #3

## Summary

Prompts work perfectly with typed arguments (bool, int, float) when called directly through FastMCP, but fail when invoked through mcp-orchestrator.io. This indicates an argument forwarding/serialization issue in the orchestrator.

## Test Results

### ✅ Local Tests (Direct FastMCP API)
All 15 tests pass in [test_prompt_typed_args.py](../tests/test_prompt_typed_args.py):

```python
# These all work locally:
await compare_swimming_spots.render(
    arguments={"min_temperature": 18.0, "safety_only": True}
)

await weekly_trend_analysis.render(
    arguments={"city": "Bern", "days": 7}
)

await daily_swimming_report.render(
    arguments={"city": "Thun", "include_forecast": False}
)
```

**Result:** All typed arguments work correctly - booleans, floats, ints, strings.

### ❌ Orchestrator Tests (mcp-orchestrator.io)

| Prompt | Arguments | Result |
|--------|-----------|--------|
| `daily-swimming-report` | None (defaults) | ✅ Works |
| `daily-swimming-report` | `city="Thun"`, `include_forecast=true` | ❌ Fails |
| `compare-swimming-spots` | None (defaults) | ✅ Works |
| `compare-swimming-spots` | `min_temperature=18.0`, `safety_only=true` | ❌ Fails |
| `weekly-trend-analysis` | None (defaults) | ✅ Works |
| `weekly-trend-analysis` | `city="Bern"`, `days=7` | ❌ Fails |

**Error:** Generic "Error occurred during tool execution"

## Root Cause Analysis

The prompts are correctly defined with type hints:

```python
async def compare_swimming_spots(
    min_temperature: float | None = None, 
    safety_only: bool = False
) -> str:
    ...
```

FastMCP correctly infers the argument schema:
```json
{
  "arguments": [
    {
      "name": "min_temperature",
      "description": "...",
      "required": false
    },
    {
      "name": "safety_only",
      "description": "Provide as a JSON string matching the following schema: {\"type\":\"boolean\"}",
      "required": false
    }
  ]
}
```

### Hypothesis: Argument Serialization Mismatch

The orchestrator may be:
1. **Double-encoding JSON** - sending `"true"` (string) instead of `true` (boolean)
2. **Not deserializing types** - keeping everything as strings
3. **Using incompatible argument format** - different from FastMCP's expected structure

## Reproduction Steps

### To verify locally (works):
```bash
cd aareguru-mcp
uv run pytest tests/test_prompt_typed_args.py -v
```

### To reproduce failure (needs orchestrator):
```bash
# Using mcp-orchestrator.io
curl -X POST https://mcp-orchestrator.io/api/v1/prompts/get \
  -H "Content-Type: application/json" \
  -d '{
    "server": "aareguru-mcp",
    "prompt": "compare-swimming-spots",
    "arguments": {
      "min_temperature": 18.0,
      "safety_only": true
    }
  }'
```

## Potential Fixes

### Option 1: Orchestrator Side (Recommended)
The orchestrator should preserve argument types when forwarding to MCP servers:
- Booleans should be sent as JSON `true`/`false`
- Numbers should be sent as JSON numbers, not strings
- Follow MCP protocol specification for argument passing

### Option 2: Server Side (Workaround)
Convert all prompt arguments to strings and parse manually:
```python
async def compare_swimming_spots(
    min_temperature: str | None = None,  # Accept string
    safety_only: str = "false"            # Accept string
) -> str:
    # Parse manually
    min_temp = float(min_temperature) if min_temperature else None
    is_safe_only = safety_only.lower() == "true"
    ...
```

**Note:** This workaround is not recommended as it:
- Breaks type safety
- Requires manual parsing in every prompt
- Doesn't fix the underlying protocol issue

## Related Files

- [src/aareguru_mcp/server.py](../src/aareguru_mcp/server.py#L124-L230) - Prompt definitions
- [tests/test_prompt_typed_args.py](../tests/test_prompt_typed_args.py) - Comprehensive tests proving prompts work
- [CHANGELOG.md](../CHANGELOG.md) - Known issues section

## Next Steps

1. ✅ **Verify server code works** - Done (all tests pass)
2. ⏳ **Debug orchestrator argument forwarding** - Needs orchestrator maintainer
3. ⏳ **Review MCP protocol compliance** - Compare orchestrator implementation with spec
4. ⏳ **Add integration tests** - Test full orchestrator → server → prompt flow

## Contact

- **Issue:** [#3](https://github.com/schlpbch/aareguru-mcp/issues/3)
- **Server:** aareguru-mcp v3.3.1+
- **Framework:** FastMCP 2.x
- **Orchestrator:** mcp-orchestrator.io

---

**Status:** Verified not a server-side issue. Awaiting orchestrator investigation.
