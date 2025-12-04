# Aareguru MCP Server - Project Proposal

## Overview

This document proposes a Python-based MCP (Model Context Protocol) server that exposes the Aareguru API as resources and tools for AI assistants.

---

## Technology Stack

### Core Dependencies

| Package | Version | Purpose |
|---------|---------|----------|
| **fastmcp** | `^2.0.0` | High-level MCP framework with decorators |
| **httpx** | `^0.27.0` | Modern async HTTP client for API calls |
| **pydantic** | `^2.0.0` | Data validation and settings management |
| **python-dotenv** | `^1.0.0` | Environment variable management |
| **structlog** | `^24.0.0` | Structured JSON logging |

### Development Dependencies

| Package | Purpose |
|---------|---------|
| **pytest** | Unit testing |
| **pytest-asyncio** | Async test support |
| **pytest-cov** | Code coverage |
| **black** | Code formatting |
| **ruff** | Fast linting |
| **mypy** | Type checking |

### Python Version
- **Minimum**: Python 3.10
- **Recommended**: Python 3.11+

---

## Project Structure

```
aareguru-mcp/
├── src/
│   └── aareguru_mcp/
│       ├── __init__.py
│       ├── server.py              # Main MCP server implementation
│       ├── client.py              # Aareguru API client wrapper
│       ├── models.py              # Pydantic models for API responses
│       ├── resources.py           # MCP resource handlers
│       ├── tools.py               # MCP tool implementations
│       └── config.py              # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_resources.py
│   ├── test_tools.py
│   └── fixtures/
│       └── sample_responses.json  # Mock API responses
├── .env.example                   # Example environment variables
├── .gitignore
├── pyproject.toml                 # Project metadata & dependencies
├── README.md
├── LICENSE
└── uv.lock                        # Lock file (if using uv)
```

---

## MCP Server Design

### Resources

Resources provide read-only access to Aareguru data:

| Resource URI | Description | Data Source |
|--------------|-------------|-------------|
| `aareguru://cities` | List of all available cities | `/v2018/cities` |
| `aareguru://current/{city}` | Current data for a city | `/v2018/current` |
| `aareguru://today/{city}` | Minimal current data | `/v2018/today` |
| `aareguru://widget` | All cities overview | `/v2018/widget` |

**Example Resource Response**:
```json
{
  "uri": "aareguru://current/bern",
  "mimeType": "application/json",
  "text": "{...full API response...}"
}
```

---

### Tools

Tools allow AI assistants to query the API dynamically. These 7 tools cover 95%+ of user needs based on the Claude Desktop integration analysis.

#### 1. `get_current_temperature`
**Description**: Get current water temperature for a city

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier (e.g., 'bern', 'thun', 'basel')",
    "default": "bern"
  }
}
```

**Returns**: 
- `temperature` (float): Water temperature in °C
- `temperature_text` (string): Swiss German description
- `temperature_text_short` (string): Short description

**Example User Questions**:
- "What's the Aare temperature in Bern?"
- "How cold is the water?"
- "Is it warm enough to swim?"

---

#### 2. `get_current_conditions`
**Description**: Get complete current conditions including water, weather, and safety data

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "default": "bern"
  }
}
```

**Returns**:
- Water temperature and flow data
- Weather conditions (air temp, precipitation, wind)
- Danger level assessment
- Forecasts (2-hour and daily)

**Example User Questions**:
- "What are the current Aare conditions?"
- "Is it safe to swim today?"
- "Give me a full swimming report"

---

#### 3. `get_historical_data`
**Description**: Retrieve historical time-series data for trend analysis

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "required": true
  },
  "start": {
    "type": "string",
    "description": "Start date/time (ISO, timestamp, or relative like '-7 days')",
    "required": true
  },
  "end": {
    "type": "string",
    "description": "End date/time (ISO, timestamp, or 'now')",
    "required": true
  }
}
```

**Returns**: Time-series arrays of temperature, flow, and weather data

**Example User Questions**:
- "How has the temperature changed this week?"
- "Show me the last 30 days of data"
- "What was the temperature last weekend?"

---

#### 4. `list_cities`
**Description**: Get all available cities with metadata

**Input Schema**: None (no parameters)

**Returns**: Array of city objects with:
- `city` (string): City identifier
- `name` (string): Display name
- `longname` (string): Full name
- `url` (string): City-specific URL

**Example User Questions**:
- "Which cities have Aare data?"
- "List all swimming spots"
- "Where can I check temperatures?"

---

#### 5. `get_flow_danger_level`
**Description**: Get current flow rate and BAFU danger assessment

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "default": "bern"
  }
}
```

