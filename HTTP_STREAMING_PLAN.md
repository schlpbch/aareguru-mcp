# Aareguru MCP Server - HTTP Streaming Implementation Plan

**Status**: 📋 Planned for Phase 3  
**Last Updated**: 2025-12-02  
**Current Phase**: Phase 1 Complete (stdio), Phase 2 In Progress

## Overview

This document outlines the strategy for exposing the Aareguru MCP server via streamable HTTP using Server-Sent Events (SSE), enabling web-based clients and remote access beyond local stdio communication.

> [!NOTE]
> **Current Status**: The stdio MCP server (Phase 1) is complete and production-ready with 135 tests passing. HTTP/SSE implementation is planned for Phase 3 (Weeks 6-7).

---

## Why HTTP Streaming?

### Benefits

| Feature | stdio (Local) | HTTP Streaming |
|---------|---------------|----------------|
| **Access** | Local process only | Remote/web access |
| **Deployment** | Desktop only | Cloud, containers, serverless |
| **Clients** | Claude Desktop | Web apps, mobile, any HTTP client |
| **Scalability** | Single user | Multiple concurrent users |
| **Authentication** | None needed | API keys, OAuth, etc. |
| **Monitoring** | Limited | Full HTTP observability |

### Use Cases

1. **Web Applications**: Integrate Aare data into web dashboards
2. **Mobile Apps**: Access from iOS/Android applications
3. **Cloud Deployment**: Run on AWS, GCP, Azure, or serverless platforms
4. **Multi-User**: Serve multiple Claude Desktop instances or clients
5. **Public API**: Expose as a public service (with rate limiting)

---

## Architecture

### MCP Protocol Transport Layers

```
┌─────────────────────────────────────────┐
│         MCP Protocol Layer              │
│  (Resources, Tools, Prompts)            │
└─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼────────┐    ┌────────▼─────────┐
│  stdio         │    │  HTTP/SSE        │
│  (Local)       │    │  (Remote)        │
└────────────────┘    └──────────────────┘
        │                       │
┌───────▼────────┐    ┌────────▼─────────┐
│ Claude Desktop │    │  Web Clients     │
│                │    │  Mobile Apps     │
│                │    │  Remote Claude   │
└────────────────┘    └──────────────────┘
```

---

## Technology Stack

### Additional Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| **starlette** | `^0.37.0` | ASGI web framework for SSE |
| **uvicorn** | `^0.29.0` | ASGI server |
| **mcp[server]** | `^1.0.0` | MCP server with HTTP support |
| **python-multipart** | `^0.0.9` | Form data parsing |

### Optional (Production)

| Package | Purpose |
|---------|---------|
| **gunicorn** | Production WSGI server |
| **redis** | Distributed caching |
| **prometheus-client** | Metrics and monitoring |
| **python-jose** | JWT authentication |

---

## Implementation Approach

The MCP Python SDK provides built-in SSE transport support.

**File**: `src/aareguru_mcp/http_server.py`

```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route
import uvicorn

from .server import create_mcp_server

app = Starlette()

@app.route("/sse", methods=["GET"])
async def handle_sse(request):
    """Handle SSE connections for MCP protocol"""
    async with SseServerTransport("/messages") as transport:
        mcp_server = create_mcp_server()
        await mcp_server.run(
            transport.read_stream,
            transport.write_stream,
            mcp_server.create_initialization_options()
        )
    
@app.route("/messages", methods=["POST"])
async def handle_messages(request):
    """Handle client messages"""
    # Process incoming MCP messages
    pass

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---


---

## Project Structure Updates

```diff
aareguru-mcp/
├── src/
│   └── aareguru_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP server (protocol layer)
+│       ├── http_server.py        # HTTP/SSE transport layer
│       ├── client.py              # Aareguru API client
│       ├── models.py              # Pydantic models
│       ├── resources.py           # MCP resources
│       ├── tools.py               # MCP tools
│       └── config.py              # Configuration
+├── docker/
+│   ├── Dockerfile                # Container image
+│   └── docker-compose.yml        # Multi-service setup
├── tests/
│   ├── test_client.py
│   ├── test_resources.py
│   ├── test_tools.py
+│   └── test_http_server.py       # HTTP endpoint tests
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

---

## Configuration

### Environment Variables

