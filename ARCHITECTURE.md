# Architecture Documentation

## Overview

Aareguru MCP Server is a production-ready Model Context Protocol (MCP) server built with FastMCP 2.0. It provides AI assistants with structured access to Swiss Aare river data through a clean, layered architecture emphasizing type safety, async operations, and resource management.

**Key Characteristics:**
- **Async-first**: All I/O operations use async/await
- **Type-safe**: Pydantic models validate all API data
- **Resource-aware**: Context managers ensure proper cleanup
- **Observable**: Structured logging with structlog
- **Resilient**: Caching, rate limiting, comprehensive error handling
- **Testable**: 87% coverage, 210 passing tests

## Design Philosophy

### 1. Separation of Concerns

Each layer has a single, well-defined responsibility:

```
┌─────────────────────────────────────────────────────┐
│  MCP Protocol Layer (server.py)                     │
│  - Decorators (@mcp.tool, @mcp.resource, @mcp.prompt)│
│  - Schema generation from type hints                │
│  - MCP message handling                             │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Business Logic (tools.py, resources.py, helpers.py)│
│  - Domain logic and data transformation             │
│  - Safety assessments and suggestions               │
│  - Swiss German translations                        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  HTTP Client (client.py)                            │
│  - Async HTTP with httpx                            │
│  - Caching and rate limiting                        │
│  - Context manager lifecycle                        │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│  Data Validation (models.py)                        │
│  - Pydantic models for API responses                │
│  - Type coercion and validation                     │
│  - JSON schema generation                           │
└─────────────────────────────────────────────────────┘
```

### 2. Dependency Inversion

Upper layers depend on abstractions (interfaces), not concrete implementations:

- MCP server uses generic async functions, not HTTP client directly
- Tools receive configuration via dependency injection (`get_settings()`)
- Client accepts settings interface, not environment variables directly

### 3. Resource Management

All resources use async context managers for automatic cleanup:

```python
async with AareguruClient(settings=get_settings()) as client:
    # HTTP connection pool created
    response = await client.get_current("bern")
    # Connection pool automatically closed on exit
```

### 4. Fail-Safe Defaults

- Cache TTL: 120s (reduces API load)
- Rate limit: 300s (respects API guidelines)
- Default city: "Bern" (most popular location)
- Timeout: 30s (prevents hanging requests)

## Layer Architecture

### Layer 1: MCP Protocol (server.py)

**Responsibility:** Expose functionality via MCP protocol

**Pattern:** Decorator-based registration with FastMCP 2.0

```python
@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Get current water temperature."""
    # Business logic delegated to tools.py
    return await tools.get_current_temperature(city)
```

**Key Features:**
- Automatic schema generation from docstrings and type hints
- MCP protocol message handling (stdio or HTTP/SSE)
- Error serialization to MCP error format
- Structured logging of all MCP operations

**Dependencies:** FastMCP framework, tools/resources modules

### Layer 2: Business Logic

#### tools.py

**Responsibility:** Core tool implementations

**Pattern:** Pure async functions with context managers

```python
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    """Fetch and enrich current temperature data."""
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_today(city)
        
        # Enrich with helpers
        if response.text:
            explanation = get_swiss_german_explanation(response.text)
        
        return {**response.model_dump(), "explanation": explanation}
```

**Key Features:**
- Scoped client instances (one per request)
- Data enrichment with helper functions
- Consistent error handling
- Logging with structured context

#### resources.py

**Responsibility:** MCP resource implementations (URI → data)

**Pattern:** Resource URIs mapped to async functions

```python
async def read_resource(uri: str) -> str:
    """Resolve URI to JSON data."""
    if uri == "aareguru://cities":
        async with AareguruClient(settings=get_settings()) as client:
            cities = await client.get_cities()
            return json.dumps([c.model_dump() for c in cities], indent=2)
```

**Key Features:**
- URI-based routing
- JSON serialization
- Same client lifecycle as tools

#### helpers.py

**Responsibility:** Domain-specific utilities

**Pattern:** Pure functions (no I/O)

```python
def get_safety_assessment(flow: float | None, threshold: int) -> str:
    """Map flow rate to BAFU safety level."""
    if flow is None or flow < 100:
        return "safe"
    elif flow < 220:
        return "moderate"
    # ... more thresholds
```

