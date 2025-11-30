"""Tests for MCP resources."""

import json

import pytest

from aareguru_mcp import resources


@pytest.mark.asyncio
async def test_list_resources():
    """Test listing all resources."""
    resource_list = await resources.list_resources()
    
    assert len(resource_list) == 4
    
    uris = [r.uri for r in resource_list]
    assert "aareguru://cities" in uris
    assert "aareguru://widget" in uris
    assert "aareguru://current/{city}" in uris
    assert "aareguru://today/{city}" in uris


@pytest.mark.asyncio
async def test_list_resources_metadata():
    """Test resource metadata."""
    resource_list = await resources.list_resources()
    
    for resource in resource_list:
        assert resource.uri.startswith("aareguru://")
        assert resource.name
        assert resource.mimeType == "application/json"
        assert resource.description


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_resource_cities():
    """Test reading cities resource."""
    content = await resources.read_resource("aareguru://cities")
    
    assert isinstance(content, str)
    data = json.loads(content)
    assert "cities" in data
    assert len(data["cities"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_resource_widget():
    """Test reading widget resource."""
    content = await resources.read_resource("aareguru://widget")
    
    assert isinstance(content, str)
    data = json.loads(content)
    assert isinstance(data, dict)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_resource_current_bern():
    """Test reading current resource for Bern."""
    content = await resources.read_resource("aareguru://current/bern")
    
    assert isinstance(content, str)
    data = json.loads(content)
    assert data["city"] == "bern"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_resource_today_bern():
    """Test reading today resource for Bern."""
    content = await resources.read_resource("aareguru://today/bern")
    
    assert isinstance(content, str)
    data = json.loads(content)
    assert data["city"] == "bern"


@pytest.mark.asyncio
async def test_read_resource_invalid_uri():
    """Test error handling for invalid URI."""
    with pytest.raises(ValueError, match="Invalid URI scheme"):
        await resources.read_resource("http://invalid")


@pytest.mark.asyncio
async def test_read_resource_unknown_path():
    """Test error handling for unknown resource path."""
    with pytest.raises(ValueError, match="Unknown resource path"):
        await resources.read_resource("aareguru://unknown")


@pytest.mark.asyncio
async def test_read_resource_malformed_uri():
    """Test error handling for malformed URI."""
    with pytest.raises(ValueError):
        await resources.read_resource("aareguru://current")  # Missing city
