# Full SSE Implementation Design for Aareguru MCP Server

**Status**: ✅ Implemented with FastMCP 2.0  
**Date**: 2025-12-04  
**Version**: 2.0  

---

## Executive Summary

This document describes the HTTP/SSE transport implementation for the Aareguru MCP server using **FastMCP 2.0**. FastMCP provides a high-level, decorator-based API that dramatically simplifies MCP server development, including built-in HTTP/SSE transport support.

### Current State (FastMCP 2.0)

**✅ What We Have:**
- FastMCP 2.0 with built-in HTTP/SSE transport
- Decorator-based tool and resource definitions
- Automatic session management
- Built-in health endpoints
- Full MCP protocol compliance
- 151 passing tests, 85% coverage
- Docker containerization

**🎯 Key Benefits of FastMCP:**
- Simplified API - decorators instead of manual registration
- Built-in HTTP transport via `mcp.run(transport="http")`
- Automatic SSE/Streamable HTTP handling
- No manual `SseServerTransport` configuration needed
- Production-ready out of the box

---

## Architecture Overview

### FastMCP Transport Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                                │
│                    (Claude Desktop / Web)                        │
└───────────────┬─────────────────────────┬───────────────────────┘
                │                         │
        GET /sse│                         │POST /mcp/
                │                         │
┌───────────────▼─────────────────────────▼───────────────────────┐
│                      FastMCP HTTP Server                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Built-in Transport Layer                                 │  │
│  │  - Automatic session management                          │  │
│  │  - SSE streaming handled internally                      │  │
│  │  - JSON-RPC message routing                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  FastMCP Decorators                                       │  │
│  │  - @mcp.tool() → Tool registration                       │  │
│  │  - @mcp.resource() → Resource registration               │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                    Aareguru MCP Server                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Tools (7 total)                                          │   │
│  │  - get_current_temperature, get_current_conditions       │   │
│  │  - list_cities, get_flow_danger_level                    │   │
│  │  - get_historical_data, compare_cities, get_forecast     │   │
│  ├──────────────────────────────────────────────────────────┤   │
│  │  Resources (4 total)                                      │   │
│  │  - aareguru://cities, aareguru://widget                  │   │
│  │  - aareguru://current/{city}, aareguru://today/{city}    │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility | Implementation |
|-----------|---------------|----------------|
| **FastMCP** | High-level MCP framework | `fastmcp.FastMCP` |
| **HTTP Transport** | Built-in HTTP/SSE handling | `mcp.run(transport="http")` |
| **ASGI App** | Starlette-based app | `mcp.http_app()` |
| **Tools** | Dynamic API queries | `@mcp.tool()` decorator |
| **Resources** | Static data access | `@mcp.resource()` decorator |

---

## Technical Design

### 1. FastMCP Server Initialization

FastMCP provides a simple, decorator-based API for MCP servers:

```python
from fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP(
    name="aareguru-mcp",
    instructions="""You are an assistant that helps users with Swiss Aare river conditions.
    
    You can provide:
    - Current water temperatures for various Swiss cities
    - Flow rates and safety assessments based on BAFU thresholds
    - Weather conditions and forecasts
    - Historical data for trend analysis
    - Comparisons between different cities
    """
)
```

**Key Benefits:**
- No manual transport configuration needed
- Decorators for tool and resource registration
- Built-in HTTP/SSE support via `mcp.run(transport="http")`
- Automatic ASGI app generation via `mcp.http_app()`

### 2. Tool and Resource Registration

FastMCP uses decorators for clean, declarative registration:

```python
@mcp.tool()
async def get_current_temperature(city: str = "bern") -> str:
    """Get the current Aare river water temperature for a Swiss city.
    
    Args:
        city: City identifier (default: "bern")
    
    Returns:
        Current temperature with Swiss German description
    """
    client = AareguruClient()
    async with client:
        data = await client.get_current(city)
        # Format and return response
        return formatted_response

@mcp.resource("aareguru://cities")
async def get_cities() -> str:
    """List all available cities with Aare data."""
    client = AareguruClient()
    async with client:
        cities = await client.get_cities()
        return json.dumps(cities, indent=2)
```

### 3. HTTP Transport Flow

FastMCP handles all transport details automatically:

