"""Recommendation API Routes for PowerFlex BD v3.

Provides deficit analysis, technology recommendation,
location optimization, and AI planning recommendations.

Phase 6: Added Decision Support endpoint for transparent,
rule-based recommendations with explicit source typing.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.recommendation_engine import (
    calculate_deficit,
    recommend_technology,
    optimize_capacity,
    generate_recommendation,
    TECHNOLOGY_PROFILES,
)
from backend.services.grid_service import get_grid_live
from backend.services.solar_service import get_solar_live
from backend.services.wind_service import get_wind_live
from backend.services.locations import BANGLADESH_LOCATIONS
from backend.weather_provider import get_weather_provider, get_weather_cache
from backend.location_intelligence import find_nearest_grid, score_site
from backend.decision_support import (
    get_decision_support,
    get_system_health,
    RecommendationType,
)

logger = logging.getLogger("powerflex.api.recommendation")

router = APIRouter(
    prefix="/api/v3/recommendation",
    tags=["AI Recommendation v3"],
)


@router.get("/deficit")
def get_deficit_analysis():
    """Calculate current demand-supply deficit.

    Uses real PGCB data when available.
    """
    now = datetime.now(timezone.utc).isoformat()

    # Get current grid data
    grid = get_grid_live()

    demand_mw = None
    supply_mw = None
    grid_status = "UNAVAILABLE"

    if grid and grid.get("grid_snapshot"):
        snapshot = grid["grid_snapshot"]
        demand_mw = snapshot.get("current_demand_mw")
        supply_mw = snapshot.get("supply_mw") or snapshot.get("current_generation_mw")
        grid_status = grid.get("grid_status", "UNKNOWN")

    deficit = calculate_deficit(demand_mw, supply_mw)

    return {
        "status": "OK",
        "analysis": deficit.to_dict(),
        "grid_status": grid_status,
        "data_source": "PGCB ERP Portal",
        "classification": "OFFICIAL",
        "timestamp": now,
    }


@router.get("/technology")
def get_technology_recommendation(
    deficit_mw: Optional[float] = Query(None, description="Override deficit MW"),
):
    """Get technology recommendation for deficit mitigation.

    Uses current data if deficit_mw not provided.
    """
    # Get current data
    grid = get_grid_live()
    solar = get_solar_live()
    wind = get_wind_live()

    # Determine deficit
    if deficit_mw is None:
        demand_mw = None
        supply_mw = None
        if grid and grid.get("grid_snapshot"):
            snapshot = grid["grid_snapshot"]
            demand_mw = snapshot.get("current_demand_mw")
            supply_mw = snapshot.get("supply_mw") or snapshot.get("current_generation_mw")

        if demand_mw is None or supply_mw is None:
            return {
                "status": "UNAVAILABLE",
                "message": "Cannot determine deficit - grid data unavailable",
                "classification": "DATA_UNAVAILABLE",
            }

        deficit_mw = demand_mw - supply_mw

    if deficit_mw <= 0:
        return {
            "status": "OK",
            "deficit_mw": deficit_mw,
            "recommendation": {
                "technology": "NONE",
                "reasons": ["No deficit detected"],
            },
            "classification": "CALCULATED",
        }

    # Get resource data for technology selection
    solar_data = None
    wind_data = None

    if solar and solar.get("zone_ranking"):
        best_solar = solar["zone_ranking"][0]
        solar_data = {
            "radiation_wm2": best_solar.get("expected_energy_mwh_per_1mw_24h", 0) * 1000 / 24,
        }

    if wind and wind.get("zone_ranking"):
        best_wind = wind["zone_ranking"][0]
        wind_data = {
            "wind_speed_kmh": best_wind.get("expected_energy_mwh_per_1mw_24h", 0) * 10,
        }

    tech_rec = recommend_technology(
        deficit_mw=deficit_mw,
        solar_data=solar_data,
        wind_data=wind_data,
    )

    return {
        "status": "OK",
        "deficit_mw": deficit_mw,
        "recommendation": tech_rec.to_dict(),
        "classification": "CALCULATED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/plant")
def get_plant_recommendation(
    deficit_mw: Optional[float] = Query(None, description="Override deficit MW"),
    technology: Optional[str] = Query(None, description="Override technology"),
    latitude: Optional[float] = Query(None, description="Location latitude"),
    longitude: Optional[float] = Query(None, description="Location longitude"),
    capacity_mw: Optional[float] = Query(None, description="Override capacity"),
):
    """Get complete plant recommendation.

    Returns technology, capacity, expected generation, and location.
    """
    # Get current data
    grid = get_grid_live()
    solar = get_solar_live()
    wind = get_wind_live()

    # Determine deficit
    if deficit_mw is None:
        demand_mw = None
        supply_mw = None
        if grid and grid.get("grid_snapshot"):
            snapshot = grid["grid_snapshot"]
            demand_mw = snapshot.get("current_demand_mw")
            supply_mw = snapshot.get("supply_mw") or snapshot.get("current_generation_mw")

        if demand_mw is not None and supply_mw is not None:
            deficit_mw = demand_mw - supply_mw

    if deficit_mw is None or deficit_mw <= 0:
        return {
            "status": "OK",
            "recommendation": {
                "technology": "NONE",
                "capacity_mw": 0,
                "reasons": ["No deficit detected"],
            },
            "classification": "CALCULATED",
        }

    # Get resource data
    solar_data = None
    wind_data = None
    if solar and solar.get("zone_ranking"):
        solar_data = {"radiation_wm2": 500}
    if wind and wind.get("zone_ranking"):
        wind_data = {"wind_speed_kmh": 12}

    # Recommend technology
    tech_rec = recommend_technology(
        deficit_mw=deficit_mw,
        solar_data=solar_data,
        wind_data=wind_data,
    )

    # Get location data
    location_data = None
    if latitude and longitude:
        grid_info = find_nearest_grid(latitude, longitude)
        location_data = {
            "latitude": latitude,
            "longitude": longitude,
            "grid_information": grid_info,
            "score": {"overall_score": 50.0},
        }
    else:
        # Use best zone
        location_data = {
            "latitude": BANGLADESH_LOCATIONS["Dhaka"][0],
            "longitude": BANGLADESH_LOCATIONS["Dhaka"][1],
            "grid_information": find_nearest_grid(
                BANGLADESH_LOCATIONS["Dhaka"][0],
                BANGLADESH_LOCATIONS["Dhaka"][1],
            ),
            "score": {"overall_score": 50.0},
        }

    # Optimize capacity
    plant = optimize_capacity(
        deficit_mw=deficit_mw,
        technology=technology or tech_rec.technology,
        capacity_factor=tech_rec.capacity_factor or 0.15,
        location_score=location_data["score"]["overall_score"],
    )

    return {
        "status": "OK",
        "recommendation": {
            "technology": plant.technology,
            "capacity_mw": plant.recommended_capacity_mw,
            "expected_generation_mw": plant.expected_hourly_generation_mw,
            "expected_daily_mwh": plant.expected_daily_energy_mwh,
            "expected_annual_gwh": plant.expected_annual_energy_gwh,
            "prediction_interval": {
                "lower": plant.prediction_interval_lower,
                "upper": plant.prediction_interval_upper,
            } if plant.prediction_interval_lower else None,
            "location": location_data,
            "reasons": plant.reasons,
            "warnings": plant.warnings,
        },
        "deficit_mw": deficit_mw,
        "classification": "CALCULATED",
        "model": "recommendation_engine_v1",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "disclaimer": (
            "This is an AI-generated planning recommendation. "
            "It does NOT constitute construction approval, "
            "engineering certification, grid connection approval, "
            "or financial guarantee."
        ),
    }


@router.get("/full")
def get_full_recommendation():
    """Generate complete AI planning recommendation.

    Full pipeline: Demand → Supply → Deficit → Technology → Location → Plant
    """
    # Get current data
    grid = get_grid_live()
    solar = get_solar_live()
    wind = get_wind_live()

    demand_mw = None
    supply_mw = None
    solar_data = None
    wind_data = None

    if grid and grid.get("grid_snapshot"):
        snapshot = grid["grid_snapshot"]
        demand_mw = snapshot.get("current_demand_mw")
        supply_mw = snapshot.get("supply_mw") or snapshot.get("current_generation_mw")

    if solar and solar.get("zone_ranking"):
        best_solar = solar["zone_ranking"][0]
        solar_data = {"radiation_wm2": 500}

    if wind and wind.get("zone_ranking"):
        best_wind = wind["zone_ranking"][0]
        wind_data = {"wind_speed_kmh": 12}

    recommendation = generate_recommendation(
        demand_mw=demand_mw,
        supply_mw=supply_mw,
        solar_data=solar_data,
        wind_data=wind_data,
    )

    return {
        "status": "OK",
        "recommendation": recommendation.to_dict(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/technologies")
def list_technologies():
    """List all supported technology profiles."""
    return {
        "status": "OK",
        "technologies": {
            name: {
                "capacity_factor": profile["capacity_factor"],
                "intermittency": profile["intermittency"],
                "weather_dependence": profile["weather_dependence"],
                "scalability": profile["scalability"],
                "cost_trend": profile["cost_trend"],
                "reasons": profile["reasons"],
                "warnings": profile["warnings"],
            }
            for name, profile in TECHNOLOGY_PROFILES.items()
        },
        "classification": "REFERENCE_DATA",
    }


@router.get("/decision-support")
def get_decision_support_recommendations():
    """Get decision support recommendations.
    
    Phase 6: Unified recommendation engine that aggregates verified
    energy-system signals into actionable guidance. All recommendations
    are:
    - Rule-based (not ML predictions)
    - Transparent with explicit source typing
    - Confidence-scored with provenance
    - Deduplicated to avoid repeated same recommendations
    - Gracefully degraded when inputs fail
    
    Returns:
        - recommendations: List of active recommendations
        - system_inputs: Current system state
        - metadata: Source type, data status, confidence average
        - missing_inputs: List of unavailable input sources
    """
    try:
        result = get_decision_support()
        return result
    except Exception as e:
        logger.exception("Decision support failed")
        return {
            "status": "ERROR",
            "message": f"Decision support calculation failed: {str(e)}",
            "recommendations": [],
            "missing_inputs": ["decision_support_engine"],
        }


@router.get("/decision-support/health")
def get_decision_support_health():
    """Get decision support system health.
    
    Returns:
        - independent_observations: Count of unique observations
        - grid_status: Current grid status
        - forecast_ready: Whether forecast gate is satisfied
        - data_quality_score: Quality score 0-1
    """
    return get_system_health()


@router.get("/decision-support/{rec_type}")
def get_specific_recommendation(rec_type: RecommendationType):
    """Get a specific recommendation type if active.
    
    Args:
        rec_type: Type of recommendation to retrieve
    """
    try:
        from backend.decision_support import get_recommendation_by_type
        result = get_recommendation_by_type(rec_type)
        if result:
            return {
                "status": "OK",
                "recommendation": result,
            }
        else:
            return {
                "status": "OK",
                "recommendation": None,
                "message": f"No active {rec_type.value} recommendation",
            }
    except Exception as e:
        logger.exception("Failed to get specific recommendation")
        return {
            "status": "ERROR",
            "message": f"Failed to retrieve recommendation: {str(e)}",
        }
