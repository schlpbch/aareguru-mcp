"""MCP tools for querying Aareguru data.

Tools allow Claude to dynamically query the Aareguru API based on user requests.
"""

import logging
from datetime import datetime
from typing import Any

from .client import AareguruClient
from .config import get_settings

logger = logging.getLogger(__name__)


def _get_seasonal_advice() -> str:
    """Get contextual advice based on the current season."""
    month = datetime.now().month
    
    if month in [11, 12, 1, 2, 3]:  # Winter
        return "❄️ Winter Season: Water is freezing. Only for experienced ice swimmers. Keep swims very short."
    elif month in [4, 5]:  # Spring
        return "🌱 Spring: Water is still very cold from snowmelt. Wetsuit recommended."
    elif month in [6, 7, 8]:  # Summer
        return "☀️ Summer: Perfect swimming season! Don't forget sunscreen."
    else:  # Autumn (9, 10)
        return "🍂 Autumn: Water is getting colder. Check daylight hours and bring warm clothes."


def _check_safety_warning(flow: float | None, threshold: float | None = 220) -> str | None:
    """Generate a warning if flow is dangerous."""
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


def _get_swiss_german_explanation(text: str | None) -> str | None:
    """Provide context for Swiss German phrases."""
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
    
    # Simple partial match
    for phrase, explanation in phrases.items():
        if phrase.lower() in text.lower():
            return explanation
            
    return None


async def _get_suggestion(current_city: str, current_temp: float | None) -> str | None:
    """Suggest a better city if current one is cold."""
    if current_temp is None or current_temp >= 18.0:
        return None
        
    try:
        # Use a new client instance to avoid connection pool issues
        async with AareguruClient(settings=get_settings()) as suggestion_client:
            all_cities = await suggestion_client.get_cities()
            
            # Find warmest city
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


async def get_current_temperature(city: str = "bern") -> dict[str, Any]:
    """Get current water temperature for a city.
    
    Use this for quick temperature checks and simple 'how warm is the water?' questions.
    Returns temperature in Celsius, Swiss German description (e.g., 'geil aber chli chalt'),
    and swimming suitability.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
         
    Returns:
        Dictionary with temperature data and Swiss German descriptions:
        - temperature: Water temperature in Celsius
        - temperature_prec: Temperature precision/decimal places
        - temperature_text: Swiss German description (e.g., "geil aber chli chalt")
        - temperature_text_short: Short Swiss German description
        - name: City short name
        - longname: City full name
         
    Example:
        >>> result = await get_current_temperature("bern")
        >>> print(f"{result['temperature']}°C - {result['temperature_text']}")
        17.2°C - geil aber chli chalt
    """
    logger.info(f"Getting current temperature for {city}")
    
    async with AareguruClient(settings=get_settings()) as client:
        # Use get_current to get flow data for safety check
        response = await client.get_current(city)
        
        if not response.aare:
            # Fallback to get_today if no aare data (unlikely but safe)
            response = await client.get_today(city)
            temp = response.aare
            text = response.text
            flow = None
        else:
            temp = response.aare.temperature
            text = response.aare.temperature_text
            flow = response.aare.flow
            
        # UX Features
        warning = _check_safety_warning(flow)
        explanation = _get_swiss_german_explanation(text)
        suggestion = await _get_suggestion(city, temp)
        season_advice = _get_seasonal_advice()
        
        result = {
            "city": city,
            "temperature": temp,
            "temperature_text": text,
            "swiss_german_explanation": explanation,
            "name": response.aare.location if (response.aare and hasattr(response.aare, "location")) else response.name,
            "warning": warning,
            "suggestion": suggestion,
            "seasonal_advice": season_advice,
        }
        
        # Add legacy fields for backward compatibility
        if response.aare and hasattr(response.aare, "temperature"):
            result["temperature_prec"] = response.aare.temperature  # Approximate
            result["temperature_text_short"] = response.aare.temperature_text_short
            result["longname"] = response.aare.location_long
        else:
            result["temperature_prec"] = response.aare_prec
            result["temperature_text_short"] = response.text_short
            result["longname"] = response.longname
            
        return result


