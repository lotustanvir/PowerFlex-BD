"""Bangladesh Location Intelligence for PowerFlex BD v3.

Determines which Bangladesh locations may provide better renewable
generation potential. This is a PLANNING model, NOT construction approval.

Uses only legitimate data sources. Unknown values remain UNKNOWN, not zero.

PROVENANCE: Uses canonical grid data from grid_canonical.py.
All substation data is UNVERIFIED until authoritative BPDB/PGCB
sources are obtained.
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.grid_canonical import (
    BANGLADESH_SUBSTATIONS,
    get_provenance_summary,
)

logger = logging.getLogger("powerflex.location_intelligence")


@dataclass
class LocationFeatures:
    """Features for a candidate location."""
    latitude: float
    longitude: float
    solar_resource: Optional[str] = "UNKNOWN"
    wind_resource: Optional[str] = "UNKNOWN"
    weather: Optional[Dict[str, Any]] = None
    expected_generation: Optional[Dict[str, float]] = None
    generation_variability: Optional[float] = None
    grid_proximity: Optional[str] = "UNKNOWN"
    grid_information: Optional[Dict[str, Any]] = None
    land_suitability: Optional[str] = "UNKNOWN"
    resource_complementarity: Optional[str] = "UNKNOWN"
    storage_suitability: Optional[str] = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "solar_resource": self.solar_resource,
            "wind_resource": self.wind_resource,
            "weather": self.weather,
            "expected_generation": self.expected_generation,
            "generation_variability": self.generation_variability,
            "grid_proximity": self.grid_proximity,
            "grid_information": self.grid_information,
            "land_suitability": self.land_suitability,
            "resource_complementarity": self.resource_complementarity,
            "storage_suitability": self.storage_suitability,
        }


@dataclass
class SiteScore:
    """Explainable site score components."""
    solar_score: float = 0.0
    wind_score: float = 0.0
    generation_score: float = 0.0
    grid_score: float = 0.0
    reliability_score: float = 0.0
    overall_score: float = 0.0
    components: Dict[str, float] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "solar_score": self.solar_score,
            "wind_score": self.wind_score,
            "generation_score": self.generation_score,
            "grid_score": self.grid_score,
            "reliability_score": self.reliability_score,
            "overall_score": self.overall_score,
            "components": self.components,
            "warnings": self.warnings,
        }


@dataclass
class CandidateLocation:
    """A candidate location for renewable energy development."""
    rank: int
    latitude: float
    longitude: float
    technology: str
    resource: str
    recommended_capacity_mw: Optional[float] = None
    expected_generation_mw: Optional[float] = None
    expected_annual_gwh: Optional[float] = None
    score: Optional[SiteScore] = None
    uncertainty: Optional[str] = None
    grid_information: Optional[Dict[str, Any]] = None
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rank": self.rank,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "technology": self.technology,
            "resource": self.resource,
            "recommended_capacity_mw": self.recommended_capacity_mw,
            "expected_generation_mw": self.expected_generation_mw,
            "expected_annual_gwh": self.expected_annual_gwh,
            "score": self.score.to_dict() if self.score else None,
            "uncertainty": self.uncertainty,
            "grid_information": self.grid_information,
            "warnings": self.warnings,
        }


# =========================================================
# BANGLADESH BOUNDING BOX
# =========================================================

BANGLADESH_BOUNDS = {
    "min_lat": 20.5,
    "max_lat": 26.7,
    "min_lon": 88.0,
    "max_lon": 92.7,
}

# =========================================================
# GRID SUBSTATIONS
# =========================================================
# 
# PROVENANCE: Using canonical grid data from grid_canonical.py
# Status: ALL UNVERIFIED - awaiting authoritative BPDB/PGCB data
# =========================================================

# Convert canonical substations to the format expected by location intelligence
GRID_SUBSTATIONS = [
    {
        "name": s.name,
        "lat": s.latitude,
        "lon": s.longitude,
        "voltage_kv": s.voltage_kv,
    }
    for s in BANGLADESH_SUBSTATIONS
]


def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points using Haversine formula."""
    R = 6371  # Earth's radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (math.sin(dlat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def find_nearest_grid(latitude: float, longitude: float) -> Dict[str, Any]:
    """Find the nearest grid substation to a location."""
    nearest = None
    min_dist = float('inf')

    for sub in GRID_SUBSTATIONS:
        dist = calculate_distance_km(latitude, longitude, sub["lat"], sub["lon"])
        if dist < min_dist:
            min_dist = dist
            nearest = sub

    if nearest is None:
        return {
            "substation": "UNKNOWN",
            "distance_km": None,
            "voltage_kv": None,
            "grid_proximity": "UNKNOWN",
        }

    if min_dist < 10:
        proximity = "EXCELLENT"
    elif min_dist < 30:
        proximity = "GOOD"
    elif min_dist < 60:
        proximity = "MODERATE"
    elif min_dist < 100:
        proximity = "DISTANT"
    else:
        proximity = "REMOTE"

    return {
        "substation": nearest["name"],
        "distance_km": round(min_dist, 1),
        "voltage_kv": nearest["voltage_kv"],
        "grid_proximity": proximity,
    }


