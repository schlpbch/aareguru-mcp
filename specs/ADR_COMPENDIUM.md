# Aareguru MCP Server - Architecture Decision Records (ADR) Compendium

**Document Version**: 1.3.0 **Last Updated**: 2026-02-08 **Total ADRs**: 15 (15 Accepted)

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

- [ADR-001: Use FastMCP 2.0 for MCP Protocol](#adr-001-use-fastmcp-20-for-mcp-protocol) ✅
- [ADR-002: Pydantic v2 for Data Models](#adr-002-pydantic-v2-for-data-models) ✅
- [ADR-003: Async/Await with httpx for API Calls](#adr-003-asyncawait-with-httpx-for-api-calls) ✅
- [ADR-004: Python 3.13+ as Minimum Version](#adr-004-python-313-as-minimum-version) ✅
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

---

## ADR-001: Use FastMCP 2.0 for MCP Protocol

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Core Architecture

### [ADR-001] Decision

Use **FastMCP 2.0** (Anthropic's MCP framework) for implementing the Model Context Protocol server.

**Rationale**:

- **Minimal Overhead**: Lightweight framework designed specifically for Python MCP servers
- **Async-First**: Built on Python's async/await for efficient concurrency
- **Declarative API**: Simple decorators (@mcp.tool, @mcp.resource, @mcp.prompt) for clean definitions
- **Type Safety**: Integrates seamlessly with Pydantic for automatic validation and schema generation
- **Protocol Compliance**: Full MCP specification compliance with automatic message handling
- **Developer Experience**: Minimal boilerplate for implementing MCP features

### [ADR-001] Example

```python
from fastmcp import FastMCP
from aareguru_mcp.client import AareguruClient

mcp = FastMCP("aareguru")

@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature for an Aare location."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump()

@mcp.resource("aareguru://cities")
async def get_cities_resource() -> str:
    """List all available Aare locations with current data."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        return json.dumps([city.model_dump() for city in response], indent=2)

@mcp.prompt()
async def daily_swimming_report(city: str = "Bern") -> str:
    """Generate a daily swimming suitability report."""
    async with AareguruClient(settings=get_settings()) as client:
        data = await client.get_current(city)
        return f"Aare conditions in {city}: {data.aare.temperature}°C, {data.aare.flow} m³/s"
```

### [ADR-001] Benefits

- **Clean API**: Decorators make component registration explicit and readable
- **Automatic Schema Generation**: Type hints generate MCP tool schemas automatically
- **Standards Alignment**: Follows industry best practices for MCP servers
- **Community**: Active maintenance from Anthropic with regular updates

### [ADR-001] Related ADRs

- [ADR-003](#adr-003-asyncawait-with-httpx-for-api-calls) - Async operations with httpx
- [ADR-007](#adr-007-async-context-manager-pattern-for-resource-management) - Resource management

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
from typing import Optional
from datetime import datetime

class AareData(BaseModel):
    """Current Aare water conditions."""
    temperature: float = Field(..., ge=-10, le=40, description="Water temperature in °C")
    flow: int = Field(..., ge=0, description="Flow rate in m³/s")
    location: str

class TodayResponse(BaseModel):
    """Response from /v2018/today endpoint."""
    aare: float  # Note: flat structure, not nested
    aare_prec: float
    text: str  # Swiss German description
    name: str
    time: int

class CurrentResponse(BaseModel):
    """Response from /v2018/current endpoint."""
    aare: AareData  # Nested structure
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

### [ADR-002] Benefits

- **Validation**: Automatic validation of API responses on parse
- **Type Hints**: IDE autocomplete and mypy checking
- **Documentation**: Field descriptions auto-generate OpenAPI docs
- **Flexibility**: Easy to evolve models as API changes

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
from aareguru_mcp.models import CurrentResponse, TodayResponse

class AareguruClient:
    """Async Aareguru API client with caching and rate limiting."""

    BASE_URL = "https://aareguru.existenz.ch"
    TIMEOUT = 30.0

    async def __aenter__(self):
        """Enter async context manager."""
        self.client = httpx.AsyncClient(timeout=self.TIMEOUT)
        return self

    async def __aexit__(self, *args):
        """Exit async context manager, cleanup."""
        await self.client.aclose()

    async def get_today(self, city: str = "Bern") -> TodayResponse:
        """Fetch current conditions asynchronously."""
        params = {
            "city": city,
            "app": "aareguru-mcp",
            "version": "4.0.0"
        }
        response = await self.client.get(
            f"{self.BASE_URL}/v2018/today",
            params=params
        )
        response.raise_for_status()
        return TodayResponse(**response.json())
```

### [ADR-003] Benefits

- **Efficiency**: Single-threaded async handles 1000+ concurrent connections
- **Resource Usage**: Minimal memory overhead vs threading
- **Error Handling**: Structured exception handling with timeouts
- **Testing**: Easy to mock async calls with pytest-asyncio

### [ADR-003] Configuration

```python
# src/aareguru_mcp/client.py
TIMEOUT = 30.0      # Request timeout in seconds
RETRIES = 3         # Retry failed requests
BACKOFF = 1.5       # Exponential backoff multiplier
```

---

## ADR-004: Python 3.13+ as Minimum Version

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Core Architecture

### [ADR-004] Decision

Require **Python 3.13+** as the minimum supported version to leverage modern language features.

**Rationale**:

- **PEP 604 Union Syntax**: Use `X | Y` instead of `Union[X, Y]` (cleaner code)
- **Type Hints Standard**: Improved typing with `dict[str, float]` (no `Dict` import)
- **ExceptionGroup**: Better exception handling for concurrent operations
- **Performance**: 15-20% faster than Python 3.11
- **Asyncio Improvements**: Enhanced async/await with better error handling
- **Security**: Modern cryptography and TLS support
- **Long-term Support**: Python 3.13 supported until October 2028

### [ADR-004] Example

```python
# Modern union syntax (Python 3.13+)
def process_location(location: dict | str | None) -> Location:
    """Type hints with modern syntax."""
    ...

# Modern dict type hints
async def fetch_data() -> dict[str, float]:
    """Async function with modern dict hints."""
    ...

# ExceptionGroup for concurrent error handling
async def fetch_multiple_cities(cities: list[str]):
    """Fetch data for multiple cities concurrently."""
    tasks = [get_weather(city) for city in cities]
    results = await asyncio.gather(*tasks, return_exceptions=True)
```

### [ADR-004] Configuration

```toml
# pyproject.toml
[project]
requires-python = ">=3.13"

[tool.uv]
python-version = "3.13"
```

### [ADR-004] Benefits

- **Language Features**: Access to latest Python improvements
- **Dependency Compatibility**: Modern packages target 3.13+
- **Support Window**: Extended support (3+ years)
- **Performance**: Baseline 15%+ performance improvement

---

## ADR-005: Layered Architecture Pattern

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Core Architecture

### [ADR-005] Decision

Use a **clean layered architecture** with clear separation of concerns across five layers.

**Rationale**:

- **Separation of Concerns**: Each layer has single, well-defined responsibility
- **Testability**: Each layer can be tested independently
- **Maintainability**: Changes to one layer don't cascade to others
- **Reusability**: Business logic decoupled from MCP protocol details
- **Clarity**: Clear data flow and dependency direction

### [ADR-005] Architecture Layers

```
┌─────────────────────────────────────────┐
│ 1. MCP Server Layer (server.py)         │
│    @mcp.tool, @mcp.resource, @mcp.prompt
│    - Tool definitions                    │
│    - Resource URIs                       │
│    - Prompt contexts                     │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 2. Business Logic Layer                 │
│    (tools.py, resources.py, helpers.py) │
│    - Domain logic                        │
│    - Data transformations                │
│    - Helper functions                    │
│    - Safety assessments                  │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 3. HTTP Client Layer (client.py)        │
│    - API communication                   │
│    - Caching logic                       │
│    - Rate limiting                       │
│    - Error handling                      │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 4. Models Layer (models.py)              │
│    - Pydantic validation                 │
│    - Request/response structures         │
│    - Type safety                         │
└──────────────┬──────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│ 5. Configuration Layer (config.py)       │
│    - Environment settings                │
│    - Constants                           │
│    - Feature flags                       │
└──────────────────────────────────────────┘
```

### [ADR-005] Data Flow Example

```python
# User/Claude Desktop sends request via MCP protocol
# ↓
# server.py @mcp.tool() handler receives request
# ↓
# tools.py function prepares parameters, logs intent
# ↓
# client.py AareguruClient checks cache, rate limiter
# ↓
# client.py makes HTTP request to Aareguru API
# ↓
# models.py Pydantic validates response structure
# ↓
# helpers.py applies business logic (safety assessment, etc.)
# ↓
# Response serialized to JSON and returned via MCP
```

### [ADR-005] Layer Responsibilities

| Layer | Responsibility | Examples |
|-------|-----------------|----------|
| MCP Server | Protocol handling, schema generation | Tool decorators, resource URIs |
| Business Logic | Domain rules, enrichment | Safety assessments, suggestions |
| HTTP Client | API communication, caching, rate limiting | Request handling, response retrieval |
| Models | Data validation, type safety | Pydantic BaseModel subclasses |
| Config | Environment-based settings | Cache TTL, request intervals |

### [ADR-005] Benefits

- **Clear Responsibility**: Each file has obvious purpose
- **Easy Testing**: Mock each layer independently
- **Future-Proof**: Easy to swap implementations (e.g., different API client)
- **Maintainability**: New developers understand structure quickly

---

## ADR-006: Helper Functions Module Pattern

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-006] Decision

Maintain a dedicated **`helpers.py` module** for shared business logic utilities that are used across multiple tools and resources.

**Rationale**:

- **DRY Principle**: Avoid duplicating logic across tools
- **Consistency**: Same rules applied everywhere
- **Testability**: Helper functions can be unit tested independently
- **Maintainability**: Single place to update business rules
- **Documentation**: Helper functions document domain knowledge

### [ADR-006] Helper Functions

```python
# src/aareguru_mcp/helpers.py

def get_seasonal_advice(month: int) -> str:
    """Contextual swimming advice by season."""
    if month in [12, 1, 2]:
        return "Winter swimming requires cold water preparation"
    elif month in [3, 4, 5]:
        return "Spring water is warming, watch for glacial melt"
    elif month in [6, 7, 8]:
        return "Summer conditions optimal for swimming"
    else:
        return "Autumn water cooling, currents may increase"

def check_safety_warning(flow: int, threshold: int = 220) -> str | None:
    """Check if flow rate triggers danger warning."""
    if flow > threshold:
        return f"⚠️ Warning: High water flow ({flow} m³/s)"
    return None

def get_safety_assessment(flow: int, threshold: int = 100) -> str:
    """Return BAFU safety level based on flow."""
    if flow < 100:
        return "safe"
    elif flow < 220:
        return "moderate"
    elif flow < 300:
        return "elevated"
    elif flow < 430:
        return "high"
    else:
        return "very_high"

def get_suggestion(cities_data: list[dict]) -> str:
    """Suggest warmer/safer alternative location."""
    sorted_by_temp = sorted(cities_data, key=lambda c: c['temperature'], reverse=True)
    best = sorted_by_temp[0]
    return f"Warmer water at {best['name']}: {best['temperature']}°C"

def get_swiss_german_explanation(text: str) -> str:
    """Translate Swiss German phrases."""
    translations = {
        "geil aber chli chalt": "Cool/nice but a bit cold",
        "fuggi": "Cold",
        "ziemlich chalt": "Pretty cold",
    }
    return translations.get(text, text)
```

### [ADR-006] Usage in Tools

```python
@mcp.tool()
async def get_current_conditions(city: str = "Bern") -> dict[str, Any]:
    """Get comprehensive conditions with safety assessment."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)

    # Use helper functions for enrichment
    safety_level = get_safety_assessment(response.aare.flow)
    warning = check_safety_warning(response.aare.flow)
    explanation = get_swiss_german_explanation(response.text)

    return {
        **response.model_dump(),
        "safety_level": safety_level,
        "warning": warning,
        "interpretation": explanation,
    }
```

### [ADR-006] Benefits

- **Code Reuse**: Single source of truth for business rules
- **Consistency**: All tools apply same logic
- **Testing**: Helper functions easy to unit test
- **Maintainability**: Update rules once, affects all tools

### [ADR-006] Related ADRs

- [ADR-005](#adr-005-layered-architecture-pattern) - Business logic layer

---

## ADR-007: Async Context Manager Pattern for Resource Management

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-007] Decision

Use **async context managers** (`async with`) for all HTTP client instantiation to ensure proper connection cleanup.

**Rationale**:

- **Resource Safety**: Guarantees cleanup even if exceptions occur
- **Connection Pooling**: Efficient reuse of HTTP connections
- **Memory Efficiency**: Prevents connection leaks
- **Readability**: Clear acquisition and release points
- **Best Practice**: Recommended pattern for async resource management

### [ADR-007] Implementation

```python
# src/aareguru_mcp/client.py

class AareguruClient:
    """Async HTTP client with context manager support."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "AareguruClient":
        """Enter async context: initialize HTTP client."""
        self.client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context: cleanup HTTP client."""
        if self.client:
            await self.client.aclose()
        return False

    async def _request(self, endpoint: str, params: dict) -> dict:
        """Internal request method."""
        if not self.client:
            raise RuntimeError("Client not initialized, use async context manager")

        response = await self.client.get(
            f"{self.settings.aareguru_base_url}{endpoint}",
            params=params
        )
        response.raise_for_status()
        return response.json()
```

### [ADR-007] Usage in Tools

```python
@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature."""
    # Context manager ensures cleanup
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump()

@mcp.tool()
async def get_current_conditions(city: str = "Bern") -> dict[str, Any]:
    """Get comprehensive conditions."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        # Cleanup happens automatically when exiting context
        return response.model_dump()
```

### [ADR-007] Benefits

- **Safety**: Connections always cleaned up, even on errors
- **Performance**: Connection pooling reduces overhead
- **Clarity**: `async with` makes intent explicit
- **Testing**: Easy to mock context managers in tests

### [ADR-007] Related ADRs

- [ADR-003](#adr-003-asyncawait-with-httpx-for-api-calls) - httpx async client
- [ADR-001](#adr-001-use-fastmcp-20-for-mcp-protocol) - Tool decorators

---

## ADR-008: Caching Strategy

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-008] Decision

Implement **time-based caching** in the HTTP client layer with configurable TTL, keyed by endpoint + sorted query parameters.

**Rationale**:

- **Performance**: Avoid redundant API calls within TTL window
- **Rate Limiting**: Reduces load on Aareguru API
- **Configurable**: TTL adjustable via environment variables
- **Transparent**: Clients don't need to know about caching
- **Simple**: Dictionary-based cache implementation

### [ADR-008] Implementation

```python
# src/aareguru_mcp/client.py

from time import time
from typing import Any

class AareguruClient:
    """HTTP client with time-based caching."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, value)

    def _cache_key(self, endpoint: str, params: dict) -> str:
        """Generate cache key from endpoint + sorted params."""
        sorted_params = json.dumps(params, sort_keys=True)
        return f"{endpoint}:{sorted_params}"

    async def _request(
        self,
        endpoint: str,
        params: dict,
        use_cache: bool = True
    ) -> dict:
        """Internal request with caching."""
        cache_key = self._cache_key(endpoint, params)

        # Check cache
        if use_cache and cache_key in self.cache:
            timestamp, cached_data = self.cache[cache_key]
            age_seconds = time() - timestamp

            if age_seconds < self.settings.cache_ttl_seconds:
                return cached_data
            else:
                # Remove expired entry
                del self.cache[cache_key]

        # Make request
        if not self.client:
            raise RuntimeError("Client not initialized")

        response = await self.client.get(
            f"{self.settings.aareguru_base_url}{endpoint}",
            params=params
        )
        response.raise_for_status()
        data = response.json()

        # Cache response
        if use_cache:
            self.cache[cache_key] = (time(), data)

        return data
```

### [ADR-008] Configuration

```python
# src/aareguru_mcp/config.py

class Settings(BaseSettings):
    """Application settings."""

    aareguru_base_url: str = "https://aareguru.existenz.ch"
    cache_ttl_seconds: int = 120  # Default: 2 minutes
    min_request_interval_seconds: int = 300  # Default: 5 minutes
```

### [ADR-008] Cache Bypass

```python
@mcp.tool()
async def get_historical_weather(city: str, days_back: int = 7) -> dict[str, Any]:
    """Get historical data (bypass cache for fresh data)."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_historical(
            city,
            days_back,
            use_cache=False  # Don't cache historical data
        )
        return response.model_dump()
```

### [ADR-008] Benefits

- **Performance**: Reduces API calls within TTL window
- **Configurable**: Adjust TTL per environment
- **Simple**: No external caching infrastructure needed
- **Transparent**: Clients unaware of caching details
- **Flexibility**: Can bypass cache when needed

### [ADR-008] Related ADRs

- [ADR-009](#adr-009-rate-limiting-strategy) - Rate limiting complements caching

---

## ADR-009: Rate Limiting Strategy

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Design Patterns

### [ADR-009] Decision

Implement **time-based rate limiting** with lock-based coordination to enforce minimum interval between requests to the Aareguru API.

**Rationale**:

- **API Compliance**: Respects Aareguru's 5-minute recommendation
- **Reliability**: Prevents overwhelming the API
- **Non-Commercial**: Aligns with free tier usage guidelines
- **Lock-Based**: Simple async lock prevents concurrent violations
- **Configurable**: Adjustable via environment variables

### [ADR-009] Implementation

```python
# src/aareguru_mcp/client.py

import asyncio
from time import time

class AareguruClient:
    """HTTP client with rate limiting."""

    _last_request_time: float = 0.0
    _request_lock: asyncio.Lock = asyncio.Lock()

    async def _enforce_rate_limit(self) -> None:
        """Ensure minimum interval between requests."""
        async with self._request_lock:
            elapsed = time() - self._last_request_time
            min_interval = self.settings.min_request_interval_seconds

            if elapsed < min_interval:
                wait_time = min_interval - elapsed
                logger.info(
                    "rate_limit_wait",
                    wait_seconds=wait_time
                )
                await asyncio.sleep(wait_time)

            self._last_request_time = time()

    async def _request(self, endpoint: str, params: dict) -> dict:
        """Internal request with rate limiting."""
        # Enforce rate limit before making request
        await self._enforce_rate_limit()

        response = await self.client.get(
            f"{self.settings.aareguru_base_url}{endpoint}",
            params=params
        )
        response.raise_for_status()
        return response.json()
```

### [ADR-009] Configuration

```bash
# .env or environment variables
AAREGURU_BASE_URL=https://aareguru.existenz.ch
MIN_REQUEST_INTERVAL_SECONDS=300  # 5 minutes (default, respects API recommendation)
CACHE_TTL_SECONDS=120              # 2 minutes (reduces rate limit impact)
```

### [ADR-009] Rate Limiting Flow

```
Request 1: Immediate (no prior requests)
  ↓ [300 seconds minimum]
Request 2: Waits if <300 seconds have passed
  ↓ [300 seconds minimum]
Request 3: Waits if <300 seconds have passed
```

### [ADR-009] Benefits

- **API Respect**: Aligns with Aareguru API recommendations
- **Reliability**: Prevents rate limit errors from API
- **Configurable**: Adjust interval per environment
- **Lock-Safe**: Async lock prevents concurrent violations
- **Transparent**: Automatic, no client code needed

### [ADR-009] Related ADRs

- [ADR-008](#adr-008-caching-strategy) - Caching reduces rate limit impact
- [ADR-003](#adr-003-asyncawait-with-httpx-for-api-calls) - Async operations

---

## ADR-010: Structured Logging with structlog

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Quality & Observability

### [ADR-010] Decision

Use **structlog** for structured JSON logging with contextual information throughout the application.

**Rationale**:

- **Structured Output**: JSON logs easily parsed and analyzed
- **Context**: Include relevant data with each log entry
- **Performance**: Zero-cost abstraction with minimal overhead
- **Debugging**: Rich context makes troubleshooting easier
- **Integration**: Works with observability platforms (Datadog, ELK, etc.)

### [ADR-010] Configuration

```python
# src/aareguru_mcp/logging.py

import structlog
import logging

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()
```

### [ADR-010] Usage Examples

```python
from structlog import get_logger

logger = get_logger(__name__)

# Tool execution logging
@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature."""
    logger.info("tool_called", tool="get_current_temperature", city=city)

    try:
        async with AareguruClient(settings=get_settings()) as client:
            response = await client.get_today(city)

            logger.info(
                "api_response_received",
                city=city,
                temperature=response.aare,
                timestamp=response.time
            )
            return response.model_dump()
    except Exception as e:
        logger.error(
            "tool_error",
            tool="get_current_temperature",
            city=city,
            error=str(e),
            exc_info=True
        )
        raise

# Rate limiting logging
logger.info(
    "rate_limit_wait",
    wait_seconds=45,
    min_interval=300
)

# API error logging
logger.error(
    "api_error",
    endpoint="/v2018/current",
    status_code=500,
    response_text="Internal Server Error"
)

# Cache hit logging
logger.debug(
    "cache_hit",
    endpoint="/v2018/today",
    cache_age_seconds=45
)
```

### [ADR-010] Log Output

```json
{
  "event": "tool_called",
  "tool": "get_current_temperature",
  "city": "Bern",
  "timestamp": "2025-12-01T10:30:45Z",
  "log_level": "info"
}

{
  "event": "api_response_received",
  "city": "Bern",
  "temperature": 17.2,
  "timestamp": 1701423045,
  "log_level": "info"
}

{
  "event": "rate_limit_wait",
  "wait_seconds": 45,
  "min_interval": 300,
  "log_level": "info"
}
```

### [ADR-010] Benefits

- **Analysis**: JSON format enables automated log analysis
- **Observability**: Integrates with monitoring platforms
- **Debugging**: Rich context makes root cause analysis easier
- **Performance**: Minimal overhead in production

### [ADR-010] Related ADRs

- [ADR-011](#adr-011-pytest-testing-with-80-coverage) - Testing with logging

---

## ADR-011: pytest Testing with 80%+ Coverage

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Quality & Observability

### [ADR-011] Decision

Use **pytest** as the testing framework with **≥80% code coverage** target and organized test layers.

**Test Layers**:

1. **Unit Tests**: Individual functions and models
2. **Integration Tests**: Multi-component workflows
3. **E2E Tests**: End-to-end conversations
4. **Async Tests**: Async functions with pytest-asyncio

### [ADR-011] Configuration

```toml
# pyproject.toml

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
minversion = "9.0"
addopts = "--cov=src/aareguru_mcp --cov-report=html --cov-report=term-missing"
markers = [
    "integration: integration tests",
    "e2e: end-to-end tests",
]

[tool.coverage.run]
source = ["src/aareguru_mcp"]
omit = [
    "*/tests/*",
    "**/__main__.py",
    "**/conftest.py",
]

[tool.coverage.report]
fail_under = 80
precision = 2
```

### [ADR-011] Test Organization

```
tests/
├── test_unit_client.py         # Client tests
├── test_unit_models.py         # Model validation tests
├── test_unit_helpers.py        # Helper function tests
├── test_unit_config.py         # Configuration tests
├── test_tools_basic.py         # Basic tool tests
├── test_tools_advanced.py      # Advanced tool scenarios
├── test_integration_workflows.py # Multi-tool workflows
├── test_http_endpoints.py      # HTTP/SSE transport
├── test_resources.py           # Resource tests
├── test_prompts.py             # Prompt tests
├── test_e2e_conversations.py   # End-to-end conversations
└── conftest.py                 # Shared fixtures
```

### [ADR-011] Example Test

```python
# tests/test_tools_basic.py

import pytest
from unittest.mock import Mock, AsyncMock
from aareguru_mcp.tools import get_current_temperature
from aareguru_mcp.models import TodayResponse

@pytest.mark.asyncio
async def test_get_current_temperature():
    """Test get_current_temperature tool."""
    # Arrange
    mock_response = TodayResponse(
        aare=17.2,
        aare_prec=17.23,
        text="geil aber chli chalt",
        name="Bern",
        time=1701423045
    )

    # Act
    with patch('aareguru_mcp.client.AareguruClient') as mock_client_class:
        mock_client = AsyncMock()
        mock_client.get_today.return_value = mock_response
        mock_client_class.return_value.__aenter__.return_value = mock_client

        result = await get_current_temperature("Bern")

    # Assert
    assert result["aare"] == 17.2
    assert result["name"] == "Bern"
    assert "chalt" in result["text"]

@pytest.mark.integration
@pytest.mark.asyncio
async def test_get_weather_with_cache(monkeypatch):
    """Test caching behavior across multiple calls."""
    call_count = 0

    async def mock_get(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        return Mock(json=lambda: {"aare": 17.2})

    # Verify cache hit on second call
    assert call_count == 1  # First call
    # Second call within TTL should use cache
    assert call_count == 1  # Still 1 (cached)
```

### [ADR-011] Coverage Status

```
Current Coverage: 87%
Target: ≥80%
Total Tests: 210 passing + 2 skipped = 212 total

Coverage by module:
├── client.py          98%
├── models.py          100%
├── helpers.py         95%
├── server.py          89%
├── config.py          100%
├── tools.py           85%
└── resources.py       80%
```

### [ADR-011] Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src/aareguru_mcp

# Run specific test file
uv run pytest tests/test_unit_client.py

# Run specific test
uv run pytest tests/test_tools_basic.py::test_get_current_temperature

# Run with markers
uv run pytest -m integration
uv run pytest -m e2e
```

### [ADR-011] Benefits

- **Quality**: Catches regressions and edge cases
- **Confidence**: High coverage enables safe refactoring
- **Documentation**: Tests serve as code examples
- **CI/CD**: Automated test runs on every commit

### [ADR-011] Related ADRs

- [ADR-012](#adr-012-mypy-strict-type-checking) - Type checking complements testing

---

## ADR-012: MyPy Strict Type Checking

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Quality & Observability

### [ADR-012] Decision

Use **MyPy in strict mode** for static type checking of all Python code.

**Rationale**:

- **Bug Prevention**: Catches type errors before runtime
- **Documentation**: Type hints serve as inline documentation
- **IDE Support**: Enhanced autocomplete and refactoring
- **Maintainability**: Easier to understand and modify code
- **Performance**: Zero runtime overhead (compile-time only)

### [ADR-012] Configuration

```toml
# pyproject.toml

[tool.mypy]
# Strict mode enforcement
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
strict_equality = true
strict_optional = true

# Plugin configuration
plugins = []

# Ignore patterns
ignore_errors = false
ignore_missing_imports = false

# Source paths
files = ["src/", "tests/"]

# Python version
python_version = "3.13"
```

### [ADR-012] Example

```python
# ✅ Correct: Full type annotations
async def get_weather(
    city: str,
    days: int = 7
) -> dict[str, Any]:
    """Fetch weather data."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        return response.model_dump()

# ❌ Error: Missing return type
async def search_location(query: str):  # error: Function is missing a return type annotation
    """Search locations."""
    ...

# ✅ Correct: Proper Optional handling
from typing import Optional

def process_data(value: str | None) -> str:
    """Handle optional values properly."""
    if value is None:
        return ""
    return value.upper()

# ✅ Correct: Type hints for complex types
def get_temperature_by_city(
    cities: list[str]
) -> dict[str, float]:
    """Get temperatures for multiple cities."""
    return {city: 17.2 for city in cities}
```

### [ADR-012] CI/CD Integration

```bash
# Run type checking
uv run mypy src/

# Generate HTML report
uv run mypy --html mypy_report src/

# Fail if any errors
uv run mypy src/ && echo "✓ Type check passed"
```

### [ADR-012] Benefits

- **Early Detection**: Catches bugs before testing
- **Better Refactoring**: Type information enables safe changes
- **Zero Overhead**: Compile-time only, no runtime cost
- **Team Alignment**: Enforces consistent typing

### [ADR-012] Related ADRs

- [ADR-011](#adr-011-pytest-testing-with-80-coverage) - Testing complements type checking

---

## ADR-013: HTTP/SSE and Stdio Transports

**Status**: ✅ Accepted **Date**: 2025-12-01 **Context**: Transport & Deployment

### [ADR-013] Decision

Support both **stdio transport** (for Claude Desktop) and **HTTP/SSE transport** (for web/cloud) using FastMCP's built-in transport abstraction.

**Rationale**:

- **Claude Desktop**: Stdio transport integrates seamlessly with Claude Desktop client
- **Web Clients**: HTTP/SSE enables browser-based integration
- **Cloud Deployment**: HTTP transport suitable for FastMCP Cloud
- **Flexibility**: Users choose transport based on use case
- **Single Implementation**: Same MCP tools work on both transports

### [ADR-013] Stdio Transport (Claude Desktop)

```python
# src/aareguru_mcp/server.py - Stdio entry point

def entry_point() -> None:
    """Run MCP server with stdio transport for Claude Desktop."""
    from aareguru_mcp.server import mcp
    mcp.run(transport="stdio")
```

Usage in Claude Desktop config:

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

### [ADR-013] HTTP/SSE Transport (Web/Cloud)

```python
# src/aareguru_mcp/server.py - HTTP/SSE entry point

async def run_http(host: str = "0.0.0.0", port: int = 8888) -> None:
    """Run MCP server with HTTP/SSE transport for web clients."""
    from aareguru_mcp.server import mcp

    # Create HTTP server with SSE transport
    import uvicorn
    app = create_app_with_sse_transport(mcp)

    uvicorn.run(app, host=host, port=port)
```

Console script entry point:

```toml
# pyproject.toml

[project.scripts]
aareguru-mcp = "aareguru_mcp.server:entry_point"          # Stdio
aareguru-mcp-http = "aareguru_mcp.server:run_http"       # HTTP/SSE
```

Running HTTP server:

```bash
# Development
uv run aareguru-mcp-http

# Production with custom host/port
uv run aareguru-mcp-http --host 0.0.0.0 --port 8888
```

### [ADR-013] Client Connection Examples

```python
# Python client (HTTP/SSE)
from anthropic import Anthropic

client = Anthropic()

# Connect to HTTP/SSE MCP server
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[
        {
            "name": "get_current_temperature",
            "description": "Get current water temperature",
            "input_schema": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "default": "Bern"}
                }
            }
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "What's the water temperature in Zurich?"
        }
    ]
)
```

### [ADR-013] Benefits

- **Dual Support**: Single codebase serves both use cases
- **Claude Desktop**: Direct integration with native client
- **Web Integration**: Enables browser-based tools
- **Cloud Ready**: HTTP transport suitable for cloud deployment
- **Flexibility**: Users choose based on architecture

### [ADR-013] Related ADRs

- [ADR-001](#adr-001-use-fastmcp-20-for-mcp-protocol) - FastMCP handles transport abstraction
- [ADR-010](#adr-010-structured-logging-with-structlog) - Logging for all transports

---

## ADR-014: Service Layer Pattern

**Status**: 🔄 Proposed **Date**: 2026-02-08 **Context**: Core Architecture

### [ADR-014] Decision

Introduce a **service layer** between tools/routes and the API client, providing business logic, data enrichment, and helper function integration.

**Rationale**:

- **Separation of Concerns**: Tools/routes focus on interface, services handle logic
- **Reusability**: Services can be called from MCP tools, REST endpoints, and Chat API
- **Enrichment**: Centralized data interpretation and formatting
- **Testability**: Service layer can be tested independently
- **Maintainability**: Easier to modify business logic without touching API code

### [ADR-014] Service Layer Architecture

```python
# src/aareguru_mcp/service.py

from aareguru_mcp.client import AareguruClient
from aareguru_mcp.helpers import (
    get_safety_assessment,
    check_safety_warning,
    get_suggestion,
    get_seasonal_advice,
)
from aareguru_mcp.models import CurrentResponse

class AareguruService:
    """Business logic service for Aareguru data."""

    def __init__(self, client: AareguruClient | None = None):
        self.client = client

    async def get_current_conditions(self, city: str = "Bern") -> dict:
        """Get weather with automatic enrichment."""
        async with AareguruClient() as client:
            response = await client.get_current(city)

            # Enrich with interpretation
            enrichment = {
                "safety_assessment": get_safety_assessment(response.aare.flow),
                "safety_warning": check_safety_warning(response.aare.flow),
                "seasonal_advice": get_seasonal_advice(datetime.now().month),
            }

            # Return combined
            return {
                **response.model_dump(),
                **enrichment
            }

    async def get_weather_with_suggestion(self, city: str) -> dict:
        """Get weather and suggest alternatives if needed."""
        async with AareguruClient() as client:
            response = await client.get_today(city)
            cities = await client.get_cities()

            # Suggest warmer location if cold
            suggestion = None
            if response.aare < 15:
                suggestion = get_suggestion([c.model_dump() for c in cities])

            return {
                **response.model_dump(),
                "suggestion": suggestion
            }

    async def get_historical_analysis(self, city: str, days_back: int = 7) -> dict:
        """Get historical data with trend analysis."""
        async with AareguruClient() as client:
            data = await client.get_historical(city, days_back)

            # Analyze trends
            temperatures = [d["temperature"] for d in data]
            avg_temp = sum(temperatures) / len(temperatures)
            trend = "warming" if temperatures[-1] > temperatures[0] else "cooling"

            return {
                "city": city,
                "period": f"Last {days_back} days",
                "average_temperature": avg_temp,
                "trend": trend,
                "data": data
            }
```

### [ADR-014] MCP Tool Usage

```python
@mcp.tool()
async def get_current_conditions(city: str = "Bern") -> dict[str, Any]:
    """Get comprehensive conditions with safety assessment."""
    service = AareguruService()
    return await service.get_current_conditions(city)
```

### [ADR-014] REST Endpoint Usage

```python
@app.get("/api/tools/current")
async def get_current_endpoint(city: str = "Bern") -> dict:
    """REST endpoint using same service."""
    service = AareguruService()
    return await service.get_current_conditions(city)
```

### [ADR-014] Chat API Usage

```python
async def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute MCP tool from chat."""
    service = AareguruService()

    if tool_name == "get_current_conditions":
        return await service.get_current_conditions(tool_input.get("city", "Bern"))
    elif tool_name == "get_weather_with_suggestion":
        return await service.get_weather_with_suggestion(tool_input["city"])
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
```

### [ADR-014] Service Classes

| Service | Responsibility |
|---------|-----------------|
| `AareguruService` | Current conditions, enrichment, interpretation |
| `HistoricalService` | Historical data queries, trend analysis |
| `LocationService` | Location search, coordinate validation |
| `ForecastService` | Weather forecast, trend prediction |
| `ChatService` | Chat handler, session management, context |

### [ADR-014] Benefits

- **DRY**: Helper functions applied consistently across APIs
- **Consistency**: Same data enrichment for all interfaces
- **Testability**: Service layer can be unit tested independently
- **Flexibility**: Easy to add new data sources or enhance existing services
- **Documentation**: Services document business logic clearly

### [ADR-014] Related ADRs

- [ADR-013](#adr-013-httpsse-and-stdio-transports) - HTTP/SSE transport foundation
- [ADR-006](#adr-006-helper-functions-module-pattern) - Helper functions used by services

---

## ADR-015: FastMCP Cloud Deployment

**Status**: ✅ Accepted **Date**: 2026-02-08 **Context**: Deployment & Integration

### [ADR-015] Decision

Use **FastMCP Cloud** for production deployment with automatic scaling, monitoring, and zero-downtime updates.

**Rationale**:

- **Managed Service**: No infrastructure management required
- **Auto-Scaling**: Automatically scales based on demand
- **Zero-Downtime**: Seamless updates and rollbacks
- **Monitoring**: Built-in observability and alerting
- **Integration**: Native integration with Claude Desktop and API clients
- **Cost**: Pay-per-request pricing (no idle costs)

### [ADR-015] Implementation Status

**Deployed**: 2026-02-08
**Production URL**: `https://aareguru.fastmcp.app/mcp`
**Configuration**: `.fastmcp/config.yaml`
**Documentation**: `docs/DEPLOYMENT.md`

The server is production-ready and deployed with:
- ✅ HTTP/SSE transport configured
- ✅ Health endpoints at `/health`
- ✅ Prometheus metrics at `/metrics`
- ✅ Auto-scaling (2-10 replicas) in EU-West-1
- ✅ Zero-downtime deployments
- ✅ Automatic rollback on failures
- ✅ MCP bundle file (`aareguru-mcp.mcpb`) for easy installation

### [ADR-015] Configuration

Complete FastMCP Cloud configuration in `.fastmcp/config.yaml`:

```yaml
# Deployment settings
deployment:
  region: "eu-west-1"           # Closer to Switzerland
  replicas: 2                   # Minimum healthy replicas
  max_replicas: 10              # Auto-scale up to 10
  timeout: 30s                  # Request timeout
  memory: 512Mi                 # Memory per replica
  cpu: "500m"                   # CPU limit

# Environment variables
environment:
  LOG_LEVEL: "INFO"
  LOG_FORMAT: "json"
  CACHE_TTL_SECONDS: "120"
  MIN_REQUEST_INTERVAL_SECONDS: "0.1"

# Health check configuration
health:
  path: "/health"
  interval: 30s
  timeout: 10s
  failure_threshold: 3

# Monitoring and alerting
monitoring:
  enabled: true
  metrics_path: "/metrics"
  alerts:
    - name: "High Error Rate"
      condition: "error_rate > 0.01"
    - name: "Critical Error Rate"
      condition: "error_rate > 0.05"
    - name: "High Latency"
      condition: "latency_p95 > 2000"

# Auto-rollback configuration
auto_rollback:
  enabled: true
  on_error_rate: 0.05           # >5% errors
  on_latency: 5000              # >5s P95 latency
  grace_period: 60s
```

### [ADR-015] Deployment Process

```bash
# 1. Build and test locally
uv sync
uv run pytest tests/
uv run mypy src/

# 2. Deploy to FastMCP Cloud (automatic on main branch push)
# OR manually: fastmcp deploy

# 3. Verify deployment
curl https://aareguru.fastmcp.app/health/

# 4. Check metrics
curl https://aareguru.fastmcp.app/metrics
```

### [ADR-015] Installation

**Option 1: Direct URL Configuration** (Claude Desktop)
```json
{
  "mcpServers": {
    "aareguru": {
      "url": "https://aareguru.fastmcp.app/mcp"
    }
  }
}
```

**Option 2: Bundle File**
- Download `aareguru-mcp.mcpb` from repository
- Drag-and-drop into Claude Desktop
- One-click installation with metadata

### [ADR-015] Benefits

- **Reliability**: Automatic failover and health checking
- **Performance**: Auto-scaling handles traffic spikes
- **Scalability**: 2-10 replicas, handles concurrent requests
- **Observability**: Built-in metrics and structured JSON logging
- **Updates**: Zero-downtime deployments with automatic rollback
- **Cost**: Pay-per-request pricing (~$0.001/request)
- **Integration**: Native Claude Desktop integration via MCP

### [ADR-015] Monitoring

**Metrics Available**:
- Request count per tool
- Response latency (P50, P95, P99)
- Error rate and types
- Active connections
- CPU/memory utilization

**Available at**: `/metrics` (Prometheus format) or FastMCP Cloud dashboard

**Logging**:
- Structured JSON logs
- 30-day retention
- Queryable via FastMCP Cloud dashboard

### [ADR-015] Related ADRs

- [ADR-013](#adr-013-httpsse-and-stdio-transports) - HTTP/SSE transport foundation
- [ADR-014](#adr-014-service-layer-pattern) - Service layer for tool execution
- [ADR-010](#adr-010-structured-logging-with-structlog) - Logging for cloud monitoring

---

## Implementation Roadmap

### Phase 1: Core Architecture ✅ (v1.0.0 - v4.0.0)

- ✅ ADR-001: FastMCP 2.0 framework
- ✅ ADR-002: Pydantic v2 data models
- ✅ ADR-003: Async/httpx patterns
- ✅ ADR-004: Python 3.13+ requirement
- ✅ ADR-005: Layered architecture
- ✅ ADR-006: Helper functions module
- ✅ ADR-007: Async context managers
- ✅ ADR-008: Caching strategy
- ✅ ADR-009: Rate limiting
- ✅ ADR-010: Structured logging
- ✅ ADR-011: pytest testing (87% coverage)
- ✅ ADR-012: MyPy strict type checking
- ✅ ADR-013: HTTP/SSE and Stdio transports

### Phase 2: Production Ready (v4.1.0+)

- ✅ ADR-014: Service Layer Pattern for code reuse
- ✅ ADR-015: FastMCP Cloud Deployment for production
- 🔄 Performance profiling and optimization
- 🔄 Enhanced monitoring and alerting

---

## Summary

This ADR compendium establishes **15 architectural decisions** for Aareguru MCP Server:

**Core Architecture** (5 ADRs - ✅ Accepted):
- FastMCP 2.0 for MCP protocol
- Pydantic v2 for type-safe data models
- Async/await with httpx for API calls
- Python 3.13+ as minimum version
- Layered architecture (server → logic → client → models → config)

**Design Patterns** (4 ADRs - ✅ Accepted):
- Helper functions module for shared business logic
- Async context managers for resource management
- Time-based caching strategy (120s TTL)
- Lock-based rate limiting (300s min interval)

**Quality & Observability** (3 ADRs - ✅ Accepted):
- Structured logging with structlog (JSON output)
- pytest with 87% coverage (target ≥80%, 212 tests)
- MyPy strict type checking

**Transport & Deployment** (3 ADRs - ✅ Accepted):
- HTTP/SSE and Stdio transports (FastMCP Cloud ready)
- Service Layer Pattern for code reuse
- FastMCP Cloud Deployment for production

---

**Document Status**: v1.3.0 - All ADRs Accepted, Production Ready
**Last Updated**: 2026-02-08
**Maintained By**: Aareguru MCP Development Team

**v4.1.0 Status**: Production ready with service layer pattern and FastMCP Cloud deployment (87% test coverage)
**Future Goals**: Performance profiling, enhanced monitoring, REST/Chat API layers
