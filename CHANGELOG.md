# Changelog

All notable changes to aareguru-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.2.0] - 2026-02-08

### Added
- **ADR-014: Service Layer Pattern** - Formalized business logic layer for code reuse
  - Created `service.py` module with `AareguruService` class
  - 7 async methods mapping 1:1 to MCP tools
  - Thin MCP tool wrappers delegate to service for business logic
  - Enables future REST/Chat API layers to reuse service methods
  - Fixed DRY violation: `get_flow_danger_level` now uses shared `get_safety_assessment()` helper
  - ~350 lines of duplicated code eliminated

- **ADR-015: FastMCP Cloud Deployment** - Formalized production deployment with explicit configuration
  - Created `.fastmcp/config.yaml` with deployment configuration
    - Auto-scaling (2-10 replicas), health checks, monitoring alerts
    - Auto-rollback on >5% error rate or P95 >5s latency
    - eu-west-1 region for low latency to Switzerland
  - Created `aareguru-mcp.mcpb` bundle file for one-click Claude Desktop installation
  - Created `docs/DEPLOYMENT.md` comprehensive deployment guide
    - Deployment process, configuration, monitoring, troubleshooting
    - Cost optimization and installation instructions
  - Created GitHub Actions validation workflow (.github/workflows/deploy-validation.yml)
    - Tests, type checks, linting validation
    - Configuration file validation
    - Production health check verification

### Changed
- **All 15 ADRs now Accepted** - Complete architecture from core to deployment
- ADR Compendium updated: Version 1.2.0 → 1.3.0
  - "15 (13 Accepted, 2 Proposed)" → "15 (15 Accepted)"
  - Reorganized roadmap section: "Future Enhancements" → "Production Ready"

### Documentation
- Updated README.md with links to DEPLOYMENT.md and ADR_COMPENDIUM.md
- All architectural decisions now documented and accepted
- Production deployment fully documented with monitoring and troubleshooting guides

### Quality
- All 209 tests passing (87% coverage)
- 0 regressions detected
- YAML and JSON configuration validation
- Production deployment remains operational

## [4.1.0] - 2026-02-08

### Fixed
- **Critical: Rate limiter was blocking parallel requests** - Root cause of "Error occurred during tool execution" for 2+ cities
- Rate limiter held asyncio.Lock during 300-second sleep, blocking all parallel requests
- Second city's fetch never executed because it was waiting for lock held by first request

### Changed
- Reduced `min_request_interval_seconds` from 300s to 0.1s (100ms) for parallel support
- Rate limiter now sleeps **outside** the lock, allowing parallel requests to proceed
- Changed interval type from `int` to `float` for sub-second precision

### Improved  
- Added verbose debug logging for parallel fetch tracing (`→ Starting fetch for {city}`)
- Better error surfacing with structured error information in results
- Errors array in response shows which cities failed and why

## [4.0.0] - 2026-02-08

### Changed
- **BREAKING: Major architectural refactoring** - Complete separation of concerns
- **server.py reduced from 495 to 218 lines** (-56%) - Now pure MCP registration layer
- Created dedicated business logic modules: tools.py, prompts.py, resources.py as single sources of truth
- Eliminated all duplicate documentation between server.py and business logic modules
- Applied functools.wraps pattern for automatic docstring copying from business logic to MCP registrations

### Fixed
- Parallel city fetching now uses `return_exceptions=True` in asyncio.gather for graceful error handling
- Simplified error handling in compare_cities and get_forecasts to match working single-city pattern
- Production bug fix: Tools no longer cascade failures when fetching multiple cities

### Improved
- **Test suite**: Rewrote resource tests to directly test business logic functions
- **Code coverage**: resources.py now at 100% coverage
- **209 tests passing** with improved test structure
- Better separation: Business logic (tools/prompts/resources) vs MCP protocol (server)
- Single source of truth: All docstrings, arguments, and logic defined once in business modules

## [3.3.0] - 2026-02-07

### Added
- **Parallel API fetching** with `asyncio.gather()` for improved performance
- **Comprehensive ARCHITECTURE.md** documentation covering design patterns, data flow, and deployment
- Optimized CLAUDE.md with updated test counts and streamlined sections

### Changed
- **Major refactoring**: Removed singleton HTTP client pattern, standardized on async context managers throughout
- **DRY improvements**: server.py now delegates to tools.py, eliminating ~300 lines of duplicate code
- Renamed fast parallel tools as primary implementation (compare_cities, get_forecasts)
- Removed redundant slow tools (list_cities, get_forecast) - parallel versions are now default
- Improved context manager pattern consistency across all resources and tools

### Fixed
- **Test suite**: All 210 tests now passing (was 201 passing, 9 failing)
- Case-sensitivity issues in test assertions ("Bern" vs "bern")
- API calls now use lowercase city names as required by Aareguru API
- City name casing standardized across codebase

### Improved
- **Code coverage**: 85% → 87% overall, server.py 69% → 84%
- **Code size**: Removed ~400 total lines through refactoring
- Architecture now fully async-first with consistent resource management
- Better separation of concerns between MCP protocol and business logic

## [3.2.0] - 2026-01-22

### Changed
- **Updated swiss-ai-mcp-commons to v1.1.0** with HTTP content negotiation support
- Enhanced JSON serialization capabilities with automatic compression
- Added framework integration helpers for FastAPI, Flask, and Starlette
- Improved bandwidth efficiency with smart gzip compression (60-80% reduction)

### Performance
- Content negotiation enables automatic response compression when beneficial
- Configurable compression thresholds (default: 1024 bytes)
- Backward compatible with existing API consumers

## [3.1.0] - 2026-01-22

### Added
- Initial production release with FastMCP 2.0
- 7 MCP tools for Aare river data queries
- 4 MCP resources for cities, API documentation, and data schemas
- 3 MCP prompts for guided interactions
- Comprehensive test suite (202 tests, 87% coverage)
- Structured logging with structlog
- HTTP/SSE transport support
- Docker deployment configuration

### Features
- Current temperature and conditions queries
- Historical data analysis with hourly granularity
- Safety assessments based on BAFU thresholds
- Swiss German temperature phrase explanations
- Seasonal swimming advice
- Multi-city support across Switzerland

[3.3.0]: https://github.com/schlpbch/aareguru-mcp/compare/v3.2.0...v3.3.0
[3.2.0]: https://github.com/schlpbch/aareguru-mcp/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/schlpbch/aareguru-mcp/releases/tag/v3.1.0