**Key Features:**
- Stateless, deterministic functions
- No external dependencies
- Easily testable
- Domain knowledge encapsulation

### Layer 3: HTTP Client (client.py)

**Responsibility:** Async HTTP communication with caching and rate limiting

**Pattern:** Async context manager with internal state

```python
class AareguruClient:
    def __init__(self, settings: Settings):
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, CacheEntry] = {}
        self._last_request_time: float | None = None
        self._lock = asyncio.Lock()
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
```

**Key Features:**
- **Caching:** In-memory cache with TTL expiration
- **Rate Limiting:** Lock-based coordination to enforce minimum intervals
- **Connection Pooling:** httpx manages connection reuse
- **Error Handling:** HTTP errors mapped to domain exceptions
- **Type Safety:** Returns validated Pydantic models

**Cache Implementation:**

```python
def _get_cache_key(self, endpoint: str, params: dict) -> str:
    """Generate deterministic cache key."""
    sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
    return f"{endpoint}?{sorted_params}"

async def _request(self, endpoint: str, params: dict, use_cache: bool = True):
    cache_key = self._get_cache_key(endpoint, params)
    
    # Check cache
    if use_cache and cache_key in self._cache:
        entry = self._cache[cache_key]
        if not entry.is_expired():
            return entry.data
    
    # Rate limiting
    async with self._lock:
        if self._last_request_time:
            elapsed = time.time() - self._last_request_time
            if elapsed < self._settings.min_request_interval_seconds:
                await asyncio.sleep(self._settings.min_request_interval_seconds - elapsed)
        
        # Make request
        response = await self._client.get(endpoint, params=params)
        self._last_request_time = time.time()
    
    # Cache and return
    data = response.json()
    if use_cache:
        self._cache[cache_key] = CacheEntry(data, ttl=self._settings.cache_ttl_seconds)
    return data
```

### Layer 4: Data Models (models.py)

**Responsibility:** Type-safe data validation and serialization

**Pattern:** Pydantic BaseModel with validators

```python
class AareData(BaseModel):
    temperature: float | None = None
    temperature_prec: float | None = None
    flow: float | None = None
    danger_level: int | None = Field(None, ge=1, le=5)
    
    @field_validator("danger_level")
    def validate_danger_level(cls, v):
        if v is not None and not (1 <= v <= 5):
            raise ValueError("danger_level must be 1-5")
        return v
```

**Key Features:**
- Automatic JSON parsing
- Type coercion (strings → numbers)
- Field validation with constraints
- Null handling for missing data
- JSON schema generation for MCP

**Critical: Different Response Structures**

The Aareguru API has inconsistent response formats:

#### /v2018/today (TodayResponse)
```python
{
  "aare": 17.2,          # ← Flat structure, direct float
  "text": "geil aber chli chalt",
  "name": "Bern"
}
```

#### /v2018/current (CurrentResponse)
```python
{
  "aare": {              # ← Nested object
    "temperature": 17.2,
    "flow": 245
  },
  "weather": {...}
}
```

#### /v2018/cities (CitiesResponse)
```python
[                        # ← Array, not object
  {"city": "Bern", "aare": 17.2},
  ...
]
```

**Always validate actual API responses when adding new endpoints.**

### Layer 5: Configuration (config.py)

**Responsibility:** Centralized settings with environment overrides

**Pattern:** Pydantic Settings with validation

```python
class Settings(BaseSettings):
    aareguru_base_url: str = "https://aareguru.existenz.ch"
    cache_ttl_seconds: int = Field(default=120, ge=0)
    min_request_interval_seconds: int = Field(default=300, ge=0)
    log_level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARNING|ERROR)$")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )

# Singleton pattern
@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

**Key Features:**
- Environment variable overrides
- Type validation and constraints
- .env file support
- Singleton caching
- Case-insensitive env vars

## Data Flow

### Typical Request Flow

```
1. Claude Desktop sends MCP request via stdio
   ↓
2. FastMCP deserializes request → calls @mcp.tool decorated function
   ↓
3. server.py delegates to tools.py function
   ↓