# =========================================================
# SITE SCORING
# =========================================================

# Default weights (configurable)
DEFAULT_WEIGHTS = {
    "solar": 0.25,
    "wind": 0.25,
    "generation": 0.20,
    "grid": 0.20,
    "reliability": 0.10,
}


def score_site(
    latitude: float,
    longitude: float,
    solar_data: Optional[Dict[str, Any]] = None,
    wind_data: Optional[Dict[str, Any]] = None,
    weather_data: Optional[Dict[str, Any]] = None,
    weights: Optional[Dict[str, float]] = None,
) -> SiteScore:
    """Calculate an explainable site score.

    All scoring is based on available data. Missing data results
    in score components of 0 with appropriate warnings.
    """
    w = weights or DEFAULT_WEIGHTS
    warnings = []

    # Solar score (0-100)
    solar_score = 0.0
    if solar_data and solar_data.get("radiation_wm2") is not None:
        radiation = solar_data["radiation_wm2"]
        if radiation > 0:
            solar_score = min(100, (radiation / 600) * 100)
        else:
            solar_score = 0
            warnings.append("Solar radiation is zero or negative")
    else:
        warnings.append("Solar data unavailable")

    # Wind score (0-100)
    wind_score = 0.0
    if wind_data and wind_data.get("wind_speed_kmh") is not None:
        wind_speed = wind_data["wind_speed_kmh"]
        if wind_speed >= 15:
            wind_score = 100
        elif wind_speed >= 10:
            wind_score = 70
        elif wind_speed >= 6:
            wind_score = 40
        elif wind_speed >= 3:
            wind_score = 20
        else:
            wind_score = 0
    else:
        warnings.append("Wind data unavailable")

    # Generation score (0-100)
    generation_score = 0.0
    if solar_data and wind_data:
        solar_contribution = solar_score * 0.6
        wind_contribution = wind_score * 0.4
        generation_score = solar_contribution + wind_contribution
    elif solar_data:
        generation_score = solar_score * 0.6
        warnings.append("Wind data missing - generation score partial")
    elif wind_data:
        generation_score = wind_score * 0.4
        warnings.append("Solar data missing - generation score partial")
    else:
        warnings.append("No generation data available")

    # Grid score (0-100)
    grid_info = find_nearest_grid(latitude, longitude)
    grid_score = 0.0
    if grid_info["grid_proximity"] == "EXCELLENT":
        grid_score = 100
    elif grid_info["grid_proximity"] == "GOOD":
        grid_score = 80
    elif grid_info["grid_proximity"] == "MODERATE":
        grid_score = 50
    elif grid_info["grid_proximity"] == "DISTANT":
        grid_score = 20
    else:
        grid_score = 0
        warnings.append("Grid connection may be challenging")

    # Reliability score (0-100)
    reliability_score = 50.0  # default
    if solar_data and wind_data:
        complementarity = 100 - abs(solar_score - wind_score)
        reliability_score = complementarity * 0.5 + 50
    elif solar_data or wind_data:
        reliability_score = 50
        warnings.append("Single resource only - limited reliability")

    # Overall score
    overall_score = (
        solar_score * w.get("solar", 0.25) +
        wind_score * w.get("wind", 0.25) +
        generation_score * w.get("generation", 0.20) +
        grid_score * w.get("grid", 0.20) +
        reliability_score * w.get("reliability", 0.10)
    )

    return SiteScore(
        solar_score=round(solar_score, 1),
        wind_score=round(wind_score, 1),
        generation_score=round(generation_score, 1),
        grid_score=round(grid_score, 1),
        reliability_score=round(reliability_score, 1),
        overall_score=round(overall_score, 1),
        components={
            "solar_weight": w.get("solar", 0.25),
            "wind_weight": w.get("wind", 0.25),
            "generation_weight": w.get("generation", 0.20),
            "grid_weight": w.get("grid", 0.20),
            "reliability_weight": w.get("reliability", 0.10),
        },
        warnings=warnings,
    )


