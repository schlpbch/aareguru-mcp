"""Tests for MCP prompts.

Tests the prompt functions that provide guided interactions for common
swimming-related queries.
"""

import pytest

from aareguru_mcp import prompts

# Use prompt functions directly (FastMCP 3 doesn't expose _prompt_manager)
daily_swimming_report = prompts.daily_swimming_report
compare_swimming_spots = prompts.compare_swimming_spots
weekly_trend_analysis = prompts.weekly_trend_analysis

# ============================================================================
# Helper Functions
# ============================================================================


async def get_prompt_text(prompt_func, **kwargs) -> str:
    """Get prompt text from a prompt function."""
    # In FastMCP 3, prompts are just regular async functions that return strings
    result = await prompt_func(**kwargs)
    return result if isinstance(result, str) else str(result)


# ============================================================================
# Unit Tests - Prompt Registration and Structure
# ============================================================================


class TestPromptRegistration:
    """Test that prompts are properly available."""

    def test_prompts_exist(self):
        """Test that all prompt functions exist and are callable."""
        assert callable(daily_swimming_report)
        assert callable(compare_swimming_spots)
        assert callable(weekly_trend_analysis)

    def test_prompts_are_async(self):
        """Test that prompt functions are async."""
        import inspect

        assert inspect.iscoroutinefunction(daily_swimming_report)
        assert inspect.iscoroutinefunction(compare_swimming_spots)
        assert inspect.iscoroutinefunction(weekly_trend_analysis)


class TestDailySwimmingReportPrompt:
    """Unit tests for daily_swimming_report prompt."""

    @pytest.mark.asyncio
    async def test_returns_string(self):
        """Test that the prompt returns a string."""
        result = await daily_swimming_report()
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_message_has_content(self):
        """Test that message has text content."""
        result = await get_prompt_text(daily_swimming_report)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_default_city_is_bern(self):
        """Test that default city is Bern."""
        result = await get_prompt_text(daily_swimming_report)
        assert "bern" in result.lower()

    @pytest.mark.asyncio
    async def test_custom_city(self):
        """Test that custom city is included in prompt."""
        result = await get_prompt_text(daily_swimming_report, city="Thun")
        assert "thun" in result.lower()

    @pytest.mark.asyncio
    async def test_includes_key_sections(self):
        """Test that prompt includes key sections."""
        result = await get_prompt_text(daily_swimming_report)
        assert "Current Conditions" in result
        assert "Safety" in result
        assert "Forecast" in result
        assert "Recommendation" in result

    @pytest.mark.asyncio
    async def test_mentions_tools(self):
        """Test that prompt mentions the tools to use."""
        result = await get_prompt_text(daily_swimming_report)
        assert "get_current_conditions" in result
        assert "get_flow_danger_level" in result
        assert "get_forecasts" in result

    @pytest.mark.asyncio
    async def test_mentions_swiss_german(self):
        """Test that prompt mentions Swiss German descriptions."""
        result = await get_prompt_text(daily_swimming_report)
        assert "Swiss German" in result

    @pytest.mark.asyncio
    async def test_mentions_danger_warning(self):
        """Test that prompt emphasizes danger warnings."""
        result = await get_prompt_text(daily_swimming_report)
        assert "dangerous" in result.lower()


class TestCompareSwimmingSpotsPrompt:
    """Unit tests for compare_swimming_spots prompt."""

    @pytest.mark.asyncio
    async def test_returns_messages(self):
        """Test that the prompt returns messages."""
        result = await compare_swimming_spots()
        # Prompts return strings in FastMCP 3, not message lists
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_message_has_content(self):
        """Test that message has text content."""
        result = await get_prompt_text(compare_swimming_spots)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_mentions_list_tool(self):
        """Test that prompt mentions the fast comparison tool."""
        result = await get_prompt_text(compare_swimming_spots)
        assert "compare_cities" in result

    @pytest.mark.asyncio
    async def test_includes_key_sections(self):
        """Test that prompt includes key sections."""
        result = await get_prompt_text(compare_swimming_spots)
        assert "Best Choice" in result
        assert "Comparison" in result or "Table" in result
        assert "Safety" in result

    @pytest.mark.asyncio
    async def test_includes_safety_thresholds(self):
        """Test that prompt includes flow thresholds."""
        result = await get_prompt_text(compare_swimming_spots)
        # Should mention safe/caution/dangerous thresholds
        assert "150" in result or "220" in result

    @pytest.mark.asyncio
    async def test_includes_emoji_legend(self):
        """Test that prompt includes emoji indicators."""
        result = await get_prompt_text(compare_swimming_spots)
        assert "🟢" in result or "🟡" in result or "🔴" in result