4. tools.py creates AareguruClient(settings) context manager
   ↓
5. client.__aenter__() creates httpx.AsyncClient
   ↓
6. client.get_current(city) called
   ↓
7. Check cache (hit → return cached data)
   ↓
8. Cache miss → acquire rate limit lock
   ↓
9. Sleep if needed to respect min_request_interval
   ↓
10. httpx makes HTTP GET to Aareguru API
   ↓
11. Response JSON parsed and validated via Pydantic model
   ↓
12. Data cached with TTL
   ↓
13. client.__aexit__() closes httpx.AsyncClient
   ↓
14. tools.py enriches data with helpers (safety, Swiss German, etc.)
   ↓
15. server.py returns dict to FastMCP
   ↓
16. FastMCP serializes response → sends to Claude Desktop
```

### Resource Request Flow

Similar to tool requests but with URI resolution:

```
Resource URI: aareguru://current/bern
   ↓
resources.py parses URI → extracts city="bern"
   ↓
Calls client.get_current("bern")
   ↓
(Same flow as above from step 4)
   ↓
Returns JSON string (not dict)
```

## Design Patterns

### 1. Context Manager Pattern

**Problem:** HTTP connections must be properly closed to prevent leaks

**Solution:** Async context managers ensure cleanup even on exceptions

```python
async with AareguruClient(settings=get_settings()) as client:
    data = await client.get_current("bern")
    # Even if exception raised, __aexit__ runs and closes connections
```

**Benefits:**
- Automatic resource cleanup
- Exception-safe
- Clear resource lifecycle
- Prevents connection leaks

### 2. Cache-Aside Pattern

**Problem:** Repeated API requests waste bandwidth and violate rate limits

**Solution:** Check cache before making requests, populate on miss

```python
# 1. Check cache
if cache_key in self._cache and not self._cache[cache_key].is_expired():
    return self._cache[cache_key].data

# 2. Make request (cache miss)
data = await self._http_get(endpoint)

# 3. Populate cache
self._cache[cache_key] = CacheEntry(data, ttl=120)
return data
```

**Benefits:**
- Reduced API load
- Faster response times
- Respects rate limits
- TTL prevents stale data

### 3. Dependency Injection Pattern

**Problem:** Hard-coded configuration makes testing difficult

**Solution:** Inject Settings via constructor or function parameter

```python
# Production
async with AareguruClient(settings=get_settings()) as client:
    ...

# Testing
async with AareguruClient(settings=mock_settings) as client:
    ...
```

**Benefits:**
- Testable (inject mocks)
- Flexible configuration
- No global state
- Clear dependencies

### 4. Repository Pattern

**Problem:** Direct API access couples business logic to HTTP implementation

**Solution:** Client acts as repository with domain methods

```python
class AareguruClient:
    async def get_current(self, city: str) -> CurrentResponse:
        """Domain method, abstracts HTTP details."""
        data = await self._request("/v2018/current", {"city": city})
        return CurrentResponse(**data)
```

**Benefits:**
- Business logic doesn't know about HTTP
- Easy to swap implementations (API versioning)
- Centralizes API interaction
- Testable with mocks

### 5. Singleton Settings Pattern

**Problem:** Parsing environment variables on every request is wasteful

**Solution:** Cache Settings instance with lru_cache

```python
@lru_cache()
def get_settings() -> Settings:
    return Settings()  # Only created once
```

**Benefits:**
- Single source of truth
- No repeated parsing
- Thread-safe (functools.lru_cache)
- Lazy initialization

## Error Handling Strategy

### 1. Layer-Specific Errors

Each layer handles its own error types:

**Client Layer:**
- `httpx.HTTPStatusError` → Log and re-raise
- `httpx.TimeoutException` → Retry once, then fail
- `pydantic.ValidationError` → Log malformed API response

**Business Logic:**
- Invalid city → Return error dict with suggestion
- Missing data → Return partial response with null fields
- Helper failures → Log warning, continue without enrichment

**MCP Layer:**
- Tool exceptions → Convert to MCP error response
- Validation errors → Return schema violation error

### 2. Fail-Safe Responses

When possible, return partial data rather than failing completely:

```python
try:
    swiss_german = get_swiss_german_explanation(response.text)
