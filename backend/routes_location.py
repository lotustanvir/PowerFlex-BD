"""Location Intelligence API Routes for PowerFlex BD v3.

Provides location analysis, site scoring, and candidate search
for renewable energy development in Bangladesh.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.location_intelligence import (
    search_candidates,
    analyze_area,
    score_site,
    find_nearest_grid,
    BANGLADESH_BOUNDS,
)
from backend.services.locations import BANGLADESH_LOCATIONS
from backend.weather_provider import get_weather_provider, get_weather_cache

logger = logging.getLogger("powerflex.api.location")

router = APIRouter(
    prefix="/api/v3/location",
    tags=["Location Intelligence v3"],
)


@router.get("/search")
def search_locations(
    latitude: Optional[float] = Query(None, description="Center latitude"),
    longitude: Optional[float] = Query(None, description="Center longitude"),
    technology: Optional[str] = Query(None, description="Filter by technology: SOLAR, WIND"),
    radius_km: float = Query(50, description="Search radius in km"),
):
    """Search for candidate locations near a point.

    Returns nearby candidate locations with grid information.
    """
    if latitude is None or longitude is None:
        candidates = search_candidates(technology=technology)
    else:
        # Filter candidates within radius
        all_candidates = search_candidates(technology=technology)
        candidates = []
        for c in all_candidates:
            from backend.location_intelligence import calculate_distance_km
            dist = calculate_distance_km(latitude, longitude, c["latitude"], c["longitude"])
            if dist <= radius_km:
                candidates.append(c)

    return {
        "status": "OK",
        "search_center": {"latitude": latitude, "longitude": longitude} if latitude else None,
        "radius_km": radius_km,
        "technology_filter": technology,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/analyze")
def analyze_location(
    latitude: float = Query(..., description="Location latitude"),
    longitude: float = Query(..., description="Location longitude"),
    technology: str = Query("SOLAR", description="Technology type"),
    capacity_mw: float = Query(10.0, description="Planned capacity in MW"),
):
    """Analyze a specific location for renewable energy potential.

    Returns location features, grid information, and site score.
    """
    # Validate location is within Bangladesh
    if not (BANGLADESH_BOUNDS["min_lat"] <= latitude <= BANGLADESH_BOUNDS["max_lat"]):
        raise HTTPException(
            status_code=400,
            detail=f"Latitude {latitude} is outside Bangladesh bounds"
        )
    if not (BANGLADESH_BOUNDS["min_lon"] <= longitude <= BANGLADESH_BOUNDS["max_lon"]):
        raise HTTPException(
            status_code=400,
            detail=f"Longitude {longitude} is outside Bangladesh bounds"
        )

    # Get grid information
    grid_info = find_nearest_grid(latitude, longitude)

    # Get weather data
    provider = get_weather_provider()
    cache = get_weather_cache()

    weather_data = None
    solar_data = None
    wind_data = None

    cached_weather = cache.get(latitude, longitude, "current")
    if cached_weather and "data" in cached_weather:
        weather_data = cached_weather["data"]
    else:
        if provider.is_available():
            current = provider.get_current(latitude, longitude)
            if current:
                weather_data = current.to_dict()
                cache.set(latitude, longitude, "current", {"data": weather_data})

    if weather_data:
        solar_data = {
            "radiation_wm2": weather_data.get("solar_radiation_wm2"),
        }
        wind_data = {
            "wind_speed_kmh": weather_data.get("wind_speed_kmh"),
        }

    # Score the site
    site_score = score_site(
        latitude=latitude,
        longitude=longitude,
        solar_data=solar_data,
        wind_data=wind_data,
        weather_data=weather_data,
    )

    # Calculate expected generation
    expected_generation = None
    if technology == "SOLAR" and solar_data and solar_data.get("radiation_wm2"):
        radiation = solar_data["radiation_wm2"]
        efficiency = 0.18
        expected_generation = round(capacity_mw * (radiation / 1000) * efficiency, 2)
    elif technology == "WIND" and wind_data and wind_data.get("wind_speed_kmh"):
        wind_speed = wind_data["wind_speed_kmh"]
        # Simple power curve approximation
        if wind_speed < 3:
            cf = 0
        elif wind_speed < 12:
            cf = 0.1 + (wind_speed - 3) * 0.09
        else:
            cf = 0.9
        expected_generation = round(capacity_mw * cf, 2)

    return {
        "status": "OK",
        "location": {
            "latitude": latitude,
            "longitude": longitude,
        },
        "technology": technology,
        "capacity_mw": capacity_mw,
        "grid_information": grid_info,
        "weather": weather_data,
        "site_score": site_score.to_dict(),
        "expected_generation_mw": expected_generation,
        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
        "classification": "CALCULATED",
        "disclaimer": (
            "This analysis is for planning purposes only. "
            "Actual development requires detailed feasibility studies."
        ),
    }


@router.get("/compare")
def compare_locations(
    locations: str = Query(..., description="Comma-separated lat,lon pairs"),
    technology: str = Query("SOLAR", description="Technology type"),
):
    """Compare multiple locations for renewable energy potential.

    Format: lat1,lon1;lat2,lon2;...
    """
    try:
        pairs = locations.split(";")
        coords = []
        for pair in pairs:
            parts = pair.split(",")
            if len(parts) != 2:
                raise ValueError(f"Invalid format: {pair}")
            lat, lon = float(parts[0].strip()), float(parts[1].strip())
            coords.append((lat, lon))
    except (ValueError, IndexError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid locations format: {e}")

    if len(coords) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 locations for comparison")

    results = []
    provider = get_weather_provider()
    cache = get_weather_cache()

    for i, (lat, lon) in enumerate(coords):
        # Get weather
        weather_data = None
        cached_weather = cache.get(lat, lon, "current")
        if cached_weather and "data" in cached_weather:
            weather_data = cached_weather["data"]
        elif provider.is_available():
            current = provider.get_current(lat, lon)
            if current:
                weather_data = current.to_dict()

        solar_data = {"radiation_wm2": weather_data.get("solar_radiation_wm2")} if weather_data else None
        wind_data = {"wind_speed_kmh": weather_data.get("wind_speed_kmh")} if weather_data else None

        site_score = score_site(lat, lon, solar_data, wind_data, weather_data)
        grid_info = find_nearest_grid(lat, lon)

        results.append({
            "rank": 0,
            "latitude": lat,
            "longitude": lon,
            "technology": technology,
            "site_score": site_score.to_dict(),
            "grid_information": grid_info,
            "weather": weather_data,
        })

    # Sort by overall score
    results.sort(key=lambda x: x["site_score"]["overall_score"], reverse=True)
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return {
        "status": "OK",
        "technology": technology,
        "location_count": len(results),
        "comparison": results,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/area-analysis")
def area_analysis(
    min_lat: float = Query(..., description="Minimum latitude"),
    max_lat: float = Query(..., description="Maximum latitude"),
    min_lon: float = Query(..., description="Minimum longitude"),
    max_lon: float = Query(..., description="Maximum longitude"),
    technology: str = Query("SOLAR", description="Technology type"),
    resolution: float = Query(0.5, description="Grid resolution in degrees"),
    capacity_mw: float = Query(10.0, description="Planned capacity per site in MW"),
):
    """Analyze a rectangular area for renewable potential.

    Returns candidate locations within the area.
    """
    area = {
        "min_lat": min_lat,
        "max_lat": max_lat,
        "min_lon": min_lon,
        "max_lon": max_lon,
    }

    # Validate bounds
    if min_lat >= max_lat:
        raise HTTPException(status_code=400, detail="min_lat must be less than max_lat")
    if min_lon >= max_lon:
        raise HTTPException(status_code=400, detail="min_lon must be less than max_lon")

    # Limit area size
    lat_range = max_lat - min_lat
    lon_range = max_lon - min_lon
    if lat_range > 5 or lon_range > 5:
        raise HTTPException(
            status_code=400,
            detail="Area too large. Maximum 5 degrees in each dimension."
        )

    result = analyze_area(
        area=area,
        technology=technology,
        resolution=resolution,
        capacity_mw=capacity_mw,
    )

    return {
        "status": "OK",
        **result,
    }


@router.get("/grid/{latitude}/{longitude}")
def get_grid_info(
    latitude: float,
    longitude: float,
):
    """Get grid connection information for a specific location."""
    grid_info = find_nearest_grid(latitude, longitude)

    return {
        "status": "OK",
        "location": {"latitude": latitude, "longitude": longitude},
        "grid": grid_info,
        "classification": "CALCULATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
