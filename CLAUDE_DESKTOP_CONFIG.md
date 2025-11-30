# Claude Desktop Configuration

To use the Aareguru MCP server with Claude Desktop, add this configuration to your `claude_desktop_config.json` file.

## Configuration File Location

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`  
**Linux**: `~/.config/Claude/claude_desktop_config.json`

## Configuration

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "python3",
      "args": [
        "-m",
        "aareguru_mcp"
      ],
      "cwd": "/absolute/path/to/aareguru-mcp",
      "env": {
        "PYTHONPATH": "/absolute/path/to/aareguru-mcp/src"
      }
    }
  }
}
```

## Setup Steps

1. **Install dependencies** (when pip is available):
   ```bash
   cd /path/to/aareguru-mcp
   pip install -e .
   ```

2. **Update the configuration**:
   - Replace `/absolute/path/to/aareguru-mcp` with your actual project path
   - Ensure Python 3.10+ is installed

3. **Restart Claude Desktop**

4. **Test the connection**:
   - Ask Claude: "What's the Aare temperature in Bern?"
   - Claude should use the `get_current_temperature` tool

## Available Tools

Once configured, Claude can use these tools:

1. **get_current_temperature** - Get water temperature for a city
2. **get_current_conditions** - Get complete conditions (water, weather, safety)
3. **get_historical_data** - Get time-series data for analysis
4. **list_cities** - Get all available cities
5. **get_flow_danger_level** - Get flow rate and safety assessment

## Available Resources

Claude can also read these resources proactively:

- `aareguru://cities` - List of all cities
- `aareguru://widget` - All cities overview
- `aareguru://current/{city}` - Current conditions for a city
- `aareguru://today/{city}` - Minimal data for a city

## Example Questions

Try asking Claude:
- "What's the Aare temperature in Bern?"
- "Is it safe to swim in the Aare today?"
- "Compare the water temperature in Bern and Thun"
- "Show me the last week's temperature data for Bern"
- "Which cities have Aare data available?"

## Troubleshooting

### Server not starting
- Check that Python 3.10+ is installed: `python3 --version`
- Verify the path in the configuration is correct
- Check Claude Desktop logs for errors

### Tools not appearing
- Restart Claude Desktop after configuration changes
- Verify the `cwd` and `PYTHONPATH` are correct
- Ensure dependencies are installed

### Import errors
- Make sure `PYTHONPATH` includes the `src` directory
- Install dependencies: `pip install mcp httpx pydantic pydantic-settings python-dotenv`

## Development Mode

For development with auto-reload:

```json
{
  "mcpServers": {
    "aareguru-dev": {
      "command": "python3",
      "args": ["-m", "aareguru_mcp"],
      "cwd": "/path/to/aareguru-mcp",
      "env": {
        "PYTHONPATH": "/path/to/aareguru-mcp/src",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Next Steps

- See [README.md](README.md) for project overview
- See [MASTER_PLAN.md](MASTER_PLAN.md) for implementation roadmap
- See [USER_QUESTIONS_SLIDES.md](USER_QUESTIONS_SLIDES.md) for 130 example questions