except Exception as e:
    logger.warning("swiss_german_explanation_failed", error=str(e))
    swiss_german = None  # Continue without it

return {
    "temperature": response.aare,
    "text": response.text,
    "explanation": swiss_german  # May be None
}
```

### 3. Structured Error Logging

All errors logged with structured context:

```python
logger.error(
    "api_request_failed",
    endpoint="/v2018/current",
    city="bern",
    status_code=500,
    error=str(e)
)
```

## Testing Architecture

### Test Organization

```
tests/
├── test_unit_*.py          # Pure function tests (no I/O)
├── test_tools_*.py         # Tool integration tests (mocked API)
├── test_integration_*.py   # Multi-component workflows
├── test_http_*.py          # HTTP server transport tests
├── test_resources.py       # Resource URI resolution
├── test_prompts.py         # Prompt generation and E2E
└── conftest.py             # Shared fixtures and mocks
```

### Testing Layers

**Unit Tests (70% of tests):**
- Pure functions (helpers.py)
- Pydantic models validation
- Cache expiration logic
- Configuration parsing

**Integration Tests (25% of tests):**
- Tools with mocked HTTP client
- Multi-tool workflows
- Cache behavior across requests
- Rate limiting enforcement

**E2E Tests (5% of tests):**
- Real API calls (marked with `@pytest.mark.e2e`)
- Full request/response cycle
- Prompt-to-tool workflows

### Mocking Strategy

**Mock at the HTTP boundary:**

```python
@pytest.fixture
def mock_http_client():
    mock_response = Mock()
    mock_response.json.return_value = {
        "aare": {"temperature": 17.2}
    }
    
    mock_client = Mock()
    mock_client.get = AsyncMock(return_value=mock_response)
    
    return mock_client
```

**Benefits:**
- Tests remain fast (no network I/O)
- Deterministic responses
- Can test error scenarios
- Business logic fully tested

### Coverage Goals

- **Overall:** 87% (current: 87% ✅)
- **Core modules:** 90%+ (client.py, tools.py, helpers.py)
- **Models:** 95%+ (critical for data integrity)
- **Server:** 80%+ (some branches only hit in production)

## Performance Characteristics

### Caching Impact

- **Cache hit:** ~1ms response time
- **Cache miss:** ~200-500ms (network + validation)
- **Cache memory:** ~10KB per entry, ~1MB for 100 cities

### Rate Limiting

- **Default interval:** 300s (5 minutes)
- **Concurrent requests:** Blocked by asyncio.Lock
- **Burst handling:** First request immediate, subsequent queued

### Connection Pooling

- **httpx default:** 100 connections max
- **Keep-alive:** 5 seconds
- **Timeout:** 30 seconds per request

## Security Considerations

### 1. Input Validation

All user inputs validated via Pydantic:

```python
@mcp.tool()
async def get_current_temperature(city: str = "Bern") -> dict[str, Any]:
    # city validated as string by FastMCP before reaching this code
    ...
```

### 2. API Key Management

Aareguru API is public (no keys), but if keys were required:

```python
class Settings(BaseSettings):
    api_key: str = Field(default="", env="AAREGURU_API_KEY")
    
    @field_validator("api_key")
    def validate_api_key(cls, v):
        if not v:
            raise ValueError("API_KEY required in production")
        return v
```

### 3. Rate Limiting as DoS Protection

Rate limiting prevents accidental DoS of Aareguru API:

- Lock prevents concurrent stampede
- Minimum interval enforced
- Caching reduces request volume

### 4. Structured Logging

Never log sensitive data:

```python
# Good: Log metadata only
logger.info("tool_executed", tool="get_current_temperature", city="bern")

# Bad: Never log API keys, tokens, PII
logger.info("request", headers=request.headers)  # ❌
```

## Deployment Architecture

### Stdio Transport (Claude Desktop)

```
┌──────────────────┐
│  Claude Desktop  │
│                  │
│  ┌────────────┐  │
│  │ MCP Client │  │
│  └──────┬─────┘  │
└─────────┼────────┘
          │ stdio (JSON-RPC)
          ↓
