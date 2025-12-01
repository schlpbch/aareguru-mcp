# Aareguru MCP Server - Master Implementation Plan

**Project**: MCP Server for Swiss Aare River Data  
**Version**: 1.0.0  
**Last Updated**: 2025-11-30  

---

## Executive Summary

This master plan consolidates all planning documents into a comprehensive roadmap for building a production-ready MCP (Model Context Protocol) server that exposes the Aareguru API to AI assistants like Claude Desktop.

### Project Goals

1. **Expose Aareguru API** via MCP protocol for natural language queries
2. **Answer 130+ user questions** about Aare river conditions
3. **Support dual deployment**: stdio (local) and HTTP/SSE (remote)
4. **Achieve 95%+ accuracy** in single-turn query resolution
5. **Maintain Swiss cultural authenticity** with Swiss German integration

### Key Deliverables

- ✅ MCP server with 7 tools and 4 resources
- ✅ Comprehensive test suite (150+ tests, 80%+ coverage)
- ✅ HTTP/SSE server for cloud deployment
- ✅ Docker containerization
- ✅ Complete documentation and examples

---

## Planning Documents Overview

| Document | Purpose | Key Insights |
|----------|---------|--------------|
| **AAREGURU_API_ANALYSIS.md** | API documentation | 5 endpoints, 50+ parameters, data sources |
| **IMPLEMENTATION_PLAN.md** | Core architecture | 7 tools, 4 resources, technology stack |
| **CLAUDE_DESKTOP_INTEGRATION_PLAN.md** | UX design | 130 user questions, response formatting |
| **HTTP_STREAMING_PLAN.md** | Deployment strategy | SSE transport, security, cloud options |
| **USER_QUESTIONS_SLIDES.md** | Question catalog | 13 categories, tool mapping |
| **TESTING_PLAN.md** | Quality assurance | 150+ tests, CI/CD, coverage goals |

---

## Technology Stack

### Core Dependencies

```toml
[project.dependencies]
mcp = ">=1.0.0"              # MCP protocol SDK
httpx = ">=0.27.0"           # Async HTTP client
pydantic = ">=2.0.0"         # Data validation
python-dotenv = ">=1.0.0"    # Environment config
starlette = ">=0.37.0"       # ASGI framework (HTTP)
uvicorn = ">=0.29.0"         # ASGI server (HTTP)
```

### Development Tools

```toml
[project.optional-dependencies.dev]
pytest = ">=8.0.0"
pytest-asyncio = ">=0.23.0"
pytest-cov = ">=4.1.0"
black = ">=24.0.0"
ruff = ">=0.3.0"
mypy = ">=1.8.0"
```

### Python Version
- **Minimum**: 3.10
- **Recommended**: 3.11+

---

## Architecture Overview

### System Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Claude Desktop                        │
│                   (or other MCP client)                  │
└────────────────┬────────────────────────┬────────────────┘
                 │                        │
          stdio  │                        │  HTTP/SSE
                 │                        │
┌────────────────▼────────┐    ┌─────────▼──────────────┐
│   MCP Server (stdio)    │    │  MCP Server (HTTP)     │
│   Local Development     │    │  Cloud Deployment      │
└────────────────┬────────┘    └─────────┬──────────────┘
                 │                        │
                 └────────────┬───────────┘
                              │
                    ┌─────────▼──────────┐
                    │   MCP Protocol     │
                    │  (Resources/Tools) │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │  Aareguru Client   │
                    │  (HTTP + Caching)  │
                    └─────────┬──────────┘
                              │
                    ┌─────────▼──────────┐
                    │   Aareguru API     │
                    │  (BAFU, MeteoTest) │
                    └────────────────────┘
```

### Component Breakdown

| Component | Responsibility | Files |
|-----------|---------------|-------|
| **MCP Server** | Protocol implementation | `server.py` |
| **HTTP Server** | SSE transport layer | `http_server.py` |
| **API Client** | Aareguru API wrapper | `client.py` |
| **Models** | Data validation | `models.py` |
| **Resources** | Static data access | `resources.py` |
| **Tools** | Dynamic queries | `tools.py` |
| **Config** | Settings management | `config.py` |

---

## MCP Interface Design

### Resources (4 total)

| URI | Description | Use Case |
|-----|-------------|----------|
| `aareguru://cities` | List all cities | Discovery, validation |
| `aareguru://current/{city}` | Full current data | Comprehensive queries |
| `aareguru://today/{city}` | Minimal data | Quick checks |
| `aareguru://widget` | All cities overview | Multi-city display |

