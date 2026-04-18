#!/bin/bash
# Run the comprehensive debug page showing all 12 FastMCP apps
set -e
cd "$(dirname "$0")"
echo "🔍 Starting comprehensive debug page with all 12 FastMCP apps..."
echo ""
echo "Default ports:"
echo "  - Web UI: http://localhost:3001"
echo "  - MCP Server: http://localhost:8888"
echo ""
echo "To use different ports: ./run-debug-all-apps.sh --dev-port 3000 --mcp-port 1337"
echo ""
uv run fastmcp dev apps dev_server.py:mcp --dev-port 3001 --mcp-port 8888 "$@"
