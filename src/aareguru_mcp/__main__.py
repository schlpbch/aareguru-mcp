"""Entry point for running Aareguru MCP server as a module.

Usage:
    python -m aareguru_mcp
"""

import asyncio

from .server import main

if __name__ == "__main__":
    asyncio.run(main())
