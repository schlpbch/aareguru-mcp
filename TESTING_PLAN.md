# Aareguru MCP Server - Testing Plan

## Overview

This testing plan describes the comprehensive test suite for the Aareguru MCP server, organized into logical categories for maintainability and clarity.

---

## Test Suite Organization

### Test File Structure

```
tests/
├── conftest.py                    # Shared fixtures
├── fixtures/
│   └── sample_responses.json      # Mock API responses
│
├── test_unit_models.py            # Pydantic model validation (14 tests)
├── test_unit_config.py            # Settings and configuration (13 tests)
├── test_unit_client.py            # API client unit tests (14 tests)
├── test_unit_server_helpers.py    # Server helper functions (32 tests)
│
├── test_tools_basic.py            # Basic tool functions (21 tests)
├── test_tools_advanced.py         # Advanced tools: compare, forecast (18 tests)
│
├── test_integration_workflows.py  # Multi-tool workflows (16 tests)
├── test_http_endpoints.py         # HTTP endpoints, performance (17 tests)
└── test_resources.py              # Resource listing and reading (9 tests)
```

### Test Pyramid

```
                    ┌─────────────┐
                    │HTTP Endpoints│  17 tests
                    │  & Resources │  26 tests
                    └─────────────┘
                  ┌───────────────────┐
                  │    Integration    │  16 tests
                  │    Workflows      │
                  └───────────────────┘
              ┌─────────────────────────────┐
              │    Tool Tests (39 tests)    │  Basic + Advanced
              └─────────────────────────────┘
          ┌─────────────────────────────────────┐
          │      Unit Tests (73 tests)          │  Models, Config, Client, Helpers
          └─────────────────────────────────────┘
```

**Total Tests**: 153 automated tests

---

## Test Categories

### 1. Unit Tests (73 tests)

Test individual components in isolation without external dependencies.

#### Model Tests (`test_unit_models.py`) - 14 tests

```python
class TestAareData:
    """Test AareData model."""
    def test_valid_data(self): ...
    def test_null_values(self): ...
    def test_danger_level_valid_range(self): ...
    def test_danger_level_invalid_zero(self): ...
    def test_danger_level_invalid_six(self): ...

class TestWeatherData:
    """Test WeatherData model."""
    def test_valid_data(self): ...

class TestCityInfo:
    """Test CityInfo model."""
    def test_valid_city(self): ...
    def test_missing_required_field(self): ...

class TestModelSerialization:
    """Test model serialization."""
    def test_json_schema_generation(self): ...
    def test_to_dict(self): ...
    def test_to_json(self): ...
```

#### Configuration Tests (`test_unit_config.py`) - 13 tests

```python
class TestSettingsDefaults:
    """Test default settings values."""
    def test_default_base_url(self): ...
    def test_default_app_name(self): ...
    def test_default_cache_ttl(self): ...
    def test_default_request_interval(self): ...
    def test_default_log_level(self): ...

class TestSettingsValidation:
    """Test settings validation."""
    def test_valid_port(self): ...
    def test_invalid_port_too_high(self): ...
    def test_invalid_port_too_low(self): ...
    def test_valid_log_levels(self): ...

class TestSettingsCaching:
    """Test settings caching."""
    def test_get_settings_returns_same_instance(self): ...
```

#### Client Unit Tests (`test_unit_client.py`) - 14 tests

```python
class TestCacheEntry:
    """Test CacheEntry class."""
    def test_not_expired_immediately(self): ...
    def test_expired_after_ttl(self): ...
    def test_stores_data(self): ...

class TestClientInitialization:
    """Test client initialization."""
    def test_default_initialization(self): ...
    def test_custom_settings(self): ...
    def test_rate_limiting_setting(self): ...

class TestCacheKeyGeneration:
    """Test cache key generation."""
    def test_basic_key_generation(self): ...
    def test_same_params_same_key(self): ...
    def test_different_params_different_key(self): ...

class TestCacheOperations:
    """Test cache get/set operations."""
    def test_cache_miss_returns_none(self): ...
    def test_cache_set_and_get(self): ...
    def test_cache_clear(self): ...

class TestContextManager:
    """Test async context manager."""
    async def test_context_manager_opens_client(self): ...
    async def test_context_manager_closes_client(self): ...
```

