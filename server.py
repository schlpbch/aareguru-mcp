"""Standalone entry point for FastMCP CLI tools.

This file provides a clean entry point for fastmcp dev/inspect commands
by using absolute imports instead of relative imports.
"""

from aareguru_mcp.server import mcp

# Re-export for FastMCP CLI
__all__ = ["mcp"]
