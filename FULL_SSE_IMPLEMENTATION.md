# Full SSE Implementation Design for Aareguru MCP Server

**Status**: 📋 Design Document  
**Date**: 2025-12-02  
**Version**: 1.0  

---

## Executive Summary

This document provides a comprehensive technical design for implementing the full MCP SSE (Server-Sent Events) transport in the Aareguru MCP server. The current implementation uses a simplified SSE approach for testing. This design outlines the complete architecture using the official `mcp.server.sse.SseServerTransport` class.

### Current State

**✅ What We Have:**
- Simplified HTTP/SSE server with basic event streaming
- API key authentication
- Rate limiting and CORS
- Health check endpoint
- 15 passing HTTP server tests

**🎯 What This Design Adds:**
- Full MCP protocol compliance via `SseServerTransport`
- Bidirectional communication (client ↔ server)
- Session management for concurrent clients
- Proper message routing and handling
- DNS rebinding protection
- Production-ready SSE implementation

---

## Architecture Overview

### SSE Transport Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Client                                │
│                    (Claude Desktop / Web)                        │
└───────────────┬─────────────────────────┬───────────────────────┘
                │                         │
        GET /sse│                         │POST /messages
                │                         │
┌───────────────▼─────────────────────────▼───────────────────────┐
│                    SseServerTransport                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Session Management                                       │  │
│  │  - Session ID generation (UUID)                          │  │
│  │  - Concurrent client tracking                            │  │
│  │  - Read/Write stream pairs per session                   │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Bidirectional Streams                                    │  │
│  │  - Server → Client (SSE event stream)                    │  │
│  │  - Client → Server (POST messages)                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└───────────────────────────────┬───────────────────────────────────┘
                                │
┌───────────────────────────────▼───────────────────────────────────┐
│                        MCP Server Core                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Protocol Layer                                           │   │
│  │  - list_resources() → 4 resources                        │   │
│  │  - read_resource(uri) → Resource data                    │   │
│  │  - list_tools() → 7 tools                                │   │
│  │  - call_tool(name, args) → Tool results                  │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────┘
```

### Key Components

| Component | Responsibility | Implementation |
|-----------|---------------|----------------|
| **SseServerTransport** | SSE protocol handling | `mcp.server.sse.SseServerTransport` |
| **Session Manager** | Track concurrent clients | Built into SseServerTransport |
| **HTTP Routes** | Endpoint exposure | Starlette routes |
| **MCP Server** | Protocol logic | Existing `server.py` |
| **Security Layer** | Auth & validation | Custom middleware |

---

## Technical Design

### 1. SseServerTransport Initialization

The `SseServerTransport` class manages SSE connections and message routing:

```python
from mcp.server.sse import SseServerTransport

# Initialize transport with message endpoint
sse_transport = SseServerTransport(
    endpoint="/messages",  # Relative path for client POST requests
    security_settings=None  # Optional DNS rebinding protection
)
```

**Key Parameters:**
- `endpoint`: Relative path where clients POST messages (e.g., `/messages`)
- `security_settings`: Optional `TransportSecuritySettings` for DNS rebinding protection

**Why Relative Paths?**
1. **Security**: Prevents cross-origin requests
2. **Flexibility**: Works at any mount point
3. **Portability**: Same config across environments

### 2. SSE Connection Flow (GET /sse)

```
Client                          Server
  │                               │
  │──── GET /sse ────────────────→│
  │                               │ 1. Validate API key
  │                               │ 2. Create session (UUID)
  │                               │ 3. Create read/write streams
  │                               │ 4. Send endpoint info
  │                               │
  │←──── 200 OK + SSE stream ─────│
  │      event: endpoint          │
  │      data: {"uri": "/messages?session_id=xxx"}
  │                               │
  │←──── Server messages ─────────│
  │      (JSON-RPC responses)     │
  │                               │
  │      (Keep-alive)             │
  │                               │
