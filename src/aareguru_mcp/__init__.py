"""Aareguru MCP Server - Swiss Aare River Data for AI Assistants.

This package provides a Model Context Protocol (MCP) server that exposes
the Aareguru API, enabling AI assistants like Claude to answer questions
about Swiss Aare river conditions, temperatures, flow rates, and safety.
"""

import logging

import structlog

__version__ = "0.1.0"

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
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import AareguruClient
from .config import Settings, get_settings
from .server import app, main, entry_point

__all__ = [
    "AareguruClient",
    "Settings",
    "get_settings",
    "app",
    "main",
    "entry_point",
    "__version__",
]
