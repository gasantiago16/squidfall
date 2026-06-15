"""Pluggable geocoding + forecast providers for the weather tools.

Mirrors the inference LLM factory: the MCP tools never hardcode an endpoint —
they call geocode() / forecast(), which dispatch on env config. This lets the
tools point at internal mirrors, or run FULLY OFFLINE with 'static' providers
(useful in air-gapped enclaves and in CI).

  GEOCODER_PROVIDER  = maps_co (default) | static
  FORECAST_PROVIDER  = weather_gov (default) | static
"""

import json
from os import getenv

from httpx import AsyncClient


def _verify(name: str) -> bool:
    return getenv(name, "true").strip().lower() not in ("0", "false", "no")


def _timeout() -> float:
    return float(getenv("WEATHER_HTTP_TIMEOUT", "30"))


# --------------------------- geocoders ---------------------------
async def _geocode_maps_co(location: str) -> dict:
    """geocode.maps.co (Nominatim-compatible). Point GEOCODER_BASE_URL at an
    internal Nominatim mirror to use a different host with the same response."""
    base = getenv("GEOCODER_BASE_URL", "https://geocode.maps.co/search")
    async with AsyncClient(verify=_verify("GEOCODER_VERIFY_SSL"), timeout=_timeout()) as client:
        resp = await client.get(
            base,
            params={"q": location, "api_key": getenv("GEOCODING_API_KEY", "")},
            follow_redirects=True,
        )
        resp.raise_for_status()
        results = resp.json()
        if not results:
            return {"error": f"No coordinates found for: {location}"}
        return {"lat": float(results[0]["lat"]), "lon": float(results[0]["lon"])}


async def _geocode_static(location: str) -> dict:
    """Offline: a JSON map (GEOCODER_STATIC) and/or a single GEOCODER_STATIC_DEFAULT."""
    table = {k.lower(): v for k, v in json.loads(getenv("GEOCODER_STATIC", "{}")).items()}
    hit = table.get(location.strip().lower())
    if hit:
        return {"lat": float(hit[0]), "lon": float(hit[1])}
    fallback = getenv("GEOCODER_STATIC_DEFAULT")  # e.g. "40.44,-79.99"
    if fallback:
        lat, lon = (float(x) for x in fallback.split(","))
        return {"lat": lat, "lon": lon}
    return {"error": f"No static coordinates for: {location}"}


_GEOCODERS = {"maps_co": _geocode_maps_co, "static": _geocode_static}


async def geocode(location: str) -> dict:
    provider = getenv("GEOCODER_PROVIDER", "maps_co").strip().lower()
    fn = _GEOCODERS.get(provider)
    if fn is None:
        return {"error": f"unknown GEOCODER_PROVIDER={provider!r}; expected {sorted(_GEOCODERS)}"}
    return await fn(location)


# --------------------------- forecasts ---------------------------
async def _forecast_weather_gov(lat: float, lon: float) -> str:
    """US National Weather Service (two-step). Point FORECAST_BASE_URL at a mirror."""
    base = getenv("FORECAST_BASE_URL", "https://api.weather.gov")
    ua = getenv("FORECAST_USER_AGENT", "(squidfall, contact@example.com)")
    async with AsyncClient(verify=_verify("FORECAST_VERIFY_SSL"), timeout=_timeout()) as client:
        points = await client.get(
            f"{base}/points/{lat},{lon}",
            headers={"User-Agent": ua, "Accept": "application/geo+json"},
            follow_redirects=True,
        )
        points.raise_for_status()
        forecast_url = points.json()["properties"]["forecast"]
        fc = await client.get(forecast_url, headers={"User-Agent": ua})
        fc.raise_for_status()
        current = fc.json()["properties"]["periods"][0]
        return f"{current['name']}: {current['detailedForecast']}"


async def _forecast_static(lat: float, lon: float) -> str:
    """Offline: a canned forecast string (FORECAST_STATIC_TEXT)."""
    return getenv("FORECAST_STATIC_TEXT", f"Forecast service offline for ({lat}, {lon}).")


_FORECASTERS = {"weather_gov": _forecast_weather_gov, "static": _forecast_static}


async def forecast(lat: float, lon: float) -> str:
    provider = getenv("FORECAST_PROVIDER", "weather_gov").strip().lower()
    fn = _FORECASTERS.get(provider)
    if fn is None:
        return f"error: unknown FORECAST_PROVIDER={provider!r}; expected {sorted(_FORECASTERS)}"
    return await fn(lat, lon)
