# Changelog

All notable changes to aareguru-mcp will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[3.2.0]: https://github.com/schlpbch/aareguru-mcp/compare/v3.1.0...v3.2.0
[3.1.0]: https://github.com/schlpbch/aareguru-mcp/releases/tag/v3.1.0
