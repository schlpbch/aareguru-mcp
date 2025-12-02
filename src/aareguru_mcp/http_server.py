"""HTTP/SSE server for Aareguru MCP.

This module implements an HTTP server with Server-Sent Events (SSE) transport
for the MCP protocol, enabling remote access to the Aareguru MCP server.

Supports two modes:
1. Simplified SSE (default): Basic SSE for testing
2. Full MCP SSE (use_full_sse=true): Complete SseServerTransport implementation
"""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Dict

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

# Initialize SSE transport (for full MCP SSE mode)
sse_transport = SseServerTransport(endpoint="/messages")

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
        self.endpoint_calls: Dict[str, int] = defaultdict(int)
        self.endpoint_errors: Dict[str, int] = defaultdict(int)
    
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
    
    def get_stats(self) -> Dict[str, object]:
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
        self.sessions: Dict[str, float] = {}  # session_id -> last_activity_time
    
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
            sid for sid, last_time in self.sessions.items()
            if now - last_time > timeout_seconds
        ]
        
        for sid in expired:
            del self.sessions[sid]
            logger.info(f"Cleaned up expired session: {sid}")
        
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
                logger.info(f"Session cleanup: removed {cleaned} expired sessions")
                logger.info(f"Active sessions: {session_tracker.get_session_count()}")
        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in session cleanup task: {e}", exc_info=True)


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
    return JSONResponse({
        "status": "healthy",
        "service": "aareguru-mcp",
        "version": settings.app_version,
    })


async def metrics_endpoint(request: Request) -> JSONResponse:
    """Metrics endpoint for monitoring.
    
    Returns:
        JSON response with server metrics
    """
    stats = metrics.get_stats()
    stats["active_sessions"] = session_tracker.get_session_count()
    
    return JSONResponse({
        "metrics": stats,
        "config": {
            "session_timeout_seconds": get_settings().sse_session_timeout_seconds,
            "cleanup_interval_seconds": get_settings().sse_cleanup_interval_seconds,
        },
    })


async def handle_sse(request: Request) -> Response:
    """Handle SSE connections for MCP protocol.
    
    This uses the official SseServerTransport for complete MCP compliance.
    
    Args:
        request: Starlette request object
        
    Returns:
        SSE response stream
    """
    # Verify API key
    if not await verify_api_key(request):
        return JSONResponse(
            {"error": "Invalid or missing API key"},
            status_code=401,
        )
    
    client_ip = get_remote_address(request)
    logger.info(f"SSE connection from {client_ip}")
    
    # Track connection metrics
    metrics.connection_started()
    metrics.endpoint_called("sse")
    
    # Create an ASGI app using SseServerTransport
    async def sse_app(scope: dict, receive: object, send: object) -> None:  # type: ignore[type-arg]
        session_id: str = "unknown"
        try:
            async with sse_transport.connect_sse(scope, receive, send) as streams:  # type: ignore[arg-type]
                read_stream, write_stream = streams
                
                # Extract session ID if available
                query_string = scope.get("query_string", b"")  # type: ignore[union-attr]
                if isinstance(query_string, bytes):
                    session_id = query_string.decode().split("session_id=")[-1].split("&")[0] or "unknown"
                session_tracker.register_activity(session_id)
                
                logger.debug(f"SSE session established for {client_ip}, session: {session_id}")
                
                try:
                    # Run the MCP server with these streams
                    await mcp_server.run(
                        read_stream,
                        write_stream,
                        mcp_server.create_initialization_options(),
                    )
                except Exception as e:
                    logger.error(f"Error in MCP server for {client_ip}: {e}", exc_info=True)
                    metrics.error_occurred("sse_full")
                    raise
                finally:
                    logger.debug(f"SSE session closed for {client_ip}, session: {session_id}")
                    metrics.connection_ended()
        except Exception as e:
            logger.error(f"SSE connection failed for {client_ip}: {e}", exc_info=True)
            metrics.connection_ended()
            metrics.error_occurred("sse_full")
            raise
    
    # Call the ASGI app with Starlette's scope/receive/send
    try:
        await sse_app(request.scope, request.receive, request._send)  # type: ignore[attr-defined]
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Failed to establish SSE connection: {e}")
        return JSONResponse(
            {"error": "SSE connection failed", "detail": str(e)},
            status_code=500,
        )


async def handle_messages(request: Request) -> Response:
    """Handle incoming MCP messages.
    
    This uses SseServerTransport's handle_post_message to route messages
    to the correct session.
    
    Args:
        request: Starlette request object
        
    Returns:
        Response
    """
    # Verify API key
    if not await verify_api_key(request):
        return JSONResponse(
            {"error": "Invalid or missing API key"},
            status_code=401,
        )
    
    client_ip = get_remote_address(request)
    session_id = request.query_params.get("session_id", "unknown")
    logger.info(f"Message received from {client_ip}, session: {session_id}")
    
    # Track message metrics
    metrics.message_received()
    metrics.endpoint_called("messages")
    
    # Update session activity
    if session_id != "unknown":
        session_tracker.register_activity(session_id)
    
    # Create an ASGI app using SseServerTransport's message handler
    async def message_app(scope: dict, receive: object, send: object) -> None:  # type: ignore[type-arg]
        try:
            await sse_transport.handle_post_message()(scope, receive, send)  # type: ignore[arg-type]
        except Exception as e:
            logger.error(f"Message handling failed for {client_ip}, session {session_id}: {e}", exc_info=True)
            metrics.error_occurred("messages_full")
            raise
    
    # Call the ASGI app with Starlette's scope/receive/send
    try:
        await message_app(request.scope, request.receive, request._send)  # type: ignore[attr-defined]
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Failed to process message: {e}")
        metrics.error_occurred("messages_full")
        return JSONResponse(
            {"error": "Message processing failed", "detail": str(e)},
            status_code=500,
        )





# Define routes
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/metrics", metrics_endpoint, methods=["GET"]),
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
http_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]


async def startup_event():
    """Handle startup events."""
    logger.info("Starting background tasks...")
    
    # Start session cleanup task
    asyncio.create_task(session_cleanup_task())
    logger.info("Session cleanup task started")


async def shutdown_event():
    """Handle shutdown events."""
    logger.info("Shutting down server...")
    logger.info(f"Final metrics: {metrics.get_stats()}")


# Register lifecycle events
http_app.add_event_handler("startup", startup_event)
http_app.add_event_handler("shutdown", shutdown_event)


def main() -> None:
    """Main entry point for HTTP server."""
    logger.info(f"Starting Aareguru MCP HTTP Server v{settings.app_version}")
    logger.info(f"Server: http://{settings.http_host}:{settings.http_port}")
    logger.info(f"API Key Required: {settings.api_key_required}")
    logger.info(f"CORS Origins: {settings.cors_origins}")
    logger.info(f"Rate Limit: {settings.rate_limit_per_minute}/minute")
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
