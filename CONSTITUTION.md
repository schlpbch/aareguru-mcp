# Aareguru MCP — Project Constitution

**Version**: 1.0.0
**Effective**: 2026-04-26
**Maintainer**: Andreas Schlapbach (<schlpbch@gmail.com>)
**Repository**: aareguru-mcp

---

## Preamble

Aareguru MCP is a non-commercial, open-source Model Context Protocol server
that exposes Swiss Aare river data — water temperature, flow rates, weather
conditions, and safety assessments — to AI assistants. The upstream data is
provided by Aare.guru GmbH and BAFU (Federal Office for the Environment). This
server exists to make that public safety data accessible, accurate, and useful
within AI conversation contexts.

This Constitution defines the principles, constraints, and standards that govern
all decisions in this project. It takes precedence over any individual document,
comment, or convention. Significant architectural decisions are recorded as ADRs
in `specs/ADR_COMPENDIUM.md`; this document governs *why* those decisions exist
and *how* future ones are made.

---

## Article I — Mission

**I.1** The project's mission is to provide accurate, attributed, and
responsibly rate-limited access to Swiss Aare river data for AI assistants.

**I.2** The server MUST remain non-commercial. It MUST NOT be used as a
component in any product, service, or workflow that generates revenue, directly
or indirectly, without explicit written permission from Aare.guru GmbH.

**I.3** The server SHOULD prioritize user safety. When BAFU flow data indicates
elevated danger, the server MUST surface that information clearly and without
downplaying it.

---

## Article II — Non-Negotiable Constraints

These constraints are absolute. No ADR, feature request, or performance
optimization may override them.

**II.1 Non-commercial use.**
All deployments, forks, and derivatives MUST comply with the Aareguru API's
non-commercial license. Any use in commercial contexts requires a separate
license from the upstream provider.

**II.2 Attribution.**
Every tool response that includes Aare river data MUST attribute the source.
Removing or suppressing attribution strings is prohibited.

**II.3 Rate limiting.**
The client layer MUST enforce a minimum request interval against the Aareguru
API (default: 300 s, configurable via `MIN_REQUEST_INTERVAL_SECONDS`). The
interval MUST NOT be set below 60 s in production deployments. See ADR-009.

**II.4 Safety data integrity.**
BAFU flow thresholds and danger levels MUST be represented exactly as defined in
`helpers.py` and `apps/_constants.py`. Thresholds MUST NOT be altered without a
corresponding ADR that documents the authoritative source for the new values.

**II.5 App identification.**
All HTTP requests to the upstream API MUST include `app` and `version` query
parameters identifying this server. Removing these identifiers is prohibited.

---

## Article III — Architecture

**III.1 Layered architecture.**
The codebase is organized into seven layers. Each layer MUST depend only on the
layer immediately below it. Cross-layer shortcuts are prohibited. See ADR-005.

```ascii
UI Apps (apps/)
  → MCP Server (server.py)
  → MCP Interface (tools.py, resources.py, prompts.py)
  → Service Layer (service.py)
  → HTTP Client (client.py)
  → Data Models (models.py)
  → Configuration (config.py)
```

**III.2 Thin tool wrappers.**
`tools.py` MUST contain only MCP protocol concerns: docstrings, type hints,
parameter defaults, and error-to-dict conversion. Business logic MUST live in
`service.py`. See ADR-014.

**III.3 Service layer reuse.**
`service.py` methods MUST be callable by both MCP tools and FastMCPApps without
modification. No method in `service.py` MAY import from `apps/`. See ADR-014,
ADR-016.

**III.4 Async-first.**
All I/O MUST use `async`/`await`. Blocking I/O calls (`time.sleep`, synchronous
`requests`, file reads outside module initialization) are prohibited in
production code paths. See ADR-003.

**III.5 Resource management.**
HTTP client instances MUST be created and released via async context managers
(`async with AareguruClient(...) as client`). Instantiating a client outside a
context manager is prohibited. See ADR-007.

**III.6 Dependency injection.**
Configuration MUST be passed via `get_settings()` or constructor injection.
Reading environment variables directly inside tool, service, or client logic is
prohibited. Global mutable state is prohibited. See ADR-005.

