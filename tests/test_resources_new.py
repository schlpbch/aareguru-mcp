"""Tests for new resources: get_forecast, get_history, get_safety_levels, get_thresholds."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp import resources


class TestGetForecast:
    """Test get_forecast resource."""

    @pytest.mark.asyncio
    async def test_returns_weatherprognosis_as_json(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            entry = MagicMock()
            entry.model_dump.return_value = {"time": "2024-01-01T14:00:00Z", "tt": 18.5, "sy": 3, "rr": 0.0, "fff": 12.5}
            mock_response = MagicMock()
            mock_response.weatherprognosis = [entry]
            mock_client.get_current = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await resources.get_forecast("Bern")

            data = json.loads(result)
            assert isinstance(data, list)
            assert len(data) == 1
            assert data[0]["tt"] == 18.5
            assert data[0]["sy"] == 3

    @pytest.mark.asyncio
    async def test_empty_prognosis_returns_empty_list(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.weatherprognosis = None
            mock_client.get_current = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await resources.get_forecast("Thun")

            data = json.loads(result)
            assert data == []

    @pytest.mark.asyncio
    async def test_plain_dict_entries_pass_through(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.weatherprognosis = [{"time": "2024-01-01T14:00:00Z", "tt": 17.5, "sy": 5}]
            mock_client.get_current = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await resources.get_forecast("Olten")

            data = json.loads(result)
            assert data[0]["tt"] == 17.5

    @pytest.mark.asyncio
    async def test_multiple_entries(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            entries = []
            for i in range(5):
                e = MagicMock()
                e.model_dump.return_value = {"tt": 18.0 + i, "sy": 1}
                entries.append(e)
            mock_response = MagicMock()
            mock_response.weatherprognosis = entries
            mock_client.get_current = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await resources.get_forecast("Bern")

            data = json.loads(result)
            assert len(data) == 5


class TestGetHistory:
    """Test get_history resource."""

    @pytest.mark.asyncio
    async def test_returns_history_as_json(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            history_data = {
                "city": "Bern",
                "timeseries": [
                    {"timestamp": 1704067200, "temperature": 16.5, "flow": 95.0},
                    {"timestamp": 1704070800, "temperature": 17.0, "flow": 100.0},
                ],
            }
            mock_client.get_history = AsyncMock(return_value=history_data)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await resources.get_history("Bern", "-7 days", "now")

            data = json.loads(result)
            assert data["city"] == "Bern"
            assert len(data["timeseries"]) == 2
            assert data["timeseries"][0]["temperature"] == 16.5

    @pytest.mark.asyncio
    async def test_passes_params_to_client(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get_history = AsyncMock(return_value={"city": "Thun", "timeseries": []})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            await resources.get_history("Thun", "2024-01-01T00:00:00Z", "2024-01-07T23:59:59Z")

            mock_client.get_history.assert_called_once_with(
                "Thun", "2024-01-01T00:00:00Z", "2024-01-07T23:59:59Z"
            )

    @pytest.mark.asyncio
    async def test_empty_timeseries(self):
        with patch("aareguru_mcp.resources.AareguruClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.get_history = AsyncMock(return_value={"city": "Bern", "timeseries": []})
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            MockClient.return_value = mock_client

            result = await resources.get_history("Bern", "-1 day", "now")

            data = json.loads(result)
            assert data["timeseries"] == []


class TestGetSafetyLevels:
    """Test get_safety_levels static resource."""

    def test_returns_5_levels(self):
        data = json.loads(resources.get_safety_levels())
        assert len(data) == 5

    def test_levels_are_1_through_5(self):
        data = json.loads(resources.get_safety_levels())
        for i, entry in enumerate(data):
            assert entry["level"] == i + 1

    def test_all_required_fields_present(self):
        data = json.loads(resources.get_safety_levels())
        for entry in data:
            assert "level" in entry
            assert "label" in entry
            assert "guidance" in entry
            assert "description" in entry
            assert "flow_range" in entry

    def test_level_1_is_safe(self):
        data = json.loads(resources.get_safety_levels())
        assert "Keine Gefahr" in data[0]["label"]
        assert data[0]["level"] == 1

    def test_level_5_is_life_threatening(self):
        data = json.loads(resources.get_safety_levels())
        assert "Lebensgefahr" in data[4]["guidance"]
        assert data[4]["level"] == 5

    def test_german_umlauts_preserved(self):
        result = resources.get_safety_levels()
        # Should not be ASCII-escaped
        assert "\\u" not in result
        assert "ä" in result or "ss" in result  # Mässige etc.

    def test_returns_valid_json(self):
        result = resources.get_safety_levels()
        assert isinstance(result, str)
        json.loads(result)  # must not raise


class TestGetThresholds:
    """Test get_thresholds static resource."""

    def test_structure(self):
        data = json.loads(resources.get_thresholds())
        assert "flow_zones" in data
        assert "safety_thresholds" in data
        assert "source" in data
        assert "attribution" in data

    def test_five_flow_zones(self):
        data = json.loads(resources.get_thresholds())
        assert len(data["flow_zones"]) == 5

    def test_zone_fields(self):
        data = json.loads(resources.get_thresholds())
        for zone in data["flow_zones"]:
            assert "lo" in zone
            assert "hi" in zone
            assert "label" in zone
            assert "color" in zone

    def test_zone_ranges_correct(self):
        data = json.loads(resources.get_thresholds())
        zones = data["flow_zones"]
        assert zones[0]["lo"] == 0 and zones[0]["hi"] == 100
        assert zones[1]["lo"] == 100 and zones[1]["hi"] == 220
        assert zones[4]["hi"] is None  # Very high has no upper bound

    def test_key_thresholds_present(self):
        data = json.loads(resources.get_thresholds())
        t = data["safety_thresholds"]
        assert "100" in t
        assert "220" in t
        assert "300" in t
        assert "430" in t

    def test_colors_are_hex(self):
        data = json.loads(resources.get_thresholds())
        for zone in data["flow_zones"]:
            assert zone["color"].startswith("#")
            assert len(zone["color"]) == 7

    def test_bafu_source_attribution(self):
        data = json.loads(resources.get_thresholds())
        assert "BAFU" in data["source"]
        assert "aare.guru" in data["attribution"]

    def test_elicitation_threshold_is_90(self):
        data = json.loads(resources.get_thresholds())
        assert data["default_elicitation_threshold_days"] == 90

    def test_returns_valid_json(self):
        result = resources.get_thresholds()
        assert isinstance(result, str)
        json.loads(result)  # must not raise

    def test_german_chars_not_escaped(self):
        result = resources.get_thresholds()
        assert "\\u" not in result
