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
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
uv run fastmcp run run_debug_apps.py:app --port 8888 "$@"