┌─────────────────────┐
│  MCP Server Process │
│  (aareguru-mcp)     │
│                     │
│  FastMCP Runtime    │
└─────────────────────┘
          ↓
   Aareguru API (HTTPS)
```

### HTTP/SSE Transport (Web)

```
┌──────────────────┐
│   Web Client     │
└────────┬─────────┘
         │ HTTP/SSE
         ↓
┌─────────────────────┐
│  FastMCP HTTP Server│  ← Runs in Docker container
│  (aareguru-mcp-http)│
│                     │
│  Port: 8000         │
│  Health: /health    │
└─────────────────────┘
          ↓
   Aareguru API (HTTPS)
```

### Docker Deployment

```yaml
version: '3.8'
services:
  mcp-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CACHE_TTL_SECONDS=120
      - MIN_REQUEST_INTERVAL_SECONDS=300
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## Monitoring and Observability

### Structured Logging

All operations logged with consistent fields:

```python
logger.info(
    "tool_executed",
    tool="get_current_temperature",
    city="bern",
    duration_ms=245,
    cache_hit=True
)
```

### Key Metrics to Track

**Tool Usage:**
- `tool_executed{tool="get_current_temperature"}` - Counter
- `tool_duration_ms{tool="get_current_temperature"}` - Histogram
- `tool_errors{tool="get_current_temperature"}` - Counter

**Cache Performance:**
- `cache_hits_total` - Counter
- `cache_misses_total` - Counter
- `cache_size` - Gauge

**Rate Limiting:**
- `rate_limit_delays_total` - Counter
- `rate_limit_delay_duration_ms` - Histogram

**API Health:**
- `api_requests_total` - Counter
- `api_errors_total{status_code="500"}` - Counter
- `api_duration_ms` - Histogram

### Health Check Endpoint

```python
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "uptime": time.time() - start_time,
        "cache_entries": len(client._cache)
    }
```

## Future Architecture Considerations

### 1. Persistent Caching

**Current:** In-memory cache (lost on restart)

**Future:** Redis or similar for shared cache across instances

```python
class RedisCache:
    async def get(self, key: str) -> dict | None:
        value = await self._redis.get(key)
        return json.loads(value) if value else None
    
    async def set(self, key: str, value: dict, ttl: int):
        await self._redis.setex(key, ttl, json.dumps(value))
```

### 2. Distributed Rate Limiting

**Current:** Per-instance rate limiting (lock-based)

**Future:** Shared rate limiting with Redis or similar

```python
class DistributedRateLimiter:
    async def acquire(self, key: str, interval: int) -> bool:
        last_request = await self._redis.get(f"ratelimit:{key}")
        if last_request and time.time() - float(last_request) < interval:
            return False
        await self._redis.set(f"ratelimit:{key}", time.time())
        return True
```

### 3. Horizontal Scaling

**Current:** Single instance

**Future:** Multiple instances behind load balancer

**Requirements:**
- Shared cache (Redis)
- Shared rate limiting (Redis)
- Sticky sessions (optional, for rate limiting fairness)

### 4. Observability

**Current:** Structured logging to stdout

**Future:** Metrics export (Prometheus), tracing (OpenTelemetry)

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("get_current_temperature")
async def get_current_temperature(city: str):
    span = trace.get_current_span()
    span.set_attribute("city", city)
    ...
```

### 5. API Versioning

**Current:** Hardcoded to v2018 API

**Future:** Support multiple API versions

```python
class AareguruClient:
    def __init__(self, settings: Settings, api_version: str = "v2018"):
        self._api_version = api_version
    
    async def get_current(self, city: str) -> CurrentResponse:
        endpoint = f"/{self._api_version}/current"
        ...
```

## Conclusion

This architecture prioritizes:

1. **Reliability:** Async context managers, error handling, rate limiting
2. **Performance:** Caching, connection pooling, async I/O
3. **Maintainability:** Layered design, dependency injection, type safety
4. **Observability:** Structured logging, health checks, clear data flow
5. **Testability:** 87% coverage, mockable components, deterministic tests

The design supports both simple stdio deployment (Claude Desktop) and complex HTTP/SSE deployments (web/cloud) with minimal code changes, demonstrating the flexibility of the layered architecture.
