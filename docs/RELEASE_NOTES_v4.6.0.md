# Release Notes: aareguru-mcp v4.6.0

**Release Date**: April 26, 2026
**Previous Version**: v4.5.0
**Status**: Stable, Production Ready

---

## Executive Summary

aareguru-mcp v4.6.0 is a governance and documentation release. It introduces
two foundational project documents — `CONSTITUTION.md` and `SKILLS.md` — that
codify project principles and capability references respectively. All 365 tests
pass with 80% coverage. No code changes.

---

## What's Changed

### CONSTITUTION.md — Project Governance

A new `CONSTITUTION.md` establishes the authoritative governance reference for
the project. It takes precedence over all other documents and defines:

- **11 Articles** covering mission, non-negotiable constraints, architecture,
  type safety, error handling, quality standards, UI apps, safety data handling,
  deployment, ADR governance, and dependency policy
- **RFC 2119 language** (MUST / SHOULD / MAY) throughout
- **Article II** (Non-Negotiable Constraints): encodes the non-commercial
  licence terms, attribution requirements, rate limiting floor, BAFU data
  integrity, and app identification as absolute rules
- **Article VIII** (Safety Data Handling): standalone article elevating BAFU
  safety data to a first-class governance concern — not a subset of code quality
- **Article X** (Governance): formalises the ADR process — when an ADR is
  required, format, numbering, immutability, status lifecycle, and maintainer
  authority
- **Amendment log** with versioned history

### SKILLS.md — Capability Reference

A new `SKILLS.md` serves as the canonical "what can I ask this server to do?"
document for both end users and developers:

- **Quick Reference table**: all 6 tools with one-line descriptions and example
  questions
- **Tool Selection Guide**: ASCII decision tree mapping question types to tools
- **Complete capability inventory**: 6 tools, 7 resources, 3 prompts, 12
  FastMCPApps — each with parameters, return values, and usage guidance
- **Use Cases by Topic**: 12 topic entries (basic temp, safety, comparison,
  history, forecasts, activity-specific, multi-step, etc.) mapping to primary
  tool + visual app
- **Developer Notes**: elicitation behavior, parallel fetching, caching, city
  identifiers, attribution policy

---

## No Code Changes

This release is documentation-only. The test suite, coverage, and all runtime
behavior are identical to v4.5.0.

| Metric | v4.5.0 | v4.6.0 |
| --- | --- | --- |
| Tests passing | 365 | 365 |
| Coverage | 80% | 80% |
| Code changes | — | 0 |
| New documents | — | 2 |

---

## Document Inventory (post-release)

| Document | Purpose |
| --- | --- |
| `README.md` | Installation, quick start, configuration |
| `SKILLS.md` | Capability reference (tools, resources, prompts, apps) |
| `CONSTITUTION.md` | Project governance, principles, constraints |
| `ARCHITECTURE.md` | Layer design, data flow, patterns |
| `specs/ADR_COMPENDIUM.md` | 18 Architecture Decision Records |
| `docs/USER_QUESTIONS_SLIDES.md` | 130-question test suite |
| `docs/DEPLOYMENT.md` | FastMCP Cloud deployment guide |
