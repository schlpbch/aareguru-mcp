"""HTTP/SSE server for Aareguru MCP.

This module implements an HTTP server with Server-Sent Events (SSE) transport
for the MCP protocol, enabling remote access to the Aareguru MCP server.

"""

import asyncio
import time
from collections import defaultdict

import structlog
import uvicorn
from mcp.server.sse import SseServerTransport
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from .config import get_settings
from .server import app as mcp_server

# Get structured logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize SSE transport (for full MCP SSE mode)
# Note: Must include trailing slash to match Mount path
sse_transport = SseServerTransport(endpoint="/messages/")


# Metrics tracking
class ServerMetrics:
    """Track server metrics for monitoring and observability."""

    def __init__(self):
        self.active_connections = 0
        self.total_connections = 0
        self.total_messages = 0
        self.total_errors = 0
        self.connection_errors = 0
        self.message_errors = 0
        self.start_time = time.time()

        # Per-endpoint metrics
        self.endpoint_calls: dict[str, int] = defaultdict(int)
        self.endpoint_errors: dict[str, int] = defaultdict(int)

    def connection_started(self):
        """Record a new connection."""
        self.active_connections += 1
        self.total_connections += 1

    def connection_ended(self):
        """Record a connection ending."""
        self.active_connections = max(0, self.active_connections - 1)

    def message_received(self):
        """Record a message received."""
        self.total_messages += 1

    def error_occurred(self, endpoint: str = "unknown"):
        """Record an error."""
        self.total_errors += 1
        self.endpoint_errors[endpoint] += 1

    def endpoint_called(self, endpoint: str):
        """Record an endpoint call."""
        self.endpoint_calls[endpoint] += 1

    def get_stats(self) -> dict[str, object]:
        """Get current statistics."""
        uptime = time.time() - self.start_time
        return {
            "uptime_seconds": round(uptime, 2),
            "active_connections": self.active_connections,
            "total_connections": self.total_connections,
            "total_messages": self.total_messages,
            "total_errors": self.total_errors,
            "connection_errors": self.connection_errors,
            "message_errors": self.message_errors,
            "endpoint_calls": dict(self.endpoint_calls),
            "endpoint_errors": dict(self.endpoint_errors),
        }


# Initialize metrics
metrics = ServerMetrics()


# Session tracking for cleanup
class SessionTracker:
    """Track active SSE sessions for cleanup."""

    def __init__(self):
        self.sessions: dict[str, float] = {}  # session_id -> last_activity_time

    def register_activity(self, session_id: str):
        """Register activity for a session."""
        self.sessions[session_id] = time.time()

    def cleanup_expired(self, timeout_seconds: int) -> int:
        """Remove expired sessions.

        Args:
            timeout_seconds: Session timeout in seconds

        Returns:
            Number of sessions cleaned up
        """
        now = time.time()
        expired = [
            sid for sid, last_time in self.sessions.items() if now - last_time > timeout_seconds
        ]

        for sid in expired:
            del self.sessions[sid]
            logger.info("cleaned_up_expired_session", session_id=sid)

        return len(expired)

    def get_session_count(self) -> int:
        """Get number of active sessions."""
        return len(self.sessions)


# Initialize session tracker
session_tracker = SessionTracker()


# Background cleanup task
async def session_cleanup_task():
    """Background task to periodically clean up expired sessions."""
    current_settings = get_settings()
    cleanup_interval = current_settings.sse_cleanup_interval_seconds
    session_timeout = current_settings.sse_session_timeout_seconds

    logger.info(
        f"Starting session cleanup task: "
        f"timeout={session_timeout}s, interval={cleanup_interval}s"
    )

    while True:
        try:
            await asyncio.sleep(cleanup_interval)

            cleaned = session_tracker.cleanup_expired(session_timeout)
            if cleaned > 0:
                logger.info(
                    "session_cleanup_completed",
                    expired_sessions_removed=cleaned,
                    active_sessions=session_tracker.get_session_count(),
                )
        except asyncio.CancelledError:
            logger.info("session_cleanup_task_cancelled")
            break
        except Exception as e:
            logger.error("session_cleanup_task_error", error=str(e), exc_info=True)


async def verify_api_key(request: Request) -> bool:
    """Verify API key from request headers.

    Args:
        request: Starlette request object

    Returns:
        True if API key is valid or auth is disabled, False otherwise
    """
    # Reload settings to support testing with different configurations
    current_settings = get_settings()

    if not current_settings.api_key_required:
        return True

    api_key = request.headers.get("X-API-Key", "")
    valid_keys = [k.strip() for k in current_settings.api_keys.split(",") if k.strip()]

    return api_key in valid_keys


async def health_check(request: Request) -> JSONResponse:
    """Health check endpoint.

    Returns:
        JSON response with health status
    """
    metrics.endpoint_called("health")
    return JSONResponse(
        {
            "status": "healthy",
            "service": "aareguru-mcp",
            "version": settings.app_version,
        }
    )


