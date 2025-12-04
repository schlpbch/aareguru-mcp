# Docker Setup for Aareguru MCP

This document describes how to build and run the Aareguru MCP server using Docker.

## Prerequisites

- Docker Engine 20.10 or later
- Docker Compose V2 (optional, for multi-container setup)

## Quick Start

### Using Docker Compose (Recommended)

1. **Copy the environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Start the service:**
   ```bash
   docker-compose up -d
   ```

3. **View logs (JSON-formatted):**
   ```bash
   docker-compose logs -f
   
   # Pretty-print JSON logs (requires jq)
   docker-compose logs -f | grep '"event":' | jq .
   ```

4. **Stop the service:**
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the image:**
   ```bash
   ./docker-build.sh
   # Or manually:
   docker build -t aareguru-mcp:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name aareguru-mcp \
     -p 8000:8000 \
     -e LOG_LEVEL=info \
     aareguru-mcp:latest
   ```

3. **View logs:**
   ```bash
   docker logs -f aareguru-mcp
   ```

4. **Stop and remove:**
   ```bash
   docker stop aareguru-mcp
   docker rm aareguru-mcp
   ```

## Configuration

### Environment Variables

Configure the server by setting environment variables in the `.env` file or passing them to Docker:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY_REQUIRED` | Require API keys for access | `false` |
| `API_KEYS` | Comma-separated list of valid API keys | _(empty)_ |
| `CORS_ORIGINS` | Allowed CORS origins (`*` for all) | `*` |
| `RATE_LIMIT_PER_MINUTE` | Max requests per minute per client | `60` |
| `LOG_LEVEL` | Logging level (debug/info/warning/error) | `info` |
| `HOST` | Host to bind to | `0.0.0.0` |
| `PORT` | Port to listen on | `8000` |

### Example with API Key Protection

```bash
docker run -d \
  --name aareguru-mcp \
  -p 8000:8000 \
  -e API_KEY_REQUIRED=true \
  -e API_KEYS=your-secret-key-1,your-secret-key-2 \
  -e LOG_LEVEL=info \
  aareguru-mcp:latest
```

## Development Setup

For development with hot-reload:

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

This will:
- Mount source code as volumes for live updates
- Enable auto-reload on code changes
- Set log level to debug

## Health Check

The container includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "0.1.0"
}
```

## Testing the Server

### SSE Endpoint

Test the Server-Sent Events endpoint:

```bash
curl -N http://localhost:8000/sse
```

### Using with MCP Client

Configure your MCP client to connect to:
```
http://localhost:8000/sse
```

## Troubleshooting

### Container won't start

Check logs:
```bash
docker-compose logs aareguru-mcp
```

### Port already in use

Change the port mapping in `docker-compose.yml` or use:
```bash
docker run -p 8001:8000 aareguru-mcp:latest
```

### Permission issues

Ensure the build script is executable:
```bash
chmod +x docker-build.sh
```

## Structured Logging

The server outputs **structured JSON logs** for better observability:

```json
{
  "version": "0.1.0",
  "host": "0.0.0.0",
  "port": 8000,
  "event": "starting_aareguru_mcp_http_server",
  "level": "info",
  "timestamp": "2025-12-02T21:50:04.708120Z"
}
```

### Viewing Structured Logs

```bash
# View raw JSON logs
docker logs aareguru-mcp-aareguru-mcp-1

# Pretty-print with jq
docker logs aareguru-mcp-aareguru-mcp-1 | grep '"event":' | jq .

# Filter by event type
docker logs aareguru-mcp-aareguru-mcp-1 | grep '"event":"sse_connection_started"'

# Follow logs in real-time
docker logs -f aareguru-mcp-aareguru-mcp-1 | jq .
```

📖 **See [STRUCTURED_LOGGING.md](STRUCTURED_LOGGING.md)** for complete documentation.

## Multi-Stage Build

The Dockerfile uses a multi-stage build for optimization:

1. **Builder stage**: Installs dependencies using `uv`
2. **Runtime stage**: Minimal Python image with only runtime dependencies

This results in a smaller, more secure final image.

## Security Considerations

1. **API Keys**: Enable `API_KEY_REQUIRED=true` in production
2. **CORS**: Restrict `CORS_ORIGINS` to your specific domains
3. **Rate Limiting**: Adjust `RATE_LIMIT_PER_MINUTE` based on your needs
4. **Network**: Use Docker networks to isolate containers
5. **Secrets**: Never commit `.env` file with real API keys

## Advanced Usage

### Custom Network

```bash
docker network create aareguru-net
docker run -d \
  --name aareguru-mcp \
  --network aareguru-net \
  -p 8000:8000 \
  aareguru-mcp:latest
```

### Persistent Logs

```bash
docker run -d \
  --name aareguru-mcp \
  -p 8000:8000 \
  -v $(pwd)/logs:/app/logs \
  aareguru-mcp:latest
```

### Resource Limits

```bash
docker run -d \
  --name aareguru-mcp \
  -p 8000:8000 \
  --memory="512m" \
  --cpus="1.0" \
  aareguru-mcp:latest
```

## Production Deployment

For production, consider:

1. **Use a reverse proxy** (nginx, Traefik) for SSL/TLS
2. **Enable health checks** for orchestration platforms
3. **Set resource limits** appropriate for your workload
4. **Use secrets management** for API keys
5. **Configure logging** to external systems
6. **Monitor metrics** and performance

Example with Docker Swarm:

```yaml
version: "3.8"
services:
  aareguru-mcp:
    image: aareguru-mcp:latest
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    ports:
      - "8000:8000"
    secrets:
      - api_keys
    environment:
      - API_KEY_REQUIRED=true

secrets:
  api_keys:
    external: true
```

## Cleaning Up

Remove all containers and images:

```bash
docker-compose down --rmi all --volumes
```

Or manually:
```bash
docker stop aareguru-mcp
docker rm aareguru-mcp
docker rmi aareguru-mcp:latest
```