---

## Article IV — Type Safety

**IV.1 MyPy strict mode.**
All production code under `src/aareguru_mcp/` MUST pass `mypy --strict` with
zero errors. Introducing `# type: ignore` annotations MUST be accompanied by an
inline comment explaining why the suppression is unavoidable. See ADR-012.

**IV.2 Pydantic v2 for external data.**
All data received from the Aareguru API MUST be parsed through a Pydantic v2
model before use. Raw `dict` access on unparsed API responses is prohibited
outside `models.py`. See ADR-002.

**IV.3 Typed public APIs.**
All public functions and methods MUST carry complete type annotations on
parameters and return types. Untyped public APIs MUST NOT be merged.

---

## Article V — Error Handling

**V.1 Error responses as dicts.**
MCP tool functions MUST return `{"error": "<message>"}` on failure. Raising
unhandled exceptions to the MCP layer is prohibited.

**V.2 Partial responses preferred.**
Where a sub-component of a response fails (e.g., Swiss German enrichment, safety
suggestion), the function SHOULD return partial data with the failed field as
`None` rather than returning a top-level error. The failure MUST be logged.

**V.3 Layer-appropriate exceptions.**
The HTTP client layer MAY raise `httpx` exceptions internally. These MUST be
caught and converted to error dicts at the MCP interface layer (`tools.py`)
before reaching the MCP protocol layer.

---

## Article VI — Quality Standards

**VI.1 Test coverage floor.**
The project MUST maintain ≥70% overall test coverage (configured as
`--cov-fail-under=70` in `pyproject.toml`). The target is ≥80%. Coverage MUST
NOT be reduced below the floor by any merge. See ADR-011.

**VI.2 Core module coverage targets.**
`client.py`, `helpers.py`, and `models.py` MUST maintain ≥90% coverage.
`models.py` MUST maintain ≥95% coverage, as data validation errors directly
affect safety data fidelity.

**VI.3 Structured logging.**
All layers MUST use `structlog` with module-scoped loggers. `print()` statements
are prohibited in production code. Log events MUST use `snake_case` event names
(e.g., `"tool_executed"`, `"api_error"`). See ADR-010.

**VI.4 Code formatting.**
All Python code MUST be formatted with `black` (line length 88) and pass
`ruff check` with the configured rule set before merge. Formatting violations
MUST NOT be committed.

**VI.5 Caching.**
The HTTP client MUST apply time-based caching with a configurable TTL (default:
120 s). Historical data endpoints SHOULD bypass the cache (`use_cache=False`).
See ADR-008.

---

## Article VII — UI Apps

**VII.1 Design token centralization.**
All colors, typography tokens, BAFU safety level definitions, and lookup tables
MUST be defined in `apps/_constants.py`. Hardcoded color values or threshold
numbers inside individual app files are prohibited. See ADR-017.

**VII.2 WCAG AA compliance.**
All foreground text colors used in FastMCPApps MUST achieve a ≥4.5:1 contrast
ratio against their background in both light and dark modes. Contrast ratios MUST
be documented in `apps/_constants.py` as inline comments. See ADR-017.

**VII.3 Self-contained delivery.**
FastMCPApps MUST NOT make external network requests for assets (fonts, icons,
scripts) at render time, except for map tile providers explicitly listed in
ADR-018. All fonts MUST be embedded as base64 data URIs. See ADR-017.

**VII.4 App isolation.**
Each `FastMCPApp` MUST be defined in its own file under `apps/`. Apps MUST NOT
import from each other. Shared utilities MUST live in `apps/_helpers.py` or
`apps/_constants.py`. See ADR-016.

---

## Article VIII — Safety Data Handling

**VIII.1 Authoritative source.**
Hydrological data originates from BAFU (Federal Office for the Environment).
This is official Swiss public safety data. It MUST be presented as-is;
reinterpretation or summarization that could reduce perceived urgency is
prohibited.

**VIII.2 Danger level accuracy.**
The five BAFU flow danger levels with thresholds at 100, 220, 300, and 430 m³/s
MUST be implemented exactly as specified in `apps/_constants.py` (`_BAFU_LEVELS`,
`_SAFETY_LEVELS`). Any change to these thresholds REQUIRES a new ADR citing the
updated BAFU source.

