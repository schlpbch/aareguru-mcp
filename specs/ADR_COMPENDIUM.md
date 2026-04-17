# Aareguru MCP Server - Architecture Decision Records (ADR) Compendium

**Document Version**: 2.0.0 **Last Updated**: 2026-04-17 **Total ADRs**: 17 (17 Accepted)

**Related Documents**:
- [README.md](../README.md) - User guide and installation
- [ARCHITECTURE.md](../ARCHITECTURE.md) - Detailed architecture documentation
- [CLAUDE.md](../CLAUDE.md) - Development guidance and patterns
- [CHANGELOG.md](../CHANGELOG.md) - Version history

---

## Status Legend

- ✅ **Accepted** - Currently in use and actively maintained
- 🔄 **Proposed** - Under consideration, not yet implemented
- ⛔ **Superseded** - Replaced by another ADR (see cross-reference)
- 🗑️ **Deprecated** - No longer applicable, kept for historical context

---

## Quick Reference by Category

### Core Architecture

- [ADR-001: Use FastMCP 3.x for MCP Protocol](#adr-001-use-fastmcp-3x-for-mcp-protocol) ✅
- [ADR-002: Pydantic v2 for Data Models](#adr-002-pydantic-v2-for-data-models) ✅
- [ADR-003: Async/Await with httpx for API Calls](#adr-003-asyncawait-with-httpx-for-api-calls) ✅
- [ADR-004: Python 3.11+ as Minimum Version](#adr-004-python-311-as-minimum-version) ✅
- [ADR-005: Layered Architecture Pattern](#adr-005-layered-architecture-pattern) ✅

### Design Patterns

- [ADR-006: Helper Functions Module Pattern](#adr-006-helper-functions-module-pattern) ✅
- [ADR-007: Async Context Manager Pattern for Resource Management](#adr-007-async-context-manager-pattern-for-resource-management) ✅
- [ADR-008: Caching Strategy](#adr-008-caching-strategy) ✅
- [ADR-009: Rate Limiting Strategy](#adr-009-rate-limiting-strategy) ✅

### Quality & Observability

- [ADR-010: Structured Logging with structlog](#adr-010-structured-logging-with-structlog) ✅
- [ADR-011: pytest Testing with 80%+ Coverage](#adr-011-pytest-testing-with-80-coverage) ✅
- [ADR-012: MyPy Strict Type Checking](#adr-012-mypy-strict-type-checking) ✅

### Transport & Deployment

- [ADR-013: HTTP/SSE and Stdio Transports](#adr-013-httpsse-and-stdio-transports) ✅

### Production Ready Enhancements

- [ADR-014: Service Layer Pattern](#adr-014-service-layer-pattern) ✅
- [ADR-015: FastMCP Cloud Deployment](#adr-015-fastmcp-cloud-deployment) ✅

### Interactive UI Layer

- [ADR-016: FastMCP Apps with prefab_ui](#adr-016-fastmcp-apps-with-prefab_ui) ✅
- [ADR-017: Visual Design System & Embedded Assets](#adr-017-visual-design-system--embedded-assets) ✅

---

## ADR-001: Use FastMCP 3.x for MCP Protocol

**Status**: ✅ Accepted **Date**: 2025-12-01 **Updated**: 2026-04-17 **Context**: Core Architecture

### [ADR-001] Decision

Use **FastMCP 3.x** (Anthropic's MCP framework) with the `[apps]` extra for implementing the Model Context Protocol server, including interactive UI apps.

**Rationale**:

- **Minimal Overhead**: Lightweight framework designed specifically for Python MCP servers
- **Async-First**: Built on Python's async/await for efficient concurrency
- **Declarative API**: Simple decorators (`@mcp.tool`, `@mcp.resource`, `@mcp.prompt`, `@app.ui`) for clean definitions
- **Type Safety**: Integrates seamlessly with Pydantic for automatic validation and schema generation
- **Protocol Compliance**: Full MCP specification compliance with automatic message handling
- **Apps Extra**: `fastmcp[apps]` enables interactive UI apps rendered directly in conversations via `prefab_ui`

### [ADR-001] Installation

```toml
# pyproject.toml
[project]
dependencies = [
    "fastmcp[apps]>=3.2.3",   # [apps] extra required for FastMCPApp and prefab_ui
    "prefab-ui>=0.18.0",
]
```

### [ADR-001] Example

```python
from fastmcp import FastMCP, FastMCPApp
from prefab_ui.app import PrefabApp

mcp = FastMCP("aareguru")

# Standard MCP tool
@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature for an Aare location."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump()

# Interactive UI app
conditions_app = FastMCPApp("conditions")

@conditions_app.ui()
async def conditions_dashboard(city: str = "Bern") -> PrefabApp:
    """Render interactive conditions dashboard."""
    ...
```

### [ADR-001] Benefits

- **Clean API**: Decorators make component registration explicit and readable
- **Automatic Schema Generation**: Type hints generate MCP tool schemas automatically
- **Standards Alignment**: Follows industry best practices for MCP servers
- **Community**: Active maintenance from Anthropic with regular updates
- **UI Apps**: `FastMCPApp` renders rich interactive UIs without a separate frontend

### [ADR-001] Related ADRs

- [ADR-003](#adr-003-asyncawait-with-httpx-for-api-calls) - Async operations with httpx
- [ADR-007](#adr-007-async-context-manager-pattern-for-resource-management) - Resource management
- [ADR-016](#adr-016-fastmcp-apps-with-prefab_ui) - Interactive UI apps layer

---

## ADR-002: Pydantic v2 for Data Models

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Core Architecture

### [ADR-002] Decision

Use **Pydantic v2** for all data models, DTOs, and request/response validation against Aareguru API.

**Benefits**:

- **Type Safety**: Full type hints with runtime validation
- **Performance**: ~5-10x faster than v1 with Rust-backed validation
- **JSON Schema**: Automatic OpenAPI/JSON schema generation
- **Serialization**: Built-in `model_dump()` and `model_dump_json()` methods
- **Field Validators**: Custom validation logic with clear error messages
- **API Alignment**: Models match exact Aareguru API response structures

### [ADR-002] Example

```python
from pydantic import BaseModel, Field

class AareData(BaseModel):
    temperature: float = Field(..., ge=-10, le=40)
    flow: int = Field(..., ge=0)
    location: str

class TodayResponse(BaseModel):
    aare: float        # Flat structure — temperature at top level
    aare_prec: float
    text: str          # Swiss German description
    name: str
    time: int

class CurrentResponse(BaseModel):
    aare: AareData     # Nested structure
    weather: dict
    weatherprognosis: list[dict]
```

### [ADR-002] API Response Structures

Critical: Different endpoints return different structures:

| Endpoint | Structure | Model |
|----------|-----------|-------|
| `/v2018/today` | Flat (temperature at top level) | `TodayResponse` |
| `/v2018/current` | Nested (aare as sub-object) | `CurrentResponse` |
| `/v2018/cities` | Array (not wrapped) | `list[CityData]` |

---

## ADR-003: Async/Await with httpx for API Calls

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Core Architecture

### [ADR-003] Decision

Use **async/await pattern with httpx** (async HTTP client) for all Aareguru API calls.

**Rationale**:

- **Non-Blocking**: Async operations prevent blocking during I/O
- **Concurrency**: Handle multiple simultaneous requests efficiently
- **httpx**: Modern replacement for requests with native async support
- **Timeout Handling**: Built-in timeout and retry mechanisms
- **Gzip Support**: Automatic compression for bandwidth efficiency

### [ADR-003] Example

```python
import httpx

class AareguruClient:
    async def __aenter__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def get_today(self, city: str = "Bern") -> TodayResponse:
        params = {"city": city, "app": "aareguru-mcp", "version": "4.3.0"}
        response = await self.client.get(f"{self.BASE_URL}/v2018/today", params=params)
        response.raise_for_status()
        return TodayResponse(**response.json())
```

### [ADR-003] Benefits

- **Efficiency**: Single-threaded async handles 1000+ concurrent connections
- **Resource Usage**: Minimal memory overhead vs threading
- **Error Handling**: Structured exception handling with timeouts
- **Testing**: Easy to mock async calls with pytest-asyncio

---

## ADR-004: Python 3.11+ as Minimum Version

**Status**: ✅ Accepted **Date**: 2025-12-01 **Updated**: 2026-04-17 **Context**: Core Architecture

### [ADR-004] Decision

Require **Python 3.11+** as the minimum supported version. Production environment currently runs Python 3.14.

**Rationale**:

- **PEP 604 Union Syntax**: `X | Y` instead of `Union[X, Y]`
- **Type Hints Standard**: `dict[str, float]` without `Dict` import
- **ExceptionGroup**: Better exception handling for concurrent operations
- **Asyncio Improvements**: Enhanced async/await support
- **Security**: Modern cryptography and TLS support

### [ADR-004] Configuration

```toml
# pyproject.toml
[project]
requires-python = ">=3.11"

[tool.mypy]
python_version = "3.11"

[tool.ruff]
target-version = "py310"   # Conservative lint target
```

### [ADR-004] Current Runtime

The development and production environment uses Python 3.14 (latest stable). The `>=3.11` minimum ensures broad compatibility while the codebase takes advantage of newer features available on 3.14.

---

## ADR-005: Layered Architecture Pattern

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Core Architecture

### [ADR-005] Decision

Use a **clean layered architecture** with clear separation of concerns across six layers (including the UI apps layer added in v4.x).

### [ADR-005] Architecture Layers

```
┌─────────────────────────────────────────┐
│ 0. UI Apps Layer (apps/)                │
│    FastMCPApp + prefab_ui components    │
│    - 7 interactive app UIs              │
│    - Design token system                │
│    - Embedded fonts & assets            │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ 1. MCP Server Layer (server.py)         │
│    @mcp.tool, @mcp.resource, @mcp.prompt│
│    - Tool definitions                   │
│    - Resource URIs                      │
│    - Prompt contexts                    │
│    - App provider registration          │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 2. Business Logic Layer                  │
│    (tools.py, resources.py, helpers.py)  │
│    - Domain logic                        │
│    - Data transformations                │
│    - Safety assessments                  │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 3. Service Layer (service.py)            │
│    - Orchestrates client + helpers       │
│    - Reusable by tools, apps, future APIs│
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 4. HTTP Client Layer (client.py)         │
│    - API communication                   │
│    - Caching logic                       │
│    - Rate limiting                       │
│    - Error handling                      │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 5. Models Layer (models.py)              │
│    - Pydantic validation                 │
│    - Request/response structures         │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 6. Configuration Layer (config.py)       │
│    - Environment settings                │
│    - Constants                           │
└──────────────────────────────────────────┘
```

### [ADR-005] Layer Responsibilities

| Layer | Responsibility | Key Files |
|-------|-----------------|-----------|
| UI Apps | Interactive dashboards, charts, tables | `apps/*.py`, `apps/_constants.py` |
| MCP Server | Protocol handling, schema generation | `server.py` |
| Business Logic | Domain rules, enrichment | `tools.py`, `helpers.py` |
| Service | Orchestration, reuse across interfaces | `service.py` |
| HTTP Client | API communication, caching, rate limiting | `client.py` |
| Models | Data validation, type safety | `models.py` |
| Config | Environment-based settings | `config.py` |

### [ADR-005] Related ADRs

- [ADR-014](#adr-014-service-layer-pattern) - Service layer detail
- [ADR-016](#adr-016-fastmcp-apps-with-prefab_ui) - UI apps layer detail

---

## ADR-006: Helper Functions Module Pattern

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-006] Decision

Maintain dedicated helper modules for shared business logic. Two separate helper modules exist:

- **`helpers.py`** (top-level): Domain logic used by tools and service layer (safety assessment, Swiss German translation, suggestions)
- **`apps/_helpers.py`**: UI-specific formatters and badge generators used exclusively by the apps layer

### [ADR-006] Top-Level Helpers (`helpers.py`)

```python
def get_seasonal_advice(month: int) -> str: ...
def check_safety_warning(flow: int, threshold: int = 220) -> str | None: ...
def get_safety_assessment(flow: int, threshold: int = 100) -> str: ...
def get_suggestion(cities_data: list[dict]) -> str: ...
def get_swiss_german_explanation(text: str) -> str: ...
```

### [ADR-006] Apps Helpers (`apps/_helpers.py`)

```python
def _safety_badge(flow: float | None) -> tuple[str, str, str]: ...  # (label, variant, hex_color)
def _fmt_temp(temp: float | None) -> str: ...    # "17.2°" or "—"
def _fmt_flow(flow: float | None) -> str: ...    # "245" or "—"
def _fmt_pct(val: float | None) -> str: ...      # "72%" or "—"
def _fmt_wind(val: float | None) -> str: ...     # "23 km/h" or "—"
def _beaufort(v: float | None) -> tuple[int, str, str]: ...
def _sy_to_emoji(sy: int | None) -> str: ...
def _bafu_level(flow: float | None, gefahrenstufe: int | None) -> int: ...
```

The split keeps UI formatting concerns out of the core domain layer and prevents `apps/` imports leaking into `tools.py`.

---

## ADR-007: Async Context Manager Pattern for Resource Management

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-007] Decision

Use **async context managers** (`async with`) for all HTTP client instantiation to ensure proper connection cleanup.

```python
async with AareguruClient(settings=get_settings()) as client:
    response = await client.get_today(city)
    return response.model_dump()
```

**Benefits**: Guarantees cleanup even on exceptions, enables connection pooling, clear acquisition/release points, easy to mock in tests.

---

## ADR-008: Caching Strategy

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-008] Decision

Implement **time-based caching** in the HTTP client layer with configurable TTL, keyed by endpoint + sorted query parameters.

```python
# Cache key: endpoint + sorted JSON params
# TTL: 120s default (CACHE_TTL_SECONDS env var)
# Bypass: use_cache=False for historical data endpoints
```

### [ADR-008] Configuration

```bash
CACHE_TTL_SECONDS=120              # 2 minutes (default)
MIN_REQUEST_INTERVAL_SECONDS=300   # 5 minutes (default)
```

---

## ADR-009: Rate Limiting Strategy

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-009] Decision

Implement **two complementary rate limiting layers**:

1. **Client-side**: `AareguruClient` enforces minimum interval (300s default) between API requests via async lock — respects Aareguru's non-commercial usage guidelines.
2. **HTTP endpoints**: `slowapi` decorators limit health/metrics endpoint access (60 req/min).

```python
# Client-side rate limiting
class AareguruClient:
    _last_request_time: float = 0.0
    _request_lock: asyncio.Lock = asyncio.Lock()

    async def _enforce_rate_limit(self) -> None:
        async with self._request_lock:
            elapsed = time() - self._last_request_time
            if elapsed < self.settings.min_request_interval_seconds:
                await asyncio.sleep(self.settings.min_request_interval_seconds - elapsed)
            self._last_request_time = time()
```

---

## ADR-010: Structured Logging with structlog

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Quality & Observability

### [ADR-010] Decision

Use **structlog** for structured JSON logging with contextual information throughout the application.

```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("tool_executed", tool="get_current_temperature", city="Bern")
logger.info("app.conditions_dashboard", city="Bern")
logger.error("api_error", endpoint="/v2018/current", status_code=500)
```

All layers (tools, service, apps, client) use structlog with module-scoped loggers. Log output is JSON-structured for observability platform integration.

---

## ADR-011: pytest Testing with 80%+ Coverage

**Status**: ✅ Accepted **Date**: 2025-12-01 **Updated**: 2026-04-17 **Context**: Quality & Observability

### [ADR-011] Decision

Use **pytest** as the testing framework with **≥80% code coverage** target and organized test layers.

### [ADR-011] Current Coverage Status

```
Total tests: 245 collected (239 passing, 5 skipped, 1 pre-existing stale)
Coverage: 83% (target ≥80%)

Coverage by module:
├── client.py          95%
├── config.py          100%
├── helpers.py         97%
├── models.py          94%
├── rate_limit.py      82%
├── resources.py       100%
├── server.py          89%
├── service.py         74%
└── tools.py           71%
```

### [ADR-011] Test Organization

```
tests/
├── conftest.py                     # Shared fixtures and mocks
├── test_apps.py                    # Apps layer tests
├── test_http_endpoints.py          # HTTP/SSE transport
├── test_integration_workflows.py   # Multi-tool workflows, caching
├── test_prompts.py                 # Prompts and E2E workflows
├── test_resources.py               # Resource listing/reading
├── test_tools_advanced.py          # Advanced tool scenarios
├── test_tools_basic.py             # Basic tool functionality
├── test_unit_client.py             # HTTP client unit tests
├── test_unit_config.py             # Configuration tests
├── test_unit_helpers.py            # Helper function tests
├── test_unit_models.py             # Pydantic model validation
├── test_unit_server_helpers.py     # Server helper tests
└── test_unit_service.py            # Service layer unit tests
```

### [ADR-011] Configuration

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--cov=src/aareguru_mcp --cov-report=term-missing"
markers = ["integration: integration tests", "e2e: end-to-end tests"]

[tool.coverage.report]
fail_under = 80
```

### [ADR-011] Running Tests

```bash
uv run pytest                           # All tests
uv run pytest --cov=aareguru_mcp        # With coverage
uv run pytest tests/test_tools_basic.py # Specific file
uv run pytest -m integration            # Integration tests only
```

---

## ADR-012: MyPy Strict Type Checking

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Quality & Observability

### [ADR-012] Decision

Use **MyPy** for static type checking of all Python code.

```toml
[tool.mypy]
python_version = "3.11"
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
strict_optional = true
```

```bash
uv run mypy src/    # Run type checking
```

---

## ADR-013: HTTP/SSE and Stdio Transports

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Transport & Deployment

### [ADR-013] Decision

Support both **stdio transport** (for Claude Desktop) and **HTTP/SSE transport** (for web/cloud).

### [ADR-013] Entry Points

```toml
# pyproject.toml
[project.scripts]
aareguru-mcp      = "aareguru_mcp.server:entry_point"   # Stdio transport
aareguru-mcp-http = "aareguru_mcp.server:run_http"      # HTTP/SSE transport
```

### [ADR-013] HTTP Server Routes

The HTTP server exposes additional operational endpoints beyond MCP:

```python
GET /health    # Health check (rate-limited: 60/min via slowapi)
GET /metrics   # Prometheus metrics (MetricsCollector tracks tool calls)
```

### [ADR-013] Claude Desktop Configuration

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "uv",
      "args": ["run", "aareguru-mcp"],
      "type": "stdio"
    }
  }
}
```

---

## ADR-014: Service Layer Pattern

**Status**: ✅ Accepted **Date**: 2026-02-08 **Context**: Production Ready Enhancements

### [ADR-014] Decision

Introduce a **service layer** (`service.py`) between the MCP tools and the HTTP client, providing reusable business logic and data enrichment.

### [ADR-014] Service Methods

```python
class AareguruService:
    async def get_current_temperature(self, city: str) -> dict[str, Any]: ...
    async def get_current_conditions(self, city: str) -> dict[str, Any]: ...
    async def get_historical_data(self, city: str, start: str, end: str) -> dict[str, Any]: ...
    async def compare_cities(self, cities: list[str]) -> dict[str, Any]: ...
    async def get_forecasts(self, cities: list[str]) -> dict[str, Any]: ...
    async def get_flow_danger_level(self, city: str) -> dict[str, Any]: ...
    async def get_cities_list(self) -> dict[str, Any]: ...
```

Methods map 1:1 to MCP tools. The service is called by both tools (MCP interface) and apps (UI interface), avoiding code duplication.

### [ADR-014] Thin Tool Wrapper Pattern

```python
# tools.py — MCP interface only
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """[MCP docstring for schema generation]"""
    try:
        service = AareguruService()
        return await service.get_current_temperature(city)
    except ValueError as e:
        return {"error": f"Invalid city: {str(e)}"}
    except Exception as e:
        return {"error": f"Failed to get temperature: {str(e)}"}
```

### [ADR-014] Benefits

- **DRY**: Business logic not duplicated between tools and apps
- **Testability**: Service can be unit tested independently
- **Extensibility**: New interfaces (REST, Chat) can reuse service methods

### [ADR-014] Related ADRs

- [ADR-006](#adr-006-helper-functions-module-pattern) - Helpers used by service
- [ADR-016](#adr-016-fastmcp-apps-with-prefab_ui) - Apps call service methods

---

## ADR-015: FastMCP Cloud Deployment

**Status**: ✅ Accepted **Date**: 2026-02-08 **Context**: Deployment & Integration

### [ADR-015] Decision

Use **FastMCP Cloud** for production deployment with automatic scaling, monitoring, and zero-downtime updates.

### [ADR-015] Configuration

```yaml
# .fastmcp/config.yaml
deployment:
  region: "eu-west-1"
  replicas: 2
  max_replicas: 10
  timeout: 30s
  memory: 512Mi

environment:
  LOG_LEVEL: "INFO"
  CACHE_TTL_SECONDS: "120"
  MIN_REQUEST_INTERVAL_SECONDS: "0.1"

health:
  path: "/health"
  interval: 30s

monitoring:
  enabled: true
  metrics_path: "/metrics"
```

### [ADR-015] Installation Options

**Direct URL** (Claude Desktop):
```json
{"mcpServers": {"aareguru": {"url": "https://aareguru.fastmcp.app/mcp"}}}
```

**Bundle file**: Download `aareguru-mcp.mcpb` and drag into Claude Desktop.

---

## ADR-016: FastMCP Apps with prefab_ui

**Status**: ✅ Accepted **Date**: 2026-04-17 **Context**: Interactive UI Layer

### [ADR-016] Decision

Use **FastMCPApp** with the **prefab_ui** component library to render interactive, data-rich UIs directly within AI conversation contexts — no separate frontend required.

**Rationale**:

- **In-Context UI**: Rich dashboards, charts, and tables rendered where the data is requested
- **Zero Frontend Overhead**: No separate React/Vue app, no deployment pipeline for UI
- **Component Library**: `prefab_ui` provides Cards, Grids, Charts, DataTables, Alerts, etc.
- **Server-Rendered**: Apps run on the MCP server, return a `PrefabApp` descriptor that the client renders
- **Reactive**: Each app has a paired `refresh_*` tool for live data updates from the UI

### [ADR-016] App Inventory

Seven apps are registered in `server.py` via `providers=`:

| App | File | UI Pattern | Primary Component |
|-----|------|-----------|-------------------|
| `conditions` | `conditions.py` | Card grid dashboard | Cards, Grid, Alert |
| `history` | `history.py` | Time-series chart | AreaChart |
| `compare` | `compare.py` | Sortable city table | DataTable |
| `forecast` | `forecast.py` | 24h forecast + chart | AreaChart, Grid |
| `intraday` | `intraday.py` | Today's sparkline | AreaChart |
| `city_finder` | `city_finder.py` | Ranked city table | DataTable |
| `safety` | `safety.py` | BAFU danger briefing | Card, Grid |

### [ADR-016] App Structure Pattern

Every app follows the same pattern:

```python
# apps/conditions.py

conditions_app = FastMCPApp("conditions")

# 1. Refresh tool — called from UI button to reload data
@conditions_app.tool()
async def refresh_conditions(city: str) -> dict[str, Any]:
    service = AareguruService()
    return await service.get_current_conditions(city)

# 2. UI function — returns PrefabApp descriptor
@conditions_app.ui()
async def conditions_dashboard(city: str = "Bern") -> PrefabApp:
    service = AareguruService()
    data = await service.get_current_conditions(city)

    with Column(gap=2, cssClass="p-2 max-w-2xl mx-auto") as view:
        # Build component tree using prefab_ui components
        Text("Aare — Bern", cssClass="text-lg font-black ...")
        with Card(...):
            with CardContent(...):
                Text(_fmt_temp(temp), cssClass="text-5xl font-black ...")

    return PrefabApp(
        view=view,
        state={"city": city, "aare": aare},
        stylesheets=[_FONT_CSS],       # Embedded DIN Next LT Pro font
    )
```

### [ADR-016] Service Layer Integration

Apps call `AareguruService` directly — the same service methods used by MCP tools. No data-fetching logic is duplicated.

```
UI request → @conditions_app.ui() → AareguruService → AareguruClient → API
                                  ↑
Same path as: @mcp.tool() ────────┘
```

### [ADR-016] Registration in Server

```python
# server.py
from aareguru_mcp.apps import (
    conditions_app, history_app, compare_app,
    forecast_app, intraday_app, city_finder_app, safety_app,
)

mcp = FastMCP("aareguru", providers=[
    conditions_app, history_app, compare_app,
    forecast_app, intraday_app, city_finder_app, safety_app,
])
```

### [ADR-016] Benefits

- **DRY**: Service layer reused by both tools and apps
- **Isolation**: Each app is a self-contained `FastMCPApp` instance
- **Testability**: Apps can be tested by calling the `@app.ui()` function directly
- **Composability**: `prefab_ui` components are declaratively composed using Python context managers

### [ADR-016] Related ADRs

- [ADR-001](#adr-001-use-fastmcp-3x-for-mcp-protocol) - FastMCPApp requires `fastmcp[apps]`
- [ADR-014](#adr-014-service-layer-pattern) - Service called by apps
- [ADR-017](#adr-017-visual-design-system--embedded-assets) - Design tokens used by all apps

---

## ADR-017: Visual Design System & Embedded Assets

**Status**: ✅ Accepted **Date**: 2026-04-17 **Context**: Interactive UI Layer

### [ADR-017] Decision

Maintain a **centralised design token system** in `apps/_constants.py` that encodes the aare.guru visual identity, enforces WCAG AA colour contrast, and embeds all UI assets (fonts, icons) as inline base64 data URIs — making every `PrefabApp` fully self-contained with no external network dependency.

**Rationale**:

- **Brand Consistency**: All 7 apps share identical colours, typography, and spacing
- **WCAG AA Compliance**: Every colour is validated for ≥4.5:1 contrast ratio; dark mode colours validated separately against dark backgrounds
- **Self-Contained Delivery**: Fonts embedded as base64 WOFF2 data URIs; no CDN or font service required
- **Single Source of Truth**: Changing a colour in `_constants.py` updates all apps automatically
- **Offline Capable**: Apps render correctly in sandboxed or network-restricted environments

### [ADR-017] Design Tokens

```python
# apps/_constants.py — Light mode
_AG_BG_WASSER  = "#2be6ff"  # Aare cyan — water card background
_AG_BG_WETTER  = "#aeffda"  # Mint green — weather card background
_AG_TXT_PRIMARY = "#0f405f"  # Dark blue — main labels
_AG_WASSER_TEMP = "#0877ab"  # Water temperature values (5.1:1 on white)
_AG_WASSER_FLOW = "#357d9e"  # Flow rate values
_AG_AIR_TEMP   = "#0771a8"  # Air temperature (5.1:1 on white)
_AG_BFU        = "#007d76"  # BAFU safety accent (4.6:1 on white)
_AG_SUNNY      = "#f2e500"  # Sunny weather accent
_AG_RADIUS     = "rounded-[3px]"  # Angular Swiss border-radius

class _DK:  # Dark mode equivalents
    TXT_PRIMARY = "#c8e6f8"
    BG_WASSER   = "#0d4a5c"
    BG_WETTER   = "#0a3d24"
    WASSER_TEMP = "#38bdf8"  # sky-400
    WASSER_FLOW = "#7dd3fc"  # sky-300
    AIR_TEMP    = "#38bdf8"
    BFU         = "#2dd4bf"  # teal-400
    SUNNY       = "#fde047"  # yellow-300
    CARD_BG     = "#1a2e3d"
```

### [ADR-017] WCAG AA Colour Contract

All foreground colours are chosen for ≥4.5:1 contrast ratio:

| Token | Light Hex | Ratio on White | Dark Hex | Ratio on `#1a2e3d` |
|-------|-----------|----------------|----------|---------------------|
| BAFU safe | `#007d76` | 4.6:1 | `#2dd4bf` | 9.1:1 |
| Moderat | `#0877ab` | 5.0:1 | `#38bdf8` | 7.9:1 |
| Erhöht | `#b45309` | 4.7:1 | `#fbbf24` | 9.4:1 |
| Hoch | `#dc2626` | 4.5:1 | `#f87171` | 5.9:1 |
| Sehr hoch | `#7f1d1d` | 10.0:1 | `#fca5a5` | 8.3:1 |

### [ADR-017] Embedded Font (DIN Next LT Pro)

```python
# apps/_constants.py
_FONT_FILE = Path(__file__).parent / "assets" / "webfonts" / "DIN-Next-LT-Pro.woff2"
_FONT_B64  = base64.b64encode(_FONT_FILE.read_bytes()).decode()
_FONT_CSS  = (
    "@font-face {"
    "font-family:'DIN Next LT Pro';"
    "src:url('data:font/woff2;base64," + _FONT_B64 + "') format('woff2');"
    "font-weight:100 900;"
    "font-style:normal;font-display:swap;"
    "}"
    "body,*{font-family:'DIN Next LT Pro',ui-sans-serif,system-ui,sans-serif !important;}"
)
```

`_FONT_CSS` is passed as `stylesheets=[_FONT_CSS]` to every `PrefabApp`. `PrefabApp` detects `{` in the string and injects it as an inline `<style>` tag — no font service, no CDN.

The font is read once at module import time and cached as a module-level constant. Startup cost is minimal; subsequent app renders have zero I/O overhead.

### [ADR-017] Asset Structure

```
apps/assets/
├── webfonts/
│   └── DIN-Next-LT-Pro.woff2      # Brand typeface — variable weight 100–900
└── img/
    └── weather/
        ├── 1.svg                   # MeteoSwiss sy-code 1 (clear)
        ├── 2.svg                   # sy-code 2 (mostly clear)
        ├── 3.svg                   # sy-code 3 (partly cloudy)
        └── 10.svg                  # sy-code 10 (heavy rain)
```

Weather SVGs correspond to MeteoSwiss symbol codes (the same `sy` field mapped by `_sy_to_emoji` in `_helpers.py`). These are available for future replacement of the current emoji fallback.

### [ADR-017] Domain Lookup Tables

`_constants.py` also centralises domain-specific lookup tables:

- **`_SAFETY_LEVELS`**: 5 BAFU flow thresholds → badge label/variant/colour
- **`_FLOW_ZONES`**: 5 proportional zones for the flow scale bar widget
- **`_BAFU_LEVELS`**: Official BAFU danger levels 1–5 with German guidance text
- **`_BEAUFORT`**: Beaufort wind scale 0–12 in German with km/h thresholds
- **`_SY_EMOJI`**: MeteoSwiss `sy`-code → emoji fallback (codes 1–30)

### [ADR-017] Benefits

- **Zero external requests**: No Google Fonts, no CDN, no font service calls
- **Consistent rendering**: Same font regardless of network or platform
- **WCAG compliance**: Contrast ratios enforced in code comments, not just design files
- **Centralised maintenance**: One file to update for brand changes across all 7 apps

### [ADR-017] Related ADRs

- [ADR-016](#adr-016-fastmcp-apps-with-prefab_ui) - Apps that consume these tokens
- [ADR-011](#adr-011-pytest-testing-with-80-coverage) - `test_apps.py` covers design token functions

---

## Implementation Roadmap

### Phase 1: Core Architecture ✅ (v1.0.0 – v4.0.0)

- ✅ ADR-001: FastMCP 3.x framework (started as 2.0, upgraded)
- ✅ ADR-002: Pydantic v2 data models
- ✅ ADR-003: Async/httpx patterns
- ✅ ADR-004: Python 3.11+ requirement
- ✅ ADR-005: Layered architecture
- ✅ ADR-006: Helper functions module (split into top-level + apps-specific)
- ✅ ADR-007: Async context managers
- ✅ ADR-008: Caching strategy
- ✅ ADR-009: Rate limiting (client + HTTP layer)
- ✅ ADR-010: Structured logging
- ✅ ADR-011: pytest testing (83% coverage, 245 tests)
- ✅ ADR-012: MyPy type checking
- ✅ ADR-013: HTTP/SSE and Stdio transports

### Phase 2: Production Ready ✅ (v4.1.0 – v4.2.x)

- ✅ ADR-014: Service Layer Pattern
- ✅ ADR-015: FastMCP Cloud Deployment

### Phase 3: Interactive UI Layer ✅ (v4.3.0)

- ✅ ADR-016: FastMCP Apps with prefab_ui (7 interactive apps)
- ✅ ADR-017: Visual Design System & Embedded Assets

### Future

- 🔄 ADR-018 (planned): Weather icon SVGs replacing emoji fallback
- 🔄 Performance profiling and optimisation
- 🔄 REST/Chat API layer reusing service methods

---

## Summary

This ADR compendium establishes **17 architectural decisions** for Aareguru MCP Server v4.3.0:

**Core Architecture** (5 ADRs):
FastMCP 3.x · Pydantic v2 · async/httpx · Python 3.11+ · layered architecture

**Design Patterns** (4 ADRs):
Helper modules (split top-level/apps) · async context managers · time-based caching · dual rate limiting

**Quality & Observability** (3 ADRs):
structlog JSON logging · pytest 83% coverage (245 tests) · MyPy type checking

**Transport & Deployment** (2 ADRs):
stdio + HTTP/SSE transports · FastMCP Cloud (eu-west-1, auto-scaling 2–10 replicas)

**Production Enhancements** (2 ADRs):
Service layer pattern · FastMCP Cloud deployment

**Interactive UI Layer** (2 ADRs):
FastMCP Apps + prefab_ui (7 apps) · visual design system with embedded assets + WCAG AA compliance

---

**Document Status**: v2.0.0 — All 17 ADRs Accepted, Production Ready
**Last Updated**: 2026-04-17
**Maintained By**: Aareguru MCP Development Team

**v4.3.0 Status**: Production ready with interactive UI layer, embedded brand font, WCAG AA compliance, service layer, and FastMCP Cloud deployment (83% test coverage, 245 tests)
**Next**: Weather SVG icon integration (ADR-018 planned)
