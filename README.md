# Aareguru MCP Server

MCP server for Swiss Aare river data, enabling AI assistants to answer questions about swimming conditions, water temperature, flow rates, and safety.

## Status

✅ **Phase 1 Weeks 1-2 Complete** - Production Ready!

- ✅ Project structure
- ✅ Configuration management (100% coverage)
- ✅ Pydantic models (100% coverage)
- ✅ Async API client with caching (77% coverage)
- ✅ MCP server (stdio)
- ✅ 4 MCP resources (100% coverage)
- ✅ 5 MCP tools (81% coverage)
- ✅ **42/42 tests passing** (100% pass rate)
- ✅ **81% overall code coverage**
- 🎯 Ready for Claude Desktop integration!

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
 
 - **5 MCP Tools** for querying Aare data (Temperature, Current Conditions, History, Flow Safety, City List)
 - **4 MCP Resources** for data access (Cities, Widget, Current, Today)
 - **Async HTTP client** with caching and rate limiting
 - **Comprehensive testing** (100% pass rate, 81% coverage)
 - **Stdio transport** for local integration (HTTP/SSE planned for Phase 3)
 
 ## Development
 
 ### API Testing
 
 A Postman collection is included for testing the Aareguru API endpoints directly:
 - Import `aareguru_postman_collection.json` into Postman
 - Includes requests for all core endpoints (cities, today, current, widget, history)
 - Pre-configured with environment variables


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