class TestWeeklyTrendAnalysisPrompt:
    """Unit tests for weekly_trend_analysis prompt."""

    @pytest.mark.asyncio
    async def test_returns_messages(self):
        """Test that the prompt returns messages."""
        result = await weekly_trend_analysis()
        # Prompts return strings in FastMCP 3, not message lists
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_message_has_content(self):
        """Test that message has text content."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_default_city_is_bern(self):
        """Test that default city is Bern."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert "bern" in result.lower()

    @pytest.mark.asyncio
    async def test_custom_city(self):
        """Test that custom city is included in prompt."""
        result = await get_prompt_text(weekly_trend_analysis, city="basel")
        assert "basel" in result.lower()

    @pytest.mark.asyncio
    async def test_mentions_historical_data_tool(self):
        """Test that prompt mentions get_historical_data tool."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert "get_historical_data" in result

    @pytest.mark.asyncio
    async def test_mentions_seven_days(self):
        """Test that prompt specifies 7-day analysis."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert "7" in result or "seven" in result.lower() or "week" in result.lower()

    @pytest.mark.asyncio
    async def test_includes_temperature_trend_section(self):
        """Test that prompt includes temperature trend section."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert "Temperature" in result
        assert "Trend" in result or "trend" in result

    @pytest.mark.asyncio
    async def test_includes_flow_trend_section(self):
        """Test that prompt includes flow trend section."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert "Flow" in result

    @pytest.mark.asyncio
    async def test_includes_outlook_section(self):
        """Test that prompt includes outlook/forecast section."""
        result = await get_prompt_text(weekly_trend_analysis)
        assert "Outlook" in result or "forecast" in result.lower()


# ============================================================================
# Integration Tests - Prompt Workflows
# ============================================================================


