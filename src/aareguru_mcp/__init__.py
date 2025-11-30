"""Aareguru MCP Server - Swiss Aare River Data for AI Assistants.

This package provides a Model Context Protocol (MCP) server that exposes
the Aareguru API, enabling AI assistants like Claude to answer questions
about Swiss Aare river conditions, temperatures, flow rates, and safety.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .client import AareguruClient
from .config import Settings, get_settings
from .server import app, main

__all__ = ["AareguruClient", "Settings", "get_settings", "app", "main", "__version__"]