# =========================================================
# CANDIDATE SEARCH
# =========================================================

# Pre-defined candidate locations across Bangladesh
BANGLADESH_CANDIDATES = [
    {"name": "Dhaka Region", "lat": 23.81, "lon": 90.41, "technology": "SOLAR"},
    {"name": "Chittagong Coast", "lat": 22.36, "lon": 91.78, "technology": "WIND"},
    {"name": "Rajshahi Solar Belt", "lat": 24.37, "lon": 88.60, "technology": "SOLAR"},
    {"name": "Khulna Wetlands", "lat": 22.85, "lon": 89.54, "technology": "SOLAR"},
    {"name": "Sylhet Highlands", "lat": 24.89, "lon": 91.87, "technology": "WIND"},
    {"name": "Rangpur Agricultural", "lat": 25.74, "lon": 89.28, "technology": "SOLAR"},
    {"name": "Barishal Delta", "lat": 22.70, "lon": 90.35, "technology": "SOLAR"},
    {"name": "Comilla Corridor", "lat": 23.46, "lon": 91.18, "technology": "SOLAR"},
    {"name": "Mymensingh North", "lat": 24.75, "lon": 90.42, "technology": "SOLAR"},
    {"name": "Cox's Bazar Coast", "lat": 21.43, "lon": 92.00, "technology": "WIND"},
]


def search_candidates(
    area: Optional[Dict[str, float]] = None,
    technology: Optional[str] = None,
    resolution: float = 0.5,
) -> List[Dict[str, Any]]:
    """Search for candidate locations within a specified area.

    Args:
        area: Bounding box {"min_lat", "max_lat", "min_lon", "max_lon"}
        technology: Filter by technology type (SOLAR, WIND)
        resolution: Grid resolution in degrees

    Returns:
        List of candidate locations.
    """
    candidates = []

    for candidate in BANGLADESH_CANDIDATES:
        if technology and candidate["technology"] != technology:
            continue

        if area:
            if not (area.get("min_lat", 0) <= candidate["lat"] <= area.get("max_lat", 90)):
                continue
            if not (area.get("min_lon", 0) <= candidate["lon"] <= area.get("max_lon", 180)):
                continue

        grid_info = find_nearest_grid(candidate["lat"], candidate["lon"])

        candidates.append({
            "name": candidate["name"],
            "latitude": candidate["lat"],
            "longitude": candidate["lon"],
            "technology": candidate["technology"],
            "grid_information": grid_info,
        })

    return candidates


# =========================================================
# AREA ANALYSIS (Background Job Support)
# =========================================================

def analyze_area(
    area: Dict[str, float],
    technology: str = "SOLAR",
    resolution: float = 0.5,
    capacity_mw: float = 10.0,
) -> Dict[str, Any]:
    """Analyze a rectangular area for renewable potential.

    Returns analysis metadata. Actual scoring requires weather data.
    """
    candidates = search_candidates(area=area, technology=technology, resolution=resolution)

    return {
        "area": area,
        "technology": technology,
        "resolution": resolution,
        "capacity_mw": capacity_mw,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "status": "ANALYSIS_COMPLETE",
        "note": "Site scoring requires weather data integration",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