async def get_current_conditions(city: str = "bern") -> dict[str, Any]:
    """Get complete current conditions for a city.
    
    Use this for safety assessments, 'is it safe to swim?' questions, and when users
    need a complete picture before swimming. This is the most detailed tool - use it
    for contextual and safety-critical queries.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
         
    Returns:
        Dictionary with comprehensive swimming conditions:
        - aare: Nested dict with water data (temperature, flow, height, forecast)
        - weather: Current weather conditions (may be None)
        - forecast: Weather forecast data (may be None)
        
    Example:
        >>> result = await get_current_conditions("bern")
        >>> print(f"Temp: {result['aare']['temperature']}°C")
        >>> print(f"Flow: {result['aare']['flow']} m³/s")
        >>> print(f"2h forecast: {result['aare']['forecast2h_text']}")
    """
    logger.info(f"Getting current conditions for {city}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        
        # Build comprehensive response from nested structure
        result: dict[str, Any] = {
            "city": city,
        }
        
        # Aare data (nested in response.aare)
        if response.aare:
            # UX Features
            warning = _check_safety_warning(response.aare.flow)
            explanation = _get_swiss_german_explanation(response.aare.temperature_text)
            
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
            
        # Add seasonal advice at top level
        result["seasonal_advice"] = _get_seasonal_advice()
        
        # Weather data
        if response.weather:
            result["weather"] = response.weather
        
        # Forecast
        if response.weatherprognosis:
            result["forecast"] = response.weatherprognosis
        
        return result


async def get_historical_data(
    city: str,
    start: str,
    end: str,
) -> dict[str, Any]:
    """Get historical time-series data.
    
    Use this for trend analysis, comparisons with past conditions, and statistical queries.
    Returns hourly data points for temperature and flow.
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten')
        start: Start date/time. Accepts:
               - ISO format: "2024-11-01T00:00:00Z"
               - Unix timestamp: "1698796800"
               - Relative expressions: "-7 days", "-1 week", "-30 days"
               Relative times are calculated from now.
        end: End date/time. Accepts ISO format, Unix timestamp, or "now" for current time.
             Use "now" for most recent data.
         
    Returns:
        Dictionary with time series data containing hourly measurements
         
    Example:
        >>> # Get last week's data
        >>> result = await get_historical_data("bern", "-7 days", "now")
        >>> print(f"Data points: {len(result['timeseries'])}")
        168  # 7 days × 24 hours
        
        >>> # Get specific date range
        >>> result = await get_historical_data(
        ...     "bern",
        ...     "2024-11-01T00:00:00Z",
        ...     "2024-11-07T23:59:59Z"
        ... )
    """
    logger.info(f"Getting historical data for {city} from {start} to {end}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_history(city, start, end)
        return response


async def list_cities() -> list[dict[str, Any]]:
    """Get all available cities with metadata.
    
    Use this for location discovery ('which cities are available?') and for comparing
    temperatures across all cities to find the warmest/coldest spot.
    
    Returns:
        List of city dictionaries with:
        - city: City identifier (use this for other API calls)
        - name: Short city name
        - longname: Full city name
        - coordinates: Geographic coordinates
        - temperature: Current water temperature (useful for comparisons)
         
    Example:
        >>> cities = await list_cities()
        >>> print([c["city"] for c in cities])
        ['bern', 'thun', 'basel', 'olten', ...]
        
        >>> # Find warmest city
        >>> warmest = max(cities, key=lambda c: c['temperature'] or 0)
        >>> print(f"Warmest: {warmest['name']} at {warmest['temperature']}°C")
    """
    logger.info("Listing all cities")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_cities()
        
        # Response is already a list
        return [
            {
                "city": city.city,
                "name": city.name,
                "longname": city.longname,
                "coordinates": city.coordinates,
                "temperature": city.aare,
            }
            for city in response
        ]


async def get_flow_danger_level(city: str = "bern") -> dict[str, Any]:
    """Get current flow rate and BAFU danger assessment.
    
    Use this for safety-critical questions about current strength and swimming danger.
    Returns flow rate in m³/s and safety assessment based on BAFU (Swiss Federal Office
    for the Environment) danger thresholds.
    
    Flow Safety Thresholds:
    - <100 m³/s: Safe - low flow
    - 100-220 m³/s: Moderate - safe for experienced swimmers
    - 220-300 m³/s: Elevated - caution advised
    - 300-430 m³/s: High - dangerous conditions
    - >430 m³/s: Very high - extremely dangerous, avoid swimming
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
         
    Returns:
        Dictionary with flow data and safety assessment:
        - flow: Current flow rate in m³/s
        - flow_text: Human-readable flow description
        - flow_threshold: BAFU danger threshold for this location
        - safety_assessment: Safety recommendation based on current flow
         
    Example:
        >>> result = await get_flow_danger_level("bern")
        >>> print(f"Flow: {result['flow']} m³/s")
        >>> print(f"Safety: {result['safety_assessment']}")
        Flow: 245 m³/s
        Safety: Moderate - safe for experienced swimmers
    """
    logger.info(f"Getting flow danger level for {city}")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        
        if not response.aare:
            return {
                "city": city,
                "flow": None,
                "flow_text": None,
                "safety_assessment": "No data available",
            }
        
        # Determine safety based on flow threshold
        flow = response.aare.flow
        threshold = response.aare.flow_scale_threshold or 220
        
        if flow is None:
            safety = "Unknown - no flow data"
            danger_level = 0
        elif flow < 100:
            safety = "Safe - low flow"
            danger_level = 1
        elif flow < threshold:
            safety = "Moderate - safe for experienced swimmers"
            danger_level = 2
        elif flow < 300:
            safety = "Elevated - caution advised"
            danger_level = 3
        elif flow < 430:
            safety = "High - dangerous conditions"
            danger_level = 4
        else:
            safety = "Very high - extremely dangerous, avoid swimming"
            danger_level = 5
        
        return {
            "city": city,
            "flow": flow,
            "flow_text": response.aare.flow_text,
            "flow_threshold": threshold,
            "safety_assessment": safety,
            "danger_level": danger_level,
        }


async def compare_cities(cities: list[str] | None = None) -> dict[str, Any]:
    """Compare water conditions across multiple cities.
    
    Use this for comparative questions like "which city has the warmest water?",
    "compare Bern and Thun", or "where's the best place to swim today?".
    
    Args:
        cities: List of city identifiers to compare (e.g., ["bern", "thun", "basel"]).
                If None, compares all available cities.
                Use list_cities() to discover available locations.
    
    Returns:
        Dictionary with comparison data:
        - cities: List of city data with temperature, flow, and safety
        - warmest: City with highest temperature
        - coldest: City with lowest temperature
        - safest: City with lowest flow rate (safest swimming)
        - comparison_summary: Human-readable summary
    
    Example:
        >>> # Compare specific cities
        >>> result = await compare_cities(["bern", "thun", "basel"])
        >>> print(f"Warmest: {result['warmest']['name']} at {result['warmest']['temperature']}°C")
        
        >>> # Compare all cities
        >>> result = await compare_cities()
        >>> for city in result['cities']:
        ...     print(f"{city['name']}: {city['temperature']}°C")
    """
    logger.info(f"Comparing cities: {cities or 'all'}")
    
    async with AareguruClient(settings=get_settings()) as client:
        # Get all cities if none specified
        if cities is None:
            all_cities = await client.get_cities()
            cities = [city.city for city in all_cities]
        
        # Fetch data for each city
        city_data = []
        for city in cities:
            try:
                response = await client.get_current(city)
                
                if response.aare:
                    # Determine safety level
                    flow = response.aare.flow
                    threshold = response.aare.flow_scale_threshold or 220
                    
                    if flow is None:
                        safety = "Unknown"
                        danger_level = 0
                    elif flow < 100:
                        safety = "Safe"
                        danger_level = 1
                    elif flow < threshold:
                        safety = "Moderate"
                        danger_level = 2
                    elif flow < 300:
                        safety = "Elevated"
                        danger_level = 3
                    elif flow < 430:
                        safety = "High"
                        danger_level = 4
                    else:
                        safety = "Very High"
                        danger_level = 5
                    
                    city_data.append({
                        "city": city,
                        "name": response.aare.location,
                        "longname": response.aare.location_long,
                        "temperature": response.aare.temperature,
                        "temperature_text": response.aare.temperature_text,
                        "flow": flow,
                        "flow_text": response.aare.flow_text,
                        "safety": safety,
                        "danger_level": danger_level,
                    })
            except Exception as e:
                logger.warning(f"Failed to get data for {city}: {e}")
                continue
        
        if not city_data:
            return {
                "cities": [],
                "warmest": None,
                "coldest": None,
                "safest": None,
                "comparison_summary": "No data available for comparison",
            }
        
        # Find warmest, coldest, and safest
        cities_with_temp = [c for c in city_data if c["temperature"] is not None]
        cities_with_flow = [c for c in city_data if c["flow"] is not None]
        
        warmest = max(cities_with_temp, key=lambda c: c["temperature"]) if cities_with_temp else None
        coldest = min(cities_with_temp, key=lambda c: c["temperature"]) if cities_with_temp else None
        safest = min(cities_with_flow, key=lambda c: c["flow"]) if cities_with_flow else None
        
        # Create summary
        summary_parts = []
        if warmest:
            summary_parts.append(f"Warmest: {warmest['name']} ({warmest['temperature']}°C)")
        if coldest:
            summary_parts.append(f"Coldest: {coldest['name']} ({coldest['temperature']}°C)")
        if safest:
            summary_parts.append(f"Safest: {safest['name']} ({safest['flow']} m³/s)")
            
        # Smart Recommendation
        recommendation = None
        if warmest and safest:
            if warmest == safest:
                recommendation = f"🏆 Best Choice: {warmest['name']} is both the warmest and safest option!"
            elif warmest['danger_level'] <= 2: # Warmest is safe enough
                recommendation = f"🏆 Best Choice: {warmest['name']} is the warmest safe option ({warmest['temperature']}°C)."
            else:
                recommendation = f"⚠️ Trade-off: {warmest['name']} is warmest but has higher flow. {safest['name']} is safer."
        
        return {
            "cities": city_data,
            "warmest": warmest,
            "coldest": coldest,
            "safest": safest,
            "comparison_summary": " | ".join(summary_parts) if summary_parts else "Comparison complete",
            "recommendation": recommendation,
            "seasonal_advice": _get_seasonal_advice(),
        }


async def get_forecast(city: str = "bern", hours: int = 2) -> dict[str, Any]:
    """Get temperature and flow forecast for a city.
    
    Use this for forecast questions like "will the water be warmer tomorrow?",
    "what's the 2-hour forecast?", or "when will it be warmest today?".
    
    Args:
        city: City identifier (e.g., 'bern', 'thun', 'basel', 'olten').
              Use list_cities() to discover available locations.
        hours: Forecast horizon in hours (typically 2). The API provides 2-hour forecasts.
    
    Returns:
        Dictionary with forecast data:
        - current: Current temperature and conditions
        - forecast_2h: Forecasted temperature in 2 hours
        - forecast_text: Human-readable forecast description
        - trend: Temperature trend ("rising", "falling", or "stable")
        - recommendation: Swimming timing recommendation
    
    Example:
        >>> result = await get_forecast("bern")
        >>> print(f"Current: {result['current']['temperature']}°C")
        >>> print(f"In 2h: {result['forecast_2h']}°C")
        >>> print(f"Trend: {result['trend']}")
        Current: 17.2°C
        In 2h: 17.8°C
        Trend: rising
    """
    logger.info(f"Getting forecast for {city} ({hours}h)")
    
    async with AareguruClient(settings=get_settings()) as client:
        response = await client.get_current(city)
        
        if not response.aare:
            return {
                "city": city,
                "current": None,
                "forecast_2h": None,
                "forecast_text": "No data available",
                "trend": "unknown",
                "recommendation": "Unable to provide forecast - no data available",
            }
        
        current_temp = response.aare.temperature
        forecast_temp = response.aare.forecast2h
        forecast_text = response.aare.forecast2h_text
        
        # Determine trend
        if forecast_temp is None or current_temp is None:
            trend = "unknown"
            recommendation = "Forecast data not available"
        else:
            temp_diff = forecast_temp - current_temp
            
            if abs(temp_diff) < 0.3:
                trend = "stable"
                recommendation = "Temperature will remain stable - good time to swim anytime"
            elif temp_diff > 0:
                trend = "rising"
                recommendation = f"Temperature rising by {temp_diff:.1f}°C - water will be warmer in 2 hours"
            else:
                trend = "falling"
                recommendation = f"Temperature falling by {abs(temp_diff):.1f}°C - swim sooner rather than later"
        
        return {
            "city": city,
            "current": {
                "temperature": current_temp,
                "temperature_text": response.aare.temperature_text,
                "flow": response.aare.flow,
            },
            "forecast_2h": forecast_temp,
            "forecast_text": forecast_text,
            "trend": trend,
            "temperature_change": forecast_temp - current_temp if (forecast_temp and current_temp) else None,
            "recommendation": recommendation,
            "seasonal_advice": _get_seasonal_advice(),
        }

