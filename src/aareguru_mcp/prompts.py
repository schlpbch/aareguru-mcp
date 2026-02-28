"""MCP prompts for querying Aareguru data.

Prompts provide template-based interaction patterns for common use cases.
"""


async def daily_swimming_report(
    city: str = "Bern", include_forecast: bool = True
) -> str:
    """Generates comprehensive daily swimming report combining conditions, safety.

    **Args:**
        city: City to generate the report for (default: `Bern`).
              Use `compare_cities` to discover available locations.
        include_forecast: Whether to include 2-hour forecast in the report (default: `true`)

    **Returns:**
        Prompt template string instructing the LLM to create a formatted report
        with current conditions, safety assessment, forecast, and recommendations.
        The report includes Swiss German descriptions and safety warnings.
    """
    forecast_instruction = (
        "\n3. **Forecast**: Use `get_forecasts` to see how conditions "
        "will change in the next few hours"
        if include_forecast
        else ""
    )

    return f"""Please provide a comprehensive daily swimming report for {city}.

Include:
1. **Current Conditions**: Use `get_current_conditions` to get temperature, \
flow rate, and weather
2. **Safety Assessment**: Use `get_flow_danger_level` to assess if \
swimming is safe{forecast_instruction}
{"4" if include_forecast else "3"}. **Recommendation**: Based on all data, \
give a clear swimming recommendation

Format the report in a friendly way with emojis. Include the Swiss German description if available.
If conditions are dangerous, make this very clear at the top of the report.
If there's a better location nearby, suggest it."""


async def compare_swimming_spots(
    min_temperature: float | None = None, safety_only: bool = False
) -> str:
    """Generates comparison of all swimming locations ranked by temperature and safety.

    **Args:**
        min_temperature: Optional minimum temperature threshold in Celsius (e.g., `18.0`).
                        Filter out cities below this temperature.
        safety_only: Whether to show only safe locations (flow < 150 m³/s). Default: `false`.

    **Returns:**
        Prompt template string instructing the LLM to compare all cities,
        rank them by temperature and safety, and provide a recommendation
        for the best swimming location today.
    """
    filter_instructions = ""
    if min_temperature is not None:
        filter_instructions += (
            f"\n- Only include cities with temperature >= {min_temperature}°C"
        )
    if safety_only:
        filter_instructions += (
            "\n- Only include cities with safe flow levels (< 150 m³/s)"
        )

    # Use fast parallel comparison tool
    return f"""Please compare all available Aare swimming locations.

**Use `compare_cities` tool** - it fetches all city data concurrently for maximum speed.
This is 8-13x faster than sequential requests.

Present:
1. **🏆 Best Choice Today**: The recommended city based on temperature and safety
2. **📊 Comparison Table**: All cities ranked by temperature with safety status
3. **⚠️ Safety Notes**: Any locations to avoid due to high flow{filter_instructions}

Format as a clear, scannable report. Use emojis for quick visual reference:
- 🟢 Safe (flow < 150 m³/s)
- 🟡 Caution (150-220 m³/s)
- 🔴 Dangerous (> 220 m³/s)

End with a personalized recommendation based on conditions."""


async def weekly_trend_analysis(city: str = "Bern", days: int = 7) -> str:
    """Generates trend analysis showing temperature and flow patterns with outlook.

    **Args:**
        city: City to analyze (default: `Bern`). Use `compare_cities` to discover locations.
        days: Number of days to analyze (`3`, `7`, or `14`). Default: `7` days (one week).

    **Returns:**
        Prompt template string instructing the LLM to analyze historical data,
        identify temperature and flow trends, and provide outlook recommendations
        for optimal swimming times.
    """
    period_name = "3-day" if days == 3 else "weekly" if days == 7 else f"{days}-day"

    return f"""Please analyze the {period_name} trends for {city}.

Use `get_historical_data` with days={days} to get the past {days} days of data, then provide:

1. **Temperature Trend**: How has water temperature changed?
   - Highest and lowest temperatures
   - Current vs. {period_name} average
   - Is it warming or cooling?

2. **Flow Trend**: How has the flow rate varied?
   - Any dangerous periods?
   - Current conditions vs. average

3. **Outlook**: Based on trends and current forecast, what should swimmers expect?

Include specific numbers and dates. Make recommendations for the best swimming times."""
