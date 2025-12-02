# Structured Logging

The Aareguru MCP server now uses **structured logging** with [structlog](https://www.structlog.org/) to provide machine-readable, JSON-formatted logs for better observability and log aggregation.

## Overview

Structured logging replaces traditional text-based logging with JSON-formatted logs that include:
- **Event names**: Snake-case identifiers for log events
- **Context fields**: Named parameters with relevant data
- **Standard fields**: `level`, `timestamp` (ISO 8601), `event`
- **Structured errors**: Error details with proper field names

## Configuration

Structlog is configured in `src/aareguru_mcp/__init__.py` with:

```python
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,  # Merge context variables
        structlog.processors.add_log_level,        # Add log level
        structlog.processors.TimeStamper(fmt="iso"),  # ISO timestamps
        structlog.processors.StackInfoRenderer(),  # Stack traces
        structlog.processors.format_exc_info,      # Exception formatting
        structlog.processors.JSONRenderer(),       # JSON output
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

## Log Examples

### Server Startup
```json
{
  "version": "0.1.0",
  "host": "0.0.0.0",
  "port": 8000,
  "url": "http://0.0.0.0:8000",
  "event": "starting_aareguru_mcp_http_server",
  "level": "info",
  "timestamp": "2025-12-02T21:50:04.708120Z"
}
```

### Server Configuration
```json
{
  "api_key_required": false,
  "cors_origins": "*",
  "rate_limit_per_minute": 60,
  "event": "server_configuration",
  "level": "info",
  "timestamp": "2025-12-02T21:50:04.708179Z"
}
```

### SSE Connection
```json
{
  "client_ip": "172.18.0.1",
  "event": "sse_connection_started",
  "level": "info",
  "timestamp": "2025-12-02T21:51:17.384857Z"
}
```

### Session Cleanup
```json
{
  "expired_sessions_removed": 2,
  "active_sessions": 5,
  "event": "session_cleanup_completed",
  "level": "info",
  "timestamp": "2025-12-02T21:55:04.123456Z"
}
```

### Error Handling
```json
{
  "client_ip": "172.18.0.1",
  "error": "Connection timeout",
  "event": "sse_connection_failed",
  "level": "error",
  "timestamp": "2025-12-02T21:52:15.789012Z",
  "exc_info": true
}
```

### Server Shutdown
```json
{
  "uptime_seconds": 1234.56,
  "active_connections": 0,
  "total_connections": 42,
  "total_messages": 156,
  "total_errors": 2,
  "event": "final_metrics",
  "level": "info",
  "timestamp": "2025-12-02T22:00:00.000000Z"
}
```

## Usage in Code

### Getting a Logger
```python
import structlog

logger = structlog.get_logger(__name__)
```

### Logging with Context
```python
# Simple event
logger.info("server_started")

# Event with context fields
logger.info(
    "request_processed",
    endpoint="/health",
    response_time_ms=12.34,
    status_code=200
)

# Error with exception
try:
    # some operation
    pass
except Exception as e:
    logger.error(
        "operation_failed",
        operation="fetch_data",
        error=str(e),
        exc_info=True
    )
```

## Benefits

1. **Machine-Readable**: JSON format is easy to parse and index
2. **Structured Context**: Named fields instead of string interpolation
3. **Easy Filtering**: Query logs by specific fields (e.g., `client_ip`, `event`)
4. **Log Aggregation**: Compatible with ELK, Splunk, CloudWatch, etc.
5. **Type Safety**: Field values maintain their types (numbers, booleans)
6. **Consistent Format**: Same structure across all modules

## Viewing Logs

### Docker Logs
```bash
# View all logs
docker logs aareguru-mcp-aareguru-mcp-1

# Follow logs in real-time
docker logs -f aareguru-mcp-aareguru-mcp-1

# Filter for specific events
docker logs aareguru-mcp-aareguru-mcp-1 | grep '"event":"sse_connection_started"'

# Pretty-print JSON (requires jq)
docker logs aareguru-mcp-aareguru-mcp-1 | grep '"event":' | jq .
```

### Local Development
```bash
# Run server with visible logs
uv run aareguru-mcp-http

# Logs will appear in stdout as JSON
```

## Log Levels

- **INFO**: Normal operations (startup, requests, cleanup)
- **DEBUG**: Detailed debugging information (session details, state changes)
- **ERROR**: Errors with context and stack traces
- **WARNING**: Deprecated features or potential issues

## Modules with Structured Logging

All modules now use structured logging:

- ✅ `http_server.py` - HTTP/SSE server operations
- ✅ `server.py` - MCP server operations
- ✅ `client.py` - API client operations
- ✅ `tools.py` - Tool execution
- ✅ `resources.py` - Resource access

## Migration from Standard Logging

### Before (Standard Logging)
```python
import logging
logger = logging.getLogger(__name__)

logger.info(f"User {user_id} logged in from {ip_address}")
logger.error(f"Failed to connect: {error}", exc_info=True)
```

### After (Structured Logging)
```python
import structlog
logger = structlog.get_logger(__name__)

logger.info("user_logged_in", user_id=user_id, ip_address=ip_address)
logger.error("connection_failed", error=str(error), exc_info=True)
```

## Testing

Structured logging is tested and verified through:
- ✅ All unit tests pass (172 passed, 5 skipped)
- ✅ Integration tests with HTTP server
- ✅ Docker container runs with structured logs
- ✅ 84% code coverage maintained

## Dependencies

- `structlog>=24.1.0` - Structured logging library
- Added to `pyproject.toml` dependencies

## Future Enhancements

Potential future improvements:
- Add correlation IDs for request tracing
- Include performance metrics in logs
- Add structured logging to test suite output
- Export metrics to Prometheus/StatsD
- Add log sampling for high-volume events

## Resources

- [structlog Documentation](https://www.structlog.org/)
- [Structured Logging Best Practices](https://www.structlog.org/en/stable/standard-library.html)
- [JSON Logging Guide](https://www.structlog.org/en/stable/processors.html#structlog.processors.JSONRenderer)
