"""Aareguru MCP Server - Swiss Aare River Data for AI Assistants.

This package provides a Model Context Protocol (MCP) server that exposes
the Aareguru API, enabling AI assistants like Claude to answer questions
about Swiss Aare river conditions, temperatures, flow rates, and safety.
"""

import logging

import structlog

__version__ = "1.0.0"
__author__ = "Andreas Schlapbach"
__email__ = "schlpbch@gmail.com"

# Configure structlog at package level
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

# Import after structlog is configured to avoid circular imports
from .client import AareguruClient  # noqa: E402
from .config import Settings, get_settings  # noqa: E402
from .helpers import (  # noqa: E402
    check_safety_warning,
    get_safety_assessment,
    get_seasonal_advice,
    get_swiss_german_explanation,
    get_warmer_suggestion,
)
from .server import app, entry_point, mcp, run_http  # noqa: E402

__all__ = [
    "AareguruClient",
    "Settings",
    "get_settings",
    "app",
    "mcp",
    "run_http",
    "entry_point",
    "check_safety_warning",
    "get_safety_assessment",
    "get_seasonal_advice",
    "get_swiss_german_explanation",
    "get_warmer_suggestion",
    "__version__",
]
