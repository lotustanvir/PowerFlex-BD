"""Deficit Analysis and Recommendation Engine for PowerFlex BD v3.

Core intelligence capability:
1. Demand/Supply Balance
2. Deficit Risk Assessment
3. Technology Optimization
4. Location Selection
5. Plant Capacity Optimization
6. AI Planning Recommendation

All values must be calculated from actual data/models.
NEVER fabricate recommendations.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger("powerflex.recommendation")


@dataclass
class DeficitAnalysis:
    """Demand-supply gap analysis."""
    forecast_demand_mw: Optional[float] = None
    forecast_supply_mw: Optional[float] = None
    forecast_gap_mw: Optional[float] = None
    gap_type: str = "UNKNOWN"  # DEFICIT_RISK, SURPLUS, BALANCED
    severity: str = "NO_RISK"  # NO_RISK, LOW, MODERATE, HIGH, CRITICAL
    confidence: Optional[float] = None
    timestamp: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast_demand_mw": self.forecast_demand_mw,
            "forecast_supply_mw": self.forecast_supply_mw,
            "forecast_gap_mw": self.forecast_gap_mw,
            "gap_type": self.gap_type,
            "severity": self.severity,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "notes": self.notes,
        }


@dataclass
class TechnologyRecommendation:
    """Recommended technology for deficit mitigation."""
    technology: str
    capacity_factor: Optional[float] = None
    expected_generation_mw_per_mw: Optional[float] = None
    suitability_score: float = 0.0
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technology": self.technology,
            "capacity_factor": self.capacity_factor,
            "expected_generation_mw_per_mw": self.expected_generation_mw_per_mw,
            "suitability_score": self.suitability_score,
            "reasons": self.reasons,
            "warnings": self.warnings,
        }


@dataclass
class PlantRecommendation:
    """Complete plant recommendation."""
    technology: str
    recommended_capacity_mw: float
    expected_hourly_generation_mw: Optional[float] = None
    expected_daily_energy_mwh: Optional[float] = None
    expected_annual_energy_gwh: Optional[float] = None
    prediction_interval_lower: Optional[float] = None
    prediction_interval_upper: Optional[float] = None
    site_score: Optional[float] = None
    location: Optional[Dict[str, Any]] = None
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    model_used: str = "UNKNOWN"
    data_quality: str = "UNKNOWN"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technology": self.technology,
            "recommended_capacity_mw": self.recommended_capacity_mw,
            "expected_hourly_generation_mw": self.expected_hourly_generation_mw,
            "expected_daily_energy_mwh": self.expected_daily_energy_mwh,
            "expected_annual_energy_gwh": self.expected_annual_energy_gwh,
            "prediction_interval_lower": self.prediction_interval_lower,
            "prediction_interval_upper": self.prediction_interval_upper,
            "site_score": self.site_score,
            "location": self.location,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "model_used": self.model_used,
            "data_quality": self.data_quality,
        }


@dataclass
class AIPlanningRecommendation:
    """Complete AI planning recommendation."""
    forecast_demand_mw: Optional[float] = None
    forecast_supply_mw: Optional[float] = None
    expected_deficit_mw: Optional[float] = None
    recommended_technology: Optional[TechnologyRecommendation] = None
    recommended_capacity_mw: Optional[float] = None
    recommended_location: Optional[Dict[str, Any]] = None
    expected_hourly_generation_mw: Optional[float] = None
    expected_daily_energy_mwh: Optional[float] = None
    expected_annual_energy_gwh: Optional[float] = None
    prediction_interval: Optional[Dict[str, float]] = None
    site_score: Optional[float] = None
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data_quality: str = "UNKNOWN"
    model_used: str = "UNKNOWN"
    timestamp: str = ""
    disclaimer: str = (
        "This is an AI-generated planning recommendation. "
        "It does NOT constitute construction approval, "
        "engineering certification, grid connection approval, "
        "or financial guarantee. Actual development requires "
        "detailed feasibility studies, environmental impact "
        "assessment, and regulatory approval."
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "forecast_demand_mw": self.forecast_demand_mw,
            "forecast_supply_mw": self.forecast_supply_mw,
            "expected_deficit_mw": self.expected_deficit_mw,
            "recommended_technology": self.recommended_technology.to_dict() if self.recommended_technology else None,
            "recommended_capacity_mw": self.recommended_capacity_mw,
            "recommended_location": self.recommended_location,
            "expected_hourly_generation_mw": self.expected_hourly_generation_mw,
            "expected_daily_energy_mwh": self.expected_daily_energy_mwh,
            "expected_annual_energy_gwh": self.expected_annual_energy_gwh,
            "prediction_interval": self.prediction_interval,
            "site_score": self.site_score,
            "reasons": self.reasons,
            "warnings": self.warnings,
            "data_quality": self.data_quality,
            "model_used": self.model_used,
            "timestamp": self.timestamp,
            "disclaimer": self.disclaimer,
        }


# =========================================================
# DEFICIT CALCULATION
# =========================================================

def calculate_deficit(
    demand_mw: Optional[float],
    supply_mw: Optional[float],
) -> DeficitAnalysis:
    """Calculate demand-supply gap and assess risk.

    Returns honest assessment based on available data.
    """
    now = datetime.now(timezone.utc).isoformat()

    if demand_mw is None and supply_mw is None:
        return DeficitAnalysis(
            timestamp=now,
            gap_type="UNKNOWN",
            severity="UNKNOWN",
            notes="Both demand and supply data unavailable",
        )

    if demand_mw is None:
        return DeficitAnalysis(
            forecast_supply_mw=supply_mw,
            timestamp=now,
            gap_type="UNKNOWN",
            severity="UNKNOWN",
            notes="Demand data unavailable",
        )

    if supply_mw is None:
        return DeficitAnalysis(
            forecast_demand_mw=demand_mw,
            timestamp=now,
            gap_type="UNKNOWN",
            severity="UNKNOWN",
            notes="Supply data unavailable",
        )

    gap = demand_mw - supply_mw

    if gap > 0:
        gap_type = "DEFICIT_RISK"
    elif gap < 0:
        gap_type = "SURPLUS"
    else:
        gap_type = "BALANCED"

    # Severity assessment (configurable thresholds)
    if gap <= 0:
        severity = "NO_RISK"
    elif gap < 500:
        severity = "LOW"
    elif gap < 1500:
        severity = "MODERATE"
    elif gap < 3000:
        severity = "HIGH"
    else:
        severity = "CRITICAL"

    return DeficitAnalysis(
        forecast_demand_mw=demand_mw,
        forecast_supply_mw=supply_mw,
        forecast_gap_mw=round(gap, 1),
        gap_type=gap_type,
        severity=severity,
        timestamp=now,
        notes=f"Demand {demand_mw} MW, Supply {supply_mw} MW, Gap {gap:.1f} MW",
    )


# =========================================================
# TECHNOLOGY SELECTION
# =========================================================

TECHNOLOGY_PROFILES = {
    "SOLAR": {
        "capacity_factor": 0.15,
        "expected_generation_mw_per_mw": 0.15,
        "intermittency": "HIGH",
        "weather_dependence": "HIGH",
        "storage_friendly": True,
        "scalability": "HIGH",
        "cost_trend": "DECREASING",
        "reasons": [
            "Abundant solar resource in Bangladesh",
            "Declining costs",
            "Scalable from kW to GW",
            "No fuel cost",
        ],
        "warnings": [
            "Intermittent - requires storage or backup",
            "Nighttime output is zero",
            "Monsoon season reduces output",
        ],
    },
    "WIND": {
        "capacity_factor": 0.25,
        "expected_generation_mw_per_mw": 0.25,
        "intermittency": "HIGH",
        "weather_dependence": "HIGH",
        "storage_friendly": False,
        "scalability": "MODERATE",
        "cost_trend": "STABLE",
        "reasons": [
            "Good wind resource in coastal areas",
            "Complementary to solar (often windy at night)",
            "Proven technology",
        ],
        "warnings": [
            "Intermittent - requires backup",
            "Limited suitable locations in Bangladesh",
            "Seasonal variation",
        ],
    },
    "SOLAR_WIND": {
        "capacity_factor": 0.20,
        "expected_generation_mw_per_mw": 0.20,
        "intermittency": "MODERATE",
        "weather_dependence": "HIGH",
        "storage_friendly": True,
        "scalability": "MODERATE",
        "cost_trend": "DECREASING",
        "reasons": [
            "Resource complementarity",
            "Higher capacity factor than single source",
            "Reduced intermittency",
        ],
        "warnings": [
            "Higher upfront cost",
            "Complex installation",
        ],
    },
    "SOLAR_BATTERY": {
        "capacity_factor": 0.15,
        "expected_generation_mw_per_mw": 0.15,
        "intermittency": "LOW",
        "weather_dependence": "MODERATE",
        "storage_friendly": True,
        "scalability": "HIGH",
        "cost_trend": "DECREASING",
        "reasons": [
            "Dispatchable solar with storage",
            "Can provide evening peak support",
            "Reduced intermittency",
        ],
        "warnings": [
            "Battery cost adds to upfront investment",
            "Battery degradation over time",
        ],
    },
    "WIND_BATTERY": {
        "capacity_factor": 0.25,
        "expected_generation_mw_per_mw": 0.25,
        "intermittency": "LOW",
        "weather_dependence": "MODERATE",
        "storage_friendly": True,
        "scalability": "MODERATE",
        "cost_trend": "STABLE",
        "reasons": [
            "Dispatchable wind with storage",
            "Can provide firm capacity",
        ],
        "warnings": [
            "Limited wind locations in Bangladesh",
            "Battery cost adds to upfront investment",
        ],
    },
    "SOLAR_WIND_BATTERY": {
        "capacity_factor": 0.20,
        "expected_generation_mw_per_mw": 0.20,
        "intermittency": "VERY_LOW",
        "weather_dependence": "LOW",
        "storage_friendly": True,
        "scalability": "MODERATE",
        "cost_trend": "DECREASING",
        "reasons": [
            "Maximum complementarity",
            "Firm dispatchable generation",
            "Highest reliability",
        ],
        "warnings": [
            "Highest upfront cost",
            "Complex system integration",
        ],
    },
}


def recommend_technology(
    deficit_mw: Optional[float],
    solar_data: Optional[Dict[str, Any]] = None,
    wind_data: Optional[Dict[str, Any]] = None,
    battery_available: bool = False,
) -> TechnologyRecommendation:
    """Recommend technology based on deficit and available resources.

    Uses actual data when available, falls back to technology profiles.
    """
    reasons = []
    warnings = []

    if deficit_mw is None or deficit_mw <= 0:
        return TechnologyRecommendation(
            technology="NONE",
            reasons=["No deficit detected"],
        )

    # Determine best technology based on available data
    has_solar = solar_data is not None and solar_data.get("radiation_wm2", 0) > 0
    has_wind = wind_data is not None and wind_data.get("wind_speed_kmh", 0) >= 6

    if has_solar and has_wind and battery_available:
        tech = "SOLAR_WIND_BATTERY"
        reasons.append("Both solar and wind resources available")
        reasons.append("Battery storage available for dispatchability")
    elif has_solar and battery_available:
        tech = "SOLAR_BATTERY"
        reasons.append("Solar resource available")
        reasons.append("Battery storage available")
    elif has_wind and battery_available:
        tech = "WIND_BATTERY"
        reasons.append("Wind resource available")
        reasons.append("Battery storage available")
    elif has_solar and has_wind:
        tech = "SOLAR_WIND"
        reasons.append("Both solar and wind resources available")
    elif has_solar:
        tech = "SOLAR"
        reasons.append("Solar resource available")
    elif has_wind:
        tech = "WIND"
        reasons.append("Wind resource available")
    else:
        tech = "SOLAR"
        reasons.append("Default to solar - most versatile")
        warnings.append("Resource data unavailable - using default")

    profile = TECHNOLOGY_PROFILES.get(tech, TECHNOLOGY_PROFILES["SOLAR"])

    return TechnologyRecommendation(
        technology=tech,
        capacity_factor=profile["capacity_factor"],
        expected_generation_mw_per_mw=profile["expected_generation_mw_per_mw"],
        suitability_score=80.0 if has_solar or has_wind else 50.0,
        reasons=reasons + profile["reasons"],
        warnings=warnings + profile["warnings"],
    )


# =========================================================
# CAPACITY OPTIMIZATION
# =========================================================

def optimize_capacity(
    deficit_mw: float,
    technology: str,
    capacity_factor: float = 0.15,
    location_score: float = 50.0,
    weather_uncertainty: float = 0.2,
) -> PlantRecommendation:
    """Determine recommended plant capacity.

    Accounts for:
    - Capacity factor
    - Weather uncertainty
    - Location quality
    - Generation variability
    """
    if deficit_mw <= 0:
        return PlantRecommendation(
            technology=technology,
            recommended_capacity_mw=0,
            reasons=["No deficit to address"],
        )

    # Required capacity = deficit / (capacity_factor * location_factor)
    location_factor = max(0.5, location_score / 100)
    required_capacity = deficit_mw / (capacity_factor * location_factor)

    # Add margin for weather uncertainty
    margin = 1 + weather_uncertainty
    recommended_capacity = round(required_capacity * margin, 1)

    # Expected generation
    expected_generation = round(recommended_capacity * capacity_factor, 1)
    expected_daily = round(expected_generation * 24, 1)
    expected_annual = round(expected_daily * 365 / 1000, 2)

    # Prediction intervals
    lower_factor = capacity_factor * (1 - weather_uncertainty)
    upper_factor = capacity_factor * (1 + weather_uncertainty)
    lower = round(recommended_capacity * lower_factor, 1)
    upper = round(recommended_capacity * upper_factor, 1)

    reasons = [
        f"Deficit of {deficit_mw:.0f} MW requires additional generation",
        f"Capacity factor: {capacity_factor:.0%}",
        f"Location quality factor: {location_factor:.2f}",
        f"Weather uncertainty margin: {weather_uncertainty:.0%}",
    ]

    return PlantRecommendation(
        technology=technology,
        recommended_capacity_mw=recommended_capacity,
        expected_hourly_generation_mw=expected_generation,
        expected_daily_energy_mwh=expected_daily,
        expected_annual_energy_gwh=expected_annual,
        prediction_interval_lower=lower,
        prediction_interval_upper=upper,
        site_score=location_score,
        reasons=reasons,
        model_used="capacity_optimizer_v1",
        data_quality="CALCULATED",
    )


# =========================================================
# FULL RECOMMENDATION PIPELINE
# =========================================================

def generate_recommendation(
    demand_mw: Optional[float],
    supply_mw: Optional[float],
    solar_data: Optional[Dict[str, Any]] = None,
    wind_data: Optional[Dict[str, Any]] = None,
    location_data: Optional[Dict[str, Any]] = None,
    battery_available: bool = False,
) -> AIPlanningRecommendation:
    """Generate complete AI planning recommendation.

    This is the main entry point for the recommendation engine.
    """
    now = datetime.now(timezone.utc).isoformat()
    warnings = []
    reasons = []

    # Step 1: Calculate deficit
    deficit = calculate_deficit(demand_mw, supply_mw)

    if deficit.gap_type == "UNKNOWN":
        warnings.append("Cannot calculate deficit - missing data")
        reasons.append("Insufficient data for deficit calculation")

    # Step 2: Recommend technology
    tech_rec = recommend_technology(
        deficit_mw=deficit.forecast_gap_mw,
        solar_data=solar_data,
        wind_data=wind_data,
        battery_available=battery_available,
    )

    if tech_rec.technology == "NONE":
        reasons.append("No additional generation currently required")
        return AIPlanningRecommendation(
            forecast_demand_mw=demand_mw,
            forecast_supply_mw=supply_mw,
            expected_deficit_mw=deficit.forecast_gap_mw,
            recommended_technology=tech_rec,
            recommended_capacity_mw=0,
            reasons=reasons,
            warnings=warnings,
            data_quality=deficit.severity,
            model_used="recommendation_engine_v1",
            timestamp=now,
        )

    # Step 3: Optimize capacity
    location_score = 50.0
    if location_data and location_data.get("score"):
        location_score = location_data["score"].get("overall_score", 50.0)

    plant = optimize_capacity(
        deficit_mw=deficit.forecast_gap_mw,
        technology=tech_rec.technology,
        capacity_factor=tech_rec.capacity_factor or 0.15,
        location_score=location_score,
    )

    reasons.extend(tech_rec.reasons)
    warnings.extend(tech_rec.warnings)

    return AIPlanningRecommendation(
        forecast_demand_mw=demand_mw,
        forecast_supply_mw=supply_mw,
        expected_deficit_mw=deficit.forecast_gap_mw,
        recommended_technology=tech_rec,
        recommended_capacity_mw=plant.recommended_capacity_mw,
        recommended_location=location_data,
        expected_hourly_generation_mw=plant.expected_hourly_generation_mw,
        expected_daily_energy_mwh=plant.expected_daily_energy_mwh,
        expected_annual_energy_gwh=plant.expected_annual_energy_gwh,
        prediction_interval={
            "lower": plant.prediction_interval_lower,
            "upper": plant.prediction_interval_upper,
        } if plant.prediction_interval_lower else None,
        site_score=location_score,
        reasons=reasons,
        warnings=warnings,
        data_quality=deficit.severity,
        model_used="recommendation_engine_v1",
        timestamp=now,
    )