class TestPromptIntegration:
    """Integration tests for prompt-based workflows."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_daily_report_prompt_structure(self):
        """Test daily report prompt provides actionable instructions."""
        result = await get_prompt_text(daily_swimming_report, city="Bern")

        # Should guide Claude to use specific tools
        tool_mentions = [
            "get_current_conditions",
            "get_flow_danger_level",
            "get_forecasts",
        ]
        for tool in tool_mentions:
            assert tool in result, f"Prompt should mention {tool}"

        # Should ask for formatted output
        assert "emoji" in result.lower() or "format" in result.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compare_spots_prompt_structure(self):
        """Test compare spots prompt provides actionable instructions."""
        result = await get_prompt_text(compare_swimming_spots)

        # Should guide Claude to use fast parallel comparison tool
        assert "compare_cities" in result

        # Should request structured output
        assert "Table" in result or "ranked" in result.lower()

        # Should include safety context
        assert "Safe" in result or "safe" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_weekly_analysis_prompt_structure(self):
        """Test weekly analysis prompt provides actionable instructions."""
        result = await get_prompt_text(weekly_trend_analysis, city="Thun")

        # Should mention the city
        assert "thun" in result.lower()

        # Should request specific data points
        assert "average" in result.lower() or "highest" in result.lower()

        # Should ask for recommendations
        assert "recommend" in result.lower() or "expect" in result.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_all_prompts_are_distinct(self):
        """Test that each prompt provides unique guidance."""
        daily = await get_prompt_text(daily_swimming_report)
        compare = await get_prompt_text(compare_swimming_spots)
        weekly = await get_prompt_text(weekly_trend_analysis)

        # Each should be unique
        assert daily != compare
        assert compare != weekly
        assert daily != weekly

        # Each should have different primary tool focus
        assert "get_current_conditions" in daily
        assert "compare_cities" in compare  # Fast parallel tool
        assert "get_historical_data" in weekly

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_prompt_city_parameter_variations(self):
        """Test prompts work with different city parameters."""
        cities = ["Bern", "Thun", "basel", "interlaken"]

        for city in cities:
            daily = await get_prompt_text(daily_swimming_report, city=city)
            weekly = await get_prompt_text(weekly_trend_analysis, city=city)

            assert city.lower() in daily.lower(), f"Daily prompt should include {city}"
            assert (
                city.lower() in weekly.lower()
            ), f"Weekly prompt should include {city}"


class TestPromptToolIntegration:
    """Test that prompts reference tools that actually work."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_daily_report_tools_exist_and_work(self):
        """Test that all tools referenced in daily report prompt work."""
        from aareguru_mcp import tools

        # Get the prompt text to verify tool names
        prompt_text = await get_prompt_text(daily_swimming_report, city="Bern")

        # Verify referenced tools exist and work
        assert "get_current_conditions" in prompt_text
        conditions = await tools.get_current_conditions("Bern")
        assert "city" in conditions
        assert conditions["city"] == "Bern"

        assert "get_flow_danger_level" in prompt_text
        danger = await tools.get_flow_danger_level("Bern")
        assert "city" in danger
        assert "danger_level" in danger

        assert "get_forecasts" in prompt_text
        forecast_result = await tools.get_forecasts(["Bern"])
        assert "forecasts" in forecast_result
        assert "Bern" in forecast_result["forecasts"]

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compare_spots_tools_exist_and_work(self):
        """Test that tools referenced in compare prompt work."""
        from aareguru_mcp import tools

        # Get the prompt text to verify tool names
        prompt_text = await get_prompt_text(compare_swimming_spots)

        # Verify referenced fast parallel tool exists
        assert "compare_cities" in prompt_text
        comparison = await tools.compare_cities()
        assert "cities" in comparison
        assert isinstance(comparison["cities"], list)
        assert len(comparison["cities"]) > 0

        # Verify the fast tool can be called
        # (Full test is in test_parallel_tools.py)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_weekly_analysis_tool_exists_and_works(self):
        """Test that get_historical_data tool referenced in prompt works."""
        from datetime import datetime, timedelta

        from aareguru_mcp import tools

        # Get the prompt text to verify tool name
        prompt_text = await get_prompt_text(weekly_trend_analysis, city="bern")

        # Verify referenced tool exists and works
        assert "get_historical_data" in prompt_text

        # Calculate date range for last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        historical = await tools.get_historical_data("bern", start_str, end_str)
        assert "city" in historical
        assert (
            "data" in historical or "data_points" in historical or "error" in historical
        )

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_daily_report_complete_workflow(self):
        """Simulate complete daily report workflow as Claude would execute it."""
        from aareguru_mcp import tools

        city = "Bern"

        # Step 1: Get current conditions (as prompted)
        conditions = await tools.get_current_conditions(city)
        assert conditions["city"] == city
        has_aare_data = "aare" in conditions

        # Step 2: Get flow danger level (as prompted)
        danger = await tools.get_flow_danger_level(city)
        assert danger["city"] == city
        assert "safety_assessment" in danger
        assert "danger_level" in danger

        # Step 3: Get forecast (as prompted)
        forecast_result = await tools.get_forecasts([city])
        assert "forecasts" in forecast_result
        assert city in forecast_result["forecasts"]
        forecast = forecast_result["forecasts"][city]

        # Verify we can build a coherent report
        report_data = {
            "city": city,
            "has_conditions": has_aare_data,
            "is_safe": danger["danger_level"] <= 2,
            "has_forecast": forecast is not None,
        }
        assert report_data["city"] == city

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compare_spots_complete_workflow(self):
        """Simulate complete compare spots workflow as Claude would execute it."""
        from aareguru_mcp import tools

        # Step 1: Compare all cities (as prompted)
        comparison = await tools.compare_cities()
        assert "cities" in comparison
        assert len(comparison["cities"]) > 0

        # Step 2: Get detailed conditions for top cities
        city_data = []
        for city_info in comparison["cities"][:3]:  # Just check first 3 cities
            city = city_info["city"]
            conditions = await tools.get_current_conditions(city)
            assert conditions["city"] == city
            city_data.append(conditions)

        # Verify we can compare data
        assert len(city_data) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_weekly_analysis_complete_workflow(self):
        """Simulate complete weekly analysis workflow as Claude would execute it."""
        from datetime import datetime, timedelta

        from aareguru_mcp import tools

        city = "bern"

        # Step 1: Get historical data for 7 days (as prompted)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        historical = await tools.get_historical_data(city, start_str, end_str)

        # Verify historical data structure
        assert historical["city"] == city
        # Note: historical data might be limited or unavailable
        # The tool should still return a valid response structure
