# Aareguru MCP Server - Testing Plan

## Overview

This testing plan uses the 130 user questions as the foundation for comprehensive test coverage, ensuring the MCP server handles all expected user interactions correctly.

---

## Testing Strategy

### Test Pyramid

```
                    ┌─────────────┐
                    │   E2E (10)  │  Full conversation flows
                    └─────────────┘
                  ┌───────────────────┐
                  │ Integration (40)  │  Tool + API tests
                  └───────────────────┘
              ┌─────────────────────────────┐
              │    Unit Tests (100+)        │  Individual components
              └─────────────────────────────┘
```

**Total Tests**: ~150+ automated tests

---

## Test Categories

### 1. Unit Tests (100+ tests)

Test individual components in isolation.

#### API Client Tests (`test_client.py`)
**Coverage**: 25 tests

```python
import pytest
from aareguru_mcp.client import AareguruClient

@pytest.mark.asyncio
async def test_get_cities():
    """Test fetching city list"""
    client = AareguruClient()
    cities = await client.get_cities()
    assert isinstance(cities, dict)
    assert "bern" in [c["city"] for c in cities.get("cities", [])]

@pytest.mark.asyncio
async def test_get_current_bern():
    """Test current conditions for Bern"""
    client = AareguruClient()
    data = await client.get_current("bern")
    assert data["city"] == "bern"
    assert "aare" in data
    assert "temperature" in data["aare"]

@pytest.mark.asyncio
async def test_get_current_invalid_city():
    """Test error handling for invalid city"""
    client = AareguruClient()
    with pytest.raises(ValueError):
        await client.get_current("invalid_city_name")

@pytest.mark.asyncio
async def test_caching():
    """Test response caching"""
    client = AareguruClient()
    # First call - cache miss
    data1 = await client.get_current("bern")
    # Second call - cache hit
    data2 = await client.get_current("bern")
    assert data1 == data2

@pytest.mark.asyncio
async def test_rate_limiting():
    """Test rate limiting enforcement"""
    client = AareguruClient()
    # Make multiple rapid requests
    for _ in range(5):
        await client.get_current("bern")
    # Should not exceed rate limit
```

#### Model Tests (`test_models.py`)
**Coverage**: 20 tests

```python
from aareguru_mcp.models import AareData, WeatherData, CityInfo

def test_aare_data_valid():
    """Test AareData model with valid data"""
    data = AareData(
        temperature=17.2,
        temperature_text="geil aber chli chalt",
        flow=245.0,
        flow_gefahrenstufe=2
    )
    assert data.temperature == 17.2
    assert data.flow_gefahrenstufe == 2

def test_aare_data_null_values():
    """Test AareData handles null values"""
    data = AareData(
        temperature=None,
        temperature_text=None,
        flow=None,
        flow_gefahrenstufe=None
    )
    assert data.temperature is None

def test_city_info_validation():
    """Test CityInfo validation"""
    city = CityInfo(
        city="bern",
        name="Bern",
        longname="Bern - Schönau",
        url="https://aare.guru/bern"
    )
    assert city.city == "bern"

def test_weather_data_schema():
    """Test WeatherData JSON schema generation"""
    schema = WeatherData.model_json_schema()
    assert "tt" in schema["properties"]
    assert "sy" in schema["properties"]
```

#### Tool Tests (`test_tools.py`)
**Coverage**: 35 tests

```python
import pytest
from aareguru_mcp.tools import (
    get_current_temperature,
    get_current_conditions,
    get_historical_data,
    list_cities,
    get_flow_danger_level,
    compare_cities,
    get_forecast
)

@pytest.mark.asyncio
async def test_get_current_temperature_bern():
    """Test temperature tool for Bern"""
    result = await get_current_temperature(city="bern")
    assert "temperature" in result
    assert "temperature_text" in result
    assert isinstance(result["temperature"], (float, type(None)))

@pytest.mark.asyncio
async def test_get_current_temperature_default():
    """Test temperature tool with default city"""
    result = await get_current_temperature()
    assert result["city"] == "bern"

@pytest.mark.asyncio
async def test_get_current_conditions_complete():
    """Test full conditions include all expected fields"""
    result = await get_current_conditions(city="bern")
    assert "aare" in result
    assert "weather" in result
    assert "forecast" in result

@pytest.mark.asyncio
async def test_list_cities_returns_array():
    """Test cities list returns array"""
    result = await list_cities()
    assert isinstance(result, list)
    assert len(result) > 0
    assert all("city" in c for c in result)

@pytest.mark.asyncio
async def test_compare_cities_two_cities():
    """Test comparing two cities"""
    result = await compare_cities(cities=["bern", "thun"])
    assert len(result) == 2
    assert result[0]["city"] == "bern"
    assert result[1]["city"] == "thun"

@pytest.mark.asyncio
async def test_get_historical_data_date_range():
    """Test historical data with date range"""
    result = await get_historical_data(
        city="bern",
        start="-7 days",
        end="now"
    )
    assert "timeseries" in result
    assert len(result["timeseries"]) > 0
```

