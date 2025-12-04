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
