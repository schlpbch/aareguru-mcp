"""HTTP/SSE server for Aareguru MCP.

This module implements an HTTP server with Server-Sent Events (SSE) transport
for the MCP protocol, enabling remote access to the Aareguru MCP server.

Supports two modes:
1. Simplified SSE (default): Basic SSE for testing
2. Full MCP SSE (use_full_sse=true): Complete SseServerTransport implementation
"""

import asyncio
import logging
from typing import Any

import uvicorn
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response, StreamingResponse
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
    return JSONResponse({
        "status": "healthy",
        "service": "aareguru-mcp",
        "version": settings.app_version,
    })


async def handle_sse_simplified(request: Request) -> Response:
    """Handle SSE connections for MCP protocol (simplified version).
    
    This is a basic SSE implementation for testing purposes.
    
    Args:
        request: Starlette request object
        
    Returns:
        SSE response stream
    """
    logger.info(f"SSE connection (simplified) from {get_remote_address(request)}")
    
    async def event_stream():
        """Generate SSE events."""
        yield "data: {\"jsonrpc\": \"2.0\", \"method\": \"initialized\"}\n\n"
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


async def handle_sse_full(request: Request) -> Response:
    """Handle SSE connections for MCP protocol (full MCP SSE transport).
    
    This uses the official SseServerTransport for complete MCP compliance.
    
    Args:
        request: Starlette request object
        
    Returns:
        SSE response stream
    """
    logger.info(f"SSE connection (full MCP) from {get_remote_address(request)}")
    
    # Create an ASGI app using SseServerTransport
    async def sse_app(scope, receive, send):
        async with sse_transport.connect_sse(scope, receive, send) as streams:
            read_stream, write_stream = streams
            
            try:
                # Run the MCP server with these streams
                await mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp_server.create_initialization_options(),
                )
            except Exception as e:
                logger.error(f"Error in MCP server: {e}", exc_info=True)
                raise
    
    # Call the ASGI app with Starlette's scope/receive/send
    await sse_app(request.scope, request.receive, request._send)
    
    # Return empty response (actual response handled by ASGI app)
    return Response(status_code=200)


async def handle_sse(request: Request) -> Response:
    """Handle SSE connections - router between simplified and full implementation.
    
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
    
    # Route to appropriate implementation based on config
    current_settings = get_settings()
    if current_settings.use_full_sse:
        return await handle_sse_full(request)
    else:
        return await handle_sse_simplified(request)


async def handle_messages_simplified(request: Request) -> Response:
    """Handle incoming MCP messages (simplified version).
    
    Args:
        request: Starlette request object
        
    Returns:
        Response
    """
    logger.info(f"Message received (simplified) from {get_remote_address(request)}")
    return Response(status_code=200)


async def handle_messages_full(request: Request) -> Response:
    """Handle incoming MCP messages (full MCP SSE transport).
    
    This uses SseServerTransport's handle_post_message to route messages
    to the correct session.
    
    Args:
        request: Starlette request object
        
    Returns:
        Response
    """
    logger.info(f"Message received (full MCP) from {get_remote_address(request)}")
    
    # Create an ASGI app using SseServerTransport's message handler
    async def message_app(scope, receive, send):
        await sse_transport.handle_post_message()(scope, receive, send)
    
    # Call the ASGI app with Starlette's scope/receive/send
    await message_app(request.scope, request.receive, request._send)
    
    # Return empty response (actual response handled by ASGI app)
    return Response(status_code=200)


async def handle_messages(request: Request) -> Response:
    """Handle incoming MCP messages - router between simplified and full implementation.
    
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
    
    # Route to appropriate implementation based on config
    current_settings = get_settings()
    if current_settings.use_full_sse:
        return await handle_messages_full(request)
    else:
        return await handle_messages_simplified(request)


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