### Tools (7 total)

| Tool | Parameters | Returns | User Questions |
|------|-----------|---------|----------------|
| `get_current_temperature` | city? | temp, text | 1-10, 81-90 |
| `get_current_conditions` | city? | full data | 11-20, 21-30, 71-80 |
| `get_historical_data` | city, start, end | time series | 41-50, 91-100 |
| `list_cities` | - | city array | 61-70 |
| `get_flow_danger_level` | city? | flow, danger | 11-20 |
| `compare_cities` | cities[] | comparison | 31-40 |
| `get_forecast` | city?, hours? | forecast | 51-60 |

**Coverage**: 130 user questions across 13 categories

---

## Implementation Phases

### Phase 1: Core MVP (Stdio) - Weeks 1-3

**Goal**: Functional MCP server answering 70% of user questions via stdio transport.

#### Week 1: Foundation ✅ **COMPLETE**
**Status**: ✅ Complete (100% test pass rate)
**Deliverables**:
- [x] Project structure (`src/aareguru_mcp/`)
- [x] `pyproject.toml` with all dependencies
- [x] `.env.example` and `.gitignore`
- [x] `config.py` - Settings management with Pydantic (100% coverage)
- [x] `models.py` - Pydantic models for all API responses (100% coverage)
- [x] `client.py` - Async HTTP client with caching (77% coverage)
- [x] Unit tests for client and models (25 tests)

**Achievements**:
- ✅ All models validate real API responses
- ✅ Client handles errors gracefully
- ✅ 100% test coverage for config and models
- ✅ Async client with caching and rate limiting
- ✅ Type-safe with Pydantic throughout

**Git Commit**: `e771b5b` - 14 files, 1,088 lines

#### Week 2: MCP Protocol Implementation ✅ **COMPLETE**
**Status**: ✅ Complete (100% test pass rate)
**Deliverables**:
- [x] `server.py` - MCP server with stdio transport (37% coverage)
- [x] `resources.py` - 4 MCP resources (100% coverage)
- [x] `tools.py` - 5 core tools (81% coverage)
- [x] Tool and resource tests (20 tests)
- [x] Model fixes to match actual API (100% coverage)

**Resources Implemented**:
1. ✅ `aareguru://cities` - List all cities
2. ✅ `aareguru://current/{city}` - Current conditions
3. ✅ `aareguru://today/{city}` - Minimal data
4. ✅ `aareguru://widget` - All cities overview

**Tools Implemented**:
1. ✅ `get_current_temperature` - Water temp + Swiss German text
2. ✅ `get_current_conditions` - Complete conditions
3. ✅ `get_historical_data` - Time series analysis
4. ✅ `list_cities` - City discovery
5. ✅ `get_flow_danger_level` - Flow + safety assessment

**Achievements**:
- ✅ 42/42 tests passing (100% pass rate)
- ✅ 81% overall code coverage
- ✅ All tools tested with real API
- ✅ Models match actual API responses
- ✅ Enhanced tool annotations optimized for 130 user questions
- ✅ Ready for Claude Desktop integration

**Git Commits**: 
- `1e3296c` - MCP server implementation (9 files, 847 lines)
- `caecfe4` - Model fixes for 100% test pass rate

#### Week 3: Testing & Documentation
- [ ] Integration tests (20 tests)
- [ ] E2E conversation tests (5 tests)
- [ ] README with usage examples
- [ ] Claude Desktop configuration guide
- [ ] Test with real Claude Desktop

**Deliverable**: MVP ready for local testing (70 questions covered)

**Milestone 1**: ✅ Working stdio MCP server

---

### Phase 2: Enhanced Features (Weeks 4-5)

**Goal**: Complete tool set + UX improvements

#### Week 4: Advanced Tools
- [ ] `compare_cities` tool implementation
- [ ] `get_forecast` tool implementation
- [ ] Response formatting with emojis and markdown
- [ ] Swiss German translations in responses
- [ ] Tool tests for new features (10 tests)

**Deliverable**: All 7 tools implemented

#### Week 5: User Experience
- [ ] Proactive safety checks
- [ ] Alternative city suggestions
- [ ] Seasonal intelligence
- [ ] Cultural context (Swiss German explanations)
- [ ] Enhanced integration tests (20 more tests)
- [ ] E2E tests for complex flows (5 more tests)

**Deliverable**: 95% question coverage with rich UX

**Milestone 2**: ✅ Complete feature set with excellent UX

---

### Phase 3: HTTP Deployment (Weeks 6-7)

**Goal**: Production-ready HTTP/SSE server

#### Week 6: HTTP Server
- [ ] Starlette/FastAPI HTTP server
- [ ] SSE transport implementation
- [ ] API key authentication
- [ ] Rate limiting (60 req/min)
- [ ] CORS configuration
- [ ] HTTP endpoint tests (15 tests)

**Deliverable**: Working HTTP/SSE server

#### Week 7: Security & Monitoring
- [ ] JWT authentication (optional)
- [ ] Prometheus metrics endpoint
- [ ] Structured logging
- [ ] Health check endpoint
- [ ] Docker containerization
- [ ] docker-compose setup

**Deliverable**: Production-ready deployment

**Milestone 3**: ✅ HTTP server ready for cloud deployment

---

### Phase 4: Cloud Deployment (Week 8)

**Goal**: Live production deployment

#### Week 8: Deployment & Optimization
- [ ] Choose cloud platform (Fly.io, GCP, AWS)
- [ ] Deploy to production
- [ ] Set up monitoring and alerts
- [ ] Performance testing and optimization
- [ ] Load testing (handle 100 concurrent users)
- [ ] Documentation updates

**Deliverable**: Live production service

**Milestone 4**: ✅ Production deployment complete

---

### Phase 5: Polish & Documentation (Week 9)

**Goal**: Complete documentation and examples

#### Week 9: Finalization
- [ ] Comprehensive README
- [ ] API documentation
- [ ] Usage examples for all tools
- [ ] Troubleshooting guide
- [ ] Contributing guidelines
- [ ] License and attribution
- [ ] Blog post / announcement

**Deliverable**: Production-ready, well-documented project

**Milestone 5**: ✅ Project complete and documented

---

## Project Structure

```
aareguru-mcp/
├── src/
│   └── aareguru_mcp/
│       ├── __init__.py
│       ├── server.py              # MCP server (stdio)
│       ├── http_server.py         # HTTP/SSE server
│       ├── client.py              # Aareguru API client
│       ├── models.py              # Pydantic models
│       ├── resources.py           # MCP resources
│       ├── tools.py               # MCP tools
│       └── config.py              # Configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py                # Pytest fixtures
│   ├── test_client.py             # Client tests (25)
│   ├── test_models.py             # Model tests (20)
│   ├── test_tools.py              # Tool tests (35)
│   ├── test_resources.py          # Resource tests (20)
│   ├── test_tool_integration.py   # Integration (30)
│   ├── test_mcp_protocol.py       # Protocol tests (10)
│   ├── test_http_server.py        # HTTP tests (15)
│   ├── test_e2e_conversations.py  # E2E tests (10)
│   ├── test_performance.py        # Performance tests
│   └── fixtures/
│       └── sample_responses.json  # Mock data
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── docs/
│   ├── AAREGURU_API_ANALYSIS.md
│   ├── IMPLEMENTATION_PLAN.md
│   ├── CLAUDE_DESKTOP_INTEGRATION_PLAN.md
│   ├── HTTP_STREAMING_PLAN.md
│   ├── USER_QUESTIONS_SLIDES.md
│   └── TESTING_PLAN.md
├── .github/
│   └── workflows/
│       ├── test.yml               # CI/CD tests
│       └── deploy.yml             # Deployment
├── .env.example
├── .gitignore
├── pyproject.toml
├── README.md
├── LICENSE
└── CHANGELOG.md
```

---

## Testing Strategy

### Test Distribution

```
Total Tests: ~165

Unit Tests (100):
├── Client: 25 tests
├── Models: 20 tests
├── Tools: 35 tests
└── Resources: 20 tests

Integration Tests (45):
├── Tool Integration: 30 tests
├── MCP Protocol: 10 tests
└── HTTP Server: 15 tests (Phase 3)

E2E Tests (10):
└── Conversation Flows: 10 tests

Performance Tests (10):
├── Load Testing: 5 tests
└── Response Time: 5 tests
```

### Coverage Goals

| Component | Target | Priority |
|-----------|--------|----------|
| API Client | 95% | High |
| Models | 100% | High |
| Tools | 90% | High |
| Resources | 90% | High |
| Server | 85% | Medium |
| HTTP Server | 80% | Medium |
| **Overall** | **85%+** | **High** |

### CI/CD Pipeline

```yaml
On Push/PR:
1. Lint (ruff, black)
2. Type check (mypy)
3. Unit tests
4. Integration tests
5. Coverage report
6. Build Docker image

On Main Branch:
7. Deploy to staging
8. E2E tests
9. Deploy to production
```

