"""Tests for prompts with typed arguments.

These tests verify that prompts work correctly when called with
boolean, number, and other non-string typed arguments.

This addresses Issue #3 - prompt argument handling with orchestrators.
"""

import pytest

from aareguru_mcp.server import (
    compare_swimming_spots,
    daily_swimming_report,
    mcp,
    weekly_trend_analysis,
)


async def get_prompt_text(prompt, **kwargs) -> str:
    """Render a prompt and extract the text content."""
    arguments = kwargs if kwargs else None
    messages = await prompt.render(arguments=arguments)
    return messages[0].content.text if messages else ""


class TestDailyReportTypedArgs:
    """Test daily_swimming_report with typed arguments."""

    @pytest.mark.asyncio
    async def test_with_boolean_include_forecast_true(self):
        """Test with include_forecast=True (boolean)."""
        result = await get_prompt_text(
            daily_swimming_report, city="Bern", include_forecast=True
        )
        assert "Forecast" in result
        assert "get_forecasts" in result

    @pytest.mark.asyncio
    async def test_with_boolean_include_forecast_false(self):
        """Test with include_forecast=False (boolean)."""
        result = await get_prompt_text(
            daily_swimming_report, city="Bern", include_forecast=False
        )
        # Should not include forecast section
        assert "get_forecasts" not in result

    @pytest.mark.asyncio
    async def test_with_string_city(self):
        """Test with string city parameter."""
        result = await get_prompt_text(
            daily_swimming_report, city="Thun", include_forecast=True
        )
        assert "Thun" in result


class TestCompareSwimmingSpotsTypedArgs:
    """Test compare_swimming_spots with typed arguments."""

    @pytest.mark.asyncio
    async def test_with_float_min_temperature(self):
        """Test with min_temperature as float."""
        result = await get_prompt_text(
            compare_swimming_spots, min_temperature=18.5
        )
        assert "18.5" in result
        assert "temperature >=" in result

    @pytest.mark.asyncio
    async def test_with_int_min_temperature(self):
        """Test with min_temperature as int."""
        result = await get_prompt_text(
            compare_swimming_spots, min_temperature=20
        )
        assert "20" in result

    @pytest.mark.asyncio
    async def test_with_boolean_safety_only_true(self):
        """Test with safety_only=True (boolean)."""
        result = await get_prompt_text(
            compare_swimming_spots, safety_only=True
        )
        assert "safe flow levels" in result.lower()
        assert "150" in result  # Threshold mentioned

    @pytest.mark.asyncio
    async def test_with_boolean_safety_only_false(self):
        """Test with safety_only=False (boolean)."""
        result = await get_prompt_text(
            compare_swimming_spots, safety_only=False
        )
        # Should not have the safety filter instruction
        assert "Only include cities with safe" not in result

    @pytest.mark.asyncio
    async def test_with_multiple_typed_args(self):
        """Test with both float and boolean arguments."""
        result = await get_prompt_text(
            compare_swimming_spots,
            min_temperature=18.0,
            safety_only=True
        )
        assert "18.0" in result
        assert "safe flow levels" in result.lower()

    @pytest.mark.asyncio
    async def test_with_none_min_temperature(self):
        """Test with None for optional min_temperature."""
        result = await get_prompt_text(
            compare_swimming_spots, min_temperature=None, safety_only=False
        )
        # Should not have temperature filter
        assert "temperature >=" not in result


class TestWeeklyTrendAnalysisTypedArgs:
    """Test weekly_trend_analysis with typed arguments."""

    @pytest.mark.asyncio
    async def test_with_int_days(self):
        """Test with days as integer."""
        result = await get_prompt_text(
            weekly_trend_analysis, city="Bern", days=7
        )
        assert "7" in result or "weekly" in result.lower()

    @pytest.mark.asyncio
    async def test_with_different_day_counts(self):
        """Test with different day counts (3, 7, 14)."""
        # 3 days
        result3 = await get_prompt_text(
            weekly_trend_analysis, city="Bern", days=3
        )
        assert "3-day" in result3 or "3" in result3

        # 7 days
        result7 = await get_prompt_text(
            weekly_trend_analysis, city="Bern", days=7
        )
        assert "weekly" in result7.lower() or "7" in result7

        # 14 days
        result14 = await get_prompt_text(
            weekly_trend_analysis, city="Bern", days=14
        )
        assert "14" in result14

    @pytest.mark.asyncio
    async def test_with_string_and_int_args(self):
        """Test with mixed string and int arguments."""
        result = await get_prompt_text(
            weekly_trend_analysis, city="Thun", days=14
        )
        assert "Thun" in result
        assert "14" in result


class TestPromptViaToolManager:
    """Test prompts when accessed via MCP tool manager."""

    @pytest.mark.asyncio
    async def test_compare_spots_via_manager(self):
        """Test compare-swimming-spots via prompt manager."""
        prompt = mcp._prompt_manager._prompts["compare-swimming-spots"]
        messages = await prompt.render(
            arguments={"min_temperature": 18.0, "safety_only": True}
        )
        text = messages[0].content.text
        assert "18.0" in text
        assert "safe" in text.lower()

    @pytest.mark.asyncio
    async def test_weekly_analysis_via_manager(self):
        """Test weekly-trend-analysis via prompt manager."""
        prompt = mcp._prompt_manager._prompts["weekly-trend-analysis"]
        messages = await prompt.render(
            arguments={"city": "Basel", "days": 3}
        )
        text = messages[0].content.text
        assert "Basel" in text
        assert "3" in text

    @pytest.mark.asyncio
    async def test_daily_report_via_manager(self):
        """Test daily-swimming-report via prompt manager."""
        prompt = mcp._prompt_manager._prompts["daily-swimming-report"]
        messages = await prompt.render(
            arguments={"city": "Thun", "include_forecast": False}
        )
        text = messages[0].content.text
        assert "Thun" in text
        assert "get_forecasts" not in text