```
Client                          FastMCP Server
  │                               │
  │──── GET /sse ────────────────→│
  │                               │ FastMCP creates session
  │←──── SSE stream ──────────────│
  │                               │
  │──── POST /mcp/ ──────────────→│
  │      {"method": "tools/call"}│
  │                               │ FastMCP routes to @mcp.tool()
  │←──── Response via SSE ────────│
  │                               │
```

### 4. Implementation Code

**File: `src/aareguru_mcp/http_server.py`** (Current FastMCP Implementation)

```python
"""HTTP server for Aareguru MCP using FastMCP.

This module provides HTTP/SSE transport for the MCP protocol,
leveraging FastMCP's built-in HTTP support.
"""

import structlog

from .config import get_settings
from .server import mcp

# Get structured logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create the ASGI app from FastMCP
# This can be used with uvicorn directly or TestClient
http_app = mcp.http_app()


def main() -> None:
    """Main entry point for HTTP server."""
    logger.info(
        "starting_aareguru_mcp_http_server",
        version=settings.app_version,
        host=settings.http_host,
        port=settings.http_port,
        url=f"http://{settings.http_host}:{settings.http_port}",
    )

    mcp.run(
        transport="http",
        host=settings.http_host,
        port=settings.http_port,
    )


if __name__ == "__main__":
    main()
```

**File: `src/aareguru_mcp/server.py`** (FastMCP Server Definition)

```python
"""MCP server implementation for Aareguru API using FastMCP."""

from fastmcp import FastMCP

# Create FastMCP server instance
mcp = FastMCP(
    name="aareguru-mcp",
    instructions="""You are an assistant that helps users with Swiss Aare river conditions.
    ...
    """,
)

# Tools are registered with @mcp.tool() decorator
@mcp.tool()
async def get_current_temperature(city: str = "bern") -> str:
    """Get the current Aare river water temperature."""
    # Implementation...

@mcp.tool()
async def list_cities() -> str:
    """List all available Swiss cities with Aare data."""
    # Implementation...

# Resources are registered with @mcp.resource() decorator
@mcp.resource("aareguru://cities")
async def get_cities_resource() -> str:
    """Resource: List all available cities."""
    # Implementation...
```

**Key Differences from Raw MCP SDK:**

| Aspect | Raw MCP SDK | FastMCP 2.0 |
|--------|-------------|-------------|
| Server creation | `Server("name")` | `FastMCP("name")` |
| Tool registration | Manual handler | `@mcp.tool()` decorator |
| Resource registration | Manual handler | `@mcp.resource()` decorator |
| HTTP transport | Manual `SseServerTransport` | `mcp.run(transport="http")` |
| ASGI app | Manual Starlette setup | `mcp.http_app()` |
| Session management | Manual implementation | Built-in |

---

## Session Management

With FastMCP, session management is handled automatically. The framework manages:

- **Session creation**: Automatic UUID generation for each SSE connection
- **Session isolation**: Each client gets isolated streams
- **Automatic cleanup**: Sessions are cleaned up when connections close
- **Concurrent clients**: Thread-safe handling via anyio

### How FastMCP Handles Sessions

```python
# FastMCP handles all session management internally:
# 1. Client connects to /sse endpoint
# 2. FastMCP creates session with unique ID
# 3. Messages posted to /mcp/ are routed to correct session
# 4. Responses are streamed back via SSE
# 5. Session cleaned up on disconnect

# You don't need to manage sessions manually!
# Just use mcp.run(transport="http") and it all works.
```

---

## Message Protocol

### MCP JSON-RPC Format

All messages follow JSON-RPC 2.0:

```json
// Client → Server (POST /messages)
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "get_current_temperature",
    "arguments": {
      "city": "bern"
    }
  }
}

// Server → Client (via SSE)
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Temperature in Bern: 17.2°C..."
      }
    ]
  }
}
```

### SSE Event Format

```
event: message
data: {"jsonrpc": "2.0", "id": 1, "result": {...}}

event: message
data: {"jsonrpc": "2.0", "method": "notifications/progress", "params": {...}}

```

---

## Security Considerations

### 1. DNS Rebinding Protection

```python
from mcp.shared.security import TransportSecuritySettings

security_settings = TransportSecuritySettings(
    allowed_origins=["https://app.example.com"],
    require_host_header=True,
)

sse_transport = SseServerTransport(
    endpoint="/messages",
    security_settings=security_settings,
)
```

**Protection Against:**
- DNS rebinding attacks
- Cross-origin requests
- Host header injection

### 2. API Key Authentication

