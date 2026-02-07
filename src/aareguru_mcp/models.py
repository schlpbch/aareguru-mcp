"""Pydantic models for Aareguru API responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AareData(BaseModel):
    """Aare river data model."""

    temperature: float | None = Field(None, description="Water temperature in °C")
    temperature_prec: float | None = Field(None, description="Precise water temperature")
    temperature_text: str | None = Field(None, description="Swiss German temperature description")
    temperature_text_short: str | None = Field(None, description="Short temperature description")
    flow: float | None = Field(None, description="Flow rate in m³/s")
    flow_text: str | None = Field(None, description="Flow description")
    flow_gefahrenstufe: int | None = Field(None, description="BAFU danger level (1-5)", ge=1, le=5)
    flow_scale_threshold: float | None = Field(None, description="Flow scale threshold")
    height: float | None = Field(None, description="Water height/level")


class WeatherData(BaseModel):
    """Weather data model."""

    tt: float | None = Field(None, description="Air temperature in °C")
    tn: float | None = Field(None, description="Minimum air temperature")
    tx: float | None = Field(None, description="Maximum air temperature")
    sy: int | None = Field(None, description="Weather symbol code")
    symt: str | None = Field(None, description="Weather symbol text")
    syt: str | None = Field(None, description="Weather symbol description")
    rr: float | None = Field(None, description="Precipitation amount")
    rrreal: float | None = Field(None, description="Actual precipitation")
    rrisk: float | None = Field(None, description="Precipitation risk/probability")
    v: float | None = Field(None, description="Wind speed")
    n: float | None = Field(None, description="Cloud coverage")
    a: float | None = Field(None, description="Atmospheric pressure")


class SunLocation(BaseModel):
    """Sun location data model."""

    name: str | None = Field(None, description="Location name")
    timeleft: int | None = Field(None, description="Time left in minutes")


class SunData(BaseModel):
    """Sun and daylight data model."""

    suntotal: int | None = Field(None, description="Total sunshine duration in minutes")
    suntotalrelative: float | None = Field(None, description="Relative sunshine percentage")
    ss: str | None = Field(None, description="Sunset time")
    sunlocations: list[SunLocation] | None = Field(None, description="Nearby sunny locations")


class ForecastData(BaseModel):
    """Forecast data model."""

    time: str | None = Field(None, description="Forecast timestamp")
    temperature: float | None = Field(None, description="Forecasted temperature")
    sy: int | None = Field(None, description="Weather symbol")
    tt: float | None = Field(None, description="Air temperature")
    rr: float | None = Field(None, description="Precipitation")


class Position(BaseModel):
    """Geographic position model."""

    lat: float | None = Field(None, description="Latitude")
    lon: float | None = Field(None, description="Longitude")


class CityInfo(BaseModel):
    """City information model."""

    city: str = Field(..., description="City identifier")
    name: str = Field(..., description="Display name")
    longname: str = Field(..., description="Full name")
    url: str | None = Field(None, description="City-specific URL")
    position: Position | None = Field(None, description="Geographic coordinates")


class AareCurrentData(BaseModel):
    """Current Aare data from /current endpoint (nested structure)."""

    location: str | None = Field(None, description="Location name")
    location_long: str | None = Field(None, description="Full location name")
    coordinates: dict[str, float] | None = Field(None, description="Lat/lon")
    forecast: bool | None = Field(None, description="Has forecast")
    timestamp: int | None = Field(None, description="Unix timestamp")
    timestring: str | None = Field(None, description="Time string")
    temperature: float | None = Field(None, description="Water temperature")
    temperature_prec: float | None = Field(None, description="Precise temperature")
    temperature_text: str | None = Field(None, description="Swiss German text")
    temperature_text_short: str | None = Field(None, description="Short text")
    flow: float | None = Field(None, description="Flow rate m³/s")
    flow_text: str | None = Field(None, description="Flow description")
    flow_scale_threshold: float | None = Field(None, description="Flow threshold")
    forecast2h: float | None = Field(None, description="2h forecast temp")
    forecast2h_text: str | None = Field(None, description="2h forecast text")
    height: float | None = Field(None, description="Water height")
    temperature_scale: list[dict[str, Any]] | None = Field(None, description="Temp scale")
    flow_scale: list[dict[str, Any]] | None = Field(None, description="Flow scale")
    historical_temp_max: dict[str, Any] | None = Field(None, description="Historical max")

    def __str__(self) -> str:
        """String representation of Aare current data."""
        temp = f"{self.temperature}°C" if self.temperature else "N/A"
        flow = f"{self.flow} m³/s" if self.flow else "N/A"
        return (
            f"AareCurrentData({self.location}: temp={temp}, "
            f"flow={flow}, text='{self.temperature_text}')"
        )


class CurrentResponse(BaseModel):
    """Complete current conditions response model."""

    aare: AareCurrentData | None = Field(None, description="Aare river data")
    aarepast: list[dict[str, Any]] | None = Field(None, description="Past data points")
    weather: dict[str, Any] | None = Field(None, description="Weather data")
    weatherprognosis: list[dict[str, Any]] | None = Field(None, description="Weather forecast")
    sun: dict[str, Any] | None = Field(None, description="Sun data")

    def __str__(self) -> str:
        """String representation of current response."""
        if self.aare:
            temp = f"{self.aare.temperature}°C" if self.aare.temperature else "N/A"
            flow = f"{self.aare.flow} m³/s" if self.aare.flow else "N/A"
            return f"CurrentResponse({self.aare.location}: temp={temp}, flow={flow})"
        return "CurrentResponse(no data)"


class TodayResponse(BaseModel):
    """Minimal today response model."""

    # Temperature fields (flat, not nested)
    aare: float | None = Field(None, description="Water temperature")
    aare_prec: float | None = Field(None, description="Precise water temperature")
    text: str | None = Field(None, description="Swiss German temperature text")
    text_short: str | None = Field(None, description="Short temperature text")

    # Metadata
    time: int | None = Field(None, description="Timestamp")
    name: str | None = Field(None, description="City name")
    longname: str | None = Field(None, description="Full city name")

    def __str__(self) -> str:
        """String representation of today response."""
        temp = f"{self.aare}°C" if self.aare else "N/A"
        return f"TodayResponse({self.name}: {temp} - {self.text})"


class CityListItem(BaseModel):
    """City list item from cities endpoint."""

    city: str = Field(..., description="City identifier")
    name: str = Field(..., description="Display name")
    longname: str = Field(..., description="Full name")
    coordinates: dict[str, float] | None = Field(None, description="Lat/lon coordinates")
    aare: float | None = Field(None, description="Current temperature")
    aare_prec: float | None = Field(None, description="Precise temperature")
    sy: int | None = Field(None, description="Weather symbol")
    tn: float | None = Field(None, description="Min temperature")
    tx: float | None = Field(None, description="Max temperature")
    forecast: bool | None = Field(None, description="Has forecast")
    time: int | None = Field(None, description="Timestamp")
    url: str | None = Field(None, description="Current URL")
    today: str | None = Field(None, description="Today URL")
    widget: str | None = Field(None, description="Widget URL")
    history: str | None = Field(None, description="History URL")

    def __str__(self) -> str:
        """String representation of city list item."""
        temp = f"{self.aare}°C" if self.aare else "N/A"
        return f"CityListItem({self.name}: {temp})"


# Type alias for cities response (it's just an array)
CitiesResponse = list[CityListItem]


class HistoricalDataPoint(BaseModel):
    """Historical data point model."""

    timestamp: datetime = Field(..., description="Data timestamp")
    temperature: float | None = Field(None, description="Water temperature")
    flow: float | None = Field(None, description="Flow rate")
    air_temperature: float | None = Field(None, description="Air temperature")


class HistoricalResponse(BaseModel):
    """Historical data response model."""

    city: str = Field(..., description="City identifier")
    start: str = Field(..., description="Start date/time")
    end: str = Field(..., description="End date/time")
    timeseries: list[HistoricalDataPoint] = Field(..., description="Time series data")


# ============================================================================
# Tool Response Models
# ============================================================================


class TemperatureToolResponse(BaseModel):
    """Response model for get_current_temperature tool."""

    city: str = Field(..., description="City identifier")
    temperature: float | None = Field(None, description="Water temperature in Celsius")
    temperature_text: str | None = Field(None, description="Swiss German description")
    swiss_german_explanation: str | None = Field(
        None, description="English translation of Swiss German phrase"
    )
    name: str | None = Field(None, description="Location name")
    warning: str | None = Field(None, description="Safety warning if flow is dangerous")
    suggestion: str | None = Field(None, description="Swimming recommendation based on temperature")
    seasonal_advice: str | None = Field(None, description="Season-specific swimming guidance")
    temperature_prec: float | None = Field(None, description="Precise temperature value")
    temperature_text_short: str | None = Field(None, description="Short temperature description")
    longname: str | None = Field(None, description="Full location name")


class AareConditionsData(BaseModel):
    """Aare conditions data for conditions tool response."""

    location: str | None = Field(None, description="Location name")
    location_long: str | None = Field(None, description="Full location name")
    temperature: float | None = Field(None, description="Water temperature in Celsius")
    temperature_text: str | None = Field(None, description="Swiss German temperature description")
    swiss_german_explanation: str | None = Field(None, description="English translation")
    temperature_text_short: str | None = Field(None, description="Short description")
    flow: float | None = Field(None, description="Flow rate in m³/s")
    flow_text: str | None = Field(None, description="Flow description")
    height: float | None = Field(None, description="Water height in meters")
    forecast2h: float | None = Field(None, description="Temperature forecast for 2 hours")
    forecast2h_text: str | None = Field(None, description="Forecast description")
    warning: str | None = Field(None, description="Safety warning if applicable")


class ConditionsToolResponse(BaseModel):
    """Response model for get_current_conditions tool."""

    city: str = Field(..., description="City identifier")
    aare: AareConditionsData | None = Field(None, description="Aare river data")
    seasonal_advice: str | None = Field(None, description="Season-specific guidance")
    weather: dict[str, Any] | None = Field(None, description="Current weather conditions")
    forecast: list[dict[str, Any]] | None = Field(None, description="Weather forecast")


class CityListResponse(BaseModel):
    """Response model for a single city in list_cities tool."""

    city: str = Field(..., description="City identifier")
    name: str = Field(..., description="Display name")
    longname: str = Field(..., description="Full location name")
    coordinates: dict[str, float] | None = Field(
        None, description="Location coordinates with lat/lon"
    )
    temperature: float | None = Field(None, description="Current water temperature in Celsius")


class FlowDangerResponse(BaseModel):
    """Response model for get_flow_danger_level tool."""

    city: str = Field(..., description="City identifier")
    flow: float | None = Field(None, description="Current flow rate in m³/s")
    flow_text: str | None = Field(None, description="Flow description")
    flow_threshold: float | None = Field(None, description="Danger threshold for this location")
    safety_assessment: str = Field(..., description="Safety evaluation")
    danger_level: int | None = Field(None, description="Numeric danger level (1-5)")


class CurrentConditionsData(BaseModel):
    """Current conditions data for forecast tool response."""

    temperature: float | None = Field(None, description="Current water temperature in Celsius")
    temperature_text: str | None = Field(None, description="Swiss German temperature description")
    flow: float | None = Field(None, description="Current flow rate in m³/s")


class ForecastToolResponse(BaseModel):
    """Response model for get_forecast tool."""

    city: str = Field(..., description="City identifier")
    current: CurrentConditionsData | None = Field(None, description="Current conditions")
    forecast_2h: float | None = Field(None, description="Forecasted temperature in 2 hours")
    forecast_text: str | None = Field(None, description="Forecast description")
    trend: str = Field(..., description="Temperature trend (rising/falling/stable/unknown)")
    temperature_change: float | None = Field(
        None, description="Expected temperature change in degrees"
    )
    recommendation: str = Field(..., description="Timing recommendation for swimming")
    seasonal_advice: str | None = Field(None, description="Season-specific guidance")
