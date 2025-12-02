# Aareguru MCP Server

[![Tests](https://img.shields.io/badge/tests-135%20passing-brightgreen)](tests/)
[![Coverage](https://img.shields.io/badge/coverage-80%2B%25-green)](tests/)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](pyproject.toml)
[![MCP](https://img.shields.io/badge/MCP-1.0.0-purple)](https://modelcontextprotocol.io/)

MCP server for Swiss Aare river data, enabling AI assistants like Claude to answer questions about swimming conditions, water temperature, flow rates, and safety.

## 🎯 Features

- **7 MCP Tools** for querying Aare river data
- **4 MCP Resources** for direct data access
- **Swiss German Integration** - Authentic temperature descriptions
- **BAFU Safety Assessments** - Official flow danger levels
- **Historical Data Analysis** - Temperature and flow trends
- **Comprehensive Testing** - 135 tests, 80%+ coverage
- **Async HTTP Client** - With caching and rate limiting
- **Stdio Transport** - Ready for Claude Desktop integration

#### ✨ Smart Features (New!)
- **Proactive Safety Checks:** Automatically warns about dangerous flow rates (>300 m³/s).
- **Intelligent Suggestions:** Suggests warmer or safer locations if your choice is less than ideal.
- **Seasonal Context:** Provides advice tailored to the current season (Winter vs Summer).
- **Cultural Flair:** Explains Swiss German terms like "geil aber chli chalt".

## � Screenshots

<p align="center">
  <img src="claude-desktop-1.png" alt="Claude Desktop Integration Example 1" width="45%">
  <img src="claude-desktop-2.png" alt="Claude Desktop Integration Example 2" width="45%">
</p>

## �🛠️ Installation

### Installation

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone and install
git clone <repository-url> aareguru-mcp
cd aareguru-mcp
uv sync

# Run tests
uv run pytest
```

### Claude Desktop Setup

1. **Edit Claude Desktop config** (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/aareguru-mcp",
        "run",
        "aareguru-mcp"
      ]
    }
  }
}
```

2. **Restart Claude Desktop**

3. **Test it** - Ask Claude: "What's the Aare temperature in Bern?"

📖 **[Full Setup Guide](CLAUDE_DESKTOP_SETUP.md)** - Detailed configuration, troubleshooting, and examples

## 🛠️ Available Tools

### 1. `get_current_temperature`
Get current water temperature with Swiss German description.

**Parameters:**
- `city` (optional) - City name (default: "bern")

**Example queries:**
- "What's the Aare temperature in Bern?"
- "How cold is the water in Thun?"
- "Is the water warm enough to swim?"

**Response:**
```json
{
  "city": "bern",
  "name": "Bern",
  "longname": "Bern, Schönau",
  "temperature": 17.2,
  "temperature_prec": 0.1,
  "temperature_text": "geil aber chli chalt"
}
```

### 2. `get_current_conditions`
Get comprehensive current conditions (temperature, flow, weather, forecast).

**Parameters:**
- `city` (optional) - City name (default: "bern")

**Example queries:**
- "What are the current conditions in Bern?"
- "Give me a full swimming report for Basel"
- "How's the Aare looking today?"

**Response:** Full current data including temperature, flow, weather, and 2-hour forecast.

### 3. `get_flow_danger_level`
Get flow rate and BAFU safety assessment.

**Parameters:**
- `city` (optional) - City name (default: "bern")

**Example queries:**
- "Is it safe to swim in the Aare today?"
- "What's the current danger level?"
- "How strong is the current in Basel?"

**Response:**
```json
{
  "city": "bern",
  "flow": 85.3,
  "flow_threshold": 100,
  "safety_assessment": "SAFE - Flow is below 100 m³/s (BAFU threshold)",
  "danger_level": "low"
}
```

**BAFU Safety Thresholds:**
- **< 100 m³/s**: Safe for swimming
- **100-220 m³/s**: Moderate - Experienced swimmers only
- **220-300 m³/s**: Elevated - Caution advised
- **300-430 m³/s**: High - Dangerous
- **> 430 m³/s**: Very High - Extremely dangerous

### 4. `list_cities`
List all monitored cities with current data.

**Example queries:**
- "Which cities have Aare data?"
- "Show me all available locations"
- "Which city has the warmest water?"

**Response:** Array of cities with temperature, flow, and location data.

### 5. `get_historical_data`
Get historical temperature and flow data.

**Parameters:**
- `city` (required) - City name
- `start` (required) - Start date (e.g., "-7 days", "2024-01-01")
- `end` (required) - End date (e.g., "now", "2024-01-31")

**Example queries:**
- "Show me the last 7 days of data for Bern"
- "What was the average temperature last month?"

### 6. `compare_cities`
Compare water conditions across multiple cities.

**Parameters:**
- `cities` (optional) - List of cities to compare (default: all cities)

**Example queries:**
- "Which city has the warmest water?"
- "Compare Bern and Thun"
- "Where is the safest place to swim?"

**Response:** Comparison summary with warmest, coldest, and safest locations.

### 7. `get_forecast`
Get temperature and flow forecast.

**Parameters:**
- `city` (optional) - City name (default: "bern")
- `hours` (optional) - Forecast horizon in hours (default: 2)

**Example queries:**
- "Will the water be warmer in 2 hours?"
- "What's the forecast for this afternoon?"
- "Is the temperature rising or falling?"

**Response:** Current conditions, 2-hour forecast, trend analysis (rising/falling/stable), and recommendations.

## 📊 Available Resources

MCP resources provide direct data access:

- **`aareguru://cities`** - List of all monitored cities
- **`aareguru://current/{city}`** - Full current data for a city
- **`aareguru://today/{city}`** - Minimal current data for a city
- **`aareguru://widget`** - Overview of all cities

## 💬 Usage Examples

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

Claude: Temperature trend for the last 7 days in Bern:
- Average: 16.8°C
- Highest: 18.5°C (3 days ago)
- Lowest: 15.2°C (yesterday)
- Current: 17.2°C

The water has warmed up slightly over the past week.
```

### Multi-City Comparison
```
User: Which city has the warmest water right now?

Claude: Current temperatures across all monitored cities:
1. Basel: 18.9°C (warmest)
2. Bern: 17.2°C
3. Thun: 16.5°C
4. Interlaken: 15.8°C

Basel has the warmest water today!
```

## 🧪 Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=aareguru_mcp

# Run specific test categories
uv run pytest -m integration  # Integration tests
uv run pytest -m e2e          # E2E conversation tests

# Run with verbose output
uv run pytest -v
```

### Test Coverage

- **135 tests** across 10 test files
- **80%+ overall coverage**
- Unit tests (67 tests) - Client, Config, Models, Tools, Resources
- Integration tests (48 tests) - Advanced Tools, Complex Flows, E2E Conversations
- E2E conversation tests covering all 13 question categories

### Code Quality

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

### API Testing

A Postman collection is included for testing the Aareguru API directly:
- Import `aareguru_postman_collection.json` into Postman
- Test all core endpoints (cities, today, current, widget, history)

## 📁 Project Structure

```
aareguru-mcp/
├── src/aareguru_mcp/
│   ├── server.py          # MCP server (stdio)
│   ├── client.py          # Aareguru API client
│   ├── models.py          # Pydantic models
│   ├── resources.py       # MCP resources
│   ├── tools.py           # MCP tools
│   └── config.py          # Configuration
├── tests/
│   ├── test_client.py     # Client tests
│   ├── test_models.py     # Model tests
│   ├── test_tools.py      # Tool tests
│   ├── test_resources.py  # Resource tests
│   ├── test_tool_integration.py  # Integration tests
│   └── test_e2e_conversations.py # E2E tests
├── CLAUDE_DESKTOP_SETUP.md  # Setup guide
├── MASTER_PLAN.md           # Implementation roadmap
└── pyproject.toml           # Project configuration
```

## 🎯 Project Status

✅ **Phase 1 Complete** - Core MVP (stdio)

**Completed:**
- ✅ **Week 1**: Foundation - Project structure, Pydantic models, Async API client
- ✅ **Week 2**: MCP Protocol - 7 Tools & 4 Resources implemented
- ✅ **Week 3**: Testing & Documentation - 135 tests, 80%+ coverage
- ✅ **Advanced Features**: `compare_cities`, `get_forecast`, Swiss German integration
- ✅ **Smart UX**: Proactive safety checks, alternative suggestions, seasonal context
- ✅ **Quality Assurance**: All 135 tests passing, comprehensive coverage
- ✅ **Documentation**: Complete guides covering 130+ user questions
- ✅ **Production Ready**: Fully functional stdio MCP server for Claude Desktop

🔄 **Phase 2 In Progress** - Enhanced Features
- ✅ **Week 4**: Advanced Tools complete
- 🔄 **Week 5**: User Experience enhancements in progress

**Next Steps (Phase 3 - HTTP Deployment):**
- [ ] HTTP/SSE server implementation (Starlette/FastAPI)
- [ ] API key authentication & Rate limiting
- [ ] Docker containerization
- [ ] Cloud deployment preparation

See [MASTER_PLAN.md](MASTER_PLAN.md) for the complete roadmap.

## 🌍 Monitored Cities

The Aareguru API monitors these cities along the Aare river:

- **Bern** (Schönau)
- **Thun**
- **Basel**
- **Interlaken**
- **Brugg**
- And more...

Use the `list_cities` tool to get the complete list with current data.

## 📚 Documentation

- **[CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md)** - Complete setup guide
- **[MASTER_PLAN.md](MASTER_PLAN.md)** - Implementation roadmap
- **[AAREGURU_API_ANALYSIS.md](AAREGURU_API_ANALYSIS.md)** - API documentation
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Technical architecture
- **[TESTING_PLAN.md](TESTING_PLAN.md)** - QA strategy
- **[USER_QUESTIONS_SLIDES.md](USER_QUESTIONS_SLIDES.md)** - 130 user questions catalog

## 🔒 Data Sources & Attribution

Data provided by:
- **[BAFU](https://www.hydrodaten.admin.ch)** - Swiss Federal Office for the Environment
- **[Aare.guru](https://aare.guru)** - Aare.guru GmbH
- **MeteoSchweiz** - Swiss weather service
- **Meteotest** - Weather forecasts

> [!IMPORTANT]
> **Non-commercial use only**
> - Please notify: aaregurus@existenz.ch
> - Link to: https://aare.guru
> - Link to: https://www.hydrodaten.admin.ch

## 📄 License

MIT License - See [LICENSE](LICENSE) file

MCP server code is MIT licensed. Data sources have their own licenses (non-commercial use).

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Ensure all tests pass
5. Submit a pull request

## 💡 Support

For issues or questions:
- Check [CLAUDE_DESKTOP_SETUP.md](CLAUDE_DESKTOP_SETUP.md) troubleshooting section
- Review test output: `uv run pytest -v`
- Contact: aaregurus@existenz.ch

## 🏊‍♂️ Enjoy!

Stay safe and enjoy swimming in the Aare! Always check current conditions and flow rates before entering the water.

---

**Built with ❤️ for the Swiss Aare swimming community**
