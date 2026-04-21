"""Tests for apps/map.py — covers _safety_color, _safety_label, _build_map_html, and aare_map UI."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from aareguru_mcp.apps.map import (
    _build_map_html,
    _fetch_map_data,
    _safety_color,
    _safety_label,
)

# =============================================================================
# Pure helpers
# =============================================================================


class TestSafetyColor:
    def test_none_returns_gray(self):
        assert _safety_color(None) == "#9ca3af"

    def test_safe_flow(self):
        color = _safety_color(50)
        assert color.startswith("#")
        assert color != "#9ca3af"

    def test_dangerous_flow(self):
        # >430 → last bucket (very high)
        color_high = _safety_color(500)
        color_safe = _safety_color(50)
        assert color_high != color_safe

    def test_boundary_values(self):
        # Test each threshold bracket
        for flow in [0, 99, 100, 150, 220, 250, 300, 400, 430, 431]:
            result = _safety_color(flow)
            assert result.startswith("#"), f"Expected hex for flow={flow}"


class TestSafetyLabel:
    def test_none_returns_unbekannt(self):
        assert _safety_label(None) == "Unbekannt"

    def test_safe(self):
        label = _safety_label(50)
        assert isinstance(label, str)
        assert len(label) > 0

    def test_very_high(self):
        assert _safety_label(500) == "Sehr hoch"

    def test_all_brackets(self):
        for flow in [0, 50, 100, 150, 220, 260, 300, 400, 431]:
            result = _safety_label(flow)
            assert isinstance(result, str)


# =============================================================================
# _build_map_html
# =============================================================================


class TestBuildMapHtml:
    def _sample_cities(self):
        return [
            {
                "city": "bern",
                "name": "Bern",
                "lat": 46.94,
                "lon": 7.44,
                "temp": 18.5,
                "flow": 80.0,
                "desc": "geil aber chli chalt",
                "safety": "Sicher",
                "color": "#22c55e",
            },
            {
                "city": "thun",
                "name": "Thun",
                "lat": 46.76,
                "lon": 7.62,
                "temp": 19.1,
                "flow": None,
                "desc": "",
                "safety": "Unbekannt",
                "color": "#9ca3af",
            },
        ]

    def test_returns_html_string(self):
        html = _build_map_html(self._sample_cities(), None)
        assert isinstance(html, str)
        assert "<!DOCTYPE html>" in html

    def test_contains_leaflet(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "leaflet" in html.lower()

    def test_contains_city_data(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "bern" in html.lower()

    def test_focus_city_embedded(self):
        html = _build_map_html(self._sample_cities(), "bern")
        assert '"bern"' in html

    def test_focus_none_embedded(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "null" in html

    def test_satellite_toggle_present(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "sat-toggle" in html
        assert "Satellit" in html

    def test_esri_satellite_url(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "arcgisonline.com" in html

    def test_carto_base_tiles(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "cartocdn.com" in html

    def test_localstorage_keys(self):
        html = _build_map_html(self._sample_cities(), None)
        assert "aareguru-map-state" in html
        assert "aareguru-map-satellite" in html

    def test_empty_cities(self):
        html = _build_map_html([], None)
        assert isinstance(html, str)
        assert "CITIES" in html


# =============================================================================
# _fetch_map_data
# =============================================================================


class TestFetchMapData:
    @pytest.mark.asyncio
    async def test_returns_tuple(self):
        mock_service = MagicMock()
        mock_service.get_cities_list = AsyncMock(return_value=[{"city": "bern"}])
        mock_service.compare_cities = AsyncMock(
            return_value={"cities": [], "total_count": 1, "safe_count": 1}
        )
        cities, compare = await _fetch_map_data(mock_service)
        assert isinstance(cities, list)
        assert isinstance(compare, dict)

    @pytest.mark.asyncio
    async def test_calls_both_methods(self):
        mock_service = MagicMock()
        mock_service.get_cities_list = AsyncMock(return_value=[])
        mock_service.compare_cities = AsyncMock(return_value={})
        await _fetch_map_data(mock_service)
        mock_service.get_cities_list.assert_called_once()
        mock_service.compare_cities.assert_called_once_with(None)


# =============================================================================
# aare_map UI handler
# =============================================================================


_MOCK_CITIES = [
    {
        "city": "bern",
        "name": "Bern",
        "longname": "Bern",
        "coordinates": {"lat": 46.94, "lon": 7.44},
        "aare": 18.5,
    },
    {
        "city": "thun",
        "name": "Thun",
        "longname": "Thun",
        "coordinates": {"lat": 46.76, "lon": 7.62},
        "aare": 19.1,
    },
    {
        "city": "solothurn",
        "name": "Solothurn",
        "longname": None,
        "coordinates": None,  # no coords → should be skipped
        "aare": None,
    },
]

_MOCK_COMPARE = {
    "cities": [
        {
            "city": "bern",
            "temperature": 18.5,
            "flow": 80.0,
            "temperature_text": "schön",
        },
        {"city": "thun", "temperature": 19.1, "flow": None, "temperature_text": ""},
    ],
    "warmest": {"city": "thun", "location": "Thun", "temperature": 19.1},
    "safe_count": 2,
    "total_count": 2,
}


class TestAareMapUI:
    @pytest.mark.asyncio
    async def test_returns_prefab_app(self):
        from prefab_ui.app import PrefabApp

        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(return_value=_MOCK_CITIES)
            instance.compare_cities = AsyncMock(return_value=_MOCK_COMPARE)

            from aareguru_mcp.apps.map import aare_map

            result = await aare_map(city=None)
            assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_with_focus_city(self):
        from prefab_ui.app import PrefabApp

        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(return_value=_MOCK_CITIES)
            instance.compare_cities = AsyncMock(return_value=_MOCK_COMPARE)

            from aareguru_mcp.apps.map import aare_map

            result = await aare_map(city="bern")
            assert isinstance(result, PrefabApp)

    @pytest.mark.asyncio
    async def test_state_includes_city(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(return_value=_MOCK_CITIES)
            instance.compare_cities = AsyncMock(return_value=_MOCK_COMPARE)

            from aareguru_mcp.apps.map import aare_map

            result = await aare_map(city="bern")
            assert result.state["city"] == "bern"

    @pytest.mark.asyncio
    async def test_state_station_count(self):
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(return_value=_MOCK_CITIES)
            instance.compare_cities = AsyncMock(return_value=_MOCK_COMPARE)

            from aareguru_mcp.apps.map import aare_map

            result = await aare_map()
            # solothurn has no coords → filtered out; bern+thun remain
            assert result.state["total"] == 2

    @pytest.mark.asyncio
    async def test_no_coords_city_skipped(self):
        """Cities without coordinates must not appear in the map."""
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(
                return_value=[{"city": "nocity", "coordinates": None, "aare": None}]
            )
            instance.compare_cities = AsyncMock(
                return_value={
                    "cities": [],
                    "warmest": {},
                    "safe_count": 0,
                    "total_count": 0,
                }
            )

            from aareguru_mcp.apps.map import aare_map

            result = await aare_map()
            assert result.state["total"] == 0

    @pytest.mark.asyncio
    async def test_empty_compare_data(self):
        """Works gracefully when compare_data is mostly empty."""
        with patch("aareguru_mcp.apps.AareguruService") as MockService:
            instance = MockService.return_value
            instance.get_cities_list = AsyncMock(return_value=_MOCK_CITIES[:1])
            instance.compare_cities = AsyncMock(
                return_value={
                    "cities": [],
                    "warmest": None,
                    "safe_count": 0,
                    "total_count": 0,
                }
            )

            from aareguru_mcp.apps.map import aare_map

            result = await aare_map()
            assert result.state["safe_count"] == 0
