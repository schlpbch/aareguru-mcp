"""Unit tests for Pydantic models.

Tests data validation, serialization, and schema generation for all API models.
"""

import pytest
from pydantic import ValidationError

from aareguru_mcp.models import (
    AareCurrentData,
    AareData,
    CityInfo,
    CurrentResponse,
    TodayResponse,
    WeatherData,
)


class TestAareData:
    """Test AareData model."""

    def test_valid_data(self):
        """Test AareData with valid data."""
        data = AareData(
            temperature=17.2,
            temperature_text="geil aber chli chalt",
            flow=245.0,
            flow_gefahrenstufe=2,
        )
        assert data.temperature == 17.2
        assert data.flow_gefahrenstufe == 2

    def test_null_values(self):
        """Test AareData handles null values."""
        data = AareData(
            temperature=None,
            temperature_text=None,
            flow=None,
            flow_gefahrenstufe=None,
        )
        assert data.temperature is None
        assert data.flow_gefahrenstufe is None

    def test_danger_level_valid_range(self):
        """Test danger level validation (1-5)."""
        for level in range(1, 6):
            data = AareData(flow_gefahrenstufe=level)
            assert data.flow_gefahrenstufe == level

    def test_danger_level_invalid_zero(self):
        """Test danger level rejects 0."""
        with pytest.raises(ValidationError):
            AareData(flow_gefahrenstufe=0)

    def test_danger_level_invalid_six(self):
        """Test danger level rejects 6."""
        with pytest.raises(ValidationError):
            AareData(flow_gefahrenstufe=6)


class TestWeatherData:
    """Test WeatherData model."""

    def test_valid_data(self):
        """Test WeatherData model."""
        data = WeatherData(
            tt=24.0,
            sy=1,
            rr=0.0,
            v=5.2,
        )
        assert data.tt == 24.0
        assert data.sy == 1


class TestCityInfo:
    """Test CityInfo model."""

    def test_valid_city(self):
        """Test CityInfo with valid data."""
        city = CityInfo(
            city="Bern",
            name="Bern",
            longname="Bern - Schönau",
        )
        assert city.city == "Bern"

    def test_missing_required_field(self):
        """Test CityInfo requires city field."""
        with pytest.raises(ValidationError):
            CityInfo(name="Bern", longname="Bern - Schönau")


class TestCurrentResponse:
    """Test CurrentResponse model."""

    def test_valid_response(self):
        """Test CurrentResponse model."""
        response = CurrentResponse(
            aare=AareCurrentData(
                location="Bärn",
                temperature=17.2,
                flow=245.0,
            ),
        )
        assert response.aare.temperature == 17.2
        assert response.aare.flow == 245.0


class TestTodayResponse:
    """Test TodayResponse model."""

    def test_valid_response(self):
        """Test TodayResponse model."""
        response = TodayResponse(
            aare=17.2,
            aare_prec=17.23,
            text="geil aber chli chalt",
            text_short="chli chalt",
            name="Bärn",
            longname="Bern, Schönau",
        )
        assert response.aare == 17.2
        assert response.text == "geil aber chli chalt"


class TestModelSerialization:
    """Test model serialization."""

    def test_json_schema_generation(self):
        """Test models generate valid JSON schemas."""
        schema = AareData.model_json_schema()
        assert "properties" in schema
        assert "temperature" in schema["properties"]
        assert "flow_gefahrenstufe" in schema["properties"]

    def test_to_dict(self):
        """Test model to dict serialization."""
        data = AareData(temperature=17.2, flow=245.0)
        dict_data = data.model_dump()
        assert dict_data["temperature"] == 17.2

    def test_to_json(self):
        """Test model to JSON serialization."""
        data = AareData(temperature=17.2, flow=245.0)
        json_data = data.model_dump_json()
        assert "17.2" in json_data
