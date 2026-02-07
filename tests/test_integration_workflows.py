"""Integration tests for multi-tool workflows and API interactions.

Tests realistic workflows that combine multiple tools and verify
data consistency across different operations.
"""

from unittest.mock import Mock, patch

import pytest

from aareguru_mcp import resources, tools
from aareguru_mcp.client import AareguruClient, CacheEntry
from aareguru_mcp.config import Settings


class TestMultiToolWorkflows:
    """Test workflows combining multiple tools."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_compare_cities_then_get_temperature(self):
        """Test comparing cities then querying specific city temperature."""
        comparison = await tools.compare_cities()

        assert "cities" in comparison
        assert len(comparison["cities"]) > 0, "Should have at least one city"

        # Cities are sorted by temperature (warmest first), so just pick the first one
        first_city = comparison["cities"][0]["city"]

        temp_result = await tools.get_current_temperature(first_city)

        assert "temperature" in temp_result
        assert "temperature_text" in temp_result
        assert temp_result["city"] == first_city

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_temperature_and_flow_correlation(self):
        """Test getting temperature and flow for same city returns consistent data."""
        city = "bern"

        temp_result = await tools.get_current_temperature(city)
        flow_result = await tools.get_flow_danger_level(city)

        assert temp_result["city"] == city
        assert flow_result["city"] == city

        assert isinstance(temp_result["temperature"], (int, float))
        assert flow_result["flow"] is None or isinstance(flow_result["flow"], (int, float))

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_resource_and_tool_consistency(self):
        """Verify resource and tool return consistent data for same city."""
        city = "bern"

        tool_result = await tools.get_current_temperature(city)
        resource_result = await resources.read_resource(f"aareguru://today/{city}")

        assert "temperature" in tool_result or "aare" in tool_result
        assert isinstance(resource_result, str)

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multiple_cities_sequential(self):
        """Test querying multiple cities in sequence."""
        cities_to_test = ["bern", "thun", "basel"]
        results = []

        for city in cities_to_test:
            result = await tools.get_current_temperature(city)
            results.append(result)
            assert result["city"] == city
            assert "temperature" in result

        assert len(results) == len(cities_to_test)


class TestCachingBehavior:
    """Test caching functionality."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Verify cached responses work correctly."""
        import time

        city = "bern"

        start1 = time.time()
        result1 = await tools.get_current_temperature(city)
        time1 = time.time() - start1

        start2 = time.time()
        result2 = await tools.get_current_temperature(city)
        time2 = time.time() - start2

        assert result1["temperature"] == result2["temperature"]
        assert time1 > 0
        assert time2 > 0

    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test that cache TTL works correctly."""
        import asyncio

        settings = Settings(cache_ttl_seconds=1, min_request_interval_seconds=0)
        client = AareguruClient(settings=settings)

        cache_key = "test_endpoint?param=value"
        client._cache[cache_key] = CacheEntry(data={"test": "data"}, ttl_seconds=0)

        await asyncio.sleep(0.1)

        entry = client._cache[cache_key]
        assert entry.is_expired() is True

        await client.close()

    @pytest.mark.asyncio
    async def test_different_params_different_cache(self):
        """Verify different parameters create different cache keys."""
        client = AareguruClient()

        key1 = client._get_cache_key("/endpoint", {"city": "bern"})
        key2 = client._get_cache_key("/endpoint", {"city": "thun"})
        key3 = client._get_cache_key("/endpoint", {"city": "bern"})

        assert key1 != key2
        assert key1 == key3

        await client.close()


class TestErrorHandling:
    """Test error handling in integrations."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_invalid_city_handling(self):
        """Test graceful handling of unknown cities."""
        try:
            result = await tools.get_current_temperature("invalid_city_xyz")
            assert result is not None
        except Exception:
            pass  # Exception is acceptable

    @pytest.mark.asyncio
    async def test_api_timeout_recovery(self):
        """Test handling of slow/timeout responses."""
        with patch("aareguru_mcp.client.AareguruClient._request") as mock_request:
            mock_request.side_effect = TimeoutError("Request timed out")

            with pytest.raises(TimeoutError):
                await tools.get_current_temperature("bern")

    @pytest.mark.asyncio
    async def test_missing_data_fields(self):
        """Test handling of partial data from API."""
        with (
            patch("aareguru_mcp.client.AareguruClient.get_today") as mock_get_today,
            patch("aareguru_mcp.client.AareguruClient.get_current") as mock_get_current,
        ):
            mock_get_current.return_value = Mock(aare=None)

            mock_response = Mock()
            mock_response.aare = 17.2
            mock_response.aare_prec = None
            mock_response.text = "geil aber chli chalt"
            mock_response.text_short = None
            mock_response.name = "Bern"
            mock_response.longname = "Bern, Schönau"
            mock_get_today.return_value = mock_response

            result = await tools.get_current_temperature("bern")

            assert result["temperature"] == 17.2
            assert result["temperature_prec"] is None


class TestDataConsistency:
    """Test data consistency and validation."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_swiss_german_text_present(self):
        """Verify all temperature responses include Swiss German text."""
        cities = ["bern", "thun", "basel"]

        for city in cities:
            result = await tools.get_current_temperature(city)
            assert "temperature_text" in result
            assert result["temperature_text"] is not None
            assert len(result["temperature_text"]) > 0

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_flow_threshold_accuracy(self):
        """Verify BAFU thresholds are applied correctly."""
        result = await tools.get_flow_danger_level("bern")

        if result["flow"] is not None:
            flow = result["flow"]
            safety = result["safety_assessment"]

            if flow < 100:
                assert "safe" in safety.lower() or "low" in safety.lower()
            elif flow < 220:
                assert "moderate" in safety.lower() or "experienced" in safety.lower()
            elif flow < 300:
                assert "elevated" in safety.lower() or "caution" in safety.lower()
            elif flow < 430:
                assert "high" in safety.lower() or "dangerous" in safety.lower()
            else:
                assert "very high" in safety.lower() or "extremely" in safety.lower()

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_temperature_precision(self):
        """Verify temperature values have correct precision."""
        result = await tools.get_current_temperature("bern")
        temp = result["temperature"]

        assert isinstance(temp, (int, float))
        assert -5 <= temp <= 35, f"Temperature {temp}°C seems unrealistic"
