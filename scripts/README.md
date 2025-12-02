# MCP Server Testing Automation

This directory contains automated tests that simulate MCP Inspector usage.

## Quick Start

### Run Automated HTTP Tests

Test the running MCP HTTP server:

```bash
# Server must be running on http://localhost:8000
uv run python scripts/test_mcp_http.py

# Or test a different URL
uv run python scripts/test_mcp_http.py --url http://localhost:8000
```

### What Gets Tested

The automated tests cover:

1. **Health Endpoint** - Verifies server is responsive
2. **Metrics Endpoint** - Checks monitoring data
3. **SSE Endpoint** - Confirms SSE endpoint is reachable
4. **Messages Endpoint** - Validates request handling

## Integration with CI/CD

The tests run automatically on every push via GitHub Actions (`.github/workflows/test.yml`):

```yaml
- Unit tests with pytest
- Start HTTP server
- Run integration tests
- Report results
```

## Manual Inspector Testing

For full interactive testing with MCP Inspector:

```bash
# Terminal 1: Start server
docker-compose up

# Terminal 2: Start MCP Inspector
npx @modelcontextprotocol/inspector

# Configure Inspector:
# - URL: http://localhost:8000/sse
# - Transport: SSE
```

## Extending the Tests

To add more automated tests, edit `scripts/test_mcp_http.py`:

```python
async def test_my_feature(self) -> bool:
    """Test description."""
    print("🧪 Testing my feature...")
    # Your test code here
    return True
```

Then add it to `run_all_tests()`:

```python
results['my_feature'] = await self.test_my_feature()
```

## Limitations

The automated tests currently focus on:
- HTTP endpoint availability
- Basic request/response validation
- Server health checks

For full MCP protocol testing (tools, resources, prompts), use:
- Existing pytest integration tests in `tests/`
- Manual testing with MCP Inspector for UX validation
- The MCP Inspector provides the best interactive testing experience

## Future Enhancements

Potential additions:
- Full SSE connection simulation
- Automated tool invocation tests
- Resource access validation
- Performance benchmarking
- Load testing scenarios
