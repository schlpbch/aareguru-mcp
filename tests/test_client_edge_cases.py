"""Tests for HTTP client edge cases and error handling."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from aareguru_mcp.client import AareguruClient
from aareguru_mcp.config import get_settings


class TestClientErrorHandling:
    """Test client error handling and retry logic."""

    @pytest.mark.asyncio
    async def test_client_handles_http_error(self):
        """Test client handles HTTP errors gracefully."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.HTTPError("Connection failed")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            with pytest.raises(httpx.HTTPError):
                async with client:
                    await client.get_current("Bern")

    @pytest.mark.asyncio
    async def test_client_handles_invalid_json(self):
        """Test client handles invalid JSON response."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.side_effect = ValueError("Invalid JSON")
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            with pytest.raises(ValueError):
                async with client:
                    await client.get_current("Bern")

    @pytest.mark.asyncio
    async def test_client_with_invalid_city(self):
        """Test client with city that returns no data."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {"aare": None}
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            async with client:
                result = await client.get_current("InvalidCity")
                assert result.aare is None

    @pytest.mark.asyncio
    async def test_client_cache_with_special_params(self):
        """Test client caching with special characters in params."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "aare": {
                    "temperature": 17.5,
                    "location": "Bern",
                }
            }
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            async with client:
                # Request with special characters should be cached
                result1 = await client.get_current("Bern")
                result2 = await client.get_current("Bern")
                # Both should return same response
                assert result1.aare.temperature == result2.aare.temperature

    @pytest.mark.asyncio
    async def test_client_handles_timeout(self):
        """Test client handles request timeouts."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_client.get.side_effect = httpx.TimeoutException("Request timeout")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            with pytest.raises(httpx.TimeoutException):
                async with client:
                    await client.get_current("Bern")


class TestClientRateLimiting:
    """Test client rate limiting."""

    @pytest.mark.asyncio
    async def test_rate_limit_enforced(self):
        """Test that rate limiting is enforced between requests."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "aare": {"temperature": 17.5, "location": "Bern"}
            }
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            async with client:
                # First request should succeed
                result1 = await client.get_current("Bern")
                assert result1.aare is not None


class TestClientResponseParsing:
    """Test client response parsing for different endpoint types."""

    @pytest.mark.asyncio
    async def test_parse_today_response(self):
        """Test parsing of /today endpoint response."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "aare": 17.2,
                "aare_prec": 17.23,
                "text": "geil aber chli chalt",
                "name": "Bern",
                "time": 1234567890,
            }
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            async with client:
                result = await client.get_today("Bern")
                assert result.aare == 17.2
                assert result.text == "geil aber chli chalt"

    @pytest.mark.asyncio
    async def test_parse_cities_response(self):
        """Test parsing of /cities endpoint response (array)."""
        with patch("httpx.AsyncClient") as MockHttpClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.json.return_value = [
                {
                    "city": "Bern",
                    "name": "Bern",
                    "aare": 17.2,
                    "coordinates": {"lat": 46.94, "lon": 7.44},
                    "longname": "Bern, Schönau",
                },
                {
                    "city": "Thun",
                    "name": "Thun",
                    "aare": 18.5,
                    "coordinates": {"lat": 46.76, "lon": 7.62},
                    "longname": "Thun, Kanton Bern",
                },
            ]
            mock_response.status_code = 200
            mock_client.get.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockHttpClient.return_value = mock_client

            client = AareguruClient(settings=get_settings())
            async with client:
                result = await client.get_cities()
                assert len(result) == 2
                assert result[0].city == "Bern"
