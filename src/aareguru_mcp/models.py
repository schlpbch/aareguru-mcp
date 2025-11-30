"""Pydantic models for Aareguru API responses."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class AareData(BaseModel):
    """Aare river data model."""

    temperature: Optional[float] = Field(None, description="Water temperature in °C")
    temperature_prec: Optional[float] = Field(None, description="Precise water temperature")
    temperature_text: Optional[str] = Field(None, description="Swiss German temperature description")
    temperature_text_short: Optional[str] = Field(None, description="Short temperature description")
    flow: Optional[float] = Field(None, description="Flow rate in m³/s")
    flow_text: Optional[str] = Field(None, description="Flow description")
    flow_gefahrenstufe: Optional[int] = Field(None, description="BAFU danger level (1-5)", ge=1, le=5)
    flow_scale_threshold: Optional[float] = Field(None, description="Flow scale threshold")
    height: Optional[float] = Field(None, description="Water height/level")


class WeatherData(BaseModel):
    """Weather data model."""

    tt: Optional[float] = Field(None, description="Air temperature in °C")
    tn: Optional[float] = Field(None, description="Minimum air temperature")
    tx: Optional[float] = Field(None, description="Maximum air temperature")
    sy: Optional[int] = Field(None, description="Weather symbol code")
    symt: Optional[str] = Field(None, description="Weather symbol text")
    syt: Optional[str] = Field(None, description="Weather symbol description")
    rr: Optional[float] = Field(None, description="Precipitation amount")
    rrreal: Optional[float] = Field(None, description="Actual precipitation")
    rrisk: Optional[float] = Field(None, description="Precipitation risk/probability")
    v: Optional[float] = Field(None, description="Wind speed")
    n: Optional[float] = Field(None, description="Cloud coverage")
    a: Optional[float] = Field(None, description="Atmospheric pressure")


class SunLocation(BaseModel):
    """Sun location data model."""

    name: Optional[str] = Field(None, description="Location name")
    timeleft: Optional[int] = Field(None, description="Time left in minutes")


class SunData(BaseModel):
    """Sun and daylight data model."""

    suntotal: Optional[int] = Field(None, description="Total sunshine duration in minutes")
    suntotalrelative: Optional[float] = Field(None, description="Relative sunshine percentage")
    ss: Optional[str] = Field(None, description="Sunset time")
    sunlocations: Optional[list[SunLocation]] = Field(None, description="Nearby sunny locations")


class ForecastData(BaseModel):
    """Forecast data model."""

    time: Optional[str] = Field(None, description="Forecast timestamp")
    temperature: Optional[float] = Field(None, description="Forecasted temperature")
    sy: Optional[int] = Field(None, description="Weather symbol")
    tt: Optional[float] = Field(None, description="Air temperature")
    rr: Optional[float] = Field(None, description="Precipitation")


class Position(BaseModel):
    """Geographic position model."""

    lat: Optional[float] = Field(None, description="Latitude")
    lon: Optional[float] = Field(None, description="Longitude")


class CityInfo(BaseModel):
    """City information model."""

    city: str = Field(..., description="City identifier")
    name: str = Field(..., description="Display name")
    longname: str = Field(..., description="Full name")
    url: Optional[str] = Field(None, description="City-specific URL")
    position: Optional[Position] = Field(None, description="Geographic coordinates")


class CurrentResponse(BaseModel):
    """Complete current conditions response model."""

    city: str = Field(..., description="City identifier")
    name: Optional[str] = Field(None, description="City name")
    longname: Optional[str] = Field(None, description="Full city name")
    url: Optional[str] = Field(None, description="City URL")
    aare: Optional[AareData] = Field(None, description="Aare river data")
    weather: Optional[WeatherData] = Field(None, description="Weather data")
    sun: Optional[SunData] = Field(None, description="Sun and daylight data")
    forecast: Optional[list[ForecastData]] = Field(None, description="Weather forecasts")
    forecast2h: Optional[ForecastData] = Field(None, description="2-hour forecast")
    today: Optional[dict[str, Any]] = Field(None, description="Today's summary")
    time: Optional[str] = Field(None, description="Measurement timestamp")
    historical_temp_max: Optional[float] = Field(None, description="Historical maximum temperature")


class TodayResponse(BaseModel):
    """Minimal today response model."""

    city: str = Field(..., description="City identifier")
    aare: Optional[AareData] = Field(None, description="Aare river data")
    text: Optional[str] = Field(None, description="Temperature text")
    text_short: Optional[str] = Field(None, description="Short temperature text")


class CitiesResponse(BaseModel):
    """Cities list response model."""

    cities: list[CityInfo] = Field(..., description="List of available cities")


class HistoricalDataPoint(BaseModel):
    """Historical data point model."""

    timestamp: datetime = Field(..., description="Data timestamp")
    temperature: Optional[float] = Field(None, description="Water temperature")
    flow: Optional[float] = Field(None, description="Flow rate")
    air_temperature: Optional[float] = Field(None, description="Air temperature")


class HistoricalResponse(BaseModel):
    """Historical data response model."""

    city: str = Field(..., description="City identifier")
    start: str = Field(..., description="Start date/time")
    end: str = Field(..., description="End date/time")
    timeseries: list[HistoricalDataPoint] = Field(..., description="Time series data")
