"""MCP resources for Aareguru data.

Resources provide read-only access to Aareguru data that Claude can
proactively read without explicit tool calls.
"""

import logging
from typing import Any

from mcp.types import Resource, TextContent

from .client import AareguruClient
from .config import get_settings

logger = logging.getLogger(__name__)


async def list_resources() -> list[Resource]:
    """List all available Aareguru resources.
    
    Returns:
        List of MCP Resource objects
    """
    return [
        Resource(
            uri="aareguru://cities",
            name="Available Cities",
            mimeType="application/json",
            description="List of all cities with Aare data available",
        ),
        Resource(
            uri="aareguru://widget",
            name="All Cities Overview",
            mimeType="application/json",
            description="Current data for all cities at once",
        ),
        # Template resources for city-specific data
        Resource(
            uri="aareguru://current/{city}",
            name="Current Conditions",
            mimeType="application/json",
            description="Complete current conditions for a specific city (e.g., aareguru://current/bern)",
        ),
        Resource(
            uri="aareguru://today/{city}",
            name="Today's Summary",
            mimeType="application/json",
            description="Minimal current data for a specific city (e.g., aareguru://today/bern)",
        ),
    ]


async def read_resource(uri: str) -> str:
    """Read a specific Aareguru resource.
    
    Args:
        uri: Resource URI (e.g., "aareguru://cities" or "aareguru://current/bern")
        
    Returns:
        JSON string with resource data
        
    Raises:
        ValueError: If URI is invalid or resource not found
    """
    logger.info(f"Reading resource: {uri}")
    
    # Parse URI
    if not uri.startswith("aareguru://"):
        raise ValueError(f"Invalid URI scheme: {uri}")
    
    path = uri.replace("aareguru://", "")
    parts = path.split("/")
    
    async with AareguruClient(settings=get_settings()) as client:
        try:
            # Handle different resource types
            if path == "cities":
                # List all cities (returns array)
                response = await client.get_cities()
                import json
                return json.dumps([city.model_dump() for city in response], indent=2)
            
            elif path == "widget":
                # All cities overview
                response = await client.get_widget()
                import json
                return json.dumps(response, indent=2)
            
            elif parts[0] == "current" and len(parts) == 2:
                # Current conditions for specific city
                city = parts[1]
                response = await client.get_current(city)
                return response.model_dump_json(indent=2)
            
            elif parts[0] == "today" and len(parts) == 2:
                # Today's summary for specific city
                city = parts[1]
                response = await client.get_today(city)
                return response.model_dump_json(indent=2)
            
            else:
                raise ValueError(f"Unknown resource path: {path}")
                
        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}")
            raise ValueError(f"Failed to read resource {uri}: {str(e)}")
