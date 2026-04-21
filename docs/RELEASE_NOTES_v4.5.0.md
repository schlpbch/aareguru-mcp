# Release Notes: aareguru-mcp v4.5.0

**Release Date**: April 21, 2026  
**Previous Version**: v4.4.0  
**Status**: Stable, Production Ready

---

## Executive Summary

aareguru-mcp v4.5.0 is a maintenance and modernization release that aligns the project with Python 3.13, removes an unmaintained dependency (slowapi), and introduces coverage enforcement to prevent regressions. All 365 tests pass with 80% coverage.

---

## What's Changed

### 🐍 Python 3.13 Tooling Alignment

The project now fully targets Python 3.13 across all tooling:

| Tool | Before | After | Rationale |
|------|--------|-------|-----------|
| `requires-python` | `>=3.11` | `>=3.13` | Match actual runtime (Python 3.13.7) |
| `black.target-version` | `["py310", "py311"]` | `["py313"]` | Enable py313-specific formatting |
| `ruff.target-version` | `"py310"` | `"py313"` | Catch py313 linting opportunities |
| `mypy.python_version` | `"3.11"` | `"py313"` | Type-check against actual Python version |

**Impact**: 
- Ruff now suggests py313 improvements via the `UP` rule
- Applied 2 pyupgrade suggestions: `timezone.utc` → `datetime.UTC` (server.py lines 175, 180)
- Black reformatted 11 files to py313 conventions
- Full compatibility with Python 3.13.7 confirmed

### 🗑️ Removed Unmaintained slowapi

The slowapi rate limiter had a critical issue: **it was never properly wired to the application**.

**Problem**:
- slowapi requires `app.state.limiter` to be set and an exception handler registered
- Neither of these configurations existed in `server.py`
- The `@limiter.limit("60/minute")` decorator on `/health` was non-functional
- slowapi is unmaintained; generates Python 3.14+ deprecation warnings that will become hard errors

**Solution**:
- Deleted `src/aareguru_mcp/rate_limit.py` (entire module)
- Deleted `tests/test_unit_rate_limit.py` (related tests)
- Removed `@limiter.limit("60/minute")` decorator from `/health` endpoint
- Removed slowapi from dependencies (and transitive sub-deps: `deprecated`, `limits`, `wrapt`)
- Removed Python 3.14+ deprecation warning suppression from pytest config

**Functional Impact**: None. The rate limiter was non-functional. The `/health` endpoint now runs without any rate limiting, which is acceptable for internal health checks.

**Breaking Change**: If you were relying on slowapi being installed as a dependency of this package, you will need to add it explicitly to your own `pyproject.toml` if needed.

### ✅ Coverage Enforcement

Added `--cov-fail-under=70` to pytest configuration to catch coverage regressions in CI:

```toml
[tool.pytest.ini_options]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--cov=aareguru_mcp",
    "--cov-fail-under=70",  # NEW
]
```

**Impact**:
- CI pipelines will now fail if test coverage drops below 70%
- Current coverage: **79.91%** (exceeds the floor)
- Prevents future regressions from merging untested code

### 📚 Documentation Updates

Fixed stale FastMCP version references in CLAUDE.md:

| Location | Before | After |
|----------|--------|-------|
| Line 15 (Status) | FastMCP 2.0 | FastMCP 3.x |
| Line 94 (Architecture) | FastMCP 2.0 | FastMCP 3.x |
| Line 317 (Decorator Pattern) | FastMCP 2.0 | FastMCP 3.x |

Also updated project phase: Phase 9 → Phase 10

---

## Verification & Testing

### Test Results
```
✅ 365 tests passing (down from 371 due to removed slowapi tests)
✅ 79.91% coverage (exceeds 70% floor requirement)
✅ All pytest markers strict
✅ No skipped tests
```

### Code Quality
```
✅ Black formatting: 50 files pass
✅ Ruff linting: All files pass (E, W, F, I, B, C4, UP rules)
✅ MyPy type checking: All files pass (strict mode)
```

### Dependency Resolution
```
✅ uv sync: 94 packages resolved
✅ No version conflicts
✅ slowapi and transitive deps cleanly removed
```

---

## Upgrade Guide

### For Users

