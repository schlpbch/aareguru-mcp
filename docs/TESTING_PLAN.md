# Testing Plan

## Test Suite

**365 tests** | **80% coverage** | **< 10s execution** | **floor: 70%**

## Structure

```
tests/
├── test_unit_models.py          # Pydantic models
├── test_unit_config.py          # Settings
├── test_unit_client.py          # API client
├── test_unit_server_helpers.py  # Server helpers
├── test_unit_metrics.py         # Prometheus metrics
├── test_tools_basic.py          # Basic tools (mocked service)
├── test_parallel_tools.py       # compare_cities, get_forecasts
├── test_client_edge_cases.py    # Client error paths, caching, rate limits
├── test_service_error_paths.py  # Service layer edge cases
├── test_integration_workflows.py # Multi-tool workflows
├── test_http_endpoints.py       # HTTP/SSE transport
├── test_resources.py            # Resource URI resolution
├── test_resources_new.py        # Additional resource tests
├── test_prompts.py              # Prompts and E2E workflows
├── test_apps.py                 # FastMCPApps (8 apps)
├── test_apps_map.py             # OpenStreetMap app
├── test_metrics_and_rate_limit.py # Metrics + HTTP rate limiting
├── test_coverage_gaps.py        # Edge cases for coverage floor
└── conftest.py                  # Shared fixtures and mocks
```

## Coverage by Component

| Component | Target | Actual |
|-----------|--------|--------|
| `config.py` | 100% | 100% |
| `tools.py` | 100% | 100% |
| `__init__.py` | 100% | 100% |
| `helpers.py` | 90% | 94% |
| `models.py` | 90% | 94% |
| `service.py` | 85% | 91% |
| `client.py` | 80% | 82% |
| `server.py` | 70% | 60% |
| `apps/*` | 70% | varies |
| **Overall** | **70%** | **80%** |

## Commands

```bash
uv run pytest                         # All tests (365)
uv run pytest --cov=aareguru_mcp      # With coverage (80%)
uv run pytest tests/test_tools_basic.py  # Specific file
uv run pytest -v                      # Verbose
uv run pytest -x                      # Stop on first failure
uv run pytest -m integration          # Integration only
uv run pytest -m e2e                  # E2E only
```

## Test Categories

- **Unit** (`test_unit_*.py`): Models, config, client, helpers, metrics — isolated, no I/O
- **Tool** (`test_tools_*.py`, `test_parallel_tools.py`): Tool + service layer with mocked API
- **Integration** (`test_integration_workflows.py`, `test_client_edge_cases.py`, `test_service_error_paths.py`): Multi-component workflows
- **HTTP** (`test_http_endpoints.py`, `test_metrics_and_rate_limit.py`): Transport, Prometheus, rate limiting
- **Resources** (`test_resources*.py`): URI resolution and data access
- **Apps** (`test_apps*.py`): FastMCPApps HTML rendering
- **E2E** (`test_prompts.py`): Full prompt-to-tool conversation flows

## Coverage Enforcement

`--cov-fail-under=70` is set in `pyproject.toml` — CI fails if coverage drops below 70%.