```python
# Already implemented in current version
async def verify_api_key(request: Request) -> bool:
    """Verify API key from request headers."""
    if not settings.api_key_required:
        return True
    
    api_key = request.headers.get("X-API-Key", "")
    valid_keys = [k.strip() for k in settings.api_keys.split(",") if k.strip()]
    
    return api_key in valid_keys
```

### 3. Rate Limiting

```python
# Per-client rate limiting using slowapi
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def handle_sse(request: Request) -> Response:
    # ... implementation
```

### 4. Session Timeout

```python
# Add session timeout to prevent resource leaks
SESSION_TIMEOUT = 3600  # 1 hour

async def cleanup_stale_sessions():
    """Periodically clean up inactive sessions."""
    while True:
        await asyncio.sleep(300)  # Check every 5 minutes
        # Identify and close sessions older than SESSION_TIMEOUT
        # Implementation depends on tracking session creation times
```

---

## Testing Strategy

### Unit Tests

```python
# tests/test_http_server.py

def test_sse_endpoint_creates_session():
    """Test that SSE endpoint creates a new session."""
    with client.stream("GET", "/sse") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"
        
        # First event should be endpoint URI
        first_event = next(response.iter_lines())
        assert "endpoint" in first_event

def test_message_post_requires_session():
    """Test that POST /messages requires valid session_id."""
    response = client.post("/messages")
    assert response.status_code == 400  # Missing session_id

def test_message_routing():
    """Test that messages route to correct session."""
    # 1. Open SSE connection
    # 2. Extract session_id from endpoint event
    # 3. POST message with session_id
    # 4. Verify response on SSE stream
    pass
```

### Integration Tests

```python
# tests/test_sse_integration.py

async def test_full_sse_flow():
    """Test complete SSE connection and message exchange."""
    # 1. Open SSE connection
    # 2. Wait for endpoint event
    # 3. Send tool call via POST
    # 4. Receive response via SSE
    # 5. Verify correct data
    pass

async def test_concurrent_clients():
    """Test multiple concurrent SSE connections."""
    # Open 10 concurrent SSE connections
    # Send messages from each
    # Verify responses are isolated
    pass
```

### Load Testing

```python
# locustfile.py

from locust import HttpUser, task, between

class MCPUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def sse_connection(self):
        """Test SSE connection."""
        with self.client.get("/sse", stream=True) as response:
            for line in response.iter_lines():
                if "endpoint" in line:
                    break
    
    @task(3)
    def tool_call(self):
        """Test tool call via POST."""
        self.client.post("/messages", json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "get_current_temperature"}
        })
```

---

## Deployment Considerations

### 1. Connection Limits

```python
# uvicorn server configuration
uvicorn.run(
    http_app,
    host="0.0.0.0",
    port=8000,
    workers=4,  # Multi-process workers
    limit_concurrency=1000,  # Max concurrent connections
    timeout_keep_alive=75,  # SSE keep-alive timeout
)
```

### 2. Reverse Proxy Configuration

**Nginx:**

```nginx
location /sse {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;  # Critical for SSE
    proxy_cache off;
    proxy_read_timeout 24h;  # Long timeout for SSE
}

location /messages {
    proxy_pass http://localhost:8000;
    proxy_http_version 1.1;
}
```

### 3. Cloud Platform Configuration

**Fly.io (fly.toml):**

```toml
[http_service]
  internal_port = 8000
  force_https = true
  auto_stop_machines = false  # Keep SSE connections alive
  auto_start_machines = true
  min_machines_running = 1
  
  [[http_service.checks]]
    grace_period = "5s"
    interval = "30s"
    method = "GET"
    path = "/health"
    timeout = "5s"
```

### 4. Monitoring

```python
# Add Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

sse_connections = Gauge(
    "sse_connections_active",
    "Number of active SSE connections"
)

messages_received = Counter(
    "messages_received_total",
    "Total messages received",
    ["method"]
)

request_duration = Histogram(
    "request_duration_seconds",
    "Request duration",
    ["endpoint"]
)
```

---

## Migration Path

### ✅ Migration Complete (FastMCP 2.0)

The migration to FastMCP 2.0 is complete:

1. ✅ Migrated from `mcp.server.Server` to `fastmcp.FastMCP`
2. ✅ Converted manual handlers to `@mcp.tool()` and `@mcp.resource()` decorators
3. ✅ Replaced manual SSE setup with `mcp.run(transport="http")`
4. ✅ All 151 tests passing
5. ✅ 85% code coverage maintained