#### Server Helper Tests (`test_unit_server_helpers.py`) - 32 tests

```python
class TestSeasonalAdvice:
    """Test _get_seasonal_advice for all seasons."""
    # Tests for all 12 months

class TestSafetyWarning:
    """Test _check_safety_warning for all flow levels."""
    def test_none_flow(self): ...
    def test_safe_flow_no_warning(self): ...
    def test_elevated_flow_caution(self): ...
    def test_danger_flow(self): ...
    def test_extreme_danger_flow(self): ...
    def test_default_threshold(self): ...

class TestSwissGermanExplanation:
    """Test _get_swiss_german_explanation for all phrases."""
    def test_geil_aber_chli_chalt(self): ...
    def test_schoen_warm(self): ...
    def test_arschkalt(self): ...
    def test_perfekt(self): ...
    def test_unknown_phrase_returns_none(self): ...
    def test_case_insensitive(self): ...

class TestSafetyAssessment:
    """Test _get_safety_assessment for all flow levels."""
    def test_safe_flow_under_100(self): ...
    def test_moderate_flow(self): ...
    def test_elevated_flow(self): ...
    def test_high_flow(self): ...
    def test_very_high_flow(self): ...
```

---

### 2. Tool Tests (39 tests)

Test MCP tool functions with mocked and real API calls.

#### Basic Tool Tests (`test_tools_basic.py`) - 21 tests

```python
class TestGetCurrentTemperature:
    """Test get_current_temperature tool."""
    async def test_default_city(self): ...
    async def test_specific_city(self): ...
    async def test_with_mocked_client(self): ...
    async def test_fallback_to_today(self): ...

class TestGetCurrentConditions:
    """Test get_current_conditions tool."""
    async def test_returns_comprehensive_data(self): ...
    async def test_includes_aare_data(self): ...
    async def test_with_weather_and_forecast(self): ...
    async def test_without_aare_data(self): ...

class TestListCities:
    """Test list_cities tool."""
    async def test_returns_array(self): ...
    async def test_city_has_required_fields(self): ...
    async def test_includes_bern(self): ...

class TestGetFlowDangerLevel:
    """Test get_flow_danger_level tool."""
    async def test_returns_safety_assessment(self): ...
    async def test_safety_text_is_readable(self): ...
    async def test_no_aare_data(self): ...

class TestGetHistoricalData:
    """Test get_historical_data tool."""
    async def test_with_relative_dates(self): ...
    async def test_with_mocked_client(self): ...

class TestErrorHandling:
    """Test tools handle errors gracefully."""
    async def test_invalid_city(self): ...
```

#### Advanced Tool Tests (`test_tools_advanced.py`) - 18 tests

```python
class TestCompareCitiesBasic:
    """Test basic compare_cities functionality."""
    async def test_specific_cities(self): ...
    async def test_all_cities_none_param(self): ...

class TestCompareCitiesSelection:
    """Test warmest, coldest, safest selection."""
    async def test_finds_warmest(self): ...
    async def test_finds_safest(self): ...

class TestCompareCitiesEdgeCases:
    """Test compare_cities edge cases."""
    async def test_handles_missing_data(self): ...
    async def test_all_cities_fail(self): ...
    async def test_empty_list(self): ...
    async def test_flow_none(self): ...
    async def test_very_high_flow(self): ...

class TestCompareCitiesRecommendations:
    """Test compare_cities recommendation logic."""
    async def test_warmest_is_safest(self): ...
    async def test_warmest_safe_but_not_safest(self): ...
    async def test_warmest_dangerous(self): ...

class TestGetForecastTrends:
    """Test forecast trend calculations."""
    async def test_rising_trend(self): ...
    async def test_falling_trend(self): ...
    async def test_stable_trend(self): ...

class TestGetForecastEdgeCases:
    """Test get_forecast edge cases."""
    async def test_missing_forecast_data(self): ...
    async def test_no_aare_data(self): ...
```

---

### 3. Integration Tests (16 tests)

