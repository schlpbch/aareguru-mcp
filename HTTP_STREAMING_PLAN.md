# Aareguru MCP Server - HTTP Streaming Implementation Plan

## Overview

This document outlines the strategy for exposing the Aareguru MCP server via streamable HTTP using Server-Sent Events (SSE), enabling web-based clients and remote access beyond local stdio communication.

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

### Option 1: MCP SDK Built-in SSE (Recommended)

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

### Option 2: Custom FastAPI Implementation

For more control and additional REST endpoints.

**File**: `src/aareguru_mcp/http_server.py`

```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio

from .server import create_mcp_server
from .client import AareguruClient

app = FastAPI(title="Aareguru MCP Server")

# Initialize MCP server
mcp_server = create_mcp_server()

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Aareguru MCP Server",
        "version": "1.0.0",
        "protocol": "MCP over HTTP/SSE",
        "endpoints": {
            "sse": "/sse",
            "health": "/health",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "aareguru-mcp"}

@app.get("/sse")
async def sse_endpoint(request: Request):
    """Server-Sent Events endpoint for MCP protocol"""
    
    async def event_generator():
        try:
            # MCP handshake and message streaming
            async for message in mcp_server.stream_messages():
                yield {
                    "event": "message",
                    "data": message.model_dump_json()
                }
        except asyncio.CancelledError:
            # Client disconnected
            pass
    
    return EventSourceResponse(event_generator())

@app.post("/messages")
async def handle_message(request: Request):
    """Handle incoming MCP messages from client"""
    data = await request.json()
    response = await mcp_server.handle_message(data)
    return response

# Optional: Direct REST endpoints for convenience
@app.get("/api/temperature/{city}")
async def get_temperature(city: str):
    """Direct REST endpoint for temperature (non-MCP)"""
    client = AareguruClient()
    data = await client.get_today(city)
    return {
        "city": city,
        "temperature": data.get("aare", {}).get("temperature"),
        "text": data.get("aare", {}).get("temperature_text")
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

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

## Next Steps

1. ✅ Implement core MCP server (stdio)
2. ⬜ Add HTTP/SSE transport layer
3. ⬜ Create Dockerfile and docker-compose
4. ⬜ Implement authentication
5. ⬜ Add rate limiting and CORS
6. ⬜ Write HTTP endpoint tests
7. ⬜ Deploy to cloud platform
8. ⬜ Set up monitoring and logging
9. ⬜ Document HTTP API usage
10. ⬜ Performance testing and optimization

---

## Conclusion

HTTP streaming via SSE provides a production-ready deployment option for the Aareguru MCP server, enabling:

- **Remote access** from any HTTP client
- **Cloud deployment** with horizontal scaling
- **Multi-user support** with authentication
- **Full observability** with metrics and logging
- **Flexible deployment** (Docker, serverless, cloud platforms)

The dual-mode approach (stdio + HTTP) offers the best of both worlds: simplicity for local development and power for production deployments.