---

## Deployment Options

### Option 1: Local (stdio)

**Use Case**: Claude Desktop, local development

```json
{
  "mcpServers": {
    "aareguru": {
      "command": "uv",
      "args": ["--directory", "/path/to/aareguru-mcp", "run", "aareguru-mcp"]
    }
  }
}
```

### Option 2: Docker (Local/Cloud)

**Use Case**: Consistent environments, cloud deployment

```bash
docker-compose up -d
```

### Option 3: Cloud (HTTP/SSE)

**Use Case**: Remote access, multi-user, production

**Platforms**:
- **Fly.io** (Recommended): Easy deployment, global edge
- **Google Cloud Run**: Serverless, auto-scaling
- **AWS ECS**: Full control, enterprise
- **Railway**: Simple, developer-friendly

```json
{
  "mcpServers": {
    "aareguru": {
      "url": "https://aareguru-mcp.fly.dev/sse",
      "transport": "sse",
      "headers": {"X-API-Key": "your-key"}
    }
  }
}
```

---

## Security Considerations

### Authentication

**Phase 1 (MVP)**: None (local stdio only)

**Phase 3 (HTTP)**:
- API key authentication (required)
- Optional JWT for user-based access

### Rate Limiting

- **Per IP**: 60 requests/minute
- **Per API Key**: 100 requests/minute
- **Burst**: 10 requests/second

### Data Privacy

- No user data stored
- API calls logged (anonymized)
- GDPR compliant (EU data sources)

### CORS

- Development: `*` (all origins)
- Production: Whitelist specific domains

---

## Performance Targets

### Response Times

| Query Type | Target | Max |
|------------|--------|-----|
| Simple (temp check) | < 500ms | 1s |
| Moderate (conditions) | < 1s | 2s |
| Complex (historical) | < 2s | 5s |
| Multi-step | < 3s | 10s |

### Throughput

- **Concurrent Users**: 100+
- **Requests/Second**: 50+
- **Cache Hit Rate**: 80%+

### Availability

- **Uptime**: 99.5%+ (stdio), 99.9%+ (HTTP)
- **Error Rate**: < 0.5%

---

## Success Metrics

### Technical Metrics

- ✅ **Test Coverage**: 85%+
- ✅ **Response Time**: 95th percentile < 2s
- ✅ **Uptime**: 99.5%+
- ✅ **Error Rate**: < 0.5%
- ✅ **Cache Hit Rate**: 80%+

### User Experience Metrics

- ✅ **Question Coverage**: 130/130 (100%)
- ✅ **Single-Turn Resolution**: 95%+
- ✅ **Accurate Responses**: 98%+
- ✅ **Helpful Formatting**: 100%
- ✅ **Swiss German Integration**: 100%

### Development Metrics

- ✅ **Documentation**: Complete
- ✅ **Examples**: 10+ use cases
- ✅ **CI/CD**: Automated
- ✅ **Deployment**: < 5 minutes

---

## Risk Management

### Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| API downtime | High | Caching, graceful degradation |
| Rate limiting | Medium | Respect 5-min intervals, cache |
| Data quality | Medium | Defensive programming, validation |
| Breaking changes | Low | Version pinning, monitoring |

### Project Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Scope creep | Medium | Phased approach, MVP first |
| Timeline delays | Low | Buffer time, clear milestones |
| Resource constraints | Low | Simple tech stack, good docs |

---

## Dependencies & Attribution

### Data Sources

- **BAFU**: Swiss Federal Office for the Environment
- **MeteoSchweiz**: Swiss weather service
- **Meteotest**: Weather forecasts (sponsored)
- **TemperAare**: Community temperature data

### License Requirements

> [!IMPORTANT]
> **Non-commercial use only**
> - Notify: aaregurus@existenz.ch
> - Link to: https://aare.guru
> - Link to: https://www.hydrodaten.admin.ch

### Open Source

- **License**: MIT (for MCP server code)
- **Attribution**: Aare.guru GmbH, Christian Studer

---

## Timeline Summary

```
Week 1-3:  Phase 1 - Core MVP (stdio)
Week 4-5:  Phase 2 - Enhanced Features
Week 6-7:  Phase 3 - HTTP Deployment
Week 8:    Phase 4 - Cloud Deployment
Week 9:    Phase 5 - Polish & Documentation

Total: 9 weeks to production
```

### Milestones

- **Week 3**: ✅ MVP working locally
- **Week 5**: ✅ Complete feature set
- **Week 7**: ✅ HTTP server ready
- **Week 8**: ✅ Production deployment
- **Week 9**: ✅ Project complete

