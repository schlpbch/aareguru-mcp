# Testing Plan

## Test Suite

**200 tests** | **87% coverage** | **< 10s execution**

## Structure

```
tests/
├── test_models.py           # Pydantic models (14 tests)
├── test_config.py           # Settings (13 tests)
├── test_client.py           # API client (14 tests)
├── test_server.py           # Server helpers (32 tests)
├── test_tools.py            # Basic tools (21 tests)
├── test_advanced_tools.py   # Compare, forecast (18 tests)
├── test_tool_integration.py # Multi-tool workflows (16 tests)
├── test_http_server.py      # HTTP endpoints (17 tests)
├── test_resources.py        # Resources (9 tests)
└── conftest.py              # Shared fixtures
```

## Coverage Goals

| Component | Target | Actual |
|-----------|--------|--------|
| Models | 100% | 100% |
| Config | 100% | 100% |
| Client | 80% | 76% |
| Server | 85% | 80% |
| Tools | 90% | 87% |
| **Overall** | **85%** | **87%** |

## Commands

```bash
uv run pytest                         # All tests
uv run pytest --cov=aareguru_mcp      # With coverage
uv run pytest tests/test_tools.py     # Specific file
uv run pytest -v                      # Verbose
uv run pytest -x                      # Stop on first failure
uv run pytest -m integration          # Integration only
```

## Test Categories

- **Unit**: Models, config, client, helpers (isolated)
- **Tool**: Tool functionality with mocked/real API
- **Integration**: Multi-tool workflows, caching
- **HTTP**: Endpoints, performance, concurrency
- **E2E**: Full conversation patterns
