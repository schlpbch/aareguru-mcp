"""Unit tests for configuration management.

Tests Settings validation, defaults, environment variable handling, and caching.
"""

import pytest
from pydantic import ValidationError

from aareguru_mcp.config import Settings, get_settings


class TestSettingsDefaults:
    """Test default settings values."""

    def test_default_base_url(self, monkeypatch):
        """Test default base URL."""
        monkeypatch.delenv("AAREGURU_BASE_URL", raising=False)
        settings = Settings()
        assert settings.aareguru_base_url == "https://aareguru.existenz.ch"

    def test_default_app_name(self, monkeypatch):
        """Test default app name."""
        monkeypatch.delenv("APP_NAME", raising=False)
        settings = Settings()
        assert settings.app_name == "aareguru-mcp"

    def test_default_cache_ttl(self, monkeypatch):
        """Test default cache TTL."""
        monkeypatch.delenv("CACHE_TTL_SECONDS", raising=False)
        settings = Settings()
        assert settings.cache_ttl_seconds == 120

    def test_default_request_interval(self, monkeypatch):
        """Test default request interval."""
        monkeypatch.delenv("MIN_REQUEST_INTERVAL_SECONDS", raising=False)
        settings = Settings()
        assert settings.min_request_interval_seconds == 300

    def test_default_log_level(self, monkeypatch):
        """Test default log level."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        settings = Settings()
        assert settings.log_level == "INFO"


class TestSettingsCustomValues:
    """Test settings with custom values."""

    def test_custom_app_name(self):
        """Test custom app name."""
        settings = Settings(app_name="custom-app")
        assert settings.app_name == "custom-app"

    def test_custom_cache_ttl(self):
        """Test custom cache TTL."""
        settings = Settings(cache_ttl_seconds=60)
        assert settings.cache_ttl_seconds == 60

    def test_custom_log_level(self):
        """Test custom log level."""
        settings = Settings(log_level="DEBUG")
        assert settings.log_level == "DEBUG"


class TestSettingsValidation:
    """Test settings validation."""

    def test_valid_port(self):
        """Test valid port value."""
        settings = Settings(http_port=8080)
        assert settings.http_port == 8080

    def test_invalid_port_too_high(self):
        """Test port validation rejects values above 65535."""
        with pytest.raises(ValidationError):
            Settings(http_port=70000)

    def test_invalid_port_too_low(self):
        """Test port validation rejects values below 1."""
        with pytest.raises(ValidationError):
            Settings(http_port=0)

    def test_valid_log_levels(self):
        """Test all valid log levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level


class TestSettingsCaching:
    """Test settings caching."""

    def test_get_settings_returns_same_instance(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2