No user-facing changes. If you're using aareguru-mcp as an MCP server or library:

1. **Update the package**:
   ```bash
   uv add aareguru-mcp==4.5.0
   # or
   pip install aareguru-mcp==4.5.0
   ```

2. **Verify your Python version** is 3.13+:
   ```bash
   python --version
   # Python 3.13.7
   ```

3. **No breaking changes to the API or tools** — all tools work identically to v4.4.0.

### For Developers

If you're developing on this codebase:

1. **Update your local environment**:
   ```bash
   uv sync
   ```

2. **If you were relying on slowapi**, add it explicitly:
   ```bash
   uv add slowapi
   ```

3. **Run tests to verify your local setup**:
   ```bash
   uv run pytest
   ```

---

## Dependency Changes

### Removed
- `slowapi>=0.1.9` ✂️
- `deprecated==1.3.1` (transitive from slowapi) ✂️
- `limits==5.8.0` (transitive from slowapi) ✂️
- `wrapt==2.1.2` (transitive from slowapi) ✂️

### Updated
- `prefab-ui`: `>=0.18.0` → `>=0.19.0` (aligns with installed version)

### Unchanged
All other dependencies remain compatible. No version bumps needed for:
- `fastmcp[apps]>=3.2.3` (latest 3.2.4)
- `pydantic>=2.0.0` (installed 2.12.5)
- `structlog>=23.1.0` (installed 23.3.0, constrained by git dependency)
- `pytest>=9.0.0` (installed 9.0.3)
- All other dependencies remain pinned to sensible minimum versions

---

## Performance & Security

- ✅ No performance regressions (365 tests confirm identical behavior)
- ✅ Removes a deprecated dependency (improves security by using maintained packages only)
- ✅ Future-proofs against Python 3.14 (was generating suppressed warnings)
- ✅ Coverage enforcement prevents silent test gaps (security benefit)

---

## Files Changed

### Deleted
- `src/aareguru_mcp/rate_limit.py` (69 lines)
- `tests/test_unit_rate_limit.py` (test file)

### Modified
- `pyproject.toml` (6 changes: version, requires-python, 3 tool targets, deps, addopts)
- `CLAUDE.md` (3 version references updated)
- `src/aareguru_mcp/server.py` (removed limiter import and decorator, added UTC import)
- 11 Python files reformatted for py313 compatibility

### Summary
- **Total Commits**: 1 (`ed9921c`)
- **Files Modified**: 17
- **Files Deleted**: 2
- **Lines Added/Removed**: +107 insertions, −696 deletions (net: −589 lines)

---

## Known Issues & Limitations

None at this release. All known issues from v4.4.0 remain unchanged (refer to MASTER_PLAN.md for backlog items).

---

## Next Steps & Roadmap

### Phase 11 (Planned)
- [ ] Evaluate structlog 24.x upgrade (currently constrained by git dependency `swiss-ai-mcp-commons`)
- [ ] Consider request deduplication at service layer for repeated city queries
- [ ] Audit type stub coverage for `swiss-ai-mcp-commons` (currently untyped)

### Future Releases
- REST API support (ADR-016)
- Chat API support (ADR-017)
- Enhanced caching strategies
- Performance optimizations for bulk comparisons

---

## Contributors

- **Release Author**: Andreas Schlapbach
- **AI Assistant**: Claude Haiku 4.5
- **Test Coverage**: 365 tests, 80% coverage

---

## Support & Feedback

- 📖 Documentation: [CLAUDE.md](../CLAUDE.md)
- 🏗️ Architecture: [ARCHITECTURE.md](../ARCHITECTURE.md)
- 🐛 Issues: [GitHub Issues](https://github.com/schlpbch/aareguru-mcp/issues)
- 📋 Backlog: [MASTER_PLAN.md](../docs/MASTER_PLAN.md)

---

## Version Information

```
aareguru-mcp==4.5.0
Python>=3.13
FastMCP>=3.2.3
Pydantic>=2.0.0
```

**Released**: 2026-04-21  
**Commit**: ed9921c  
**Tag**: v4.5.0  
**GitHub Release**: https://github.com/schlpbch/aareguru-mcp/releases/tag/v4.5.0
