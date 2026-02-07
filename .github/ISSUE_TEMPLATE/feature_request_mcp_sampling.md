---
name: MCP Sampling Support
about: Add MCP sampling capability for enhanced LLM-powered responses
title: '[FEATURE] Add MCP Sampling for Dynamic Content Generation'
labels: enhancement, mcp-protocol
assignees: ''
---

## Feature Request: MCP Sampling Support

### Description
Enable MCP sampling to allow the server to request LLM-generated content for enhanced, context-aware responses.

### Use Cases

#### 1. Dynamic Swiss German Explanations
Instead of hardcoded translations, generate contextual, cultural explanations:
```python
explanation = await mcp.request_sampling(
    messages=[{
        "role": "user",
        "content": f"Explain the Swiss German phrase '{swiss_german_text}' in context of swimming in Aare river"
    }]
)
```

#### 2. Intelligent Safety Warnings
Generate context-aware safety messages based on multiple factors:
```python
safety_warning = await mcp.request_sampling(
    messages=[{
        "role": "user",
        "content": f"Generate a safety warning for: flow={flow}m³/s, temp={temp}°C, weather={weather}. Be clear and direct."
    }]
)
```

#### 3. Historical Trend Summaries
Let the LLM summarize complex trend data:
```python
trend_summary = await mcp.request_sampling(
    messages=[{
        "role": "user",
        "content": f"Summarize this week's water temperature trend: {historical_data}. Highlight key patterns."
    }]
)
```

#### 4. Comparative City Analysis
Enhanced multi-city comparisons with natural language:
```python
comparison = await mcp.request_sampling(
    messages=[{
        "role": "user",
        "content": f"Compare these swimming locations and recommend the best: {cities_data}"
    }]
)
```

### Technical Considerations

**Pros:**
- ✅ More natural, context-aware responses
- ✅ Dynamic content generation
- ✅ Better personalization
- ✅ Reduced hardcoded text
- ✅ Cultural context for Swiss German phrases

**Cons:**
- ❌ Adds latency (LLM call per sampling request)
- ❌ Requires client sampling support
- ❌ Less predictable/testable
- ❌ May duplicate work (client would call LLM anyway)

### Implementation Plan

1. **Check FastMCP 2.0 Support**
   - Verify if `mcp.request_sampling()` is available
   - Check MCP protocol version requirements

2. **Add Sampling Helpers**
   ```python
   async def generate_safety_warning(flow: float, temp: float) -> str:
       if not hasattr(mcp, 'request_sampling'):
           return _static_safety_warning(flow, temp)
       
       return await mcp.request_sampling(
           messages=[...],
           max_tokens=150
       )
   ```

3. **Optional Enhancement**
   - Keep current simple responses as default
   - Add `--enable-sampling` flag or config option
   - Use sampling only when it adds clear value

4. **Priority Areas**
   - Safety warnings (critical, context-dependent)
   - Swiss German cultural explanations (valuable context)
   - Comparative analyses (complex multi-city comparisons)

### Configuration

Add settings for sampling control:
```python
class Settings(BaseSettings):
    # Sampling configuration
    enable_sampling: bool = Field(
        default=False,
        description="Enable MCP sampling for enhanced responses"
    )
    sampling_max_tokens: int = Field(
        default=150,
        description="Maximum tokens for sampling requests"
    )
    sampling_timeout: float = Field(
        default=10.0,
        description="Timeout for sampling requests in seconds"
    )
```

### Testing Requirements

- [ ] Test sampling availability detection
- [ ] Test fallback when sampling unavailable
- [ ] Test sampling timeout handling
- [ ] Test sampling error handling
- [ ] Test response quality with/without sampling
- [ ] Performance benchmarks with sampling enabled

### Dependencies

- FastMCP 2.0+ with sampling support
- MCP protocol version with sampling capability
- Client support for sampling (Claude Desktop, etc.)

### Related

- MCP Protocol Specification: Sampling
- FastMCP Documentation
- Issue #XXX: Improve Swiss German translations

### Priority

**Medium** - Enhancement that improves user experience but not critical for core functionality.

Start with:
1. Swiss German cultural explanations (high value, low latency impact)
2. Safety warnings (critical content, worth the latency)
3. Historical trend summaries (complex analysis benefit)