**Returns**:
- `flow` (float): Flow rate in m³/s
- `flow_gefahrenstufe` (int): BAFU danger level (1-5)
- `flow_text` (string): Human-readable description
- Safety assessment and recommendations

**Example User Questions**:
- "Is the Aare flow dangerous?"
- "What's the current danger level?"
- "How fast is the water flowing?"

---

#### 6. `compare_cities`
**Description**: Compare conditions across multiple cities

**Input Schema**:
```json
{
  "cities": {
    "type": "array",
    "items": {"type": "string"},
    "description": "List of city identifiers to compare",
    "minItems": 2
  }
}
```

**Returns**: Comparison table with temperature, flow, weather, and safety for each city

**Example User Questions**:
- "Compare Bern and Thun temperatures"
- "Which city has the warmest water?"
- "Where's the best place to swim today?"

---

#### 7. `get_forecast`
**Description**: Get weather and temperature forecasts

**Input Schema**:
```json
{
  "city": {
    "type": "string",
    "description": "City identifier",
    "default": "bern"
  },
  "hours": {
    "type": "integer",
    "description": "Number of hours ahead (2-48)",
    "default": 24
  }
}
```

**Returns**: Forecasted temperatures, weather conditions, and optimal swimming times

**Example User Questions**:
- "Will the water be warmer tomorrow?"
- "What's the forecast for this weekend?"
- "Should I wait until later to swim?"

---

## User Experience Design

### Response Formatting Guidelines

To provide the best experience in Claude Desktop, tools should return well-formatted, contextual responses:

#### Temperature Responses
```markdown
🌡️ **Aare Temperature in Bern**
- Current: 17.2°C
- Description: "geil aber chli chalt" (awesome but a bit cold)
- Status: Good for swimming! 🏊

💧 Water feels refreshing but comfortable for most swimmers.
```

#### Safety Assessments
```markdown
⚠️ **Safety Assessment for Bern**
- Flow Rate: 245 m³/s
- Danger Level: 2/5 (Moderate)
- Recommendation: Safe for experienced swimmers, use caution

🏊 Conditions are generally safe, but be aware of the current.
```

#### City Comparisons
```markdown
📊 **City Comparison**

| City | Temp | Flow | Safety |
|------|------|------|--------|
| Bern | 17.2°C | 245 m³/s | ⚠️ Moderate |
| Thun | 18.1°C | 180 m³/s | ✅ Safe |
| Basel | 16.8°C | 310 m³/s | ⚠️ Caution |

🏆 **Recommendation**: Thun has the warmest water and safest conditions today!
```

### Conversation Patterns

Claude can naturally handle these query types:

**Direct Questions**:
- "What's the temperature?"
- "Is it safe?"
- "Show me Bern"

**Conversational**:
- "I'm thinking about swimming, what do you think?"
- "How's the Aare looking?"
- "Should I go now or wait?"

**Complex Multi-Part**:
- "Compare Bern and Thun, then tell me which is safer for kids"
- "Show me the last week's data and predict tomorrow"
- "Find the warmest spot with low flow"

**Implicit Context**:
- "What about Thun?" (after discussing Bern)
- "And the flow?" (after temperature query)
- "How does that compare?" (after showing data)

### Proactive Intelligence

The MCP server should enable Claude to:

1. **Automatic Safety Checks**: When asked about swimming, automatically include flow/danger assessment
2. **Alternative Suggestions**: If conditions are poor, suggest nearby cities with better conditions
3. **Forecast Integration**: If current conditions aren't ideal, proactively check forecast
4. **Cultural Context**: Explain Swiss German temperature descriptions automatically
5. **Seasonal Intelligence**: Adjust "warm enough" thresholds by season with historical context

### Swiss German Integration

