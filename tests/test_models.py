"""Tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from aareguru_mcp.models import (
    AareData,
    CityInfo,
    CurrentResponse,
    TodayResponse,
    WeatherData,
)


def test_aare_data_valid():
    """Test AareData model with valid data."""
    data = AareData(
        temperature=17.2,
        temperature_text="geil aber chli chalt",
        flow=245.0,
        flow_gefahrenstufe=2,
    )
    assert data.temperature == 17.2
    assert data.flow_gefahrenstufe == 2


def test_aare_data_null_values():
    """Test AareData handles null values."""
    data = AareData(
        temperature=None,
        temperature_text=None,
        flow=None,
        flow_gefahrenstufe=None,
    )
    assert data.temperature is None
    assert data.flow_gefahrenstufe is None


def test_aare_data_danger_level_validation():
    """Test danger level validation (1-5)."""
    # Valid levels
    for level in range(1, 6):
        data = AareData(flow_gefahrenstufe=level)
        assert data.flow_gefahrenstufe == level
    
    # Invalid levels
    with pytest.raises(ValidationError):
        AareData(flow_gefahrenstufe=0)
    
    with pytest.raises(ValidationError):
        AareData(flow_gefahrenstufe=6)


def test_weather_data():
    """Test WeatherData model."""
    data = WeatherData(
        tt=24.0,
        sy=1,
        rr=0.0,
        v=5.2,
    )
    assert data.tt == 24.0
    assert data.sy == 1


def test_city_info_required_fields():
    """Test CityInfo requires city, name, longname."""
    # Valid
    city = CityInfo(
        city="bern",
        name="Bern",
        longname="Bern - Schönau",
    )
    assert city.city == "bern"
    
    # Missing required field
    with pytest.raises(ValidationError):
        CityInfo(name="Bern", longname="Bern - Schönau")


def test_current_response():
    """Test CurrentResponse model."""
    response = CurrentResponse(
        city="bern",
        name="Bern",
        aare=AareData(temperature=17.2),
        weather=WeatherData(tt=24.0),
    )
    assert response.city == "bern"
    assert response.aare.temperature == 17.2
    assert response.weather.tt == 24.0


def test_today_response():
    """Test TodayResponse model."""
    response = TodayResponse(
        city="bern",
        aare=AareData(temperature=17.2, temperature_text="geil aber chli chalt"),
        text="geil aber chli chalt",
    )
    assert response.city == "bern"
    assert response.aare.temperature == 17.2


def test_model_json_schema():
    """Test models generate valid JSON schemas."""
    schema = AareData.model_json_schema()
    assert "properties" in schema
    assert "temperature" in schema["properties"]
    assert "flow_gefahrenstufe" in schema["properties"]


def test_model_serialization():
    """Test model serialization to dict/JSON."""
    data = AareData(temperature=17.2, flow=245.0)
    
    # To dict
    dict_data = data.model_dump()
    assert dict_data["temperature"] == 17.2
    
    # To JSON
    json_data = data.model_dump_json()
    assert "17.2" in json_data
