"""Configuration management for Aareguru MCP server."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Aareguru API Configuration
    aareguru_base_url: str = Field(
        default="https://aareguru.existenz.ch",
        description="Base URL for Aareguru API",
    )
    app_name: str = Field(
        default="aareguru-mcp",
        description="Application name for API requests",
    )
    app_version: str = Field(
        default="0.1.0",
        description="Application version for API requests",
    )

    # Cache Configuration
    cache_ttl_seconds: int = Field(
        default=120,
        description="Cache TTL in seconds (API recommends 2 minutes)",
        ge=0,
    )

    # Rate Limiting
    min_request_interval_seconds: int = Field(
        default=300,
        description="Minimum interval between requests in seconds (API recommends 5 minutes)",
        ge=0,
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: Literal["text", "json"] = Field(
        default="text",
        description="Log output format",
    )

    # HTTP Server Configuration (Phase 3)
    http_host: str = Field(
        default="0.0.0.0",
        description="HTTP server host",
    )
    http_port: int = Field(
        default=8000,
        description="HTTP server port",
        ge=1,
        le=65535,
    )
    http_workers: int = Field(
        default=4,
        description="Number of HTTP worker processes",
        ge=1,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()