```

### 3. Message Handling Flow (POST /messages)

```
Client                          Server
  │                               │
  │──── POST /messages?session_id=xxx ────→│
  │      Content-Type: application/json   │
  │      Body: {"jsonrpc": "2.0", ...}    │
  │                               │ 1. Validate API key
  │                               │ 2. Extract session_id
  │                               │ 3. Find session streams
  │                               │ 4. Route to MCP server
  │                               │ 5. Process request
  │                               │
  │←──── 204 No Content ──────────│
  │                               │
  │←──── Response via SSE ────────│
  │      (on GET /sse stream)     │
  │                               │
```

### 4. Implementation Code

**File: `src/aareguru_mcp/http_server.py`**

```python
"""HTTP/SSE server for Aareguru MCP with full SSE transport."""

import asyncio
import logging
from typing import Any
from uuid import UUID

import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route
from mcp.server.sse import SseServerTransport

from .config import get_settings
from .server import app as mcp_server

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize SSE transport
sse_transport = SseServerTransport(endpoint="/messages")


async def verify_api_key(request: Request) -> bool:
    """Verify API key from request headers."""
    current_settings = get_settings()
    
    if not current_settings.api_key_required:
        return True
    
    api_key = request.headers.get("X-API-Key", "")
    valid_keys = [k.strip() for k in current_settings.api_keys.split(",") if k.strip()]
    
    return api_key in valid_keys


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "service": "aareguru-mcp",
        "version": settings.app_version,
    })


async def handle_sse(request: Request) -> Response:
    """Handle SSE connections for MCP protocol.
    
    This endpoint:
    1. Validates API key
    2. Creates a new SSE session
    3. Returns a long-lived SSE stream for server→client messages
    4. Sends the endpoint URI for client→server messages
    """
    # Verify API key
    if not await verify_api_key(request):
        return JSONResponse(
            {"error": "Invalid or missing API key"},
            status_code=401,
        )
    
    logger.info(f"SSE connection from {get_remote_address(request)}")
    
    # Use SseServerTransport's connect_sse method
    # This is an ASGI application that handles the SSE connection
    async def sse_app(scope, receive, send):
        async with sse_transport.connect_sse(scope, receive, send) as streams:
            read_stream, write_stream = streams
            
            # Run the MCP server with these streams
            try:
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
            except Exception as e:
                logger.error(f"Error in MCP server: {e}", exc_info=True)
    
    # Call the ASGI app with Starlette's scope/receive/send
    return await sse_app(request.scope, request.receive, request._send)


async def handle_messages(request: Request) -> Response:
    """Handle incoming MCP messages from client.
    
    This endpoint:
    1. Validates API key
    2. Extracts session_id from query params
    3. Routes the message to the correct SSE session
    4. Returns 204 (response sent via SSE)
    """
    # Verify API key
    if not await verify_api_key(request):
        return JSONResponse(
            {"error": "Invalid or missing API key"},
            status_code=401,
        )
    
    logger.info(f"Incoming message from {get_remote_address(request)}")
    
    # Use SseServerTransport's handle_post_message method
    # This is an ASGI application that processes POST messages
    async def message_app(scope, receive, send):
        await sse_transport.handle_post_message()(scope, receive, send)
    
    # Call the ASGI app with Starlette's scope/receive/send
    return await message_app(request.scope, request.receive, request._send)


# Define routes
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/sse", handle_sse, methods=["GET"]),
    Route("/messages", handle_messages, methods=["POST"]),
]

# Parse CORS origins
cors_origins = [
    origin.strip() 
    for origin in settings.cors_origins.split(",") 
    if origin.strip()
]

# Define middleware
middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    ),
]

# Create Starlette application
http_app = Starlette(
    debug=False,
    routes=routes,
    middleware=middleware,
)