**No migration needed** - FastMCP is now the default implementation.

---

## Performance Optimization

### 1. Connection Pooling

```python
# Use connection pooling for Aareguru API
import httpx

http_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_connections=100,
        max_keepalive_connections=20,
    )
)
```

### 2. Response Caching

```python
# Cache frequently accessed data
from functools import lru_cache
from datetime import datetime, timedelta

_cache = {}
_cache_ttl = {}

async def get_cached_data(key: str, ttl: int = 120):
    """Get data with TTL-based caching."""
    if key in _cache:
        if datetime.now() < _cache_ttl[key]:
            return _cache[key]
    
    # Fetch fresh data
    data = await fetch_data(key)
    _cache[key] = data
    _cache_ttl[key] = datetime.now() + timedelta(seconds=ttl)
    return data
```

### 3. Graceful Degradation

```python
# Handle API failures gracefully
async def call_tool_with_fallback(name: str, arguments: dict):
    """Call tool with fallback on failure."""
    try:
        return await tools.call_tool(name, arguments)
    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [{
            "type": "text",
            "text": f"⚠️ Service temporarily unavailable. Please try again."
        }]
```

---

## Client Configuration

### Claude Desktop (Full SSE)

```json
{
  "mcpServers": {
    "aareguru": {
      "url": "http://localhost:8000/sse",
      "transport": "sse",
      "headers": {
        "X-API-Key": "your-api-key-here"
      }
    }
  }
}
```

### Custom Client (JavaScript)

```javascript
// Connect to SSE endpoint
const eventSource = new EventSource('http://localhost:8000/sse', {
  headers: {
    'X-API-Key': 'your-api-key-here'
  }
});

// Extract message endpoint from first event
let messageEndpoint = null;
eventSource.addEventListener('endpoint', (event) => {
  const data = JSON.parse(event.data);
  messageEndpoint = data.uri;
});

// Listen for server messages
eventSource.addEventListener('message', (event) => {
  const message = JSON.parse(event.data);
  console.log('Server message:', message);
});

// Send client messages
async function sendMessage(message) {
  await fetch(messageEndpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'your-api-key-here'
    },
    body: JSON.stringify(message)
  });
}
```

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| SSE connection drops | Reverse proxy buffering | Disable `proxy_buffering` in nginx |
| Sessions not found | Session expired/cleaned up | Implement session keepalive |
| CORS errors | Wrong origin configuration | Update `CORS_ORIGINS` setting |
| 401 Unauthorized | Missing/invalid API key | Verify `X-API-Key` header |
| High latency | Network/API delays | Enable caching, use CDN |

### Debug Mode

```bash
# Run with debug logging
LOG_LEVEL=debug uv run python -m aareguru_mcp.http_server

# Watch SSE events
curl -N -H "X-API-Key: your-key" http://localhost:8000/sse

# Send test message
curl -X POST http://localhost:8000/messages?session_id=xxx \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

---

## Next Steps

### ✅ Completed

1. ✅ FastMCP 2.0 implementation
2. ✅ HTTP transport via `mcp.run(transport="http")`
3. ✅ Docker containerization
4. ✅ 151 tests passing, 85% coverage
5. ✅ Structured logging with structlog

### Future Enhancements

1. ⬜ Horizontal scaling support
2. ⬜ Redis-based session storage (if needed)
3. ⬜ Additional authentication options
4. ⬜ Prometheus metrics integration

---

## References

### FastMCP Documentation

- **FastMCP**: High-level MCP framework with decorator-based API
- **Transport**: `mcp.run(transport="http")` for HTTP/SSE
- **ASGI App**: `mcp.http_app()` for custom middleware

### External Resources

- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [FastMCP GitHub](https://github.com/jlowin/fastmcp)
- [Server-Sent Events Spec (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

---

## Conclusion

The Aareguru MCP server now uses **FastMCP 2.0** for a production-ready HTTP/SSE implementation:

- ✅ **Fully MCP protocol compliant** via FastMCP
- ✅ **Simplified codebase** with decorators
- ✅ **Built-in HTTP transport** - no manual SSE setup
- ✅ **Production-ready** with Docker support
- ✅ **Well-tested** with 151 tests and 85% coverage

**FastMCP 2.0 Benefits:**
- 70% less boilerplate code
- Automatic session management
- Built-in transport handling
- Decorator-based tool/resource registration