async def metrics_endpoint(request: Request) -> JSONResponse:
    """Metrics endpoint for monitoring.

    Returns:
        JSON response with server metrics
    """
    metrics.endpoint_called("metrics")
    stats = metrics.get_stats()
    stats["active_sessions"] = session_tracker.get_session_count()

    return JSONResponse(
        {
            "metrics": stats,
            "config": {
                "session_timeout_seconds": get_settings().sse_session_timeout_seconds,
                "cleanup_interval_seconds": get_settings().sse_cleanup_interval_seconds,
            },
        }
    )


class HybridSSEHandler:
    """Hybrid SSE/message handler for compatibility with different MCP clients.

    This ASGI app handles:
    - GET requests: Establishes SSE connection (standard MCP SSE)
    - POST requests: Routes messages to session (MCP Inspector compatibility)

    This makes it work with both standard MCP SSE clients and MCP Inspector's
    StreamableHttp transport which expects POST to the same /sse endpoint.
    """

    async def __call__(self, scope: dict, receive, send):  # type: ignore[no-untyped-def]
        """Handle both GET (SSE) and POST (messages) requests."""
        request = Request(scope, receive, send)

        # Verify API key
        if not await verify_api_key(request):
            response = JSONResponse(
                {"error": "Invalid or missing API key"},
                status_code=401,
            )
            await response(scope, receive, send)
            return

        client_ip = scope.get("client", ["unknown"])[0] if scope.get("client") else "unknown"  # type: ignore[union-attr]
        method = scope.get("method", "GET")  # type: ignore[union-attr]

        if method == "GET":
            # Handle SSE connection
            logger.info("sse_connection_started", client_ip=client_ip)
            metrics.connection_started()
            metrics.endpoint_called("sse")

            session_id: str = "unknown"
            try:
                async with sse_transport.connect_sse(scope, receive, send) as streams:  # type: ignore[arg-type]
                    read_stream, write_stream = streams

                    # Extract session ID if available
                    query_string = scope.get("query_string", b"")  # type: ignore[union-attr]
                    if isinstance(query_string, bytes):
                        session_id = (
                            query_string.decode().split("session_id=")[-1].split("&")[0]
                            or "unknown"
                        )
                    session_tracker.register_activity(session_id)

                    logger.debug(
                        "sse_session_established",
                        client_ip=client_ip,
                        session_id=session_id,
                    )

                    try:
                        # Run the MCP server with these streams
                        await mcp_server.run(
                            read_stream,
                            write_stream,
                            mcp_server.create_initialization_options(),
                        )
                    except Exception as e:
                        logger.error(
                            "mcp_server_error",
                            client_ip=client_ip,
                            error=str(e),
                            exc_info=True,
                        )
                        metrics.error_occurred("sse")
                        raise
                    finally:
                        logger.debug(
                            "sse_session_closed",
                            client_ip=client_ip,
                            session_id=session_id,
                        )
                        metrics.connection_ended()
            except Exception as e:
                logger.error(
                    "sse_connection_failed",
                    client_ip=client_ip,
                    error=str(e),
                    exc_info=True,
                )
                metrics.connection_ended()
                metrics.error_occurred("sse")
                raise

        elif method == "POST":
            # Handle message posting (for MCP Inspector compatibility)
            logger.info("message_post_received", client_ip=client_ip)
            metrics.message_received()
            metrics.endpoint_called("sse_post")

            # Route to the message handler
            await sse_transport.handle_post_message(scope, receive, send)


# Create hybrid handler instance
handle_sse_hybrid = HybridSSEHandler()


# Note: The /messages endpoint is handled directly by SseServerTransport.handle_post_message
# which is mounted as an ASGI app. No custom wrapper needed as the SDK handles
# auth, session routing, and response management internally.


# Define routes
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/metrics", metrics_endpoint, methods=["GET"]),
    Mount("/sse", app=handle_sse_hybrid),  # Hybrid endpoint: GET for SSE, POST for messages
    Mount("/messages", app=sse_transport.handle_post_message),  # Standard MCP SSE message handler
]

# Parse CORS origins
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

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
http_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


async def startup_event():
    """Handle startup events."""
    logger.info("starting_background_tasks")

    # Start session cleanup task
    asyncio.create_task(session_cleanup_task())
    logger.info("session_cleanup_task_started")


async def shutdown_event():
    """Handle shutdown events."""
    logger.info("shutting_down_server")
    logger.info("final_metrics", **metrics.get_stats())


# Register lifecycle events
http_app.add_event_handler("startup", startup_event)
http_app.add_event_handler("shutdown", shutdown_event)


def main() -> None:
    """Main entry point for HTTP server."""
    logger.info(
        "starting_aareguru_mcp_http_server",
        version=settings.app_version,
        host=settings.http_host,
        port=settings.http_port,
        url=f"http://{settings.http_host}:{settings.http_port}",
    )
    logger.info(
        "server_configuration",
        api_key_required=settings.api_key_required,
        cors_origins=settings.cors_origins,
        rate_limit_per_minute=settings.rate_limit_per_minute,
    )
    logger.info(f"Session Timeout: {settings.sse_session_timeout_seconds}s")
    logger.info(f"Cleanup Interval: {settings.sse_cleanup_interval_seconds}s")

    uvicorn.run(
        http_app,
        host=settings.http_host,
        port=settings.http_port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
