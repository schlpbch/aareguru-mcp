# v4.2.0: Service Layer & Cloud Deployment

**Release Date:** February 8, 2026 | **Status:** ✅ Production Ready

## What's New

### ADR-014: Service Layer Pattern
- Centralized business logic in `service.py` module
- Thin MCP tool wrappers delegate to service layer
- ~350 lines of duplicate code eliminated
- Foundation for future REST/Chat APIs

### ADR-015: FastMCP Cloud Deployment
- Explicit `.fastmcp/config.yaml` configuration
- Auto-scaling: 2-10 replicas with health checks
- One-click installation via `aareguru-mcp.mcpb`
- Monitoring, alerting, and auto-rollback configured

### All 15 ADRs Accepted ✅
Complete architecture formalized from core framework to cloud deployment.

## Installation

**Option 1: Direct URL** (Claude Desktop)
```json
{
  "mcpServers": {
    "aareguru": {
      "url": "https://aareguru.fastmcp.app/mcp"
    }
  }
}
```

**Option 2: Bundle File** (Claude Desktop)
- Download `aareguru-mcp.mcpb`
- Drag-and-drop into Claude Desktop
- One-click installation

**Option 3: Python**
```bash
pip install aareguru-mcp
```

## Quality

- ✅ 209 tests passing (87% coverage)
- ✅ 0 regressions detected
- ✅ All type checks, linting, formatting passing
- ✅ YAML and JSON configurations validated

## Key Metrics

| Metric | Value |
|--------|-------|
| Average Response | <500ms |
| P95 Latency | <2s |
| Cache Hit Rate | ~80% |
| Test Coverage | 87% |
| Auto-Scale Time | <60s |

## Documentation

- **[Comprehensive Release Notes](RELEASE_NOTES_v4.2.0.md)** - Full details
- **[Deployment Guide](docs/DEPLOYMENT.md)** - Cloud setup
- **[Architecture Decisions](specs/ADR_COMPENDIUM.md)** - All 15 ADRs
- **[README](README.md)** - Quick start

## Deployment

✅ **Live on FastMCP Cloud**
- URL: https://aareguru.fastmcp.app/mcp
- Health: https://aareguru.fastmcp.app/health/
- Metrics: https://aareguru.fastmcp.app/metrics

## Backward Compatibility

✅ **No breaking changes** - Safe upgrade from v4.1.0
- All existing APIs unchanged
- Configuration optional
- Direct upgrade path

## What Changed

- 11 files modified/created
- 2,177 insertions
- Service layer implementation (172 lines)
- Cloud deployment configuration (2.8 KB)
- Comprehensive documentation

## Features

- **6 MCP Tools** - Temperature, flow, safety, forecasts, history, comparisons
- **3 MCP Resources** - Direct data access
- **3 MCP Prompts** - Daily reports and analysis
- **Auto-scaling** - 2-10 replicas
- **Health Monitoring** - Every 30s with alerts
- **Structured Logging** - JSON format
- **Caching** - 120s TTL (~80% hit rate)

## Next Steps

See [full release notes](RELEASE_NOTES_v4.2.0.md) for detailed information on:
- Use cases and examples
- Configuration reference
- Troubleshooting guide
- Development roadmap

---

**🎉 v4.2.0 is production ready and recommended for all users.**

For issues or questions: [GitHub Issues](https://github.com/schlpbch/aareguru-mcp/issues)