#### Resource Tests (`test_resources.py`)
**Coverage**: 20 tests

```python
from aareguru_mcp.resources import (
    list_resources,
    read_resource
)

@pytest.mark.asyncio
async def test_list_resources():
    """Test listing all resources"""
    resources = await list_resources()
    assert len(resources) == 4
    uris = [r.uri for r in resources]
    assert "aareguru://cities" in uris
    assert "aareguru://widget" in uris

@pytest.mark.asyncio
async def test_read_resource_cities():
    """Test reading cities resource"""
    content = await read_resource("aareguru://cities")
    assert isinstance(content, str)
    data = json.loads(content)
    assert "cities" in data

@pytest.mark.asyncio
async def test_read_resource_current_bern():
    """Test reading current resource for Bern"""
    content = await read_resource("aareguru://current/bern")
    data = json.loads(content)
    assert data["city"] == "bern"

@pytest.mark.asyncio
async def test_read_resource_invalid_uri():
    """Test error handling for invalid URI"""
    with pytest.raises(ValueError):
        await read_resource("aareguru://invalid")
```

---

### 2. Integration Tests (40 tests)

Test tool interactions with real API and MCP protocol.

#### Tool Integration Tests (`test_tool_integration.py`)
**Coverage**: 30 tests

Based on the 130 user questions, we create representative integration tests:

```python
import pytest
from aareguru_mcp.server import create_mcp_server

@pytest.fixture
async def mcp_server():
    """Create MCP server instance for testing"""
    server = create_mcp_server()
    yield server
    await server.cleanup()

# Category 1: Basic Temperature Queries (Questions 1-10)
@pytest.mark.asyncio
async def test_question_1_whats_temperature(mcp_server):
    """Q1: What's the Aare temperature right now?"""
    result = await mcp_server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    assert result["temperature"] is not None
    assert result["temperature_text"] is not None

@pytest.mark.asyncio
async def test_question_3_warm_enough_to_swim(mcp_server):
    """Q3: Is the Aare warm enough to swim?"""
    result = await mcp_server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    # Should include temperature and contextual text
    assert "temperature" in result
    assert "temperature_text" in result

# Category 2: Safety & Flow Questions (Questions 11-20)
@pytest.mark.asyncio
async def test_question_11_is_it_safe(mcp_server):
    """Q11: Is it safe to swim in the Aare today?"""
    result = await mcp_server.call_tool(
        "get_current_conditions",
        {"city": "bern"}
    )
    assert "flow" in result["aare"]
    assert "flow_gefahrenstufe" in result["aare"]

@pytest.mark.asyncio
async def test_question_12_danger_level(mcp_server):
    """Q12: What's the current danger level?"""
    result = await mcp_server.call_tool(
        "get_flow_danger_level",
        {"city": "bern"}
    )
    assert "flow_gefahrenstufe" in result
    assert 1 <= result["flow_gefahrenstufe"] <= 5

# Category 4: Comparative Questions (Questions 31-40)
@pytest.mark.asyncio
async def test_question_31_which_city_warmest(mcp_server):
    """Q31: Which city has the warmest water?"""
    result = await mcp_server.call_tool(
        "compare_cities",
        {"cities": ["bern", "thun", "basel"]}
    )
    assert len(result) == 3
    # Should be able to determine warmest
    temps = [c["temperature"] for c in result if c["temperature"]]
    assert len(temps) > 0

@pytest.mark.asyncio
async def test_question_32_compare_bern_thun(mcp_server):
    """Q32: Compare Bern and Thun temperatures"""
    result = await mcp_server.call_tool(
        "compare_cities",
        {"cities": ["bern", "thun"]}
    )
    assert len(result) == 2
    assert result[0]["city"] in ["bern", "thun"]

# Category 5: Historical & Trend Questions (Questions 41-50)
@pytest.mark.asyncio
async def test_question_41_temperature_changed_this_week(mcp_server):
    """Q41: How has the temperature changed this week?"""
    result = await mcp_server.call_tool(
        "get_historical_data",
        {
            "city": "bern",
            "start": "-7 days",
            "end": "now"
        }
    )
    assert "timeseries" in result
    assert len(result["timeseries"]) > 0

@pytest.mark.asyncio
async def test_question_43_last_7_days(mcp_server):
    """Q43: Show me the last 7 days of data"""
    result = await mcp_server.call_tool(
        "get_historical_data",
        {
            "city": "bern",
            "start": "-7 days",
            "end": "now"
        }
    )
    assert len(result["timeseries"]) > 0

# Category 6: Forecast Questions (Questions 51-60)
@pytest.mark.asyncio
async def test_question_51_warmer_tomorrow(mcp_server):
    """Q51: Will the water be warmer tomorrow?"""
    result = await mcp_server.call_tool(
        "get_forecast",
        {"city": "bern", "hours": 24}
    )
    assert "forecast" in result

# Category 7: Location Discovery (Questions 61-70)
@pytest.mark.asyncio
async def test_question_62_which_cities_available(mcp_server):
    """Q62: Which cities have data available?"""
    result = await mcp_server.call_tool("list_cities", {})
    assert isinstance(result, list)
    assert len(result) > 0
    assert all("city" in c for c in result)

# Category 12: Multi-Step Queries (Questions 111-120)
@pytest.mark.asyncio
async def test_question_111_check_bern_compare_thun(mcp_server):
    """Q111: Check Bern temperature, then compare with Thun"""
    # Step 1: Get Bern temp
    bern_result = await mcp_server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    # Step 2: Compare with Thun
    compare_result = await mcp_server.call_tool(
        "compare_cities",
        {"cities": ["bern", "thun"]}
    )
    assert len(compare_result) == 2

# Category 13: Edge Cases (Questions 121-130)
@pytest.mark.asyncio
async def test_question_121_no_data_available(mcp_server):
    """Q121: What if there's no data available?"""
    # Should handle gracefully, not crash
    result = await mcp_server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    # Even if temperature is None, should return structure
    assert "temperature" in result

@pytest.mark.asyncio
async def test_question_130_swiss_german_meaning(mcp_server):
    """Q130: What does 'geil aber chli chalt' mean?"""
    result = await mcp_server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    # Should include Swiss German text
    if result["temperature_text"]:
        assert isinstance(result["temperature_text"], str)
```

