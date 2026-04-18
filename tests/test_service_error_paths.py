"""Tests for service layer error handling and edge cases."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp.service import AareguruService


class TestServiceErrorHandling:
    """Test service error handling."""

    @pytest.mark.asyncio
    async def test_get_current_temperature_with_api_error(self):
        """Test get_current_temperature handles API errors."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get_current.side_effect = Exception("API Error")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            with pytest.raises(Exception, match="API Error"):
                await service.get_current_temperature("Bern")

    @pytest.mark.asyncio
    async def test_get_current_conditions_with_partial_data(self):
        """Test get_current_conditions handles partial data."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.aare = None
            mock_response.weather = None
            mock_response.weatherprognosis = None
            mock_response.sun = None
            mock_client.get_current.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            result = await service.get_current_conditions("Bern")
            assert result["city"] == "Bern"
            assert result.get("aare") is None

    @pytest.mark.asyncio
    async def test_compare_cities_with_empty_list(self):
        """Test compare_cities with empty city list."""
        service = AareguruService()
        result = await service.compare_cities([])
        assert "cities" in result
        assert result["cities"] == []

    @pytest.mark.asyncio
    async def test_get_forecasts_with_single_city(self):
        """Test get_forecasts with single city."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.aare = MagicMock()
            mock_response.aare.temperature = 17.0
            mock_response.aare.forecast2h = 18.0
            mock_response.aare.location = "Bern"
            mock_response.aare.flow = 100.0
            mock_client.get_current.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            result = await service.get_forecasts(["Bern"])
            assert "forecasts" in result
            assert len(result["forecasts"]) == 1

    @pytest.mark.asyncio
    async def test_get_historical_data_with_valid_dates(self):
        """Test get_historical_data with valid date range."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            # Return a mock history response
            mock_response = [
                {"time": 1234567890, "aare": 17.0, "flow": 100.0},
                {"time": 1234567900, "aare": 17.5, "flow": 105.0},
            ]
            mock_client.get_history.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            result = await service.get_historical_data(
                "Bern", "-7 days", "now"
            )
            assert len(result) == 2

    @pytest.mark.asyncio
    async def test_get_cities_list(self):
        """Test get_cities_list returns available cities."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            # Return Pydantic models with model_dump method
            mock_city1 = MagicMock()
            mock_city1.model_dump.return_value = {"city": "Bern", "name": "Bern"}
            mock_city2 = MagicMock()
            mock_city2.model_dump.return_value = {"city": "Thun", "name": "Thun"}
            mock_cities = [mock_city1, mock_city2]
            mock_client.get_cities.return_value = mock_cities
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            result = await service.get_cities_list()
            assert len(result) == 2


class TestServiceDataEnrichment:
    """Test service layer data enrichment."""

    @pytest.mark.asyncio
    async def test_get_current_temperature_enrichment(self):
        """Test temperature enrichment with warnings."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.aare = MagicMock()
            mock_response.aare.temperature = 12.0
            mock_response.aare.temperature_text = "sehr kalt"
            mock_response.aare.flow = 350.0  # High flow - should trigger warning
            mock_response.aare.location = "Bern"
            mock_response.aare.location_long = "Bern, Schönau"
            mock_response.aare.temperature_text_short = "kalt"
            mock_client.get_current.return_value = mock_response
            mock_client.get_today.return_value = None
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            result = await service.get_current_temperature("Bern")
            assert "warning" in result
            assert result["temperature"] == 12.0

    @pytest.mark.asyncio
    async def test_compare_cities_identifies_warmest(self):
        """Test compare_cities identifies warmest city."""
        with patch("aareguru_mcp.service.AareguruClient") as MockClient:
            mock_client = AsyncMock()

            def make_response(city: str):
                response = MagicMock()
                response.aare = MagicMock()
                response.aare.flow = 100.0
                response.aare.location = city
                if city == "Bern":
                    response.aare.temperature = 17.0
                elif city == "Thun":
                    response.aare.temperature = 19.0
                else:
                    response.aare.temperature = 16.0
                return response

            mock_client.get_current = AsyncMock(side_effect=make_response)
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            MockClient.return_value = mock_client

            service = AareguruService()
            result = await service.compare_cities(["Bern", "Thun", "Basel"])
            assert result["warmest"]["city"] == "Thun"
            assert result["coldest"]["city"] == "Basel"
