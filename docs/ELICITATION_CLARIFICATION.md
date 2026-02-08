# MCP Elicitation - Current Status

## Understanding Two Different Features

There are **two distinct MCP features** often confused:

### 1. **Prompt Arguments** (✅ Implemented)
What prompts have optional parameters that AI assistants can ask users about.

**Example:**
```python
@mcp.prompt(name="daily-swimming-report")
async def daily_swimming_report(city: str = "Bern", include_forecast: bool = True):
    ...
```

**User Experience:**
```
User: "Give me a swimming report"
AI: "Would you like the report for Bern, or a different city?"
User: "Thun"
AI: [generates report for Thun]
```

**Status:** ✅ Fully implemented in aareguru-mcp
- All prompts have properly typed arguments
- 15 tests verify typed arguments work correctly
- See: [test_prompt_typed_args.py](../tests/test_prompt_typed_args.py)

---

### 2. **Server-Side Elicitation** (❌ Not Implemented)
Where a *tool* can pause execution and ask the client to prompt the user for more information.

**Example:**
```python
@mcp.tool()
async def get_current_temperature(city: str | None = None):
    if city is None:
        # Pause execution and ask user for city
        city = await elicit_from_user("Which city would you like?", 
                                      options=["Bern", "Thun", "Basel", ...])
    return get_temp_for_city(city)
```

**User Experience:**
```
User: "What's the water temperature?"
[Server realizes city is missing]
Server → Orchestrator: "Please ask user: Which city?"
Orchestrator → User: "Which city would you like?"
User: "Bern"
Orchestrator → Server: "Bern"
Server → Orchestrator: [temperature data for Bern]
```

**Status:** ❌ Not implemented in aareguru-mcp
- All tools use **default values** instead (e.g., `city = "Bern"`)
- No dynamic user prompting during tool execution
- Tracked separately in Issue #3: "Elicitation support: Not yet implemented"

---

## Current Behavior

### What Happens Now

When you call `get_current_temperature` without arguments:

```python
@mcp.tool(name="get_current_temperature")
async def get_current_temperature(city: str = "Bern") -> TemperatureToolResponse:
    """Get current water temperature for a city."""
    # Simply uses the default
    return await tools.get_current_temperature(city)
```

**Result:** Always returns Bern's temperature (the default)

**No interaction like:**
- ❌ "Which city would you like?"
- ❌ Dynamic prompt during execution
- ❌ Callback to client to ask user

---

## Why Elicitation Isn't Implemented

### 1. **FastMCP Support Unknown**
FastMCP may not yet expose the MCP elicitation protocol. Need to verify:
- Is `request_sampling` or similar available in FastMCP API?
- How would a tool signal it needs user input?
- What's the callback mechanism?

### 2. **Design Decision: Defaults Over Interruption**
Current design philosophy:
- **Defaults provide instant results** - "What's the temperature?" → immediate answer for Bern
- **AI can ask separately** - If user doesn't like default, AI asks "Did you want a different city?"
- **Prompt arguments handle customization** - Use prompts for interactive flows

### 3. **Client Support Required**
Elicitation requires:
- **Client implementation** - mcp-orchestrator.io must support the elicitation protocol
- **UI for prompting** - Client needs to show prompts to user and collect responses
- **Bidirectional flow** - HTTP/SSE transport complexity increases

---

## Comparison: Elicitation vs. Current Approach

| Aspect | Server Elicitation ❌ | Current (Defaults) ✅ |
|--------|---------------------|---------------------|
| **Speed** | Slower (waits for user) | Fast (instant default) |
| **User Experience** | Conversational, clear | May surprise with default |
| **Complexity** | High (bidirectional) | Low (one-way) |
| **Error Handling** | User can cancel/timeout | Always succeeds |
| **Discovery** | Shows available options | Users must know cities exist |
| **AI Assistance** | Less needed | AI picks up slack |

### Real-World Flow Without Elicitation

```
User: "What's the water temperature?"
MCP Tool: [returns Bern temperature instantly]
AI: "The water in Bern is 17.2°C. Would you like to check a different city?"
User: "Yes, Thun"
AI: [calls tool with city="Thun"]
MCP Tool: [returns Thun temperature]
AI: "The water in Thun is 18.1°C"
```

**Result:** Two tool calls instead of one, but no protocol changes needed

---

## Implementing Elicitation

### If FastMCP Supports It

```python
from fastmcp import FastMCP, elicit
from fastmcp.types import ElicitRequest, ElicitChoice

@mcp.tool()
async def get_current_temperature(city: str | None = None):
    if city is None:
        # Get list of cities
        async with AareguruClient() as client:
            cities = await client.get_cities()
            
        # Ask user to choose
        choice = await elicit(
            ElicitRequest(
                prompt="Which city would you like the temperature for?",
                choices=[
                    ElicitChoice(id=c.city, label=c.longname)
                    for c in cities
                ]
            )
        )
        city = choice.id
    
    # Continue with execution
    return await get_temp_for_city(city)
```

### Requirements

1. **FastMCP elicitation API** - Check if available in FastMCP 2.x or 3.x
2. **Client support** - mcp-orchestrator.io must implement elicitation protocol
3. **Transport changes** - HTTP/SSE must support bidirectional requests
4. **Timeout handling** - What if user doesn't respond?
5. **Cancel handling** - What if user cancels the prompt?

---

## Current Documentation Issue

The file [MCP_ELICITATION_EXAMPLES.md](MCP_ELICITATION_EXAMPLES.md) is **misleadingly named**.

It describes **prompt arguments**, not **server elicitation**:
- ✅ Correct Content: How prompt arguments work
- ❌ Wrong Title: Calls them "elicitation" instead of "prompt arguments"
- 🔧 Fix Needed: Rename to `PROMPT_ARGUMENTS_GUIDE.md`

---

## Recommendations

### Short Term (Keep Current Approach)
1. ✅ Use sensible defaults (Bern, 7 days, etc.)
2. ✅ Let AI assistants handle clarification questions
3. ✅ Use prompt arguments for guided workflows
4. 📝 Rename MCP_ELICITATION_EXAMPLES.md → PROMPT_ARGUMENTS_GUIDE.md

### Long Term (If Demand Exists)
1. 🔍 Research FastMCP elicitation support
2. 🔍 Verify orchestrator client support
3. ⚠️ Consider UX tradeoffs (speed vs. clarity)
4. 💡 Implement for ambiguous cases only (invalid city, etc.)

---

## Related

- **Issue #3:** [Smoke Test Failures](https://github.com/schlpbch/aareguru-mcp/issues/3)
  - Related section: "Elicitation support: Not yet implemented (tracked separately)"
- **Test Suite:** [test_prompt_typed_args.py](../tests/test_prompt_typed_args.py)
  - Proves prompt arguments work correctly
- **Prompt Arguments Doc:** [MCP_ELICITATION_EXAMPLES.md](MCP_ELICITATION_EXAMPLES.md)
  - Should be renamed to avoid confusion

---

## Summary

**Prompt Arguments (Implemented)** ≠ **Server Elicitation (Not Implemented)**

- ✅ Prompts can have arguments → AI asks users → Values passed to prompt
- ❌ Tools cannot pause execution → Request user input → Resume with answer

Current approach works well:
- Fast responses with sensible defaults
- AI handles clarification naturally
- No protocol complexity

Elicitation would provide:
- More explicit user interaction
- Better discoverability
- But adds complexity and latency

**Status:** Working as designed. Elicitation tracked as future enhancement.
