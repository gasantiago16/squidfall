# Standard library imports.
from logging import getLogger

# Third party imports.
from fastmcp import FastMCP
from fastmcp.utilities.logging import configure_logging

# Local imports — pluggable geocoding/forecast providers (see providers.py).
from .providers import geocode, forecast

# Init a MCP server and set its logging level.
mcp = FastMCP(name="squidfall")
configure_logging(level="DEBUG")
logger = getLogger("squidfall")


@mcp.tool(description="Get the latitude and longitude for a location.")
async def get_coordinates(location: str) -> dict:
    """Get the latitude and longitude for a location.

    Args:
        location: A city name, address, or ZIP code (e.g. 'Pittsburgh, PA').

    Returns:
        A dict with 'lat' and 'lon' keys, or an error message under 'error'.
    """
    return await geocode(location)


@mcp.tool(description="Get the current weather forecast for a coordinate pair.")
async def get_forecast(lat: float, lon: float) -> str:
    """Get the current weather forecast for a coordinate pair.

    Args:
        lat: Latitude.
        lon: Longitude.

    Returns:
        The current forecast period as a plain text string.
    """
    return await forecast(lat, lon)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=8002,
    )
