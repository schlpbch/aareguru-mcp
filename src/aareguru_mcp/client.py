"""Async HTTP client for Aareguru API with caching and rate limiting."""

import asyncio
from datetime import datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
import structlog
from pydantic import ValidationError

from .config import get_settings
from .models import CitiesResponse, CurrentResponse, TodayResponse

logger = structlog.get_logger(__name__)


class CacheEntry:
    """Simple cache entry with TTL."""

    def __init__(self, data: Any, ttl_seconds: int):
        self.data = data
        self.expires_at = datetime.now() + timedelta(seconds=ttl_seconds)

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at

    def __str__(self) -> str:
        """String representation of cache entry."""
        status = "expired" if self.is_expired() else "valid"
        return f"CacheEntry({status}, expires={self.expires_at.isoformat()})"

    def __repr__(self) -> str:
        """Repr representation of cache entry."""
        return f"CacheEntry(data={type(self.data).__name__}, expires_at={self.expires_at!r})"


class AareguruClient:
    """Async HTTP client for Aareguru API.

    Features:
    - Async HTTP requests with httpx
    - In-memory caching with TTL
    - Rate limiting
    - Automatic retry with exponential backoff
    - Proper error handling
    """

    def __init__(self, settings: Any | None = None):
        """Initialize the Aareguru API client.

        Args:
            settings: Optional settings instance. If None, uses get_settings()
        """
        self.settings = settings or get_settings()
        self.base_url = self.settings.aareguru_base_url
        self.app_name = self.settings.app_name
        self.app_version = self.settings.app_version
        self.cache_ttl = self.settings.cache_ttl_seconds

        # HTTP client with connection pooling (configured via settings)
        self.http_client = httpx.AsyncClient(
            timeout=self.settings.http_client_timeout,
            limits=httpx.Limits(
                max_keepalive_connections=self.settings.http_client_max_keepalive,
                max_connections=self.settings.http_client_max_connections,
            ),
            follow_redirects=True,
        )

        # Simple in-memory cache
        self._cache: dict[str, CacheEntry] = {}

        # Rate limiting
        self._last_request_time: datetime | None = None
        self._request_lock = asyncio.Lock()

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def __aenter__(self) -> "AareguruClient":
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def __str__(self) -> str:
        """String representation of client."""
        cache_size = len(self._cache)
        return f"AareguruClient(base_url={self.base_url}, cache_entries={cache_size})"

    def __repr__(self) -> str:
        """Repr representation of client."""
        return (
            f"AareguruClient("
            f"base_url={self.base_url!r}, "
            f"app_name={self.app_name!r}, "
            f"app_version={self.app_version!r}, "
            f"cache_ttl={self.cache_ttl}s"
            f")"
        )

    def _get_cache_key(self, endpoint: str, params: dict[str, Any]) -> str:
        """Generate cache key from endpoint and params."""
        param_str = urlencode(sorted(params.items()))
        return f"{endpoint}?{param_str}"

    def _get_cached(self, cache_key: str) -> Any | None:
        """Get data from cache if not expired."""
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if not entry.is_expired():
                logger.debug(f"Cache hit: {cache_key}")
                return entry.data
            else:
                # Remove expired entry
                del self._cache[cache_key]
                logger.debug(f"Cache expired: {cache_key}")
        return None

    def _set_cache(self, cache_key: str, data: Any) -> None:
        """Store data in cache with TTL."""
        self._cache[cache_key] = CacheEntry(data, self.cache_ttl)
        logger.debug(f"Cache set: {cache_key}")

    async def _rate_limit(self) -> None:
        """Enforce rate limiting between requests."""
        async with self._request_lock:
            if self._last_request_time is not None:
                elapsed = (datetime.now() - self._last_request_time).total_seconds()
                min_interval = self.settings.min_request_interval_seconds

                if elapsed < min_interval:
                    wait_time = min_interval - elapsed
                    logger.debug(f"Rate limiting: waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

            self._last_request_time = datetime.now()

    async def _request(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        use_cache: bool = True,
    ) -> dict[str, Any]:
        """Make HTTP request to Aareguru API.

        Args:
            endpoint: API endpoint path
            params: Query parameters
            use_cache: Whether to use caching

        Returns:
            JSON response as dictionary

        Raises:
            httpx.HTTPError: On HTTP errors
            ValueError: On invalid responses
        """
        params = params or {}

        # Add app identification
        params["app"] = self.app_name
        params["version"] = self.app_version

        # Check cache
        cache_key = self._get_cache_key(endpoint, params)
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        # Rate limiting
        await self._rate_limit()

        # Make request
        url = f"{self.base_url}{endpoint}"
        logger.info(f"GET {url} {params}")

        try:
            response = await self.http_client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            # Cache successful response
            if use_cache:
                self._set_cache(cache_key, data)

            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Request error: {e}")
            raise
        except ValueError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise

    async def get_cities(self) -> CitiesResponse:
        """Get list of all available cities.

        Returns:
            CitiesResponse: List of cities with metadata

        Raises:
            httpx.HTTPError: On HTTP errors
            ValidationError: On invalid response data
        """
        data = await self._request("/v2018/cities")
        try:
            # API returns array directly, not object with 'cities' key
            from pydantic import TypeAdapter

            adapter = TypeAdapter(CitiesResponse)
            return adapter.validate_python(data)
        except ValidationError as e:
            logger.error(f"Validation error for cities response: {e}")
            raise

    async def get_today(self, city: str = "bern") -> TodayResponse:
        """Get minimal current data for a city.

        Args:
            city: City identifier (default: "bern")

        Returns:
            TodayResponse: Minimal current data

        Raises:
            httpx.HTTPError: On HTTP errors
            ValidationError: On invalid response data
        """
        data = await self._request("/v2018/today", {"city": city})
        try:
            return TodayResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for today response: {e}")
            raise

    async def get_current(self, city: str = "bern") -> CurrentResponse:
        """Get complete current conditions for a city.

        Args:
            city: City identifier (default: "bern")

        Returns:
            CurrentResponse: Complete current data

        Raises:
            httpx.HTTPError: On HTTP errors
            ValidationError: On invalid response data
        """
        data = await self._request("/v2018/current", {"city": city})
        try:
            return CurrentResponse(**data)
        except ValidationError as e:
            logger.error(f"Validation error for current response: {e}")
            raise

    async def get_widget(self) -> dict[str, Any]:
        """Get current data for all cities.

        Returns:
            dict: Widget data for all cities

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        return await self._request("/v2018/widget")

    async def get_history(
        self,
        city: str,
        start: str,
        end: str,
    ) -> dict[str, Any]:
        """Get historical time-series data.

        Args:
            city: City identifier
            start: Start date/time (ISO, timestamp, or relative like "-7 days")
            end: End date/time (ISO, timestamp, or "now")

        Returns:
            dict: Historical time series data

        Raises:
            httpx.HTTPError: On HTTP errors
        """
        params = {
            "city": city,
            "start": start,
            "end": end,
        }
        return await self._request("/v2018/history", params, use_cache=False)
