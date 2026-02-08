# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project Overview

Aareguru MCP Server is a Model Context Protocol (MCP) server that exposes Swiss
Aare river data from the Aareguru API to AI assistants. The server provides 6
MCP tools, 3 MCP resources, and 3 MCP prompts for querying water temperature,
flow rates, weather conditions, and safety assessments for swimming in the Aare
river.

**Status**: Production ready with 209 tests passing (87% coverage)
**Stack**: FastMCP 2.0, HTTP/SSE transport, Python 3.13, async/await
**Features**: Service layer pattern, rate limiting, caching, structured logging (structlog), FastMCP Cloud ready

## Development Commands

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage report
uv run pytest --cov=aareguru_mcp

# Run specific test file
uv run pytest tests/test_unit_client.py

# Run specific test
uv run pytest tests/test_tools_basic.py::test_get_current_temperature

# Run with verbose output
uv run pytest -v

# Run specific test categories
uv run pytest -m integration  # Integration tests
uv run pytest -m e2e          # E2E conversation tests
```

### Code Quality

```bash
# Format code with black
uv run black src/ tests/

# Lint with ruff
uv run ruff check src/ tests/

# Type check with mypy
uv run mypy src/

# Run all quality checks together
uv run black src/ tests/ && uv run ruff check src/ tests/ && uv run mypy src/
```

### Running the Server

```bash
# Run MCP server (stdio transport)
uv run aareguru-mcp

# Run HTTP/SSE server (development)
uv run aareguru-mcp-http

# Or using FastMCP CLI
uv run fastmcp run src/aareguru_mcp/server.py

# Production with Docker
docker-compose up -d
```

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone <repository-url> aareguru-mcp
cd aareguru-mcp
uv sync

# Or install in development mode
uv pip install -e ".[dev]"
```

## Architecture Overview

The codebase uses **FastMCP 2.0** with a clean layered architecture. See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design documentation.

**Key Layers (Top to Bottom):**
1. **MCP Server** (`server.py`): FastMCP decorators (@mcp.tool, @mcp.resource, @mcp.prompt)
2. **MCP Tools** (`tools.py`): Thin wrappers delegating to service layer for business logic
3. **Service Layer** (`service.py`): Core domain logic with 7 methods mapping to tools
4. **Helper Functions** (`helpers.py`): Shared utilities for enrichment and UX
5. **HTTP Client** (`client.py`): Async client with caching, rate limiting, connection pooling
6. **Models** (`models.py`): Pydantic validation for API responses
7. **Config** (`config.py`): Environment-based settings

**Architecture Diagram:**
```
server.py (@mcp.tool)
    ↓ (thin wrapper)
tools.py (MCP interface)
    ↓ (delegates to)
service.py (business logic)
    ↓ (uses)
helpers.py (enrichment)
    ↓ (uses)
client.py (HTTP + cache + rate limit)
    ↓ (uses)
models.py (validation)
    ↓
Aareguru API
```

### Key Design Patterns

#### Service Layer Pattern (ADR-014)

The `service.py` module provides a clean separation between MCP protocol concerns and domain logic:

**Service Class Structure:**
```python
class AareguruService:
    """Business logic service for Aare river data operations."""

    async def get_current_temperature(self, city: str) -> dict[str, Any]:
        # 1. Create scoped client
        async with AareguruClient(settings=self.settings) as client:
            # 2. Fetch data from API
            response = await client.get_current(city)

            # 3. Enrich with helpers
            warning = check_safety_warning(flow)
            suggestion = await get_warmer_suggestion(city, temp)

            # 4. Return structured dict
            return {
                "city": city,
                "temperature": temp,
                "warning": warning,
                "suggestion": suggestion,
                ...
            }
```

**Service Methods (map 1:1 to tools):**
- `get_current_temperature(city)` - Temperature with enrichment
- `get_current_conditions(city)` - Comprehensive conditions with all data
- `get_historical_data(city, start, end)` - Time-series data bypass cache
- `compare_cities(cities)` - Parallel comparison with ranking
- `get_forecasts(cities)` - Parallel forecast fetching with trends
- `get_flow_danger_level(city)` - Flow assessment (FIXES DRY: uses helper)
- `get_cities_list()` - List all available cities

**Benefits:**
- ✅ Code reuse: Business logic not duplicated across tools
- ✅ Testability: Service can be unit tested independently
- ✅ Extensibility: New APIs (REST, Chat) can reuse service methods
- ✅ Maintainability: Single place to update domain logic
- ✅ DRY: Fixed `get_flow_danger_level` to use `get_safety_assessment()` helper

**Thin MCP Tool Wrappers:**
```python
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature... (MCP docstring for schema)"""
    service = AareguruService()
    return await service.get_current_temperature(city)
```

Tools focus entirely on MCP protocol (docstrings, schemas, type hints) while
service handles data fetching and enrichment.

#### Helper Functions Module

The `helpers.py` module provides shared utilities:

