# Debug All Apps - Visual Testing Page

This directory contains files for rendering all 12 FastMCP apps on a single page
for comprehensive visual debugging.

## Files Created

1. **`debug_all_apps_comprehensive.py`** - Main debug app implementation
   - Renders all 12 apps in organized sections
   - Includes headers, descriptions, and borders for each app
   - Uses the Aare.guru color scheme and design system

2. **`run_debug_apps.py`** - Runner file that exports the debug_app
   - Simple loader for the FastMCP dev server

3. **`run-debug-all-apps.sh`** - Convenience script to start the debug server
   - Pre-configured with non-conflicting ports (3001 for UI, 8888 for MCP)
   - Executable and ready to use

## Usage

### Quick Start

```bash
# Run the debug server
./run-debug-all-apps.sh
```

Then visit: http://localhost:3001

### Custom Ports

If the default ports are in use:

```bash
./run-debug-all-apps.sh --dev-port 3000 --mcp-port 1337
```

### Manual Run

```bash
uv run fastmcp dev apps run_debug_apps.py --dev-port 3001 --mcp-port 8888
```

## What's Included

The debug page shows all 12 apps organized into 7 sections:

### Section 1: Complete Dashboard

- Main conditions app with all 4 sections combined

### Section 2: Individual Condition Cards

- 2a. Temperature Card
- 2b. Flow & Safety Card
- 2c. Weather Card
- 2d. Sun/Sunset Card

### Section 3: Time-Series Data

- 3a. Historical Chart (7-day trends)
- 3b. Intraday Sparkline (today's data)

### Section 4: Weather Forecast

- 24-hour air temperature forecast

### Section 5: Multi-City Comparison & Ranking

- 5a. Compare Cities Table (sortable, searchable)
- 5b. City Finder (ranked by temperature)

### Section 6: Safety Assessment

- BAFU danger level briefing

### Section 7: Interactive Map

- Leaflet.js map with all monitoring stations

## Benefits

✅ **Visual Regression Testing** - Quickly spot layout issues across all apps ✅
**Design System Verification** - Ensure consistent styling and colors ✅ **Quick
Overview** - See all UI components in one place ✅ **Debugging** - Test
interactions and data loading for all apps simultaneously ✅ **Documentation** -
Visual reference for all available apps

## Architecture

The debug page follows the same pattern as other FastMCP apps:

```python
# Create FastMCPApp instance
debug_app = FastMCPApp("debug-all-apps")

# Define UI with @debug_app.ui() decorator
@debug_app.ui()
async def all_apps_debug_view(city: str = "Bern") -> PrefabApp:
    # Import and render all 12 apps
    # ...
```

The runner file (`run_debug_apps.py`) simply imports and exports the app for
FastMCP dev server to discover.

## Customization

You can modify `debug_all_apps_comprehensive.py` to:

- Change default city parameter
- Adjust grid layouts
- Add/remove apps from the display
- Modify styling and borders
- Change historical data date ranges

## Testing

The debug page uses the same service layer as production apps, so it fetches
real data from the Aareguru API. This makes it perfect for end-to-end testing.

## Notes

- Default city is "Bern" but can be changed via UI parameters
- All apps use live data (not mocked)
- Respects rate limiting and caching like production
- Uses the same design constants from `apps/_constants.py`
