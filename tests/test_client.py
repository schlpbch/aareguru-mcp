"""Tests for Aareguru API client."""

import pytest

from aareguru_mcp.client import AareguruClient, CacheEntry
from aareguru_mcp.models import CitiesResponse, CurrentResponse, TodayResponse


def test_cache_entry_expiration():
    """Test cache entry TTL."""
    import time
    
    entry = CacheEntry("test_data", ttl_seconds=1)
    assert not entry.is_expired()
    
    time.sleep(1.1)
    assert entry.is_expired()


def test_client_initialization(test_settings):
    """Test client initialization."""
    client = AareguruClient(settings=test_settings)
    assert client.base_url == test_settings.aareguru_base_url
    assert client.app_name == test_settings.app_name
    assert client.cache_ttl == test_settings.cache_ttl_seconds


def test_cache_key_generation():
    """Test cache key generation."""
    client = AareguruClient()
    
    key1 = client._get_cache_key("/test", {"city": "bern", "app": "test"})
    key2 = client._get_cache_key("/test", {"app": "test", "city": "bern"})
    
    # Same params in different order should produce same key
    assert key1 == key2


def test_cache_operations():
    """Test cache get/set operations."""
    client = AareguruClient()
    
    # Cache miss
    assert client._get_cached("test_key") is None
    
    # Cache set
    client._set_cache("test_key", {"data": "value"})
    
    # Cache hit
    cached = client._get_cached("test_key")
    assert cached == {"data": "value"}


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test client as async context manager."""
    async with AareguruClient() as client:
        assert client.http_client is not None
    
    # Client should be closed after context
    assert client.http_client.is_closed


# Integration tests (require real API)
@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_cities_real_api(api_client):
    """Test fetching cities from real API."""
    response = await api_client.get_cities()
    
    assert isinstance(response, list)  # CitiesResponse is a list
    assert len(response) > 0
    assert any(c.city == "bern" for c in response)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_today_real_api(api_client):
    """Test fetching today data from real API."""
    response = await api_client.get_today("bern")
    
    assert isinstance(response, TodayResponse)
    # TodayResponse has flat fields, no city field
    assert response.aare is not None or response.text is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_current_real_api(api_client):
    """Test fetching current data from real API."""
    response = await api_client.get_current("bern")
    
    assert isinstance(response, CurrentResponse)
    # CurrentResponse has nested aare object
    assert response.aare is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_caching_works(api_client):
    """Test that caching reduces API calls."""
    # First call - cache miss
    response1 = await api_client.get_today("bern")
    
    # Second call - cache hit (should be instant)
    response2 = await api_client.get_today("bern")
    
    # Should return same data
    assert response1.model_dump() == response2.model_dump()
