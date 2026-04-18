"""Development server wrapper for FastMCP CLI.

This file allows fastmcp run/dev to properly import and run the mcp server
with the correct module context.
"""

from aareguru_mcp.server import mcp

__all__ = ["mcp"]