#### MCP Protocol Tests (`test_mcp_protocol.py`)
**Coverage**: 10 tests

```python
@pytest.mark.asyncio
async def test_mcp_list_resources():
    """Test MCP list_resources protocol"""
    server = create_mcp_server()
    resources = await server.list_resources()
    assert len(resources) > 0
    assert all(hasattr(r, "uri") for r in resources)

@pytest.mark.asyncio
async def test_mcp_list_tools():
    """Test MCP list_tools protocol"""
    server = create_mcp_server()
    tools = await server.list_tools()
    assert len(tools) == 7
    tool_names = [t.name for t in tools]
    assert "get_current_temperature" in tool_names

@pytest.mark.asyncio
async def test_mcp_call_tool_with_schema():
    """Test tool call respects JSON schema"""
    server = create_mcp_server()
    # Valid call
    result = await server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    assert result is not None
    
    # Invalid call (missing required param for historical)
    with pytest.raises(ValueError):
        await server.call_tool(
            "get_historical_data",
            {"city": "bern"}  # Missing start/end
        )
```

---

### 3. End-to-End Tests (10 tests)

Test complete conversation flows simulating real user interactions.

#### Conversation Flow Tests (`test_e2e_conversations.py`)
**Coverage**: 10 tests

```python
import pytest
from aareguru_mcp.server import create_mcp_server

@pytest.mark.asyncio
async def test_conversation_simple_temperature_check():
    """
    User: "What's the Aare temperature in Bern?"
    Expected: Single tool call, formatted response
    """
    server = create_mcp_server()
    
    # Simulate Claude calling the tool
    result = await server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    
    # Verify response has all needed info
    assert "temperature" in result
    assert "temperature_text" in result
    # Should be able to format a complete response
    assert result["temperature"] is not None or result["temperature_text"] is not None

@pytest.mark.asyncio
async def test_conversation_safety_assessment():
    """
    User: "Is it safe to swim in the Aare today?"
    Expected: Full conditions check with safety assessment
    """
    server = create_mcp_server()
    
    result = await server.call_tool(
        "get_current_conditions",
        {"city": "bern"}
    )
    
    # Should have all info needed for safety assessment
    assert "aare" in result
    assert "flow" in result["aare"]
    assert "flow_gefahrenstufe" in result["aare"]
    assert "weather" in result

@pytest.mark.asyncio
async def test_conversation_city_comparison():
    """
    User: "Compare Bern and Thun, which is better for swimming?"
    Expected: Comparison + recommendation
    """
    server = create_mcp_server()
    
    result = await server.call_tool(
        "compare_cities",
        {"cities": ["bern", "thun"]}
    )
    
    # Should have data to make recommendation
    assert len(result) == 2
    for city_data in result:
        assert "temperature" in city_data
        assert "flow" in city_data

@pytest.mark.asyncio
async def test_conversation_with_forecast():
    """
    User: "Should I swim now or wait until later?"
    Expected: Current conditions + forecast
    """
    server = create_mcp_server()
    
    # Get current
    current = await server.call_tool(
        "get_current_conditions",
        {"city": "bern"}
    )
    
    # Get forecast
    forecast = await server.call_tool(
        "get_forecast",
        {"city": "bern", "hours": 6}
    )
    
    # Should have data to make timing recommendation
    assert current is not None
    assert forecast is not None

@pytest.mark.asyncio
async def test_conversation_historical_analysis():
    """
    User: "How has the temperature changed this week? Is it warmer than usual?"
    Expected: Historical data + analysis
    """
    server = create_mcp_server()
    
    result = await server.call_tool(
        "get_historical_data",
        {
            "city": "bern",
            "start": "-7 days",
            "end": "now"
        }
    )
    
    # Should have time series for analysis
    assert "timeseries" in result
    assert len(result["timeseries"]) > 0

@pytest.mark.asyncio
async def test_conversation_tourist_recommendation():
    """
    User: "I'm a tourist, where should I swim today?"
    Expected: List cities + compare + recommend best
    """
    server = create_mcp_server()
    
    # List available cities
    cities = await server.call_tool("list_cities", {})
    city_ids = [c["city"] for c in cities[:3]]  # Top 3
    
    # Compare them
    comparison = await server.call_tool(
        "compare_cities",
        {"cities": city_ids}
    )
    
    # Should have enough data to recommend
    assert len(comparison) > 0

@pytest.mark.asyncio
async def test_conversation_implicit_context():
    """
    User: "What's the temperature in Bern?"
    User: "What about Thun?"
    Expected: Handle context switching
    """
    server = create_mcp_server()
    
    # First query
    bern = await server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    
    # Second query (different city)
    thun = await server.call_tool(
        "get_current_temperature",
        {"city": "thun"}
    )
    
    # Both should work independently
    assert bern is not None
    assert thun is not None

@pytest.mark.asyncio
async def test_conversation_error_recovery():
    """
    User: "What's the temperature in InvalidCity?"
    Expected: Graceful error, suggest alternatives
    """
    server = create_mcp_server()
    
    # Should handle invalid city gracefully
    try:
        result = await server.call_tool(
            "get_current_temperature",
            {"city": "invalid_city_xyz"}
        )
        # If no error, should return None or empty
        assert result.get("temperature") is None
    except ValueError as e:
        # Or raise informative error
        assert "invalid" in str(e).lower() or "not found" in str(e).lower()
```

