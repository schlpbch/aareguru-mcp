"""Tests for configuration management."""

import pytest
from pydantic import ValidationError

from aareguru_mcp.config import Settings, get_settings


def test_settings_defaults():
    """Test default settings values."""
    settings = Settings()
    assert settings.aareguru_base_url == "https://aareguru.existenz.ch"
    assert settings.app_name == "aareguru-mcp"
    assert settings.cache_ttl_seconds == 120
    assert settings.min_request_interval_seconds == 300
    assert settings.log_level == "INFO"


def test_settings_custom_values():
    """Test settings with custom values."""
    settings = Settings(
        app_name="custom-app",
        cache_ttl_seconds=60,
        log_level="DEBUG",
    )
    assert settings.app_name == "custom-app"
    assert settings.cache_ttl_seconds == 60
    assert settings.log_level == "DEBUG"


def test_settings_validation():
    """Test settings validation."""
    # Valid port
    settings = Settings(http_port=8080)
    assert settings.http_port == 8080
    
    # Invalid port (too high)
    with pytest.raises(ValidationError):
        Settings(http_port=70000)
    
    # Invalid port (too low)
    with pytest.raises(ValidationError):
        Settings(http_port=0)


def test_get_settings_cached():
    """Test that get_settings returns cached instance."""
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2  # Same instance


def test_settings_log_levels():
    """Test valid log levels."""
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        settings = Settings(log_level=level)
        assert settings.log_level == level