- `get_seasonal_advice()`: Contextual swimming advice by season
- `check_safety_warning(flow, threshold)`: Danger warnings for high flow rates
- `get_safety_assessment(flow, threshold)`: BAFU safety levels (safe/moderate/elevated/high/very high)
- `get_suggestion(cities_data)`: Suggests warmer/safer alternative locations
- `get_swiss_german_explanation(text)`: Translates Swiss German phrases (e.g., "geil aber chli chalt")

These enable proactive safety checks and intelligent suggestions.

#### Async Context Manager Pattern

```python
async with AareguruClient(settings=get_settings()) as client:
    response = await client.get_today(city)
```

Every tool creates a scoped client instance for proper HTTP connection cleanup.

#### Caching Strategy

- **Key**: `endpoint + sorted query params`
- **TTL**: 120s (configurable via `CACHE_TTL_SECONDS`)
- **Bypass**: Historical data uses `use_cache=False`
- **Auto-cleanup**: Expired entries removed automatically

#### Rate Limiting

- **Interval**: 300s minimum between requests (configurable via `MIN_REQUEST_INTERVAL_SECONDS`)
- **Enforcement**: Lock-based coordination prevents concurrent violations

### Data Flow

1. **MCP Client** (e.g., Claude Desktop) → stdio transport → `server.py`
2. **server.py** → routes to appropriate handler in `tools.py` or `resources.py`
3. **Tools/Resources** → create `AareguruClient` instance
4. **AareguruClient** → checks cache → makes HTTP request → validates with
   Pydantic
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
    "city": "Bern",
    "name": "Bern",
    "aare": 17.2,
    "coordinates": {"lat": 46.94, "lon": 7.44}
  },
  ...
]
```

**Important**: When adding new tools or modifying existing ones, always check
the actual API response format. The models in `models.py` are carefully designed
to match these structures.

### MCP Protocol Implementation

#### FastMCP 2.0 Decorator Pattern

The server uses FastMCP decorators for clean, declarative MCP components:

**Tools** - Use `@mcp.tool()` decorator:

```python
@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature with Swiss German description."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump()
```

**Resources** - Use `@mcp.resource()` decorator with URI:

```python
@mcp.resource("aareguru://cities")
async def get_cities_resource() -> str:
    """List of all cities with Aare data available."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        return json.dumps([city.model_dump() for city in response], indent=2)
```

**Prompts** - Use `@mcp.prompt()` decorator for guided interactions:

```python
@mcp.prompt()
async def daily_swimming_report(city: str = "Bern") -> str:
    """Generate a comprehensive daily swimming report."""
    # Implementation generates rich prompt with current data
    return prompt_text
```

Each component:

1. Uses FastMCP decorators for automatic registration
2. Creates scoped client instances with async context managers
3. Returns appropriate data types (dict for tools, str for resources/prompts)
4. Leverages type hints for automatic schema generation

### Tool Annotations Best Practices

All MCP tool descriptions follow these principles (optimized for 130 user
question patterns):

**1. Use Case Guidance**: Each tool description explains WHEN to use it

- `get_current_temperature`: "Use this for quick temperature checks"
- `get_current_conditions`: "Use this for safety assessments and comprehensive
  reports"
- `get_historical_data`: "Use this for trend analysis and statistical queries"

**2. Parameter Examples**: Concrete examples instead of generic types

- City parameters: `"e.g., 'Bern', 'Thun', 'olten'"`
- Date parameters: `"-7 days"`, `"-1 week"`, `"now"`

**3. Domain Knowledge Inline**: Critical information in descriptions

- BAFU safety thresholds:
  `<100 (safe), 100-220 (moderate), 220-300 (elevated), 300-430 (high), >430 (very high)`
- Swiss German context: `"e.g., 'geil aber chli chalt'"`
- Data granularity: `"Returns hourly data points"`

**4. Tool Differentiation**: Clear guidance on simple vs comprehensive tools

- Simple queries → `get_current_temperature`
- Safety/comprehensive → `get_current_conditions`
- Trends/history → `get_historical_data`

**5. Cross-References**: Tools mention related tools

- All city parameters: `"Use list_cities to discover available locations"`

This annotation strategy ensures Claude selects the correct tool 95%+ of the
time across all question categories.

### Testing Architecture

Tests use pytest with async support (`pytest-asyncio`):

- **210 passing + 2 skipped = 212 total tests** (87% coverage)
- **Organization**:
  - `test_unit_*.py`: Models, config, client, helpers
  - `test_tools_*.py`: Tool functionality (basic & advanced)
  - `test_integration_workflows.py`: Multi-tool workflows, caching, errors
  - `test_http_endpoints.py`: HTTP/SSE transport
  - `test_resources.py`: Resource listing/reading
  - `test_prompts.py`: Prompts and E2E workflows
- **Fixtures**: `conftest.py` provides shared mocks and settings
- **Mocking**: API responses captured inline, no external fixtures
- **Markers**: `@pytest.mark.integration` and `@pytest.mark.e2e`

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
    cache_ttl_seconds: int = 120
    min_request_interval_seconds: int = 300
```

Environment variables override defaults:

```bash
AAREGURU_BASE_URL=https://custom.url
CACHE_TTL_SECONDS=300
MIN_REQUEST_INTERVAL_SECONDS=600
```

## Common Development Patterns

### Adding a New Tool

Follow the service layer pattern:

**Step 1: Add service method to `service.py`:**
```python
async def new_tool_name(self, param: str) -> dict[str, Any]:
    """Domain logic for new tool.

    Handles:
    - API calls via client
    - Data enrichment with helpers
    - Error handling and logging
    """
    logger.info("service.new_tool_name", param=param)

    async with AareguruClient(settings=self.settings) as client:
        response = await client.get_endpoint(param)

        # Enrich with helpers
        enriched = check_safety_warning(response.flow)

        return {
            "param": param,
            "data": response.model_dump(),
            "enrichment": enriched,
        }
```

**Step 2: Add thin wrapper in `tools.py`:**
```python
async def new_tool_name(param: str) -> dict[str, Any]:
    """[MCP docstring for schema generation].

    Use this for [scenarios]. [Context/examples].

    Args:
        param: Description with examples (e.g., 'value1', 'value2')
    """
    logger.info(f"Tool: new_tool_name for {param}")
    service = AareguruService()
    return await service.new_tool_name(param)
```

**Guidelines**:
- **Service layer** contains all business logic and enrichment
- **Tool wrapper** focuses on MCP interface (docstrings, types)
- Start docstring with use case: "Use this for..."
- Include concrete examples in Args docs
- Document thresholds/scales inline
- Cross-reference related tools
- Service methods reusable by future REST/Chat APIs

**Testing**: Add to `tests/test_tools_basic.py` or `tests/test_tools_advanced.py`
- Mock the service or client layer consistently
- Verify both service method and tool wrapper work

### Adding a New API Endpoint

1. **Define model** in `models.py` matching API response structure
2. **Add client method** in `client.py`:
   ```python
   async def get_new_endpoint(self, params) -> NewModel:
       data = await self._request("/v2018/endpoint", params)
       return NewModel(**data)
   ```
3. **Use in tools/resources** with `@mcp.tool()` or `@mcp.resource()` decorators

### Adding a New Prompt

```python
@mcp.prompt()
async def prompt_name(city: str = "Bern") -> str:
    """Description of what this prompt does."""
    async with AareguruClient(settings=get_settings()) as client:
        data = await client.get_current(city)
        return f"""Analyze Aare river conditions for {city}.