Test multi-tool workflows and API interactions.

#### Integration Workflow Tests (`test_integration_workflows.py`) - 16 tests

```python
class TestMultiToolWorkflows:
    """Test workflows combining multiple tools."""
    async def test_list_cities_then_get_temperature(self): ...
    async def test_temperature_and_flow_correlation(self): ...
    async def test_resource_and_tool_consistency(self): ...
    async def test_multiple_cities_sequential(self): ...

class TestComplexScenarios:
    """Test complex multi-step scenarios."""
    async def test_cautious_swimmer_flow(self): ...
    async def test_group_planner_flow(self): ...

class TestCachingBehavior:
    """Test caching functionality."""
    async def test_cache_hit_performance(self): ...
    async def test_cache_expiration(self): ...
    async def test_different_params_different_cache(self): ...

class TestErrorHandling:
    """Test error handling in integrations."""
    async def test_invalid_city_handling(self): ...
    async def test_api_timeout_recovery(self): ...
    async def test_missing_data_fields(self): ...

class TestDataConsistency:
    """Test data consistency and validation."""
    async def test_swiss_german_text_present(self): ...
    async def test_flow_threshold_accuracy(self): ...
    async def test_temperature_precision(self): ...
```

---

### 4. HTTP & Resource Tests (26 tests)

Test HTTP endpoints, performance, and MCP resources.

#### HTTP Endpoint Tests (`test_http_endpoints.py`) - 17 tests

```python
class TestHealthEndpoint:
    """Test health check endpoint."""
    def test_health_returns_200(self): ...
    def test_health_response_format(self): ...
    def test_health_with_origin_header(self): ...
    def test_multiple_health_requests(self): ...

class TestCoreEndpoints:
    """Test core HTTP endpoints."""
    def test_missing_endpoint_404(self): ...

class TestSessionConfiguration:
    """Test session timeout configuration."""
    def test_default_session_config(self): ...
    def test_custom_session_config(self): ...
    def test_minimum_timeout_validation(self): ...

class TestConcurrency:
    """Test concurrent request handling."""
    async def test_concurrent_health_checks(self): ...

class TestPerformance:
    """Baseline performance tests."""
    def test_health_check_performance(self): ...
    def test_sequential_requests_performance(self): ...

class TestServerConfiguration:
    """Test FastMCP server configuration."""
    def test_server_name(self): ...
    def test_server_has_instructions(self): ...
    def test_server_has_tools(self): ...
    def test_server_has_resources(self): ...
```

#### Resource Tests (`test_resources.py`) - 9 tests

```python
async def test_list_resources(self): ...
async def test_list_resources_metadata(self): ...
async def test_read_resource_cities(self): ...
async def test_read_resource_widget(self): ...
async def test_read_resource_current_bern(self): ...
async def test_read_resource_today_bern(self): ...
async def test_read_resource_invalid_uri(self): ...
async def test_read_resource_unknown_path(self): ...
async def test_read_resource_malformed_uri(self): ...
```

---

## Test Coverage Goals

### By Component

| Component | Target | Actual |
|-----------|--------|--------|
| Models | 100% | 100% |
| Config | 100% | 100% |
| Client | 80% | 76% |
| Resources | 90% | 100% |
| Server | 85% | 80% |
| Tools | 90% | 87% |
| **Overall** | **85%** | **85%** |

---

## Running Tests

### Common Commands

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=aareguru_mcp

# Run specific category
uv run pytest tests/test_unit*.py       # Unit tests only
uv run pytest tests/test_tools*.py      # Tool tests only
uv run pytest tests/test_integration*   # Integration tests
uv run pytest tests/test_http*          # HTTP tests

# Run with verbose output
uv run pytest -v

# Stop on first failure
uv run pytest -x

# Run in parallel
uv run pytest -n auto
```

### Test Markers

```bash
# Integration tests (require API)
uv run pytest -m integration

# Skip slow tests
uv run pytest -m "not slow"
```

---

## Success Metrics

✅ **153 tests passing**
✅ **85% code coverage**
✅ **0% flaky tests**
✅ **< 10 seconds test execution**
✅ **Well-organized test structure**
