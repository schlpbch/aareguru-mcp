"""Unit tests for Aareguru API client.

Tests client initialization, caching, and basic operations without external API calls.
"""

import time

import pytest

from aareguru_mcp.client import AareguruClient, CacheEntry
from aareguru_mcp.config import Settings


class TestCacheEntry:
    """Test CacheEntry class."""

    def test_not_expired_immediately(self):
        """Test cache entry is not expired immediately."""
        entry = CacheEntry("test_data", ttl_seconds=10)
        assert not entry.is_expired()

    def test_expired_after_ttl(self):
        """Test cache entry expires after TTL."""
        entry = CacheEntry("test_data", ttl_seconds=0)
        time.sleep(0.1)
        assert entry.is_expired()

    def test_stores_data(self):
        """Test cache entry stores data correctly."""
        entry = CacheEntry({"key": "value"}, ttl_seconds=10)
        assert entry.data == {"key": "value"}


class TestClientInitialization:
    """Test client initialization."""

    def test_default_initialization(self):
        """Test client initialization with defaults."""
        client = AareguruClient()
        assert client.base_url is not None
        assert client.app_name is not None

    def test_custom_settings(self, test_settings):
        """Test client initialization with custom settings."""
        client = AareguruClient(settings=test_settings)
        assert client.base_url == test_settings.aareguru_base_url
        assert client.app_name == test_settings.app_name
        assert client.cache_ttl == test_settings.cache_ttl_seconds

    def test_rate_limiting_setting(self):
        """Test rate limiting configuration."""
        settings = Settings(min_request_interval_seconds=1)
        client = AareguruClient(settings=settings)
        assert client.settings.min_request_interval_seconds == 1


class TestCacheKeyGeneration:
    """Test cache key generation."""

    def test_basic_key_generation(self):
        """Test basic cache key generation."""
        client = AareguruClient()
        key = client._get_cache_key("/test", {"city": "Bern"})
        assert key is not None
        assert len(key) > 0

    def test_same_params_same_key(self):
        """Test same params produce same key regardless of order."""
        client = AareguruClient()
        key1 = client._get_cache_key("/test", {"city": "Bern", "app": "test"})
        key2 = client._get_cache_key("/test", {"app": "test", "city": "Bern"})
        assert key1 == key2

    def test_different_params_different_key(self):
        """Test different params produce different keys."""
        client = AareguruClient()
        key1 = client._get_cache_key("/endpoint", {"city": "Bern"})
        key2 = client._get_cache_key("/endpoint", {"city": "Thun"})
        assert key1 != key2


class TestCacheOperations:
    """Test cache get/set operations."""

    def test_cache_miss_returns_none(self):
        """Test cache miss returns None."""
        client = AareguruClient()
        assert client._get_cached("nonexistent_key") is None

    def test_cache_set_and_get(self):
        """Test cache set then get."""
        client = AareguruClient()
        client._set_cache("test_key", {"data": "value"})
        cached = client._get_cached("test_key")
        assert cached == {"data": "value"}

    def test_cache_clear(self):
        """Test cache clearing."""
        client = AareguruClient()
        client._cache["test_key"] = CacheEntry({"data": "test"}, ttl_seconds=10)
        assert len(client._cache) > 0
        client._cache.clear()
        assert len(client._cache) == 0


class TestContextManager:
    """Test async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager_opens_client(self):
        """Test context manager opens HTTP client."""
        async with AareguruClient() as client:
            assert client.http_client is not None

    @pytest.mark.asyncio
    async def test_context_manager_closes_client(self):
        """Test context manager closes HTTP client."""
        async with AareguruClient() as client:
            pass
        assert client.http_client.is_closed
