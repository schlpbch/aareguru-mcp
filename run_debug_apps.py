"""Runner file for the comprehensive debug page showing all 12 FastMCP apps.

Usage:
    uv run fastmcp dev run_debug_apps.py
    # or
    ./run-debug-all-apps.sh
"""

from debug_all_apps_comprehensive import debug_app

app = debug_app
