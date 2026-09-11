"""Tests for graceful degradation when the client's negotiated MCP protocol
doesn't support server-initiated elicitation (fastmcp 4.x / MCP SDK v2 raises
ToolError instead of allowing ctx.elicit() to proceed).

See _elicit_safe in server.py: it converts that ToolError into a sentinel so
callers can fall back to a sensible default instead of the tool call failing.
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastmcp.exceptions import ToolError

from aareguru_mcp.server import (
    _ELICIT_UNAVAILABLE,
    _elicit_city,
    _elicit_safe,
    complete_checkout_tool,
    get_flow_danger_level_tool,
    get_historical_data_tool,
)


def _make_ctx(*, raises: bool) -> AsyncMock:
    ctx = AsyncMock()
    if raises:
        ctx.elicit = AsyncMock(side_effect=ToolError("elicitation unavailable"))
    return ctx


class TestElicitSafe:
    @pytest.mark.asyncio
    async def test_returns_result_when_supported(self):
        ctx = AsyncMock()
        ctx.elicit = AsyncMock(return_value="ok")
        result = await _elicit_safe(ctx, "msg", str)
        assert result == "ok"

    @pytest.mark.asyncio
    async def test_returns_sentinel_when_unsupported(self):
        ctx = _make_ctx(raises=True)
        result = await _elicit_safe(ctx, "msg", str)
        assert result is _ELICIT_UNAVAILABLE


class TestElicitCityFallback:
    @pytest.mark.asyncio
    async def test_unsupported_elicitation_returns_none(self):
        """_elicit_city must not raise when elicitation is unsupported."""
        with patch("aareguru_mcp.server.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(
                return_value=[{"city": "bern"}, {"city": "thun"}]
            )
            ctx = _make_ctx(raises=True)
            chosen = await _elicit_city(ctx, "bad-city")
        assert chosen is None


class TestHistoricalDataFallback:
    @pytest.mark.asyncio
    async def test_large_range_proceeds_when_elicitation_unsupported(self):
        """A >90 day range must still return data, not abort, when the
        client can't be asked for confirmation."""
        with patch("aareguru_mcp.tools.get_historical_data") as mock_get:
            mock_get.return_value = {"timeseries": [{"timestamp": 1, "temp": 17.0}]}
            ctx = _make_ctx(raises=True)
            result = await get_historical_data_tool("Bern", "-400 days", "now", ctx)
        assert "error" not in result
        assert result == {"timeseries": [{"timestamp": 1, "temp": 17.0}]}
        mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_large_range_still_aborts_on_explicit_decline(self):
        """A supported client that explicitly declines must still abort —
        only the "can't ask at all" case should proceed automatically."""
        from fastmcp.server.elicitation import DeclinedElicitation

        with patch("aareguru_mcp.tools.get_historical_data") as mock_get:
            ctx = AsyncMock()
            ctx.elicit = AsyncMock(return_value=DeclinedElicitation())
            result = await get_historical_data_tool("Bern", "-400 days", "now", ctx)
        assert result["error"] == "Abgebrochen"
        mock_get.assert_not_called()


class TestFlowDangerLevelFallback:
    @pytest.mark.asyncio
    async def test_high_danger_returns_full_data_when_elicitation_unsupported(self):
        """A dangerous flow level must still return full details, not be
        withheld, when the confirmation gate can't be shown."""
        with patch("aareguru_mcp.server.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_flow_danger_level = AsyncMock(
                return_value={
                    "city": "Bern",
                    "flow": 350.0,
                    "danger_level": 4,
                    "safety_assessment": "High",
                }
            )
            ctx = _make_ctx(raises=True)
            result = await get_flow_danger_level_tool("Bern", ctx)
        assert result["danger_level"] == 4
        assert result["flow"] == 350.0
        assert "warning" not in result


class TestCompleteCheckoutFallback:
    @pytest.mark.asyncio
    async def test_billing_error_returned_unchanged_when_elicitation_unsupported(self):
        """When the billing-address prompt can't be shown, the underlying
        error must still be returned cleanly instead of raising."""
        with patch("aareguru_mcp.server.ShopService") as MockService:
            instance = MockService.return_value
            instance.complete_checkout = AsyncMock(
                return_value={"error": "Billing address is required."}
            )
            ctx = _make_ctx(raises=True)
            result = await complete_checkout_tool("session-123", ctx)
        assert result == {"error": "Billing address is required."}
