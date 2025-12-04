"""Shared helper functions for Aareguru MCP server.

This module contains utility functions used across tools and server components
for safety assessment, seasonal advice, and Swiss German phrase explanations.
"""

from datetime import datetime

from .client import AareguruClient
from .config import get_settings


def get_seasonal_advice() -> str:
    """Get contextual advice based on the current season.

    Returns:
        Seasonal advice string with appropriate emoji and swimming guidance.
    """
    month = datetime.now().month

    if month in [11, 12, 1, 2, 3]:  # Winter
        return (
            "❄️ Winter Season: Water is freezing. "
            "Only for experienced ice swimmers. Keep swims very short."
        )
    elif month in [4, 5]:  # Spring
        return "🌱 Spring: Water is still very cold from snowmelt. Wetsuit recommended."
    elif month in [6, 7, 8]:  # Summer
        return "☀️ Summer: Perfect swimming season! Don't forget sunscreen."
    else:  # Autumn (9, 10)
        return "🍂 Autumn: Water is getting colder. Check daylight hours and bring warm clothes."


def check_safety_warning(flow: float | None, threshold: float | None = 220) -> str | None:
    """Generate a warning if flow rate is dangerous.

    Args:
        flow: Current flow rate in m³/s
        threshold: Custom safety threshold (default: 220 m³/s)

    Returns:
        Warning message string or None if conditions are safe.
    """
    if flow is None:
        return None

    threshold = threshold or 220

    if flow > 430:
        return "⛔ EXTREME DANGER: Flow is very high (>430 m³/s). Swimming is life-threatening."
    elif flow > 300:
        return "⚠️ DANGER: High flow rate (>300 m³/s). Swimming NOT recommended."
    elif flow > threshold:
        return "⚠️ CAUTION: Elevated flow rate. Only for experienced swimmers."

    return None


def get_swiss_german_explanation(text: str | None) -> str | None:
    """Provide context for Swiss German phrases from Aareguru.

    Args:
        text: Text that may contain Swiss German phrases

    Returns:
        Explanation of the phrase in English, or None if no match.
    """
    if not text:
        return None

    phrases = {
        "geil aber chli chalt": "Awesome but a bit cold (typical Bernese understatement)",
        "schön warm": "Nice and warm",
        "arschkalt": "Freezing cold",
        "perfekt": "Perfect conditions",
        "chli chalt": "A bit cold",
        "brrr": "Very cold",
    }

    for phrase, explanation in phrases.items():
        if phrase.lower() in text.lower():
            return explanation

    return None


async def get_warmer_suggestion(current_city: str, current_temp: float | None) -> str | None:
    """Suggest a warmer city if the current one is cold.

    Args:
        current_city: Current city identifier
        current_temp: Current temperature in the city

    Returns:
        Suggestion string or None if no warmer option available.
    """
    if current_temp is None or current_temp >= 18.0:
        return None

    try:
        async with AareguruClient(settings=get_settings()) as client:
            all_cities = await client.get_cities()

            warmest = None
            max_temp = -100.0

            for city in all_cities:
                if city.city != current_city and city.aare is not None:
                    if city.aare > max_temp:
                        max_temp = city.aare
                        warmest = city

            # Suggest if significantly warmer (>1°C difference)
            if warmest and max_temp > (current_temp + 1.0):
                return f"💡 Tip: {warmest.name} is warmer right now ({warmest.aare}°C)"

    except Exception:
        # Fail silently on suggestions
        pass

    return None


def get_safety_assessment(flow: float | None, threshold: float = 220) -> tuple[str, int]:
    """Get safety assessment and danger level from flow rate.

    Args:
        flow: Current flow rate in m³/s
        threshold: Custom threshold for elevated flow warning

    Returns:
        Tuple of (assessment string, danger level 0-5)
    """
    if flow is None:
        return "Unknown - no flow data", 0
    elif flow < 100:
        return "Safe - low flow", 1
    elif flow < threshold:
        return "Moderate - safe for experienced swimmers", 2
    elif flow < 300:
        return "Elevated - caution advised", 3
    elif flow < 430:
        return "High - dangerous conditions", 4
    else:
        return "Very high - extremely dangerous, avoid swimming", 5


# Legacy aliases for backward compatibility
_get_seasonal_advice = get_seasonal_advice
_check_safety_warning = check_safety_warning
_get_swiss_german_explanation = get_swiss_german_explanation
_get_suggestion = get_warmer_suggestion
_get_safety_assessment = get_safety_assessment