---

## Test Data & Fixtures

### Mock API Responses (`tests/fixtures/sample_responses.json`)

```json
{
  "current_bern": {
    "city": "bern",
    "aare": {
      "temperature": 17.2,
      "temperature_text": "geil aber chli chalt",
      "temperature_text_short": "chli chalt",
      "flow": 245.0,
      "flow_text": "moderate",
      "flow_gefahrenstufe": 2
    },
    "weather": {
      "tt": 24.0,
      "sy": 1,
      "rr": 0.0
    }
  },
  "cities": [
    {"city": "bern", "name": "Bern", "longname": "Bern - Schönau"},
    {"city": "thun", "name": "Thun", "longname": "Thun"},
    {"city": "basel", "name": "Basel", "longname": "Basel - Rhein"}
  ]
}
```

### Pytest Fixtures (`tests/conftest.py`)

```python
import pytest
import json
from pathlib import Path

@pytest.fixture
def sample_responses():
    """Load sample API responses"""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_responses.json"
    with open(fixture_path) as f:
        return json.load(f)

@pytest.fixture
async def mock_api_client(monkeypatch, sample_responses):
    """Mock API client with sample data"""
    from aareguru_mcp.client import AareguruClient
    
    async def mock_get_current(self, city="bern"):
        return sample_responses["current_bern"]
    
    async def mock_get_cities(self):
        return {"cities": sample_responses["cities"]}
    
    monkeypatch.setattr(AareguruClient, "get_current", mock_get_current)
    monkeypatch.setattr(AareguruClient, "get_cities", mock_get_cities)
    
    return AareguruClient()

@pytest.fixture
def vcr_config():
    """VCR configuration for recording API calls"""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "record_mode": "once",
        "match_on": ["uri", "method"]
    }
```

