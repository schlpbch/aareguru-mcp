"""Tests for MCP resources."""

import json

import pytest

from aareguru_mcp import resources


@pytest.mark.asyncio
async def test_list_resources():
    """Test listing all resources."""
    resource_list = await resources.list_resources()
    
    assert len(resource_list) == 4
    
    uris = [str(r.uri) for r in resource_list]  # Convert AnyUrl to string
    assert "aareguru://cities" in uris
    assert "aareguru://widget" in uris
    # Template variables get URL-encoded
    assert any("current" in uri and "city" in uri.lower() for uri in uris)
    assert any("today" in uri and "city" in uri.lower() for uri in uris)


@pytest.mark.asyncio
async def test_list_resources_metadata():
    """Test resource metadata."""
    resource_list = await resources.list_resources()
    
    for resource in resource_list:
        assert str(resource.uri).startswith("aareguru://")  # Convert to string
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
    # API returns array directly
    assert isinstance(data, list)
    assert len(data) > 0
    assert "city" in data[0]


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
    # Current endpoint has nested aare object
    assert "aare" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_read_resource_today_bern():
    """Test reading today resource for Bern."""
    content = await resources.read_resource("aareguru://today/bern")
    
    assert isinstance(content, str)
    data = json.loads(content)
    # Today endpoint has flat structure
    assert "aare" in data or "text" in data


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
