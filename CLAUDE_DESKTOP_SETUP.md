# Claude Desktop Setup Guide

Complete guide for integrating the Aareguru MCP server with Claude Desktop.

## Quick Start: FastMCP Cloud (Recommended)

The easiest way to use Aareguru with Claude Desktop is via the **FastMCP Cloud** deployment - no local installation required!

### Configuration

Add this to your `claude_desktop_config.json`:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`  
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "https://aareguru.fastmcp.app/sse"]
    }
  }
}
```

That's it! Restart Claude Desktop and start asking about Aare river conditions.

> **Note:** Requires Node.js/npm installed. The `mcp-remote` package bridges Claude Desktop to the remote MCP server.

---

## Local Installation (Alternative)

If you prefer to run the server locally, follow the steps below.

## Prerequisites

- **Claude Desktop** installed ([Download here](https://claude.ai/download))
- **Python 3.10+** installed
- **uv** package manager ([Installation guide](https://docs.astral.sh/uv/))

## Installation

### 1. Clone and Install the MCP Server

```bash
# Clone the repository
git clone <repository-url> aareguru-mcp
cd aareguru-mcp

# Install dependencies with uv
uv sync

# Verify installation
uv run pytest
```

### 2. Configure Claude Desktop

Claude Desktop uses a JSON configuration file to register MCP servers.

#### Configuration File Location

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

**Linux:**
```
~/.config/Claude/claude_desktop_config.json
```

#### Configuration Content

Add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "uv",
      "args": [
        "--directory",
        "C:\\Users\\YourUsername\\path\\to\\aareguru-mcp",
        "run",
        "aareguru-mcp"
      ]
    }
  }
}
```

> [!IMPORTANT]
> Replace `C:\\Users\\YourUsername\\path\\to\\aareguru-mcp` with the **absolute path** to your aareguru-mcp directory.
> On Windows, use double backslashes (`\\`) in the path.

#### macOS/Linux Example

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "uv",
      "args": [
        "--directory",
        "/Users/yourname/code/aareguru-mcp",
        "run",
        "aareguru-mcp"
      ]
    }
  }
}
```

### 3. Restart Claude Desktop

After saving the configuration file:

1. **Quit Claude Desktop completely** (not just close the window)
2. **Restart Claude Desktop**
3. The MCP server should now be available

## Verification

### Check MCP Server Status

In Claude Desktop, you should see an MCP indicator (usually a small icon or status message) showing that the Aareguru server is connected.

### Test with a Simple Query

Try asking Claude:

```
What's the current temperature of the Aare in Bern?
```

Claude should use the `get_current_temperature` tool and return:
- Current water temperature
- Swiss German description (e.g., "geil aber chli chalt")
- Location name

## Available Tools

The Aareguru MCP server provides 5 tools:

### 1. `get_current_temperature`
Get current water temperature with Swiss German description.

**Example queries:**
- "What's the Aare temperature in Bern?"
- "How cold is the water in Thun?"
- "Is the water warm enough to swim in Basel?"

### 2. `get_current_conditions`
Get comprehensive current conditions (temperature, flow, weather, forecast).

**Example queries:**
- "What are the current conditions in Bern?"
- "Give me a full swimming report for Basel"
- "How's the Aare looking today?"

### 3. `get_flow_danger_level`
Get flow rate and BAFU safety assessment.

**Example queries:**
- "Is it safe to swim in the Aare today?"
- "What's the current danger level in Bern?"
- "How strong is the current in Basel?"

### 4. `list_cities`
List all monitored cities with current data.

**Example queries:**
- "Which cities have Aare data?"
- "Show me all available locations"
- "Which city has the warmest water?"

### 5. `get_historical_data`
Get historical temperature and flow data.

**Example queries:**
- "How has the temperature changed this week?"
- "Show me the last 7 days of data for Bern"
- "What was the average temperature last month?"

## Available Resources

The server also provides 4 MCP resources for direct data access:

- `aareguru://cities` - List of all cities
- `aareguru://current/{city}` - Full current data for a city
- `aareguru://today/{city}` - Minimal current data for a city
- `aareguru://widget` - Overview of all cities

## Troubleshooting

### Server Not Connecting

**Symptom:** Claude Desktop doesn't show the Aareguru MCP server

**Solutions:**
1. **Check the configuration file path** - Make sure you're editing the correct file
2. **Verify JSON syntax** - Use a JSON validator to check for syntax errors
3. **Check absolute path** - Ensure the path to aareguru-mcp is correct and absolute
4. **Restart Claude Desktop** - Completely quit and restart the application
5. **Check logs** - Look for error messages in Claude Desktop's developer console

### Path Issues on Windows

**Symptom:** Error about invalid path or command not found

**Solutions:**
- Use double backslashes: `C:\\Users\\...`
- Or use forward slashes: `C:/Users/...`
- Ensure no trailing slashes
- Verify the path exists

### uv Command Not Found

**Symptom:** Error that `uv` command is not recognized

**Solutions:**
1. Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Add uv to PATH
3. Restart your terminal/Claude Desktop
4. Verify with: `uv --version`

### Python Version Issues

**Symptom:** Error about Python version compatibility

**Solutions:**
- Ensure Python 3.10+ is installed: `python --version`
- Update Python if needed
- Verify uv is using the correct Python version

### Tests Failing

**Symptom:** `uv run pytest` shows test failures

**Solutions:**
1. Check internet connection (tests hit real API)
2. Verify dependencies: `uv sync`
3. Check for API rate limiting (wait 5 minutes)
4. Review test output for specific errors

### Slow Responses

**Symptom:** Claude takes a long time to respond

**Possible causes:**
- First request to API (no cache)
- Network latency
- API rate limiting

**Solutions:**
- Subsequent requests should be faster (cached)
- Check internet connection
- Wait a few minutes if rate limited

### Invalid City Names

**Symptom:** Error when asking about a city

**Solutions:**
- Use `list_cities` tool to see available cities
- Common cities: bern, thun, basel, interlaken, brugg
- City names are lowercase
- Not all Swiss cities are monitored (only those on the Aare river)

## Advanced Configuration

### Environment Variables

Create a `.env` file in the aareguru-mcp directory:

```env
# Optional: Override base URL
AAREGURU_BASE_URL=https://aareguru.existenz.ch

# Optional: Adjust cache TTL (seconds)
CACHE_TTL_SECONDS=300

# Optional: Minimum request interval (seconds)
MIN_REQUEST_INTERVAL_SECONDS=5

# Optional: Log level
LOG_LEVEL=INFO
```

### Custom Settings

You can customize the server behavior by editing `src/aareguru_mcp/config.py` or using environment variables.

## Usage Examples

### Basic Temperature Check
```
User: What's the water temperature in Bern?

Claude: The current water temperature in Bern (Schönau) is 17.2°C. 
In Swiss German: "geil aber chli chalt" (awesome but a bit cold).
```

### Safety Assessment
```
User: Is it safe to swim in the Aare today?

Claude: Based on current conditions in Bern:
- Flow: 85 m³/s
- Safety: SAFE - Flow is below 100 m³/s (BAFU threshold)
- Temperature: 17.2°C

Swimming is safe for experienced swimmers. Always be cautious of currents.
```

### Historical Analysis
```
User: How has the temperature changed this week in Bern?

Claude: [Uses get_historical_data tool]
Temperature trend for the last 7 days in Bern:
- Average: 16.8°C
- Highest: 18.5°C (3 days ago)
- Lowest: 15.2°C (yesterday)
- Current: 17.2°C

The water has warmed up slightly over the past week.
```

### Multi-City Comparison
```
User: Which city has the warmest water right now?

Claude: [Uses list_cities tool]
Current temperatures across all monitored cities:
1. Basel: 18.9°C (warmest)
2. Bern: 17.2°C
3. Thun: 16.5°C
4. Interlaken: 15.8°C

Basel has the warmest water today!
```

## Best Practices

1. **Be specific with city names** - Use lowercase city names (bern, basel, thun)
2. **Ask natural questions** - Claude will select the appropriate tool
3. **Request comprehensive data** - Ask for "full report" or "all conditions"
4. **Use Swiss German** - The server provides authentic Swiss German descriptions
5. **Check safety first** - Always ask about flow/danger levels before swimming

## Data Sources

The Aareguru MCP server uses data from:
- **BAFU** - Swiss Federal Office for the Environment (flow data)
- **MeteoSchweiz** - Swiss weather service
- **Meteotest** - Weather forecasts
- **TemperAare** - Community temperature data

## License & Attribution

> [!IMPORTANT]
> **Non-commercial use only**
> - Data provided by [Aare.guru](https://aare.guru)
> - Please notify: aaregurus@existenz.ch
> - Link to: https://www.hydrodaten.admin.ch

## Support

For issues or questions:
1. Check this troubleshooting guide
2. Review test output: `uv run pytest -v`
3. Check Claude Desktop logs
4. Contact: aaregurus@existenz.ch

## Next Steps

Once configured, try:
1. Ask about current conditions in different cities
2. Request historical data analysis
3. Compare temperatures across cities
4. Get safety assessments for swimming
5. Explore Swiss German temperature descriptions

Enjoy your Aare swimming adventures! 🏊‍♂️🌊
