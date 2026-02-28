"""Entry point for running Aareguru MCP server as a module.

Usage:
    python -m aareguru_mcp
"""

from .server import entry_point

if __name__ == "__main__":
    entry_point()
