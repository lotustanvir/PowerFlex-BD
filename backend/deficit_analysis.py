"""Deficit Analysis & Technology Comparison for PowerFlex BD.

Provides realistic deficit calculations with capacity factors,
technology comparison matrices, and plant-level recommendations.

All calculations use Bangladesh Standard Time (UTC+06:00).
Data Classification: CALCULATED + FORECAST
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("powerflex.deficit_analysis")

BST = timezone(timedelta(hours=6))


@dataclass
class TechnologyProfile:
    """Complete profile for an energy technology."""
    name: str
    capacity_factor: float
    capital_cost_per_mw_usd: float
    operating_cost_per_mwh_usd: float
    lifetime_years: int
    co2_emissions_kg_per_mwh: float
    ramp_rate_pct_per_min: float
    availability_pct: float
    water_consumption_l_per_mwh: float
    land_requirement_acres_per_mw: float
    construction_time_months: int
    fuel_cost_per_mwh: float = 0.0
    data_classification: str = "OFFICIAL"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "capacity_factor": self.capacity_factor,
            "capital_cost_per_mw_usd": self.capital_cost_per_mw_usd,
            "operating_cost_per_mwh_usd": self.operating_cost_per_mwh_usd,
            "lifetime_years": self.lifetime_years,
            "co2_emissions_kg_per_mwh": self.co2_emissions_kg_per_mwh,
            "ramp_rate_pct_per_min": self.ramp_rate_pct_per_min,
            "availability_pct": self.availability_pct,
            "water_consumption_l_per_mwh": self.water_consumption_l_per_mwh,
            "land_requirement_acres_per_mw": self.land_requirement_acres_per_mw,
            "construction_time_months": self.construction_time_months,
            "fuel_cost_per_mwh": self.fuel_cost_per_mwh,
            "data_classification": self.data_classification,
        }


TECHNOLOGY_PROFILES: Dict[str, TechnologyProfile] = {
    "SOLAR_PV": TechnologyProfile(
        name="Solar PV",
        capacity_factor=0.20,
        capital_cost_per_mw_usd=800_000,
        operating_cost_per_mwh_usd=15,
        lifetime_years=25,
        co2_emissions_kg_per_mwh=40,
        ramp_rate_pct_per_min=100,
        availability_pct=0.98,
        water_consumption_l_per_mwh=10,
        land_requirement_acres_per_mw=5,
        construction_time_months=12,
    ),
    "WIND_ONSHORE": TechnologyProfile(
        name="Onshore Wind",
        capacity_factor=0.30,
        capital_cost_per_mw_usd=1_200_000,
        operating_cost_per_mwh_usd=25,
        lifetime_years=25,
        co2_emissions_kg_per_mwh=12,
        ramp_rate_pct_per_min=50,
        availability_pct=0.97,
        water_consumption_l_per_mwh=0,
        land_requirement_acres_per_mw=30,
        construction_time_months=18,
    ),
    "NATURAL_GAS_CCGT": TechnologyProfile(
        name="Natural Gas CCGT",
        capacity_factor=0.85,
        capital_cost_per_mw_usd=900_000,
        operating_cost_per_mwh_usd=45,
        lifetime_years=30,
        co2_emissions_kg_per_mwh=350,
        ramp_rate_pct_per_min=5,
        availability_pct=0.92,
        water_consumption_l_per_mwh=700,
        land_requirement_acres_per_mw=1,
        construction_time_months=36,
        fuel_cost_per_mwh=55,
    ),
    "COAL": TechnologyProfile(
        name="Coal",
        capacity_factor=0.75,
        capital_cost_per_mw_usd=1_500_000,
        operating_cost_per_mwh_usd=50,
        lifetime_years=40,
        co2_emissions_kg_per_mwh=900,
        ramp_rate_pct_per_min=2,
        availability_pct=0.88,
        water_consumption_l_per_mwh=1800,
        land_requirement_acres_per_mw=2,
        construction_time_months=60,
        fuel_cost_per_mwh=40,
    ),
    "HYDRO": TechnologyProfile(
        name="Hydroelectric",
        capacity_factor=0.45,
        capital_cost_per_mw_usd=2_000_000,
        operating_cost_per_mwh_usd=10,
        lifetime_years=50,
        co2_emissions_kg_per_mwh=5,
        ramp_rate_pct_per_min=50,
        availability_pct=0.95,
        water_consumption_l_per_mwh=5000,
        land_requirement_acres_per_mw=100,
        construction_time_months=60,
    ),
    "BATTERY_STORAGE": TechnologyProfile(
        name="Battery Energy Storage (BESS)",
        capacity_factor=0.90,
        capital_cost_per_mw_usd=1_500_000,
        operating_cost_per_mwh_usd=20,
        lifetime_years=15,
        co2_emissions_kg_per_mwh=50,
        ramp_rate_pct_per_min=100,
        availability_pct=0.99,
        water_consumption_l_per_mwh=0,
        land_requirement_acres_per_mw=1,
        construction_time_months=6,
    ),
    "BIOMASS": TechnologyProfile(
        name="Biomass",
        capacity_factor=0.60,
        capital_cost_per_mw_usd=2_500_000,
        operating_cost_per_mwh_usd=35,
        lifetime_years=25,
        co2_emissions_kg_per_mwh=100,
        ramp_rate_pct_per_min=5,
        availability_pct=0.85,
        water_consumption_l_per_mwh=500,
        land_requirement_acres_per_mw=20,
        construction_time_months=24,
        fuel_cost_per_mwh=30,
    ),
    "WASTE_TO_ENERGY": TechnologyProfile(
        name="Waste-to-Energy",
        capacity_factor=0.70,
        capital_cost_per_mw_usd=3_000_000,
        operating_cost_per_mwh_usd=40,
        lifetime_years=25,
        co2_emissions_kg_per_mwh=600,
        ramp_rate_pct_per_min=3,
        availability_pct=0.90,
        water_consumption_l_per_mwh=800,
        land_requirement_acres_per_mw=2,
        construction_time_months=30,
        fuel_cost_per_mwh=10,
    ),
}


@dataclass
class DeficitAnalysis:
    """Realistic deficit analysis result."""
    timestamp_utc: datetime
    timestamp_local: datetime
    demand_mw: float
    supply_mw: float
    deficit_mw: float
    reserve_margin_pct: float
    reserve_status: str
    peak_deficit_mw: float
    average_deficit_mw: float
    hours_of_deficit: int
    capacity_shortfall_mw: float
    data_classification: str = "CALCULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "timestamp_local": self.timestamp_local.isoformat(),
            "demand_mw": round(self.demand_mw, 2),
            "supply_mw": round(self.supply_mw, 2),
            "deficit_mw": round(self.deficit_mw, 2),
            "reserve_margin_pct": round(self.reserve_margin_pct, 2),
            "reserve_status": self.reserve_status,
            "peak_deficit_mw": round(self.peak_deficit_mw, 2),
            "average_deficit_mw": round(self.average_deficit_mw, 2),
            "hours_of_deficit": self.hours_of_deficit,
            "capacity_shortfall_mw": round(self.capacity_shortfall_mw, 2),
            "data_classification": self.data_classification,
        }


@dataclass
class TechnologyRecommendation:
    """Technology recommendation based on deficit analysis."""
    technology: str
    profile: TechnologyProfile
    capacity_needed_mw: float
    estimated_cost_usd: float
    annual_generation_mwh: float
    co2_avoided_kg: float
    feasibility_score: float
    rank: int
    data_classification: str = "CALCULATED"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "technology": self.technology,
            "profile": self.profile.to_dict(),
            "capacity_needed_mw": round(self.capacity_needed_mw, 2),
            "estimated_cost_usd": round(self.estimated_cost_usd, 0),
            "annual_generation_mwh": round(self.annual_generation_mwh, 0),
            "co2_avoided_kg": round(self.co2_avoided_kg, 0),
            "feasibility_score": round(self.feasibility_score, 3),
            "rank": self.rank,
            "data_classification": self.data_classification,
        }


def calculate_deficit(
    demand_mw: float,
    supply_mw: float,
    historical_demands: Optional[List[float]] = None,
) -> DeficitAnalysis:
    """Calculate deficit with reserve margin analysis."""
    now_utc = datetime.now(timezone.utc)
    now_bst = now_utc.astimezone(BST)

    deficit_mw = max(0, demand_mw - supply_mw)
    reserve_margin = ((supply_mw - demand_mw) / demand_mw * 100) if demand_mw > 0 else 0

    if reserve_margin >= 20:
        reserve_status = "ADEQUATE"
    elif reserve_margin >= 10:
        reserve_status = "MARGINAL"
    elif reserve_margin >= 0:
        reserve_status = "STRESSED"
    elif reserve_margin >= -10:
        reserve_status = "CRITICAL"
    else:
        reserve_status = "EMERGENCY"

    peak_deficit = deficit_mw
    avg_deficit = deficit_mw
    hours_deficit = 1 if deficit_mw > 0 else 0
    capacity_shortfall = max(0, demand_mw * 0.15 - supply_mw)

    if historical_demands:
        peak_deficit = max(d - supply_mw for d in historical_demands if d > supply_mw) if any(d > supply_mw for d in historical_demands) else deficit_mw
        avg_deficit = sum(max(0, d - supply_mw) for d in historical_demands) / len(historical_demands)
        hours_deficit = sum(1 for d in historical_demands if d > supply_mw)

    return DeficitAnalysis(
        timestamp_utc=now_utc,
        timestamp_local=now_bst,
        demand_mw=demand_mw,
        supply_mw=supply_mw,
        deficit_mw=deficit_mw,
        reserve_margin_pct=reserve_margin,
        reserve_status=reserve_status,
        peak_deficit_mw=peak_deficit,
        average_deficit_mw=avg_deficit,
        hours_of_deficit=hours_deficit,
        capacity_shortfall_mw=capacity_shortfall,
    )


def recommend_technologies(
    deficit_mw: float,
    target_reserve_pct: float = 20.0,
    budget_usd: Optional[float] = None,
    priority_techs: Optional[List[str]] = None,
) -> List[TechnologyRecommendation]:
    """Recommend technologies to address deficit."""
    capacity_needed = deficit_mw * (1 + target_reserve_pct / 100)
    recommendations = []

    for tech_key, profile in TECHNOLOGY_PROFILES.items():
        if priority_techs and tech_key not in priority_techs:
            continue

        annual_gen = capacity_needed * profile.capacity_factor * 8760
        cost = capacity_needed * profile.capital_cost_per_mw_usd
        annual_co2 = annual_gen * profile.co2_emissions_kg_per_mwh

        feasibility = 0.5
        if profile.capacity_factor >= 0.3:
            feasibility += 0.15
        if profile.construction_time_months <= 18:
            feasibility += 0.15
        if profile.operating_cost_per_mwh_usd <= 30:
            feasibility += 0.1
        if profile.co2_emissions_kg_per_mwh <= 100:
            feasibility += 0.1

        if budget_usd and cost > budget_usd:
            feasibility *= 0.5

        feasibility = min(1.0, feasibility)

        recommendations.append(TechnologyRecommendation(
            technology=tech_key,
            profile=profile,
            capacity_needed_mw=capacity_needed,
            estimated_cost_usd=cost,
            annual_generation_mwh=annual_gen,
            co2_avoided_kg=annual_co2,
            feasibility_score=feasibility,
            rank=0,
        ))

    recommendations.sort(key=lambda r: r.feasibility_score, reverse=True)
    for i, rec in enumerate(recommendations):
        rec.rank = i + 1

    return recommendations


def generate_comparison_matrix(
    technologies: Optional[List[str]] = None,
    capacity_mw: float = 100.0,
) -> Dict[str, Any]:
    """Generate comparison matrix for technologies."""
    techs = technologies or list(TECHNOLOGY_PROFILES.keys())
    comparison = []

    for tech_key in techs:
        if tech_key not in TECHNOLOGY_PROFILES:
            continue
        profile = TECHNOLOGY_PROFILES[tech_key]
        annual_gen = capacity_mw * profile.capacity_factor * 8760
        annual_cost = annual_gen * (profile.operating_cost_per_mwh_usd + profile.fuel_cost_per_mwh)
        levelized_cost = (profile.capital_cost_per_mw_usd * capacity_mw) / (annual_gen * profile.lifetime_years) + profile.operating_cost_per_mwh_usd + profile.fuel_cost_per_mwh

        comparison.append({
            "technology": tech_key,
            "profile": profile.to_dict(),
            "capacity_mw": capacity_mw,
            "annual_generation_mwh": round(annual_gen, 0),
            "annual_cost_usd": round(annual_cost, 0),
            "levelized_cost_per_mwh": round(levelized_cost, 2),
            "co2_emissions_annual_kg": round(annual_gen * profile.co2_emissions_kg_per_mwh, 0),
        })

    comparison.sort(key=lambda x: x["levelized_cost_per_mwh"])

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capacity_mw": capacity_mw,
        "technologies": comparison,
        "data_classification": "CALCULATED",
    }
