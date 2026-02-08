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
        default="4.0.0",
        description="Application version for API requests",
    )

    # Cache Configuration
    cache_ttl_seconds: int = Field(
        default=120,
        description="Cache TTL in seconds (API recommends 2 minutes)",
        ge=0,
    )

    # Rate Limiting
    min_request_interval_seconds: float = Field(
        default=0.1,
        description="Minimum interval between requests in seconds (0.1s default for parallel support)",
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

    # HTTP Client Configuration
    http_client_timeout: float = Field(
        default=30.0,
        description="HTTP client timeout in seconds",
        ge=1.0,
    )
    http_client_max_keepalive: int = Field(
        default=20,
        description="Maximum number of keepalive connections",
        ge=1,
    )
    http_client_max_connections: int = Field(
        default=100,
        description="Maximum number of total connections",
        ge=1,
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

    # HTTP Server Security
    api_key_required: bool = Field(
        default=False,
        description="Require API key authentication for HTTP endpoints",
    )
    api_keys: str = Field(
        default="",
        description="Comma-separated list of valid API keys",
    )

    # CORS Configuration
    cors_origins: str = Field(
        default="*",
        description="Comma-separated list of allowed CORS origins (* for all)",
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60,
        description="Maximum requests per minute per IP address",
        ge=1,
    )

    # SSE Transport Configuration
    sse_session_timeout_seconds: int = Field(
        default=3600,
        description="SSE session timeout in seconds (default: 1 hour)",
        ge=60,
    )
    sse_cleanup_interval_seconds: int = Field(
        default=300,
        description="Interval for cleaning up stale SSE sessions (default: 5 minutes)",
        ge=60,
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Returns:
        Settings: Application settings
    """
    return Settings()