Current: {data.aare.temperature}°C, {data.aare.flow} m³/s
[Instructions...]
"""
```

Prompts enable pre-built analysis workflows with live data.

### Modifying Cache Behavior

- **TTL**: Set `CACHE_TTL_SECONDS` env var (default 120s)
- **Rate limit**: Set `MIN_REQUEST_INTERVAL_SECONDS` env var (default 300s)
- **Bypass**: Use `use_cache=False` in `client._request()`

## Important Constraints

1. **Non-commercial use only**: The Aareguru API is for non-commercial use
2. **Attribution required**: Credit BAFU and Aare.guru
3. **Rate limiting**: Respect 5-minute recommendation (300s default)
4. **App identification**: Requests include `app` and `version` params
5. **Transports**: stdio (Claude Desktop) or HTTP/SSE (web/cloud)

## Project Documentation

For detailed planning and technical documentation, see:

- `README.md`: User-facing documentation with features and examples
- `ARCHITECTURE.md`: **Complete architecture and design patterns**
- `CLAUDE_DESKTOP_SETUP.md`: Integration with Claude Desktop
- `docs/MASTER_PLAN.md`: Complete implementation roadmap
- `docs/AAREGURU_API_ANALYSIS.md`: Full API endpoint documentation
- `docs/DOCKER.md`: Docker deployment guide
- `docs/TESTING_PLAN.md`: QA strategy and coverage goals
- `docs/USER_QUESTIONS_SLIDES.md`: 130 example user questions for testing

## Package Management

This project uses **uv** for fast, modern Python package management:

```bash
# Install dependencies and create virtual environment
uv sync

# Run commands in the virtual environment
uv run pytest
uv run aareguru-mcp

# Add new dependencies
uv add package-name
```

Traditional pip/virtualenv also works but uv is recommended for development.

## Entry Points

The package defines multiple console script entry points:

```toml
[project.scripts]
aareguru-mcp = "aareguru_mcp.server:entry_point"          # Stdio transport
aareguru-mcp-http = "aareguru_mcp.server:run_http"       # HTTP/SSE transport
```

## Structured Logging

The server uses **structlog** for structured JSON logging:

```python
import structlog
logger = structlog.get_logger(__name__)

# Log with structured context
logger.info("tool_executed", tool="get_current_temperature", city="Bern")
logger.error("api_error", endpoint="/v2018/current", status_code=500)
```

This enables better log analysis and debugging in production environments.