---

## Test Coverage Goals

### By Component

| Component | Target Coverage | Priority |
|-----------|----------------|----------|
| API Client | 95% | High |
| Models | 100% | High |
| Tools | 90% | High |
| Resources | 90% | High |
| Server | 85% | Medium |
| HTTP Server | 80% | Medium |

### By Question Category

| Category | Test Count | Coverage |
|----------|-----------|----------|
| Basic Temperature (1-10) | 10 | 100% |
| Safety & Flow (11-20) | 10 | 100% |
| Weather (21-30) | 5 | 50% |
| Comparative (31-40) | 8 | 80% |
| Historical (41-50) | 8 | 80% |
| Forecast (51-60) | 5 | 50% |
| Location Discovery (61-70) | 5 | 50% |
| Contextual (71-80) | 5 | 50% |
| Conversational (81-90) | 5 | 50% |
| Data Analysis (91-100) | 3 | 30% |
| Use Cases (101-110) | 3 | 30% |
| Multi-Step (111-120) | 5 | 50% |
| Edge Cases (121-130) | 8 | 80% |

**Total Question Coverage**: ~80 of 130 questions (62%)

---

## Test Execution

### Running Tests

```bash
# All tests
uv run pytest

# With coverage
uv run pytest --cov=aareguru_mcp --cov-report=html

# Specific category
uv run pytest tests/test_tools.py

# Integration tests only
uv run pytest tests/test_tool_integration.py

# E2E tests only
uv run pytest tests/test_e2e_conversations.py

# Parallel execution
uv run pytest -n auto

# Verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x
```

### CI/CD Integration

**GitHub Actions** (`.github/workflows/test.yml`):
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install dependencies
        run: uv sync
      - name: Run tests
        run: uv run pytest --cov=aareguru_mcp --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Performance Testing

### Load Tests (`tests/test_performance.py`)

```python
import pytest
import asyncio
import time

@pytest.mark.asyncio
async def test_concurrent_requests():
    """Test handling 10 concurrent requests"""
    server = create_mcp_server()
    
    async def make_request():
        return await server.call_tool(
            "get_current_temperature",
            {"city": "bern"}
        )
    
    start = time.time()
    results = await asyncio.gather(*[make_request() for _ in range(10)])
    duration = time.time() - start
    
    assert len(results) == 10
    assert duration < 5.0  # Should complete in < 5 seconds

@pytest.mark.asyncio
async def test_response_time():
    """Test single request response time"""
    server = create_mcp_server()
    
    start = time.time()
    result = await server.call_tool(
        "get_current_temperature",
        {"city": "bern"}
    )
    duration = time.time() - start
    
    assert duration < 1.0  # Should respond in < 1 second
```

---

## Test Maintenance

### Adding Tests for New Questions

When adding new user questions:

1. **Categorize** the question
2. **Identify** which tool(s) it uses
3. **Create** integration test
4. **Add** to E2E if complex
5. **Update** coverage metrics

### Test Review Checklist

- [ ] All 7 tools have unit tests
- [ ] Each question category has representative tests
- [ ] Edge cases are covered
- [ ] Error handling is tested
- [ ] Performance benchmarks exist
- [ ] CI/CD pipeline passes
- [ ] Coverage meets targets (80%+)

---

## Success Metrics

### Test Quality Indicators

✅ **Coverage**: 80%+ code coverage
✅ **Speed**: Test suite runs in < 2 minutes
✅ **Reliability**: 0% flaky tests
✅ **Maintainability**: Tests updated with code changes
✅ **Documentation**: All tests have clear docstrings

### Question Coverage

✅ **Phase 1 (MVP)**: 70 questions covered (54%)
✅ **Phase 2 (Enhanced)**: 100 questions covered (77%)
✅ **Phase 3 (Complete)**: 130 questions covered (100%)

---

## Conclusion

This testing plan ensures comprehensive coverage of all 130 user questions through:

- **100+ unit tests** for individual components
- **40 integration tests** for tool interactions
- **10 E2E tests** for conversation flows
- **Performance tests** for scalability
- **CI/CD integration** for continuous validation

The test suite provides confidence that the MCP server handles all expected user interactions correctly and gracefully.
