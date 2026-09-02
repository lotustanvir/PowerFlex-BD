"""
Grid Risk Score Engine — PowerFlex BD

Computes a unified Grid Risk Score (0–100) from:
  • supply-demand deficit ratio
  • reserve margin
  • data-source reliability
  • renewable intermittency
  • load-shedding exposure

The composite score feeds the LoadShield response so the
frontend can render risk gauges, scenario comparisons, and
trend sparklines.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.data_classification import (
    DataClassification,
    normalize_classification,
)


# =========================================================
# CONSTANTS
# =========================================================

# Weights for the composite risk score (must sum to 1.0)
WEIGHT_DEFICIT = 0.35
WEIGHT_RESERVE = 0.25
WEIGHT_RELIABILITY = 0.20
WEIGHT_INTERMITTENCY = 0.10
WEIGHT_LOAD_SHEDDING = 0.10

# Reserve-margin thresholds (%)
RESERVE_HEALTHY = 10.0
RESERVE_WARN = 5.0
RESERVE_CRITICAL = 0.0

# Reliability weights by classification
CLASSIFICATION_RELIABILITY = {
    DataClassification.OFFICIAL: 1.0,
    DataClassification.MEASURED: 0.95,
    DataClassification.LIVE_FEED: 0.90,
    DataClassification.DELAYED: 0.70,
    DataClassification.FORECAST: 0.60,
    DataClassification.CALCULATED: 0.55,
    DataClassification.POTENTIAL: 0.40,
    DataClassification.PROJECT: 0.35,
    DataClassification.EXPERIMENTAL: 0.20,
    DataClassification.PROTOTYPE: 0.10,
    DataClassification.DATA_UNAVAILABLE: 0.0,
}

# Risk-level bands
RISK_LOW_MAX = 30
RISK_MODERATE_MAX = 55
RISK_ELEVATED_MAX = 75
# > 75 → HIGH

# Scenario presets
SCENARIOS = {
    "current": {
        "label": "Current Conditions",
        "demand_multiplier": 1.0,
        "supply_multiplier": 1.0,
        "renewable_curtailment": 0.0,
    },
    "peak_evening": {
        "label": "Peak Evening Demand",
        "demand_multiplier": 1.15,
        "supply_multiplier": 0.90,
        "renewable_curtailment": 0.0,
    },
    "solar_drop": {
        "label": "Solar Cloud Cover",
        "demand_multiplier": 1.0,
        "supply_multiplier": 0.95,
        "renewable_curtailment": 0.30,
    },
    "wind_calm": {
        "label": "Wind Calm Period",
        "demand_multiplier": 1.0,
        "supply_multiplier": 0.97,
        "renewable_curtailment": 0.15,
    },
    "extreme_heat": {
        "label": "Extreme Heat Wave",
        "demand_multiplier": 1.25,
        "supply_multiplier": 0.85,
        "renewable_curtailment": 0.0,
    },
    "worst_case": {
        "label": "Worst-Case Compound",
        "demand_multiplier": 1.30,
        "supply_multiplier": 0.80,
        "renewable_curtailment": 0.40,
    },
}


# =========================================================
# DATA CLASSES
# =========================================================


@dataclass
class RiskComponent:
    """Single risk dimension (0–100)."""

    name: str
    score: float  # 0–100
    weight: float
    detail: str = ""
    raw_value: float = 0.0
    unit: str = ""


@dataclass
class GridRiskResult:
    """Full risk assessment output."""

    composite_score: float  # 0–100
    risk_level: str  # LOW / MODERATE / ELEVATED / HIGH
    components: List[RiskComponent] = field(default_factory=list)
    scenarios: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""
    data_sources: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "composite_score": round(self.composite_score, 1),
            "risk_level": self.risk_level,
            "components": [
                {
                    "name": c.name,
                    "score": round(c.score, 1),
                    "weight": c.weight,
                    "detail": c.detail,
                    "raw_value": round(c.raw_value, 2),
                    "unit": c.unit,
                }
                for c in self.components
            ],
            "scenarios": self.scenarios,
            "timestamp": self.timestamp,
            "data_sources": self.data_sources,
        }


# =========================================================
# SCORE HELPERS
# =========================================================


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _risk_level(score: float) -> str:
    if score <= RISK_LOW_MAX:
        return "LOW"
    if score <= RISK_MODERATE_MAX:
        return "MODERATE"
    if score <= RISK_ELEVATED_MAX:
        return "ELEVATED"
    return "HIGH"


# =========================================================
# COMPONENT SCORERS
# =========================================================


def _score_deficit(demand_mw: float, supply_mw: float) -> RiskComponent:
    """Score based on supply-demand gap percentage."""
    demand = max(demand_mw, 0.0)
    supply = max(supply_mw, 0.0)

    if demand <= 0:
        gap_pct = 0.0
    else:
        gap_pct = max(((demand - supply) / demand) * 100, 0.0)

    # Linear scale: 0% gap → risk 0, 30%+ gap → risk 100
    score = _clamp(gap_pct * (100.0 / 30.0))

    if gap_pct <= 5:
        detail = "Supply closely matches demand."
    elif gap_pct <= 15:
        detail = f"Moderate deficit of {gap_pct:.1f}%. Monitor closely."
    elif gap_pct <= 25:
        detail = f"Significant deficit of {gap_pct:.1f}%. Activation likely."
    else:
        detail = f"Critical deficit of {gap_pct:.1f}%. Immediate action required."

    return RiskComponent(
        name="Supply-Demand Deficit",
        score=score,
        weight=WEIGHT_DEFICIT,
        detail=detail,
        raw_value=gap_pct,
        unit="%",
    )


def _score_reserve(demand_mw: float, supply_mw: float) -> RiskComponent:
    """Score based on reserve margin."""
    demand = max(demand_mw, 0.0)
    supply = max(supply_mw, 0.0)

    if demand <= 0:
        reserve_pct = 50.0  # plenty of margin
    else:
        reserve_pct = ((supply - demand) / demand) * 100

    # Negative reserve → risk 100; ≥10% → risk 0
    if reserve_pct >= RESERVE_HEALTHY:
        score = 0.0
    elif reserve_pct >= RESERVE_WARN:
        score = _clamp((RESERVE_HEALTHY - reserve_pct) * (40.0 / 5.0))
    elif reserve_pct >= RESERVE_CRITICAL:
        score = _clamp(40.0 + (RESERVE_WARN - reserve_pct) * (30.0 / 5.0))
    else:
        score = _clamp(70.0 + abs(reserve_pct) * (30.0 / 10.0))

    if reserve_pct >= RESERVE_HEALTHY:
        detail = f"Healthy reserve margin of {reserve_pct:.1f}%."
    elif reserve_pct >= RESERVE_WARN:
        detail = f"Tight reserve margin of {reserve_pct:.1f}%. Watch closely."
    elif reserve_pct >= RESERVE_CRITICAL:
        detail = f"Very thin reserve of {reserve_pct:.1f}%."
    else:
        detail = f"Negative reserve ({reserve_pct:.1f}%). Supply below demand."

    return RiskComponent(
        name="Reserve Margin",
        score=score,
        weight=WEIGHT_RESERVE,
        detail=detail,
        raw_value=reserve_pct,
        unit="%",
    )


def _score_reliability(
    data_classifications: Dict[str, DataClassification],
) -> RiskComponent:
    """Score based on data-source reliability."""
    if not data_classifications:
        return RiskComponent(
            name="Data Reliability",
            score=50.0,
            weight=WEIGHT_RELIABILITY,
            detail="No classification data available.",
            raw_value=0.0,
            unit="sources",
        )

    total = 0.0
    count = 0
    for _src, cls in data_classifications.items():
        total += CLASSIFICATION_RELIABILITY.get(cls, 0.5)
        count += 1

    avg_reliability = total / count if count > 0 else 0.5
    score = _clamp((1.0 - avg_reliability) * 100.0)

    reliable_count = sum(
        1 for c in data_classifications.values()
        if CLASSIFICATION_RELIABILITY.get(c, 0) >= 0.8
    )

    detail = (
        f"{reliable_count}/{count} sources are high-reliability "
        f"(≥80%). Average reliability: {avg_reliability * 100:.0f}%."
    )

    return RiskComponent(
        name="Data Reliability",
        score=score,
        weight=WEIGHT_RELIABILITY,
        detail=detail,
        raw_value=avg_reliability * 100,
        unit="%",
    )


def _score_intermittency(
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    solar_installed_mw: float = 0.0,
    wind_installed_mw: float = 0.0,
) -> RiskComponent:
    """Score based on renewable generation variability."""
    solar_gen = _safe_nested(
        solar_data,
        ["current_hour_generation", "mw_per_1mw_installed"],
        0.0,
    )
    wind_gen = _safe_nested(
        wind_data,
        ["current_hour_generation", "mw_per_1mw_installed"],
        0.0,
    )

    total_installed = solar_installed_mw + wind_installed_mw
    if total_installed <= 0:
        return RiskComponent(
            name="Renewable Intermittency",
            score=0.0,
            weight=WEIGHT_INTERMITTENCY,
            detail="No renewable capacity installed.",
            raw_value=0.0,
            unit="MW",
        )

    # Low generation relative to capacity → higher risk
    solar_fraction = solar_installed_mw / total_installed
    wind_fraction = wind_installed_mw / total_installed

    solar_risk = _clamp((1.0 - min(solar_gen / 0.8, 1.0)) * 100.0)
    wind_risk = _clamp((1.0 - min(wind_gen / 0.6, 1.0)) * 100.0)

    weighted_risk = (
        solar_risk * solar_fraction + wind_risk * wind_fraction
    )

    detail = (
        f"Solar: {solar_gen:.3f} MW/MW, Wind: {wind_gen:.3f} MW/MW. "
        f"Combined intermittency risk: {weighted_risk:.0f}/100."
    )

    return RiskComponent(
        name="Renewable Intermittency",
        score=weighted_risk,
        weight=WEIGHT_INTERMITTENCY,
        detail=detail,
        raw_value=weighted_risk,
        unit="score",
    )


def _score_load_shedding(
    load_shedding_mw: float, demand_mw: float
) -> RiskComponent:
    """Score based on current load-shedding exposure."""
    ls = max(load_shedding_mw, 0.0)
    demand = max(demand_mw, 0.0)

    if demand <= 0:
        ls_pct = 0.0
    else:
        ls_pct = (ls / demand) * 100

    # Linear: 0% → risk 0, 15%+ → risk 100
    score = _clamp(ls_pct * (100.0 / 15.0))

    if ls <= 0:
        detail = "No active load shedding."
    elif ls_pct <= 5:
        detail = f"Minor load shedding of {ls:.1f} MW ({ls_pct:.1f}%)."
    elif ls_pct <= 10:
        detail = f"Moderate load shedding of {ls:.1f} MW ({ls_pct:.1f}%)."
    else:
        detail = f"Severe load shedding of {ls:.1f} MW ({ls_pct:.1f}%)."

    return RiskComponent(
        name="Load Shedding Exposure",
        score=score,
        weight=WEIGHT_LOAD_SHEDDING,
        detail=detail,
        raw_value=ls_pct,
        unit="%",
    )


# =========================================================
# SCENARIO ENGINE
# =========================================================


def compute_scenarios(
    demand_mw: float,
    supply_mw: float,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    data_classifications: Dict[str, DataClassification],
    load_shedding_mw: float = 0.0,
) -> Dict[str, Any]:
    """Run risk under each scenario preset."""
    results = {}

    for key, scenario in SCENARIOS.items():
        adj_demand = demand_mw * scenario["demand_multiplier"]
        adj_supply = supply_mw * scenario["supply_multiplier"]

        # Apply renewable curtailment
        curt = scenario["renewable_curtailment"]
        adj_solar = _curtail(solar_data, curt)
        adj_wind = _curtail(wind_data, curt)

        components = [
            _score_deficit(adj_demand, adj_supply),
            _score_reserve(adj_demand, adj_supply),
            _score_reliability(data_classifications),
            _score_intermittency(adj_solar, adj_wind),
            _score_load_shedding(load_shedding_mw, adj_demand),
        ]

        composite = sum(c.score * c.weight for c in components)

        results[key] = {
            "label": scenario["label"],
            "risk_score": round(composite, 1),
            "risk_level": _risk_level(composite),
            "demand_mw": round(adj_demand, 1),
            "supply_mw": round(adj_supply, 1),
            "gap_mw": round(max(adj_demand - adj_supply, 0), 1),
        }

    return results


# =========================================================
# MAIN ENTRY POINT
# =========================================================


def compute_grid_risk(
    demand_mw: float,
    supply_mw: float,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_data: Optional[Dict[str, Any]] = None,
    waste_data: Optional[Dict[str, Any]] = None,
    hydro_total_mw: float = 0.0,
    load_shedding_mw: float = 0.0,
    solar_installed_mw: float = 0.0,
    wind_installed_mw: float = 0.0,
    include_scenarios: bool = True,
) -> GridRiskResult:
    """Compute the full Grid Risk Score."""

    # Classify data sources
    classifications: Dict[str, DataClassification] = {}
    if solar_data:
        classifications["solar"] = _extract_classification(solar_data)
    if wind_data:
        classifications["wind"] = _extract_classification(wind_data)
    if biomass_data:
        classifications["biomass"] = _extract_classification(biomass_data)
    if waste_data:
        classifications["waste"] = _extract_classification(waste_data)

    # Compute individual components
    components = [
        _score_deficit(demand_mw, supply_mw),
        _score_reserve(demand_mw, supply_mw),
        _score_reliability(classifications),
        _score_intermittency(
            solar_data, wind_data, solar_installed_mw, wind_installed_mw
        ),
        _score_load_shedding(load_shedding_mw, demand_mw),
    ]

    # Composite score
    composite = sum(c.score * c.weight for c in components)
    composite = _clamp(composite)
    level = _risk_level(composite)

    # Scenarios
    scenarios = {}
    if include_scenarios:
        scenarios = compute_scenarios(
            demand_mw,
            supply_mw,
            solar_data,
            wind_data,
            classifications,
            load_shedding_mw,
        )

    # Data source labels
    data_sources = {}
    for src, cls in classifications.items():
        data_sources[src] = cls.value

    return GridRiskResult(
        composite_score=composite,
        risk_level=level,
        components=components,
        scenarios=scenarios,
        timestamp=datetime.now().isoformat(),
        data_sources=data_sources,
    )


# =========================================================
# INTERNAL HELPERS
# =========================================================


def _safe_nested(
    data: Dict[str, Any], keys: List[str], default: float = 0.0
) -> float:
    """Safely traverse nested dict keys."""
    current: Any = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    try:
        return float(current)
    except (TypeError, ValueError):
        return default


def _extract_classification(
    source_data: Dict[str, Any],
) -> DataClassification:
    """Pull data_classification from a source dict, defaulting to UNKNOWN."""
    raw = source_data.get("data_classification", "")
    if not raw:
        raw = source_data.get("classification", "")
    return normalize_classification(raw) if raw else DataClassification.UNKNOWN


def _curtail(
    source_data: Dict[str, Any], fraction: float
) -> Dict[str, Any]:
    """Return a copy with generation values curtailed."""
    import copy

    data = copy.deepcopy(source_data)
    gen = data.get("current_hour_generation", {})
    if isinstance(gen, dict):
        val = gen.get("mw_per_1mw_installed", 0.0)
        gen["mw_per_1mw_installed"] = val * (1.0 - fraction)
    return data
