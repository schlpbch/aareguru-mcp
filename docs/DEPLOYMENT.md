# FastMCP Cloud Deployment Guide

## Overview

Aareguru MCP is deployed on **FastMCP Cloud** with automatic scaling, monitoring, and zero-downtime updates.

**Production URL**: `https://aareguru.fastmcp.app/mcp`
**Health Check**: `https://aareguru.fastmcp.app/health/`
**Metrics**: `https://aareguru.fastmcp.app/metrics` (Prometheus format)

## Prerequisites

- FastMCP Cloud account
- GitHub repository access
- `fastmcp` CLI installed (`pip install fastmcp`)

## Deployment Process

### Automatic Deployment (Current)

FastMCP Cloud automatically deploys when you push to main:

1. Push to GitHub main branch
2. FastMCP Cloud detects changes
3. Runs `uv sync` to install dependencies
4. Builds container automatically
5. Deploys with zero downtime
6. Health checks verify deployment
7. Auto-rollback if health checks fail

### Manual Deployment

```bash
# 1. Build and test locally
uv sync
uv run pytest tests/
uv run mypy src/

# 2. Deploy to FastMCP Cloud
fastmcp deploy

# 3. Verify deployment
curl https://aareguru.fastmcp.app/health/
```

## Configuration

### Environment Variables

Production environment variables are configured in `.fastmcp/config.yaml`:

- `LOG_LEVEL`: INFO (production logging level)
- `LOG_FORMAT`: json (structured logging)
- `CACHE_TTL_SECONDS`: 120 (2-minute cache)
- `MIN_REQUEST_INTERVAL_SECONDS`: 0.1 (supports parallel requests)

### Scaling Configuration

- **Min Replicas**: 2 (high availability)
- **Max Replicas**: 10 (handles traffic spikes)
- **Auto-Scale Trigger**: 70% CPU/memory
- **Region**: EU-West-1 (close to Switzerland)

### Health Checks

- **Path**: `/health`
- **Interval**: 30s
- **Timeout**: 10s
- **Failure Threshold**: 3 consecutive failures

## Monitoring

### Metrics Available

FastMCP Cloud provides built-in metrics:

- **Request Count**: Requests per tool
- **Latency**: P50, P95, P99 response times
- **Error Rate**: Percentage of failed requests
- **Active Connections**: Current concurrent connections
- **Resource Usage**: CPU and memory utilization

### Prometheus Metrics

Additional metrics at `/metrics`:

```
# Tool usage
aareguru_tool_calls_total{tool="get_current_temperature"}
aareguru_tool_duration_seconds{tool="get_current_temperature"}

# API requests
aareguru_api_requests_total{endpoint="/v2018/current"}
aareguru_api_request_duration_seconds

# System
aareguru_active_requests
aareguru_cache_size
aareguru_errors_total{error_type="validation"}
```

### Alerts

Configured alerts (`.fastmcp/config.yaml`):

- ⚠️ Warning: Error rate >1%, P95 latency >2s
- 🚨 Critical: Error rate >5%, P99 latency >5s
- 💻 Resource: CPU >80%, Memory >80%

## Rollback

### Automatic Rollback

Configured in `.fastmcp/config.yaml`:

- Triggers on >5% error rate
- Triggers on P95 >5s latency
- Grace period: 60s before rollback

### Manual Rollback

```bash
# List deployments
fastmcp deployments list

# Rollback to previous version
fastmcp rollback <deployment-id>
```

## Disaster Recovery

### Health Check Grace Period

- 60s grace period on startup
- Allows time for cache warmup
- Prevents premature failure marking

### Backup Strategy

- FastMCP Cloud maintains deployment history
- Can rollback to any previous deployment
- No persistent state (stateless service)

## Troubleshooting

### Check Deployment Status

```bash
# View current deployment
fastmcp status

# View logs
fastmcp logs --follow

# View metrics
fastmcp metrics
```

### Common Issues

**Issue**: High latency
- **Check**: Aareguru API response times
- **Solution**: Increase cache TTL or add regional caching

**Issue**: Rate limit errors
- **Check**: Request frequency
- **Solution**: Adjust MIN_REQUEST_INTERVAL_SECONDS

**Issue**: Memory spikes
- **Check**: Cache size metrics
- **Solution**: Reduce CACHE_TTL_SECONDS or increase memory limit

## Cost Optimization

FastMCP Cloud uses pay-per-request pricing:

- **Pricing**: $0.001 per request
- **Estimated Monthly Cost**: ~$10-50 (depending on usage)
- **Free Tier**: First 10,000 requests/month free

### Cost Reduction Tips

1. **Caching**: 120s TTL reduces API calls significantly
2. **Min Replicas**: Keep at 2 for balance of cost/availability
3. **Auto-Scale**: Set appropriate CPU/memory triggers

## Installation & Usage

### Claude Desktop Integration

**Option 1: Direct Configuration**

Edit your Claude Desktop config file (`~/.config/Claude/claude_desktop_config.json` on Linux/Mac or `%APPDATA%\Claude\claude_desktop_config.json` on Windows):

```json
{
  "mcpServers": {
    "aareguru": {
      "url": "https://aareguru.fastmcp.app/mcp"
    }
  }
}
```

**Option 2: Using Bundle File**

1. Download `aareguru-mcp.mcpb` from the repository
2. Open Claude Desktop
3. Go to Settings → Extensions → Add Custom Connector
4. Select `aareguru-mcp.mcpb`

### MCP Client Integration

For other MCP clients:

```python
from anthropic import Anthropic

client = Anthropic()

# Connect to Aareguru MCP
response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[
        {
            "type": "mcp",
            "url": "https://aareguru.fastmcp.app/mcp"
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "What's the current temperature in the Aare river at Bern?"
        }
    ]
)
```

## References

- [FastMCP Cloud Documentation](https://fastmcp.cloud/docs)
- [ADR-015: FastMCP Cloud Deployment](../specs/ADR_COMPENDIUM.md#adr-015-fastmcp-cloud-deployment)
- [Health Endpoint Implementation](../src/aareguru_mcp/server.py)
- [Architecture Documentation](../ARCHITECTURE.md)
