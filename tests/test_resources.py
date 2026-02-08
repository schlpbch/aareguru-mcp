"""Tests for MCP resources."""

import json

import pytest

from aareguru_mcp import resources


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_cities():
    """Test getting cities resource."""
    content = await resources.get_cities()

    assert isinstance(content, str)
    data = json.loads(content)
    # API returns array directly
    assert isinstance(data, list)
    assert len(data) > 0
    assert "city" in data[0]
    assert "name" in data[0]
    assert "aare" in data[0]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_current():
    """Test getting current resource for a city."""
    city = "Bern"
    content = await resources.get_current(city)

    assert isinstance(content, str)
    data = json.loads(content)
    assert isinstance(data, dict)
    # Current endpoint has nested aare object
    assert "aare" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_current_different_city():
    """Test getting current resource for different city."""
    city = "Thun"
    content = await resources.get_current(city)

    assert isinstance(content, str)
    data = json.loads(content)
    assert isinstance(data, dict)
    assert "aare" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_today():
    """Test getting today resource for a city."""
    city = "Bern"
    content = await resources.get_today(city)

    assert isinstance(content, str)
    data = json.loads(content)
    assert isinstance(data, dict)
    # Today endpoint has flat structure
    assert "aare" in data or "text" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_today_different_city():
    """Test getting today resource for different city."""
    city = "Thun"
    content = await resources.get_today(city)

    assert isinstance(content, str)
    data = json.loads(content)
    assert isinstance(data, dict)
    assert "aare" in data or "text" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_cities_returns_valid_json():
    """Test that cities resource returns valid JSON."""
    content = await resources.get_cities()
    data = json.loads(content)

    # Verify structure
    for city in data:
        assert "city" in city
        assert "longname" in city
        assert isinstance(city["aare"], (int, float)) or city["aare"] is None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_current_returns_valid_json():
    """Test that current resource returns valid JSON."""
    content = await resources.get_current("Bern")
    data = json.loads(content)

    # Verify structure
    assert "aare" in data
    assert isinstance(data["aare"], dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_today_returns_valid_json():
    """Test that today resource returns valid JSON."""
    content = await resources.get_today("Bern")
    data = json.loads(content)

    # Verify structure
    assert "aare" in data or "text" in data