**.env.example**:
```bash
# Aareguru API Configuration
AAREGURU_BASE_URL=https://aareguru.existenz.ch
APP_NAME=aareguru-mcp-http
APP_VERSION=1.0.0

# HTTP Server Configuration
HTTP_HOST=0.0.0.0
HTTP_PORT=8000
HTTP_WORKERS=4

# Security
API_KEY_REQUIRED=true
API_KEYS=key1,key2,key3  # Comma-separated

# CORS
CORS_ORIGINS=*  # Or specific origins: https://example.com,https://app.com

# Cache & Rate Limiting
CACHE_TTL_SECONDS=120
MIN_REQUEST_INTERVAL_SECONDS=300
RATE_LIMIT_PER_MINUTE=60

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Security Considerations

### 1. Authentication

**API Key Authentication**:
```python
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header"""
    valid_keys = settings.api_keys.split(",")
    if x_api_key not in valid_keys:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/sse", dependencies=[Depends(verify_api_key)])
async def sse_endpoint(request: Request):
    # ... SSE implementation
```

**JWT Authentication** (for user-based access):
```python
from fastapi import Depends
from fastapi.security import HTTPBearer
from jose import jwt

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    """Verify JWT token"""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

### 2. Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/sse")
@limiter.limit("10/minute")
async def sse_endpoint(request: Request):
    # ... implementation
```

### 3. CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Deployment Options

### 1. Local Development

```bash
# Start HTTP server
uv run python -m aareguru_mcp.http_server

# Or with uvicorn directly
uv run uvicorn aareguru_mcp.http_server:app --reload --port 8000
```

### 2. Docker Container

**Dockerfile**:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/

# Install dependencies
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run server
CMD ["uv", "run", "uvicorn", "aareguru_mcp.http_server:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  aareguru-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AAREGURU_BASE_URL=https://aareguru.existenz.ch
      - APP_NAME=aareguru-mcp-http
      - HTTP_HOST=0.0.0.0
      - HTTP_PORT=8000
      - LOG_LEVEL=INFO
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

**Run**:
```bash
docker-compose up -d
```

### 3. Cloud Deployment

#### AWS (Elastic Beanstalk)
```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p python-3.11 aareguru-mcp

# Create environment
eb create aareguru-mcp-prod

# Deploy
eb deploy
```

#### Google Cloud Run
```bash
# Build and deploy
gcloud run deploy aareguru-mcp \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

#### Fly.io
```toml
# fly.toml
app = "aareguru-mcp"

[build]
  builder = "paketobuildpacks/builder:base"

[[services]]
  http_checks = []
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

```bash
fly launch
fly deploy
```

### 4. Serverless (AWS Lambda + API Gateway)

Requires adapter for ASGI:

```python
from mangum import Mangum
from .http_server import app

handler = Mangum(app)
```

---

## Client Configuration

### Claude Desktop (HTTP/SSE)

**claude_desktop_config.json**:
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

### Remote Server

```json
{
  "mcpServers": {
    "aareguru": {
      "url": "https://aareguru-mcp.example.com/sse",
      "transport": "sse",
      "headers": {
        "X-API-Key": "your-api-key-here"
      }
    }
  }
}
```

---

## Testing

### HTTP Endpoint Tests

**tests/test_http_server.py**:
```python
from fastapi.testclient import TestClient
from aareguru_mcp.http_server import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_sse_endpoint():
    with client.stream("GET", "/sse") as response:
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/event-stream"

def test_api_key_required():
    response = client.get("/sse")
    assert response.status_code == 401

def test_with_valid_api_key():
    headers = {"X-API-Key": "valid-key"}
    response = client.get("/sse", headers=headers)
    assert response.status_code == 200
```

### Load Testing

```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost:8000
```

**tests/load_test.py**:
```python
from locust import HttpUser, task, between

class AareguruUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def health_check(self):
        self.client.get("/health")
    
    @task(3)
    def get_temperature(self):
        self.client.get("/api/temperature/bern")
```

---

## Monitoring & Observability

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, generate_latest

# Metrics
request_count = Counter('http_requests_total', 'Total HTTP requests')
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    request_count.inc()
    with request_duration.time():
        response = await call_next(request)
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    logger.info("request_started", 
                method=request.method, 
                path=request.url.path)
    response = await call_next(request)
    logger.info("request_completed", 
                status_code=response.status_code)
    return response
```

---

## Performance Optimization

### 1. Connection Pooling

```python
# In client.py
class AareguruClient:
    def __init__(self):
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=20,
                max_connections=100
            )
        )
```

### 2. Response Caching

```python
from aiocache import cached, Cache
from aiocache.serializers import JsonSerializer

@cached(ttl=120, cache=Cache.MEMORY, serializer=JsonSerializer())
async def get_cached_current(city: str):
    """Cache current conditions for 2 minutes"""
    client = AareguruClient()
    return await client.get_current(city)
```

### 3. Async Workers

```bash
# Run with multiple workers
uvicorn aareguru_mcp.http_server:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4
```

---

## Migration Path

### Phase 1: Dual Mode (stdio + HTTP)
- Keep existing stdio implementation
- Add HTTP server as alternative
- Both use same MCP server core

### Phase 2: HTTP Primary
- Default to HTTP deployment
- stdio available for local development
- Document both approaches

### Phase 3: Cloud Native
- Full cloud deployment
- Horizontal scaling
- Production monitoring

---

## Comparison: stdio vs HTTP

| Aspect | stdio | HTTP/SSE |
|--------|-------|----------|
| **Deployment** | Local only | Anywhere |
| **Complexity** | Simple | Moderate |
| **Security** | Implicit (local) | Explicit (auth) |
| **Scalability** | Single user | Multi-user |
| **Monitoring** | Limited | Full observability |
| **Cost** | Free | Hosting costs |
| **Latency** | Lowest | Network dependent |
| **Use Case** | Desktop apps | Web/mobile/cloud |

---

## Recommended Approach

1. **Start with stdio** for MVP and local testing
2. **Add HTTP/SSE** for production deployment
3. **Use Docker** for consistent environments
4. **Deploy to cloud** for public access
5. **Implement auth** for security
6. **Add monitoring** for reliability

---

## Implementation Status

### ✅ Phase 1: Core MCP Server (stdio) - COMPLETE

**Completed (Weeks 1-3):**
- ✅ Implement core MCP server (stdio transport)
- ✅ 7 MCP tools implemented and tested
- ✅ 4 MCP resources implemented and tested
- ✅ Comprehensive test suite (135 tests, 80%+ coverage)
- ✅ Production-ready for Claude Desktop
- ✅ Complete documentation

### 🔄 Phase 2: Enhanced Features - IN PROGRESS

**Completed (Week 4):**
- ✅ Advanced tools (`compare_cities`, `get_forecast`)
- ✅ Swiss German integration
- ✅ Response formatting with emojis

**In Progress (Week 5):**
- 🔄 Proactive safety checks
- 🔄 Seasonal intelligence
- 🔄 Enhanced UX features

### ⏳ Phase 3: HTTP Deployment - PLANNED (Weeks 6-7)

**Planned:**
1. ⬜ Add HTTP/SSE transport layer (`http_server.py`)
2. ⬜ Create Dockerfile and docker-compose
3. ⬜ Implement API key authentication
4. ⬜ Add rate limiting and CORS
5. ⬜ Write HTTP endpoint tests (15 tests)
6. ⬜ Set up monitoring and logging
7. ⬜ Document HTTP API usage

### ⏳ Phase 4: Cloud Deployment - PLANNED (Week 8)

**Planned:**
8. ⬜ Deploy to cloud platform (Fly.io/GCP/AWS)
9. ⬜ Performance testing and optimization
10. ⬜ Production monitoring setup

---

## Current Implementation

### What's Working Now (Phase 1)

✅ **stdio MCP Server** - Fully functional and production-ready:
- 7 MCP tools for querying Aare river data
- 4 MCP resources for direct data access
- 135 tests passing with 80%+ coverage
- Ready for Claude Desktop integration
- Complete documentation and examples

### What's Coming Next (Phase 3)

⏳ **HTTP/SSE Server** - Planned features:
- Remote access from any HTTP client
- Cloud deployment with horizontal scaling
- Multi-user support with authentication
- Full observability with metrics and logging
- Flexible deployment (Docker, serverless, cloud platforms)

---

## Conclusion

HTTP streaming via SSE will provide a production-ready deployment option for the Aareguru MCP server, enabling:

- **Remote access** from any HTTP client
- **Cloud deployment** with horizontal scaling
- **Multi-user support** with authentication
- **Full observability** with metrics and logging
- **Flexible deployment** (Docker, serverless, cloud platforms)

The dual-mode approach (stdio + HTTP) offers the best of both worlds: simplicity for local development and power for production deployments.

**Timeline**: HTTP/SSE implementation scheduled for Phase 3 (Weeks 6-7) after Phase 2 UX enhancements are complete.
