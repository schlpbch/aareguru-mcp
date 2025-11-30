# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Aareguru MCP Server is a Model Context Protocol (MCP) server that exposes Swiss Aare river data from the Aareguru API to AI assistants. The server provides 5 MCP tools and 4 MCP resources for querying water temperature, flow rates, weather conditions, and safety assessments for swimming in the Aare river.

**Status**: Phase 1 complete - Production ready with 42/42 tests passing (81% coverage)

## Development Commands

### Testing
```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=aareguru_mcp

# Run specific test file
pytest tests/test_client.py

# Run specific test
pytest tests/test_tools.py::test_get_current_temperature

# Run with verbose output
pytest -v
```

### Code Quality
```bash
# Format code with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/

# Run all quality checks together
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

### Running the Server
```bash
# Run MCP server (stdio transport)
python -m aareguru_mcp.server

# Or use the entry point
aareguru-mcp
```

### Installation
```bash
# Install package in development mode with all dependencies
pip install -e ".[dev]"

# Install production dependencies only
pip install -e .
```

## Architecture Overview

### Layer Structure

The codebase follows a clean layered architecture:

1. **MCP Server Layer** (`server.py`): Entry point that implements MCP protocol handlers
2. **Tools & Resources Layer** (`tools.py`, `resources.py`): Business logic for MCP operations
3. **HTTP Client Layer** (`client.py`): Async HTTP client with caching and rate limiting
4. **Data Models Layer** (`models.py`): Pydantic models for API responses
5. **Configuration Layer** (`config.py`): Settings management with pydantic-settings

### Key Design Patterns

#### Async Context Manager Pattern
The `AareguruClient` uses async context managers for proper resource cleanup:

```python
async with AareguruClient(settings=get_settings()) as client:
    response = await client.get_today(city)
```

Every tool function creates a fresh client instance and closes it properly. This ensures HTTP connections are cleaned up.

#### Caching Strategy
The HTTP client implements in-memory caching with TTL:
- Cache key: `endpoint + sorted query params`
- TTL: 120 seconds (configurable via `CACHE_TTL_SECONDS`)
- Automatic expiration and cleanup
- Historical data endpoints bypass cache (`use_cache=False`)

#### Rate Limiting
Built-in rate limiting prevents API abuse:
- Minimum interval between requests: 300 seconds (configurable)
- Lock-based coordination to prevent concurrent violations
- Tracks `_last_request_time` to enforce delays

### Data Flow

1. **MCP Client** (e.g., Claude Desktop) → stdio transport → `server.py`
2. **server.py** → routes to appropriate handler in `tools.py` or `resources.py`
3. **Tools/Resources** → create `AareguruClient` instance
4. **AareguruClient** → checks cache → makes HTTP request → validates with Pydantic
5. **Response** → formatted as JSON → returned via MCP protocol

### Critical API Response Structures

The Aareguru API has **different response structures** for different endpoints:

#### `/v2018/today` (TodayResponse)
Flat structure with temperature at top level:
```python
{
  "aare": 17.2,              # Direct float, not nested
  "aare_prec": 17.23,
  "text": "geil aber chli chalt",
  "name": "Bern",
  "time": 1234567890
}
```

#### `/v2018/current` (CurrentResponse)
Nested structure with Aare data in sub-object:
```python
{
  "aare": {                  # Nested object
    "temperature": 17.2,
    "flow": 245,
    "location": "Bern"
  },
  "weather": {...},
  "weatherprognosis": [...]
}
```

#### `/v2018/cities` (CitiesResponse)
Returns array directly (not wrapped in object):
```python
[
  {
    "city": "bern",
    "name": "Bern",
    "aare": 17.2,
    "coordinates": {"lat": 46.94, "lon": 7.44}
  },
  ...
]
```

**Important**: When adding new tools or modifying existing ones, always check the actual API response format. The models in `models.py` are carefully designed to match these structures.

### MCP Protocol Implementation

#### Resources vs Tools
- **Resources** (`resources.py`): Static, read-only data access via URI scheme (`aareguru://`)
- **Tools** (`tools.py`): Dynamic queries with parameters, executed on demand