# Add rate limiter
http_app.state.limiter = limiter
http_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def main() -> None:
    """Main entry point for HTTP server."""
    logger.info(f"Starting Aareguru MCP HTTP Server v{settings.app_version}")
    logger.info(f"Server: http://{settings.http_host}:{settings.http_port}")
    logger.info(f"SSE Endpoint: /sse")
    logger.info(f"Messages Endpoint: /messages")
    logger.info(f"API Key Required: {settings.api_key_required}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"Rate Limit: {settings.rate_limit_per_minute}/minute")
    
    uvicorn.run(
        http_app,
        host=settings.http_host,
        port=settings.http_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
```

---

## Session Management

### Session Lifecycle

```python
# SseServerTransport manages sessions internally:

class SseServerTransport:
    _read_stream_writers: dict[UUID, MemoryObjectSendStream[SessionMessage | Exception]]
    
    # On GET /sse:
    # 1. Generate session_id = uuid4()
    # 2. Create memory streams for bidirectional communication
    # 3. Store in _read_stream_writers[session_id]
    # 4. Send endpoint URI to client: "/messages?session_id={session_id.hex}"
    
    # On POST /messages?session_id=xxx:
    # 1. Extract session_id from query params
    # 2. Look up streams in _read_stream_writers[session_id]
    # 3. Route message to correct session
    # 4. MCP server processes and responds via SSE stream
```

### Concurrent Client Support

- Each SSE connection gets a unique session ID
- Sessions are isolated (no cross-talk)
- Automatic cleanup when SSE connection closes
- Thread-safe stream management via anyio

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

### Phase 1: Parallel Implementation (Week 1)

1. ✅ Keep existing simplified SSE (for tests)
2. ⬜ Add full SSE implementation alongside
3. ⬜ Feature flag to switch between implementations
4. ⬜ Update tests gradually

```python
# config.py
class Settings(BaseSettings):
    use_full_sse: bool = Field(default=False, description="Use full MCP SSE transport")
```

### Phase 2: Testing & Validation (Week 2)

1. ⬜ Test full SSE with real MCP clients
2. ⬜ Performance benchmarking
3. ⬜ Fix any issues found
4. ⬜ Update documentation

### Phase 3: Switch Over (Week 3)

1. ⬜ Make full SSE the default
2. ⬜ Remove simplified implementation
3. ⬜ Update all tests
4. ⬜ Deploy to production

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

### Immediate (Week 1)

1. ⬜ Implement full SSE transport code
2. ⬜ Add session management tests
3. ⬜ Test with real MCP clients
4. ⬜ Document any SDK quirks found

### Short Term (Weeks 2-3)

1. ⬜ Performance benchmarking
2. ⬜ Load testing with multiple clients
3. ⬜ Security audit
4. ⬜ Production deployment

### Long Term (Month 2+)

1. ⬜ Horizontal scaling support
2. ⬜ Redis-based session storage
3. ⬜ WebSocket fallback option
4. ⬜ GraphQL alternative endpoint

---

## References

### MCP SDK Documentation

- **SseServerTransport**: `mcp.server.sse.SseServerTransport`
- **Server**: `mcp.server.Server`
- **Types**: `mcp.types` (Tool, Resource, TextContent, etc.)

### External Resources

- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [Server-Sent Events Spec (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Starlette Documentation](https://www.starlette.io/)
- [ASGI Specification](https://asgi.readthedocs.io/)

---

## Conclusion

This design provides a complete roadmap for implementing full MCP SSE transport in the Aareguru MCP server. The implementation will:

- ✅ Be fully MCP protocol compliant
- ✅ Support concurrent clients with session isolation
- ✅ Provide production-ready security
- ✅ Enable cloud deployment
- ✅ Maintain backward compatibility during migration

**Estimated Implementation Time**: 2-3 weeks  
**Complexity**: Medium  
**Priority**: High for production deployment

The phased migration approach ensures zero downtime and allows thorough testing at each stage.
