"""Business logic service layer for Aareguru MCP server.

This module provides the AareguruService class that encapsulates all business
logic for querying and enriching Aare river data. Services act as an intermediary
between MCP tools and the HTTP client, handling:

1. Client lifecycle management (async context managers)
2. Data enrichment using helper functions
3. Error handling and structured logging
4. Response formatting and validation

The service layer enables:
- Code reuse across different API interfaces (MCP, REST, Chat)
- Testability of business logic independent of MCP protocol
- Centralized maintenance of domain logic
- Easier addition of new features without modifying tools
"""

import asyncio
from typing import Any

import structlog

from .client import AareguruClient
from .config import Settings, get_settings
from .helpers import (
    check_safety_warning,
    get_safety_assessment,
    get_seasonal_advice,
    get_swiss_german_explanation,
    get_warmer_suggestion,
)

logger = structlog.get_logger(__name__)


class AareguruService:
    """Business logic service for Aare river data operations.

    This service encapsulates all data fetching and enrichment logic,
    providing methods that map to MCP tools. Each method:
    1. Creates a scoped AareguruClient instance
    2. Fetches data from the API
    3. Enriches with helper functions for UX
    4. Returns structured data

    Usage:
        service = AareguruService()
        result = await service.get_current_temperature("Bern")
    """

    def __init__(self, settings: Settings | None = None):
        """Initialize the service with optional settings override.

        Args:
            settings: Optional Settings instance. If None, uses get_settings().
        """
        self.settings = settings or get_settings()

    async def get_current_temperature(self, city: str = "Bern") -> dict[str, Any]:
        """Get current temperature with enrichment (warnings, suggestions, seasonal advice).

        This method fetches current water temperature and provides:
        - Safety warnings if flow is high
        - Swiss German explanation of temperature description
        - Suggestion to warmer cities if cold
        - Seasonal swimming advice

        Args:
            city: City identifier (e.g., 'Bern', 'Thun', 'olten')

        Returns:
            Dictionary with:
            - temperature: Water temperature in Celsius
            - temperature_text: Swiss German description
            - swiss_german_explanation: English context for Swiss German phrase
            - warning: Safety warning if flow is dangerous (or None)
            - suggestion: Alternative warmer city suggestion (or None)
            - seasonal_advice: Contextual advice based on current month
            - Plus: metadata (city name, precision, short descriptions)

        Raises:
            Any exception from AareguruClient (network, API, validation)
        """
        logger.info("service.get_current_temperature", city=city)

        async with AareguruClient(settings=self.settings) as client:
            # Try current endpoint first (has nested aare data + flow)
            response = await client.get_current(city)

            if not response.aare:
                # Fallback to today endpoint if no aare data
                response = await client.get_today(city)
                temp = response.aare
                text = response.text
                flow = None
            else:
                temp = response.aare.temperature
                text = response.aare.temperature_text
                flow = response.aare.flow

            # Enrich with helpers
            warning = check_safety_warning(flow)
            explanation = get_swiss_german_explanation(text)
            suggestion = await get_warmer_suggestion(city, temp)
            season_advice = get_seasonal_advice()

            result = {
                "city": city,
                "temperature": temp,
                "temperature_text": text,
                "swiss_german_explanation": explanation,
                "name": (
                    response.aare.location
                    if (response.aare and hasattr(response.aare, "location"))
                    else response.name
                ),
                "warning": warning,
                "suggestion": suggestion,
                "seasonal_advice": season_advice,
            }

            # Add legacy fields for backward compatibility
            if response.aare and hasattr(response.aare, "temperature"):
                result["temperature_prec"] = response.aare.temperature
                result["temperature_text_short"] = response.aare.temperature_text_short
                result["longname"] = response.aare.location_long
            else:
                result["temperature_prec"] = response.aare_prec
                result["temperature_text_short"] = response.text_short
                result["longname"] = response.longname

            return result

    async def get_current_conditions(self, city: str = "Bern") -> dict[str, Any]:
        """Get comprehensive current conditions with all enrichment.

        This method is the most detailed, providing:
        - Complete aare water data (temperature, flow, height, forecast)
        - Safety warnings for dangerous conditions
        - Swiss German explanations
        - Current weather conditions (if available)
        - Weather forecast data (if available)
        - Seasonal swimming advice

        Args:
            city: City identifier (e.g., 'Bern', 'Thun', 'olten')

        Returns:
            Dictionary with:
            - aare: Nested dict with temperature, flow, height, forecasts + enrichment
            - seasonal_advice: Month-based swimming guidance
            - weather: Current weather conditions (if available)
            - forecast: Weather forecast data (if available)

        Raises:
            Any exception from AareguruClient
        """
        logger.info("service.get_current_conditions", city=city)

        async with AareguruClient(settings=self.settings) as client:
            response = await client.get_current(city)

            result: dict[str, Any] = {"city": city}

            # Aare data with enrichment
            if response.aare:
                warning = check_safety_warning(response.aare.flow)
                explanation = get_swiss_german_explanation(
                    response.aare.temperature_text
                )

                result["aare"] = {
                    "location": response.aare.location,
                    "location_long": response.aare.location_long,
                    "temperature": response.aare.temperature,
                    "temperature_text": response.aare.temperature_text,
                    "swiss_german_explanation": explanation,
                    "temperature_text_short": response.aare.temperature_text_short,
                    "flow": response.aare.flow,
                    "flow_text": response.aare.flow_text,
                    "height": response.aare.height,
                    "forecast2h": response.aare.forecast2h,
                    "forecast2h_text": response.aare.forecast2h_text,
                    "warning": warning,
                }

            # Add seasonal advice
            result["seasonal_advice"] = get_seasonal_advice()

            # Weather data (optional)
            if response.weather:
                result["weather"] = response.weather

            # Forecast data (optional)
            if response.weatherprognosis:
                result["forecast"] = response.weatherprognosis

            return result

    async def get_historical_data(
        self, city: str, start: str, end: str
    ) -> dict[str, Any]:
        """Get historical time-series data for trend analysis.

        Fetches hourly data points bypassing cache for accurate historical analysis.

        Args:
            city: City identifier
            start: Start date/time as ISO format, Unix timestamp, or relative expression
            end: End date/time (same formats), or "now" for current time

        Returns:
            Dictionary with time series data containing hourly measurements

        Raises:
            Any exception from AareguruClient
        """
        logger.info(
            "service.get_historical_data", city=city, start=start, end=end
        )

        async with AareguruClient(settings=self.settings) as client:
            response = await client.get_history(city, start, end)
            return response

    async def get_flow_danger_level(self, city: str = "Bern") -> dict[str, Any]:
        """Get current flow rate with BAFU safety assessment.

        Uses the get_safety_assessment helper to provide consistent danger level
        calculation across the application (fixes DRY violation).

        BAFU Flow Safety Thresholds:
        - <100 m³/s: Safe - low flow (level 1)
        - 100-220 m³/s: Moderate - safe for experienced swimmers (level 2)
        - 220-300 m³/s: Elevated - caution advised (level 3)
        - 300-430 m³/s: High - dangerous conditions (level 4)
        - >430 m³/s: Very high - extremely dangerous (level 5)

        Args:
            city: City identifier

        Returns:
            Dictionary with:
            - flow: Current flow rate in m³/s (or None)
            - flow_text: Human-readable flow description
            - flow_threshold: BAFU danger threshold for location
            - safety_assessment: Text assessment from helper
            - danger_level: Numeric level 0-5

        Raises:
            Any exception from AareguruClient
        """
        logger.info("service.get_flow_danger_level", city=city)

        async with AareguruClient(settings=self.settings) as client:
            response = await client.get_current(city)

            if not response.aare:
                return {
                    "city": city,
                    "flow": None,
                    "flow_text": None,
                    "safety_assessment": "No data available",
                    "danger_level": 0,
                }

            flow = response.aare.flow
            threshold = response.aare.flow_scale_threshold or 220

            # Use helper function for consistent safety assessment (DRY fix)
            safety, danger_level = get_safety_assessment(flow, threshold)

            return {
                "city": city,
                "flow": flow,
                "flow_text": response.aare.flow_text,
                "flow_threshold": threshold,
                "safety_assessment": safety,
                "danger_level": danger_level,
            }

    async def compare_cities(
        self, cities: list[str] | None = None
    ) -> dict[str, Any]:
        """Compare conditions across multiple cities with parallel fetching.

        Fetches data for multiple cities concurrently and ranks by temperature.
        Handles partial failures gracefully - returns successful cities even if
        some fail.

        Args:
            cities: List of city identifiers. If None, compares all available cities.

        Returns:
            Dictionary with:
            - cities: List of city data sorted by temperature (warmest first)
            - warmest: Best city object (or None)
            - coldest: Coldest city object (or None)
            - safe_count: Number of cities with safe flow (<150 m³/s)
            - total_count: Number of successfully fetched cities
            - requested_count: Total cities requested
            - errors: List of errors for failed cities (or None)

        Raises:
            RuntimeError if ALL cities fail to fetch
        """
        async with AareguruClient(settings=self.settings) as client:
            if cities is None:
                # Get all available cities
                all_cities = await client.get_cities()
                cities = [city.city for city in all_cities]

            logger.info(f"Comparing {len(cities)} cities in parallel: {cities}")

            async def fetch_conditions(city: str):
                logger.info(f"→ Starting fetch for {city}")
                try:
                    result = await client.get_current(city)
                    logger.info(f"✓ Successfully fetched {city}")
                    return {"city": city, "result": result, "error": None}
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    logger.error(f"✗ Failed to fetch {city}: {error_msg}", exc_info=True)
                    return {"city": city, "result": None, "error": error_msg}

            # Fetch with return_exceptions to handle failures gracefully
            results = await asyncio.gather(
                *[fetch_conditions(city) for city in cities], return_exceptions=True
            )

            # Process results
            city_data = []
            errors = []

            for item in results:
                # Handle exceptions that escaped the try/except
                if isinstance(item, Exception):
                    error_msg = f"{type(item).__name__}: {str(item)}"
                    logger.error(
                        f"Unexpected exception in parallel fetch: {error_msg}",
                        exc_info=item,
                    )
                    errors.append({"city": "unknown", "error": error_msg})
                    continue

                city = item["city"]
                result = item["result"]
                error = item["error"]

                if error:
                    errors.append({"city": city, "error": error})
                    continue

                if result is None:
                    errors.append({"city": city, "error": "No data returned"})
                    continue

                if not hasattr(result, "aare") or not result.aare:
                    errors.append({"city": city, "error": "No aare data available"})
                    continue

                try:
                    city_data.append(
                        {
                            "city": city,
                            "temperature": result.aare.temperature,
                            "flow": result.aare.flow,
                            "safe": result.aare.flow < 150 if result.aare.flow else True,
                            "temperature_text": result.aare.temperature_text,
                            "location": result.aare.location,
                        }
                    )
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    logger.error(f"Error processing {city}: {error_msg}", exc_info=True)
                    errors.append({"city": city, "error": error_msg})
                    continue

            # Sort by temperature (warmest first)
            if city_data:
                city_data.sort(key=lambda x: x["temperature"] or 0, reverse=True)

            success_count = len(city_data)
            total_count = len(cities)

            logger.info(
                f"Comparison complete: {success_count}/{total_count} cities succeeded"
            )

            # Raise if ALL cities failed
            if success_count == 0 and total_count > 0:
                error_summary = "; ".join(
                    [f"{e['city']}: {e['error']}" for e in errors[:3]]
                )
                raise RuntimeError(
                    f"Failed to fetch data for all {total_count} cities. "
                    f"Errors: {error_summary}"
                )

            return {
                "cities": city_data,
                "warmest": city_data[0] if city_data else None,
                "coldest": city_data[-1] if city_data else None,
                "safe_count": sum(1 for c in city_data if c["safe"]),
                "total_count": success_count,
                "requested_count": total_count,
                "errors": errors if errors else None,
            }

    async def get_forecasts(self, cities: list[str]) -> dict[str, Any]:
        """Get weather forecasts for multiple cities with parallel fetching.

        Fetches current temperature, 2-hour forecast, and calculates trend for
        each city concurrently. Handles partial failures gracefully.

        Args:
            cities: List of city identifiers

        Returns:
            Dictionary with:
            - forecasts: Mapping of city name to forecast data
                - current: Current temperature
                - forecast_2h: Temperature 2 hours from now
                - trend: One of 'rising', 'falling', 'stable', or 'unknown'
                - change: Temperature difference (forecast - current)
            - success_count: Number of successfully fetched cities
            - requested_count: Total cities requested
            - errors: List of errors (or None if all succeeded)

        Raises:
            RuntimeError if ALL cities fail to fetch
        """
        async with AareguruClient(settings=self.settings) as client:
            logger.info(f"Fetching forecasts for {len(cities)} cities: {cities}")

            async def fetch_forecast(city: str):
                logger.info(f"→ Starting forecast fetch for {city}")
                try:
                    response = await client.get_current(city)
                    if not response.aare:
                        logger.warning(f"No aare data for {city}")
                        return {
                            "city": city,
                            "result": None,
                            "error": "No aare data available",
                        }

                    current = response.aare.temperature
                    forecast_2h = response.aare.forecast2h

                    # Calculate trend
                    if current is None or forecast_2h is None:
                        trend = "unknown"
                    elif forecast_2h > current:
                        trend = "rising"
                    elif forecast_2h < current:
                        trend = "falling"
                    else:
                        trend = "stable"

                    logger.info(f"✓ Successfully fetched forecast for {city}")
                    return {
                        "city": city,
                        "result": {
                            "current": current,
                            "forecast_2h": forecast_2h,
                            "trend": trend,
                            "change": forecast_2h - current
                            if (forecast_2h and current)
                            else None,
                        },
                        "error": None,
                    }
                except Exception as e:
                    error_msg = f"{type(e).__name__}: {str(e)}"
                    logger.error(
                        f"✗ Failed to fetch forecast for {city}: {error_msg}",
                        exc_info=True,
                    )
                    return {"city": city, "result": None, "error": error_msg}

            # Fetch with return_exceptions to handle failures gracefully
            results = await asyncio.gather(
                *[fetch_forecast(city) for city in cities], return_exceptions=True
            )

            forecasts = {}
            errors = []

            for item in results:
                # Handle exceptions that escaped the try/except
                if isinstance(item, Exception):
                    error_msg = f"{type(item).__name__}: {str(item)}"
                    logger.error(
                        f"Unexpected exception in parallel fetch: {error_msg}",
                        exc_info=item,
                    )
                    errors.append({"city": "unknown", "error": error_msg})
                    continue

                city = item["city"]
                result = item["result"]
                error = item["error"]

                if error:
                    errors.append({"city": city, "error": error})
                    continue

                if result is not None:
                    forecasts[city] = result

            success_count = len(forecasts)
            total_count = len(cities)

            logger.info(
                f"Forecast fetch complete: {success_count}/{total_count} cities succeeded"
            )

            # Raise if ALL cities failed
            if success_count == 0 and total_count > 0:
                error_summary = "; ".join(
                    [f"{e['city']}: {e['error']}" for e in errors[:3]]
                )
                raise RuntimeError(
                    f"Failed to fetch forecasts for all {total_count} cities. "
                    f"Errors: {error_summary}"
                )

            return {
                "forecasts": forecasts,
                "success_count": success_count,
                "requested_count": total_count,
                "errors": errors if errors else None,
            }

    async def get_cities_list(self) -> list[dict[str, Any]]:
        """Get list of all available cities.

        Args:
            None

        Returns:
            List of city data dictionaries

        Raises:
            Any exception from AareguruClient
        """
        logger.info("service.get_cities_list")

        async with AareguruClient(settings=self.settings) as client:
            cities = await client.get_cities()
            return [city.model_dump() for city in cities]