#### Tool Design Pattern
All tools follow this pattern:
```python
async def tool_name(params) -> dict[str, Any]:
    logger.info(f"Tool operation: {params}")
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.api_method(params)
        return formatted_dict
```

Each tool:
1. Logs the operation
2. Creates a scoped client instance
3. Calls appropriate client method
4. Returns plain dictionaries (not Pydantic models) for JSON serialization

### Testing Architecture

Tests use pytest with async support (`pytest-asyncio`):
- **conftest.py**: Shared fixtures and mock settings
- **test_*.py**: Organized by module (client, tools, resources, models)
- **Mocking strategy**: Real API responses captured in test code, not external fixtures
- **Coverage target**: 81% overall (100% for config/models, 77-81% for client/tools)

Key testing patterns:
```python
# Mock httpx responses
mock_response = Mock()
mock_response.json.return_value = {...}
mock_client.get = AsyncMock(return_value=mock_response)
```

### Configuration Management

Uses `pydantic-settings` with environment variable support:
```python
class Settings(BaseSettings):
    aareguru_base_url: str = "https://aareguru.existenz.ch"
    app_name: str = "aareguru-mcp"
    app_version: str = "0.1.0"
    cache_ttl_seconds: int = 120
    min_request_interval_seconds: int = 300
```

Environment variables override defaults (prefix with nothing, direct match):
```bash
AAREGURU_BASE_URL=https://custom.url
CACHE_TTL_SECONDS=300
```

## Common Development Patterns

### Adding a New Tool

1. Add tool definition to `server.py` `handle_list_tools()`:
```python
Tool(
    name="tool_name",
    description="What it does",
    inputSchema={...}
)
```

2. Add route handler in `server.py` `handle_call_tool()`:
```python
elif name == "tool_name":
    result = await tools.tool_name(arguments["param"])
```

3. Implement in `tools.py`:
```python
async def tool_name(param: str) -> dict[str, Any]:
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_endpoint(param)
        return {"formatted": "response"}
```

4. Add tests in `tests/test_tools.py`

### Adding a New API Endpoint

1. Define Pydantic model in `models.py` matching API response structure
2. Add client method in `client.py`:
```python
async def get_new_endpoint(self, params) -> NewResponseModel:
    data = await self._request("/v2018/endpoint", params)
    return NewResponseModel(**data)
```
3. Use in tools/resources as needed

### Modifying Cache Behavior

Cache configuration is in `config.py`:
- `cache_ttl_seconds`: How long to cache responses
- `min_request_interval_seconds`: Minimum delay between API calls

To bypass cache for specific endpoints, use `use_cache=False` in `_request()`.

## Important Constraints

1. **Non-commercial Use**: The Aareguru API is for non-commercial use only
2. **Attribution Required**: Must credit BAFU and Aare.guru
3. **Rate Limiting**: Respect 5-minute recommendation for repeated queries
4. **App Identification**: All requests include `app` and `version` parameters
5. **Stdio Transport Only**: Currently only supports stdio (no HTTP/SSE yet - see Phase 3 plans)

## Project Documentation

For detailed planning and API documentation, see:
- `MASTER_PLAN.md`: Complete implementation roadmap
- `AAREGURU_API_ANALYSIS.md`: Full API endpoint documentation
- `IMPLEMENTATION_PLAN.md`: Technical architecture details
- `TESTING_PLAN.md`: QA strategy and coverage goals
- `CLAUDE_DESKTOP_CONFIG.md`: Integration with Claude Desktop

## Package Management

This project uses standard Python packaging with `pyproject.toml`. While the original plan recommended `uv`, standard pip/virtualenv works fine:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"
```

## Entry Points

The package defines a console script entry point:
```toml
[project.scripts]
aareguru-mcp = "aareguru_mcp.server:main"
```

After installation, run with `aareguru-mcp` command.