Preserve and explain Swiss German terms from the API:
- "geil aber chli chalt" → "awesome but a bit cold"
- "schön warm" → "nicely warm"
- "usschwümme" → "swim out/float down"

These add cultural authenticity and should be included in responses with translations.

---

## Implementation Details

### 1. API Client (`client.py`)

```python
class AareguruClient:
    """Async HTTP client for Aareguru API"""
    
    def __init__(self, base_url: str, app_name: str, app_version: str):
        self.base_url = base_url
        self.app_name = app_name
        self.app_version = app_version
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def get_cities(self) -> dict
    async def get_today(self, city: str = "bern") -> dict
    async def get_current(self, city: str = "bern") -> dict
    async def get_widget(self) -> dict
    async def get_history(self, city: str, start: str, end: str) -> dict
```

**Features**:
- Automatic retry logic with exponential backoff
- Caching with TTL (respecting API's 2-minute cache)
- Proper error handling and logging
- Rate limiting (respect 5-minute recommendation)

---

### 2. Data Models (`models.py`)

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class AareData(BaseModel):
    temperature: Optional[float]
    temperature_text: Optional[str]
    flow: Optional[float]
    flow_text: Optional[str]
    flow_gefahrenstufe: Optional[int]

class WeatherData(BaseModel):
    tt: Optional[float]  # Air temperature
    sy: Optional[int]    # Weather symbol
    rr: Optional[float]  # Precipitation

class CityInfo(BaseModel):
    city: str
    name: str
    longname: str
    url: str

class CurrentResponse(BaseModel):
    city: str
    aare: AareData
    weather: Optional[WeatherData]
    # ... other fields
```

**Benefits**:
- Type safety and validation
- Auto-generated JSON schemas
- Easy serialization/deserialization
- IDE autocomplete support

---

### 3. MCP Server (`server.py`)

```python
from fastmcp import FastMCP

mcp = FastMCP(
    name="aareguru-mcp",
    instructions="""You are an assistant that helps users with Swiss Aare river conditions."""
)

@mcp.resource("aareguru://cities")
async def get_cities() -> str:
    """List all available cities with Aare data."""
    # Return formatted city data

@mcp.tool()
async def get_current_temperature(city: str = "bern") -> str:
    """Get current water temperature for a city."""
    # Fetch and return temperature

@mcp.tool()
async def get_current_conditions(city: str = "bern") -> str:
    """Get complete current conditions including water, weather, and safety data."""
    # Fetch and return conditions
```

---

### 4. Configuration (`config.py`)

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    aareguru_base_url: str = "https://aareguru.existenz.ch"
    app_name: str = "aareguru-mcp"
    app_version: str = "1.0.0"
    
    # Cache Configuration
    cache_ttl_seconds: int = 120  # 2 minutes
    
    # Rate Limiting
    min_request_interval_seconds: int = 300  # 5 minutes
    
    class Config:
        env_file = ".env"
```

---

## Package Management

### Option 1: UV (Recommended)

**Why UV?**
- ⚡ Extremely fast (10-100x faster than pip)
- 🔒 Built-in lock file support
- 📦 Handles virtual environments automatically
- 🎯 Modern Python tooling

**Setup**:
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Initialize project
uv init aareguru-mcp
cd aareguru-mcp

# Add dependencies
uv add mcp httpx pydantic python-dotenv
uv add --dev pytest pytest-asyncio pytest-cov black ruff mypy

# Run server
uv run python -m aareguru_mcp.server
```

## pyproject.toml (UV/Poetry)

```toml
[project]
name = "aareguru-mcp"
version = "1.0.0"
description = "MCP server for Aareguru API - Swiss Aare river data"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.10"
license = {text = "MIT"}

dependencies = [
    "mcp>=1.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "ruff>=0.3.0",
    "mypy>=1.8.0",
]

[project.scripts]
aareguru-mcp = "aareguru_mcp.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.black]
line-length = 100
target-version = ["py310", "py311"]

[tool.ruff]
line-length = 100
target-version = "py310"

[tool.mypy]
python_version = "3.10"
strict = true
```

---

## Development Workflow

### 1. Setup
```bash
# Clone/create project
git clone <repo> aareguru-mcp
cd aareguru-mcp

# Install dependencies (using uv)
uv sync

# Copy environment template
cp .env.example .env
```

### 2. Development
```bash
# Run tests
uv run pytest

# Format code
uv run black src/ tests/

# Lint
uv run ruff check src/ tests/

# Type check
uv run mypy src/
```

### 3. Run Server
```bash
# Development mode
uv run python -m aareguru_mcp.server

# Or using the script
uv run aareguru-mcp
```

---

## Testing Strategy

### Unit Tests
- Mock API responses using `pytest` fixtures
- Test each tool independently
- Validate Pydantic models with edge cases

### Integration Tests
- Test against real API (with rate limiting)
- Validate MCP protocol compliance
- Test resource URIs and tool calls

### Coverage Target
- Minimum: 80%
- Goal: 90%+

---

## Deployment Options

### 1. Local MCP Server
Run as a local process, configured in Claude Desktop or other MCP clients

### 2. Docker Container
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install uv && uv sync
CMD ["uv", "run", "aareguru-mcp"]
```

### 3. Systemd Service (Linux)
For always-on local deployment

---

## Configuration Example

**.env.example**:
```bash
# Aareguru API Configuration
AAREGURU_BASE_URL=https://aareguru.existenz.ch
APP_NAME=aareguru-mcp
APP_VERSION=1.0.0

# Cache & Rate Limiting
CACHE_TTL_SECONDS=120
MIN_REQUEST_INTERVAL_SECONDS=300

# Logging
LOG_LEVEL=INFO
```

---

## MCP Client Configuration

**Claude Desktop** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "aareguru": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/aareguru-mcp",
        "run",
        "aareguru-mcp"
      ]
    }
  }
}
```

---

## Recommended: UV

**I recommend using UV** for this project because:

1. ✅ **Speed**: 10-100x faster than pip/poetry
2. ✅ **Simplicity**: Single tool for everything (venv, deps, scripts)
3. ✅ **Modern**: Built with Rust, actively developed by Astral (creators of Ruff)
4. ✅ **Lock files**: Built-in deterministic builds
5. ✅ **No config overhead**: Works with standard `pyproject.toml`

---

## Next Steps

### Phase 1: Core Implementation (MVP)
1. **Initialize project structure** with chosen package manager
2. **Implement API client** with caching and error handling
3. **Define Pydantic models** for type safety
4. **Create MCP resources** for static data access (4 resources)
5. **Implement core MCP tools** (tools 1-5):
   - `get_current_temperature`
   - `get_current_conditions`
   - `get_historical_data`
   - `list_cities`
   - `get_flow_danger_level`
6. **Write tests** with good coverage (80%+)
7. **Document usage** in README

### Phase 2: Enhanced Features
8. **Implement advanced tools** (tools 6-7):
   - `compare_cities`
   - `get_forecast`
9. **Add response formatting** with emojis and markdown
10. **Implement Swiss German translations** in responses
11. **Add proactive safety checks** and recommendations
12. **Enhance test coverage** to 90%+

### Phase 3: Deployment & Validation
13. **Test with MCP client** (Claude Desktop)
14. **Validate conversation patterns** with real queries
15. **Performance optimization** (caching, rate limiting)
16. **Create comprehensive documentation** and examples
17. **Deploy and monitor** in production

---

## Success Metrics

A successful implementation should enable Claude to:

1. ✅ Answer 95%+ of temperature queries in one tool call
2. ✅ Provide automatic safety assessments without user prompting
3. ✅ Handle multi-city comparisons naturally
4. ✅ Explain Swiss German terms automatically
5. ✅ Suggest optimal swimming times based on forecasts
6. ✅ Understand implicit context and follow-up questions
7. ✅ Provide rich, formatted responses with emojis and tables
8. ✅ Handle missing data gracefully with alternatives

---

## Example Tool Usage (AI Assistant Perspective)

```
User: "What's the current Aare temperature in Bern?"

Assistant uses tool: get_current_temperature(city="bern")

Response: {
  "temperature": 17.2,
  "temperature_text": "geil aber chli chalt",
  "temperature_text_short": "chli chalt"
}
```
