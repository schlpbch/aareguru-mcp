# Aareguru MCP Server

MCP server for Swiss Aare river data, enabling AI assistants to answer questions about swimming conditions, water temperature, flow rates, and safety.

## Status

🚧 **Phase 1 Week 1 - In Progress**

- ✅ Project structure
- ✅ Configuration management
- ✅ Pydantic models
- ✅ Async API client with caching
- ✅ Initial test suite
- ⏳ MCP server implementation (Week 2)

## Quick Start

```bash
# Install dependencies (requires Python 3.10+)
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=aareguru_mcp
```

## Features

- **7 MCP Tools** for querying Aare data
- **4 MCP Resources** for static data access
- **Async HTTP client** with caching and rate limiting
- **Comprehensive testing** (target: 85%+ coverage)
- **Dual deployment**: stdio (local) and HTTP/SSE (remote)

## Documentation

See the `docs/` directory for comprehensive planning documents:

- [MASTER_PLAN.md](MASTER_PLAN.md) - Complete implementation roadmap
- [AAREGURU_API_ANALYSIS.md](AAREGURU_API_ANALYSIS.md) - API documentation
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - Technical architecture
- [TESTING_PLAN.md](TESTING_PLAN.md) - QA strategy

## License

MIT - See LICENSE file

## Attribution

Data sources:
- [BAFU](https://www.hydrodaten.admin.ch) - Swiss Federal Office for the Environment
- [Aare.guru](https://aare.guru) - Aare.guru GmbH

Non-commercial use only. Please notify aaregurus@existenz.ch if using this API.
