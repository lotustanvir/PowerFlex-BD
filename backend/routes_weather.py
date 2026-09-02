"""Weather API Routes for PowerFlex BD v3.

Provides weather data endpoints with proper classification,
provenance, and caching.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from backend.weather_provider import get_weather_provider, get_weather_cache
from backend.services.locations import BANGLADESH_LOCATIONS

logger = logging.getLogger("powerflex.api.weather")

router = APIRouter(
    prefix="/api/v3/weather",
    tags=["Weather v3"],
)


@router.get("/current")
def get_current_weather(
    latitude: float = Query(None, description="Latitude"),
    longitude: float = Query(None, description="Longitude"),
    zone: str = Query(None, description="Bangladesh zone name"),
):
    """Get current weather for a location.

    Either (latitude, longitude) or zone name is required.
    """
    provider = get_weather_provider()
    cache = get_weather_cache()

    # Resolve location
    if zone:
        if zone not in BANGLADESH_LOCATIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown zone: {zone}. Available: {list(BANGLADESH_LOCATIONS.keys())}"
            )
        lat, lon = BANGLADESH_LOCATIONS[zone]
    elif latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either (latitude, longitude) or zone"
        )

    # Check cache (fresh)
    cached = cache.get(lat, lon, "current")
    if cached:
        return cached

    # Fetch from provider
    if not provider.is_available():
        # Try stale cache as fallback
        stale = cache.get_stale(lat, lon, "current")
        if stale:
            stale["status"] = "CACHED"
            stale["message"] = "Weather provider unavailable, serving cached data"
            stale["classification"] = "LIVE_FEED"
            return stale
        return {
            "status": "UNAVAILABLE",
            "message": "Weather provider not available",
            "classification": "DATA_UNAVAILABLE",
            "source": "open_meteo",
            "location": {"latitude": lat, "longitude": lon},
        }

    data = provider.get_current(lat, lon)
    if data is None:
        # Try stale cache as fallback
        stale = cache.get_stale(lat, lon, "current")
        if stale:
            stale["status"] = "CACHED"
            stale["message"] = "Weather fetch failed, serving cached data"
            stale["classification"] = "LIVE_FEED"
            return stale
        return {
            "status": "UNAVAILABLE",
            "message": "Failed to retrieve weather data",
            "classification": "DATA_UNAVAILABLE",
            "source": "open_meteo",
            "location": {"latitude": lat, "longitude": lon},
        }

    result = {
        "status": "OK",
        "data": data.to_dict(),
        "classification": "LIVE_FEED",
        "source": "open_meteo",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "timezone": "Asia/Dhaka",
    }

    cache.set(lat, lon, "current", result)
    return result


@router.get("/forecast")
def get_weather_forecast(
    latitude: float = Query(None, description="Latitude"),
    longitude: float = Query(None, description="Longitude"),
    zone: str = Query(None, description="Bangladesh zone name"),
    hours: int = Query(24, ge=1, le=384, description="Forecast hours"),
):
    """Get weather forecast for a location."""
    provider = get_weather_provider()
    cache = get_weather_cache()

    # Resolve location
    if zone:
        if zone not in BANGLADESH_LOCATIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown zone: {zone}"
            )
        lat, lon = BANGLADESH_LOCATIONS[zone]
    elif latitude is not None and longitude is not None:
        lat, lon = latitude, longitude
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either (latitude, longitude) or zone"
        )

    # Check cache
    cache_key = f"forecast_{hours}"
    cached = cache.get(lat, lon, cache_key)
    if cached:
        return cached

    # Fetch from provider
    if not provider.is_available():
        return {
            "status": "UNAVAILABLE",
            "message": "Weather provider not available",
            "classification": "DATA_UNAVAILABLE",
            "source": "open_meteo",
            "location": {"latitude": lat, "longitude": lon},
        }

    forecast = provider.get_forecast(lat, lon, hours)
    if forecast is None:
        return {
            "status": "UNAVAILABLE",
            "message": "Failed to retrieve forecast",
            "classification": "DATA_UNAVAILABLE",
            "source": "open_meteo",
            "location": {"latitude": lat, "longitude": lon},
        }

    result = {
        "status": "OK",
        "data": forecast.to_dict(),
        "classification": "LIVE_FEED",
        "source": "open_meteo",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }

    cache.set(lat, lon, cache_key, result)
    return result


@router.get("/zones")
def get_all_zones_weather():
    """Get current weather for all 9 Bangladesh zones."""
    provider = get_weather_provider()
    cache = get_weather_cache()

    results = {}
    for zone_name, (lat, lon) in BANGLADESH_LOCATIONS.items():
        cached = cache.get(lat, lon, "current")
        if cached:
            results[zone_name] = cached
            continue

        if not provider.is_available():
            results[zone_name] = {
                "status": "UNAVAILABLE",
                "classification": "DATA_UNAVAILABLE",
            }
            continue

        data = provider.get_current(lat, lon)
        if data:
            result = {
                "status": "OK",
                "data": data.to_dict(),
                "classification": "LIVE_FEED",
                "source": "open_meteo",
            }
            cache.set(lat, lon, "current", result)
            results[zone_name] = result
        else:
            results[zone_name] = {
                "status": "UNAVAILABLE",
                "classification": "DATA_UNAVAILABLE",
            }

    return {
        "status": "OK",
        "zones": results,
        "zone_count": len(results),
        "classification": "LIVE_FEED",
        "source": "open_meteo",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }
