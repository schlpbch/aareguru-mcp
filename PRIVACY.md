# Privacy Policy — Aareguru MCP Server

**Effective Date:** 2026-04-26  
**Last Updated:** 2026-04-26  
**Contact:** schlpbch@gmail.com

## Summary

Aareguru MCP Server does not collect, store, or transmit any personal data.

## Data Collected

**None.** The server:

- Does not require authentication or user accounts
- Does not log IP addresses or user identifiers
- Does not store query history
- Does not use cookies or tracking technologies
- Does not transmit any data to third parties beyond what is needed to fetch
  public river data

## Data Sources

All data served by this MCP is sourced from publicly available Swiss APIs:

- **Aare.guru** (https://aare.guru) — water temperature, flow rate, river
  conditions. Non-commercial use only.
- **BAFU / Federal Office for the Environment**
  (https://www.hydrodaten.admin.ch) — official hydrological safety levels.
- **MeteoSwiss** (https://www.meteoswiss.admin.ch) — weather forecasts.

These APIs are public. No personal data passes through this server.

## Rate Limiting

The server enforces rate limits (100 requests/minute per IP address) to
prevent abuse. Rate limiting is applied per IP address transiently in memory
and is not persisted or logged.

## Authentication

No authentication is required or supported. The MCP endpoint is public.

## Infrastructure

The server runs on FastMCP Cloud (EU West region, eu-west-1). Ephemeral
structured logs (INFO level, JSON format) are retained for up to 30 days for
operational purposes. Logs do not contain personal data.

## Non-Commercial Use

The underlying data from Aare.guru is licensed for non-commercial use only.
This MCP server is a non-commercial, open-source project licensed under the
MIT License.

## Policy Updates

This policy may be updated. Changes will be reflected in the git commit
history at https://github.com/schlpbch/aareguru-mcp/commits/main/PRIVACY.md

## Contact

For privacy questions or concerns:  
Andreas Schlapbach — schlpbch@gmail.com