**VIII.3 Safety warnings in tool responses.**
`get_current_conditions` and `get_flow_danger_level` MUST include a safety
assessment field in every successful response. Omitting the safety field when
flow data is available is prohibited.

**VIII.4 MCP elicitation for dangerous conditions.**
When flow rates exceed the "elevated" threshold (>220 m³/s), the server SHOULD
use MCP elicitation to request acknowledgement before proceeding with
recommendations that could be construed as endorsing swimming.

---

## Article IX — Deployment

**IX.1 Production region.**
The canonical production deployment is FastMCP Cloud, region `eu-west-1`. Data
MUST NOT be routed through regions outside the EU without explicit review. See
ADR-015.

**IX.2 Health and metrics.**
The HTTP transport MUST expose `/health` and `/metrics` endpoints. The `/metrics`
endpoint MUST use the Prometheus format. Both MUST be rate-limited. See ADR-013.

**IX.3 Transports.**
The server MUST support both stdio (Claude Desktop) and HTTP/SSE (cloud/web)
transports from the same codebase. Transport-specific logic MUST be isolated to
the entry-point functions in `server.py`. See ADR-013, ADR-015.

**IX.4 Python version.**
Production deployments MUST use Python 3.11 or later. The codebase targets
Python 3.13. The minimum version MUST NOT be lowered without an ADR. See ADR-004.

---

## Article X — Governance (ADR Process)

**X.1 ADR requirement.**
Any decision that affects the public API surface, layer boundaries, external
dependencies, rate limiting behavior, safety thresholds, or test coverage floor
MUST be documented as an ADR before implementation.

**X.2 ADR format.**
ADRs MUST be appended to `specs/ADR_COMPENDIUM.md`. Each ADR MUST include:
status, date, context category, decision, rationale, and related ADRs.

**X.3 ADR numbering.**
ADRs are numbered sequentially. The current highest number is ADR-019. Gaps in
numbering are not permitted.

**X.4 ADR immutability.**
Accepted ADRs are immutable. A decision that supersedes an accepted ADR MUST
create a new ADR with status "Accepted" and mark the superseded ADR as
"Superseded" with a cross-reference. Editing the body of an accepted ADR in
place is prohibited.

**X.5 ADR status lifecycle.**
Valid statuses are: `Proposed` → `Accepted` → `Superseded` or `Deprecated`.
Code implementing a Proposed ADR MUST NOT be merged until the ADR is Accepted.

**X.6 Single maintainer.**
This is a single-maintainer project. The maintainer (Andreas Schlapbach) holds
final authority on all ADR decisions. External contributors MAY propose ADRs via
pull request. The maintainer MAY accept, reject, or amend proposals.

---

## Article XI — Dependency Policy

**XI.1 Minimal surface.**
New runtime dependencies MUST be justified by a concrete capability gap. Adding
a dependency solely for convenience is insufficient justification.

**XI.2 Pinned minimums.**
All dependencies MUST specify a minimum version in `pyproject.toml`. Unpinned
or wildcard dependencies in the `[project]` block are prohibited.

**XI.3 `uv` as canonical tool.**
Package management MUST use `uv`. `pip install` MAY be used in documented
fallback scenarios but MUST NOT be the default path.

---

## Amendment Procedure

This Constitution MAY be amended by the maintainer via a pull request that:

1. Increments the version number in the header.
2. Adds a dated entry to the amendment log below.
3. References any ADR that motivated the change, if applicable.

Amendments that weaken Article II (Non-Negotiable Constraints) or Article VIII
(Safety Data Handling) MUST include an explicit justification section.

---

## Amendment Log

| Version | Date       | Change Summary       | ADR Ref |
|---------|------------|----------------------|---------|
| 1.0.0   | 2026-04-26 | Initial constitution | —       |

---

*This document is the authoritative governance reference for aareguru-mcp.
When in doubt, consult the ADR Compendium (`specs/ADR_COMPENDIUM.md`) for
technical rationale and this Constitution for the principles those decisions
serve.*
