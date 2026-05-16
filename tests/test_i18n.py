"""Tests for the i18n module and lang= parameter on FastMCPApps."""

from unittest.mock import AsyncMock, patch

import pytest

from aareguru_mcp.apps._i18n import LOCALES, STRINGS, t

# ---------------------------------------------------------------------------
# _i18n core tests
# ---------------------------------------------------------------------------


def test_all_locales_resolve_all_keys() -> None:
    """Every key defined in the German locale must exist in all other locales."""
    de_keys = set(STRINGS["de"].keys())
    for locale in LOCALES:
        locale_keys = set(STRINGS[locale].keys())
        missing = de_keys - locale_keys
        assert not missing, f"Locale '{locale}' is missing keys: {missing}"


def test_fallback_to_german_for_unknown_locale() -> None:
    """t() with an unsupported locale returns the German string."""
    assert t("card_water_temp", "xx") == "Wassertemperatur"
    assert t("safety_safe", "zz") == "Sicher"


def test_fallback_returns_key_when_missing_in_all_locales() -> None:
    """t() returns the raw key when it doesn't exist in any locale."""
    assert t("nonexistent_key_xyz", "en") == "nonexistent_key_xyz"


def test_german_default_lang() -> None:
    """t() defaults to German when no lang is supplied."""
    assert t("page_compare") == "Städtevergleich"


def test_english_translations_spot_check() -> None:
    """Spot-check English translations for critical UI strings."""
    assert t("card_water_temp", "en") == "Water Temperature"
    assert t("safety_safe", "en") == "Safe"
    assert t("safety_very_high", "en") == "Very High"
    assert t("bafu_5_guidance", "en") == "Life-threatening — avoid water"
    assert t("alert_safety_title", "en") == "⚠ Safety Warning"
    assert t("badge_warmest_city", "en") == "WARMEST CITY"


def test_french_translations_spot_check() -> None:
    """Spot-check French translations."""
    assert t("card_water_temp", "fr") == "Température de l'eau"
    assert t("safety_safe", "fr") == "Sûr"
    assert t("bafu_1_label", "fr") == "Absence de danger"
    assert t("page_forecast", "fr") == "Prévision"
    assert t("label_now", "fr") == "Maintenant"


def test_italian_translations_spot_check() -> None:
    """Spot-check Italian translations."""
    assert t("card_water_temp", "it") == "Temperatura dell'acqua"
    assert t("safety_safe", "it") == "Sicuro"
    assert t("bafu_5_label", "it") == "Pericolo molto elevato"
    assert t("page_safety", "it") == "Sicurezza"
    assert t("label_satellite", "it") == "Satellite"


def test_bafu_levels_complete() -> None:
    """All five BAFU levels have label, guidance, and desc in every locale."""
    for lang in LOCALES:
        for lvl in range(1, 6):
            assert t(f"bafu_{lvl}_label", lang), f"Missing bafu_{lvl}_label in {lang}"
            assert t(f"bafu_{lvl}_guidance", lang), f"Missing bafu_{lvl}_guidance in {lang}"
            assert t(f"bafu_{lvl}_desc", lang), f"Missing bafu_{lvl}_desc in {lang}"


# ---------------------------------------------------------------------------
# App UI function lang= parameter tests (smoke tests with mocked service)
# ---------------------------------------------------------------------------

_CURRENT_CONDITIONS = {
    "aare": {
        "temperature": 18.5,
        "flow": 95.0,
        "height": 1.2,
        "location": "Bern",
        "location_long": "Bern",
        "temperature_text": "geil und warm",
        "forecast2h": 18.8,
        "forecast2h_text": None,
        "warning": None,
        "flow_gefahrenstufe": 1,
    },
    "weather": {
        "current": {"tt": 22.0},
        "today": {},
        "forecast": [],
    },
    "sun": {
        "today": {"suntotal": "6h 30m", "sunrelative": 75},
        "sunlocations": [{"name": "Bern", "sunsetlocal": "21:15", "timeleft": 7200}],
    },
    "forecast": [],
    "aarepast": [
        {"time": 1700000000, "aare": 17.5},
        {"time": 1700003600, "aare": 18.0},
    ],
    "seasonal_advice": None,
}

_SERVICE_PATH = "aareguru_mcp.apps.AareguruService"


@pytest.fixture()
def mock_service_conditions() -> AsyncMock:
    service = AsyncMock()
    service.get_current_conditions = AsyncMock(return_value=_CURRENT_CONDITIONS)
    return service


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_conditions_dashboard_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.conditions import conditions_dashboard

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_current_conditions = AsyncMock(
            return_value=_CURRENT_CONDITIONS
        )
        result = await conditions_dashboard(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_temperature_card_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.conditions_temperature import temperature_card

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_current_conditions = AsyncMock(
            return_value=_CURRENT_CONDITIONS
        )
        result = await temperature_card(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_flow_card_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.conditions_flow import flow_card

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_current_conditions = AsyncMock(
            return_value=_CURRENT_CONDITIONS
        )
        result = await flow_card(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_safety_briefing_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.safety import safety_briefing

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_current_conditions = AsyncMock(
            return_value=_CURRENT_CONDITIONS
        )
        result = await safety_briefing(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_forecast_view_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.forecast import forecast_view

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_current_conditions = AsyncMock(
            return_value=_CURRENT_CONDITIONS
        )
        result = await forecast_view(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_intraday_view_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.intraday import intraday_view

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_current_conditions = AsyncMock(
            return_value=_CURRENT_CONDITIONS
        )
        result = await intraday_view(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_historical_chart_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.history import historical_chart

    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.get_historical_data = AsyncMock(return_value=[
            {"time": "2025-01-01T12:00:00", "aare": 15.0, "flow": 80.0},
        ])
        result = await historical_chart(city="Bern", lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_compare_cities_table_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.compare import compare_cities_table

    compare_data = {
        "cities": [
            {"city": "bern", "location": "Bern", "temperature": 18.5,
             "flow": 95.0, "temperature_text": "geil"},
        ],
        "warmest": {"city": "bern", "location": "Bern", "temperature": 18.5},
        "safe_count": 1,
        "total_count": 1,
    }
    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.compare_cities = AsyncMock(return_value=compare_data)
        result = await compare_cities_table(cities=None, lang=lang)
    assert result is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("lang", ["de", "en", "fr", "it"])
async def test_city_finder_view_accepts_lang(lang: str) -> None:
    from aareguru_mcp.apps.city_finder import city_finder_view

    compare_data = {
        "cities": [
            {"city": "bern", "location": "Bern", "temperature": 18.5, "flow": 95.0},
        ],
        "warmest": {"city": "bern", "location": "Bern", "temperature": 18.5},
        "safe_count": 1,
        "total_count": 1,
    }
    with patch(_SERVICE_PATH) as MockService:
        MockService.return_value.compare_cities = AsyncMock(return_value=compare_data)
        result = await city_finder_view(lang=lang)
    assert result is not None