---

## Development Workflow

### Daily Workflow

```bash
# 1. Pull latest
git pull origin main

# 2. Create feature branch
git checkout -b feature/tool-compare-cities

# 3. Develop with tests
uv run pytest --watch

# 4. Format and lint
uv run black src/ tests/
uv run ruff check src/ tests/

# 5. Type check
uv run mypy src/

# 6. Run full test suite
uv run pytest --cov=aareguru_mcp

# 7. Commit and push
git commit -m "feat: add compare_cities tool"
git push origin feature/tool-compare-cities

# 8. Create PR
gh pr create
```

### Code Review Checklist

- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Type hints present
- [ ] Error handling implemented
- [ ] Performance considered
- [ ] Security reviewed

---

## Monitoring & Observability

### Metrics to Track

**Application Metrics**:
- Request count by tool
- Response times (p50, p95, p99)
- Error rates by type
- Cache hit/miss ratio

**Infrastructure Metrics**:
- CPU usage
- Memory usage
- Network I/O
- Disk usage

**Business Metrics**:
- Active users
- Popular cities
- Peak usage times
- Question categories

### Logging

```python
# Structured logging format
{
  "timestamp": "2025-11-30T17:00:00Z",
  "level": "INFO",
  "tool": "get_current_temperature",
  "city": "bern",
  "response_time_ms": 234,
  "cache_hit": true
}
```

### Alerts

- **Critical**: Error rate > 5% for 5 minutes
- **Warning**: Response time p95 > 5s for 10 minutes
- **Info**: Cache hit rate < 50% for 1 hour

---

## Future Enhancements

### Post-Launch (Phase 6+)

**Advanced Features**:
- [ ] Predictive temperature modeling
- [ ] Swimming route recommendations
- [ ] Water quality integration
- [ ] Multi-language support (French, Italian)
- [ ] Mobile app integration
- [ ] Webhook notifications

**Technical Improvements**:
- [ ] GraphQL API option
- [ ] WebSocket support
- [ ] Redis distributed caching
- [ ] Horizontal scaling
- [ ] CDN integration

**Community Features**:
- [ ] User-submitted swimming reports
- [ ] Photo sharing integration
- [ ] Social features (check-ins)
- [ ] Gamification (badges, streaks)

---

## Resources & Links

### Documentation
- [Aareguru API](https://aare.guru/api)
- [MCP Protocol](https://modelcontextprotocol.io/)
- [Claude Desktop](https://claude.ai/desktop)

### Planning Documents
- [Aareguru API Analysis](AAREGURU_API_ANALYSIS.md)
- [Implementation Plan](IMPLEMENTATION_PLAN.md)
- [Claude Desktop Integration](CLAUDE_DESKTOP_INTEGRATION_PLAN.md)
- [HTTP Streaming Plan](HTTP_STREAMING_PLAN.md)
- [User Questions (130)](USER_QUESTIONS_SLIDES.md)
- [Testing Plan](TESTING_PLAN.md)

### Community
- **Email**: aaregurus@existenz.ch
- **Website**: https://aare.guru
- **GitHub**: (to be created)

---

## Getting Started

### Quick Start (5 minutes)

```bash
# 1. Clone repository
git clone <repo-url> aareguru-mcp
cd aareguru-mcp

# 2. Install dependencies
curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync

# 3. Configure environment
cp .env.example .env

# 4. Run tests
uv run pytest

# 5. Start server (stdio)
uv run aareguru-mcp

# 6. Configure Claude Desktop
# Edit: ~/Library/Application Support/Claude/claude_desktop_config.json
```

### Next Steps

1. Read [IMPLEMENTATION_PLAN.md](./IMPLEMENTATION_PLAN.md)
2. Review [TESTING_PLAN.md](./TESTING_PLAN.md)
3. Start with Phase 1, Week 1 tasks
4. Join development discussions

---

## Conclusion

This master plan provides a comprehensive roadmap for building a production-ready MCP server for the Aareguru API. By following the phased approach, the project will deliver:

- **Week 3**: Working MVP (70% coverage)
- **Week 5**: Complete features (95% coverage)
- **Week 7**: Production-ready HTTP server
- **Week 9**: Fully documented, deployed project

The plan balances **technical excellence** (85%+ test coverage, 99.5%+ uptime) with **user experience** (130 questions, Swiss German, rich formatting) to create a valuable tool for the Swiss swimming community.

**Let's build something awesome! 🏊‍♂️🇨🇭**
