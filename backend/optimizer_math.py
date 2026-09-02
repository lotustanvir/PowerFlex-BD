"""Mathematical optimization engine for LoadShield.

Uses scipy.optimize.linprog to solve a linear program that
determines the optimal resource dispatch across 9 Bangladesh
zones, minimizing unserved energy while respecting zone caps,
resource availability, and cost priorities.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

import numpy as np
from scipy.optimize import linprog

from backend.prototype_config import SOLAR_INSTALLED_MW, WIND_INSTALLED_MW

from backend.optimizer import (
    BANGLADESH_ZONES,
    MAX_ZONE_ALLOCATION_PERCENT,
    BATTERY_POWER_MW,
    FLEXIBLE_DEMAND_MW,
    safe_float,
    build_zone_analysis,
    optimize as heuristic_optimize,
)

logger = logging.getLogger("powerflex.optimizer_math")


# =========================================================
# DATA STRUCTURES
# =========================================================

RESOURCES = ["solar", "wind", "hydro", "biomass", "waste"]

RESOURCE_COSTS = {
    "solar": 0.0,
    "wind": 0.0,
    "hydro": 1.0,
    "biomass": 5.0,
    "waste": 5.0,
}

UNSERVED_PENALTY = 10000.0

BATTERY_COST = 10.0
FLEX_DEMAND_COST = 8.0


@dataclass
class OptimizationResult:
    status: str
    deficit: float
    total_dispatch: float
    remaining_gap: float
    zone_dispatches: Dict[str, Dict[str, float]]
    battery_mw: float
    flex_demand_mw: float
    objective_value: float


# =========================================================
# INDEX HELPERS
# =========================================================

NUM_ZONES = len(BANGLADESH_ZONES)
NUM_RESOURCES = len(RESOURCES)
ZONE_RESOURCE_VARS = NUM_ZONES * NUM_RESOURCES
BATTERY_VAR = ZONE_RESOURCE_VARS
FLEX_DEMAND_VAR = ZONE_RESOURCE_VARS + 1
UNSERVED_VAR = ZONE_RESOURCE_VARS + 2
TOTAL_VARS = ZONE_RESOURCE_VARS + 3


def _zr_index(zone_idx: int, resource_idx: int) -> int:
    return zone_idx * NUM_RESOURCES + resource_idx


# =========================================================
# BUILD ZONE RESOURCE AVAILABILITY
# =========================================================

def _build_resource_pool(
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[Dict[str, Any]],
    waste_zones: Optional[Dict[str, Any]],
) -> List[Dict[str, float]]:
    """Build per-zone available MW for each resource."""

    zone_analysis = build_zone_analysis(
        solar_data, wind_data, biomass_divisions, waste_zones
    )

    solar_current_hour = safe_float(
        solar_data.get("current_hour_generation", {})
        .get("mw_per_1mw_installed", 0.0)
    )
    wind_current_hour = safe_float(
        wind_data.get("current_hour_generation", {})
        .get("mw_per_1mw_installed", 0.0)
    )

    num_zones = len(BANGLADESH_ZONES)
    solar_per_zone_installed = SOLAR_INSTALLED_MW / num_zones
    wind_per_zone_installed = WIND_INSTALLED_MW / num_zones

    pools = []
    for za in zone_analysis:
        pools.append({
            "zone": za["zone"],
            "solar": solar_current_hour * solar_per_zone_installed,
            "wind": wind_current_hour * wind_per_zone_installed,
            "hydro": safe_float(za.get("hydro_available_mw")),
            "biomass": safe_float(za.get("biomass_available_mw")),
            "waste": safe_float(za.get("waste_available_mw")),
            "combined_score": safe_float(za.get("combined_renewable_score")),
        })

    pools.sort(key=lambda p: p["combined_score"], reverse=True)
    return pools


# =========================================================
# LINEAR PROGRAMMING SOLVER
# =========================================================

def _solve_lp(
    deficit: float,
    resource_pools: List[Dict[str, float]],
    battery_mw: float,
    flex_demand_mw: float,
) -> Optional[OptimizationResult]:
    """Solve the dispatch LP using scipy linprog."""

    # --- Objective coefficients (minimize) ---
    c = np.zeros(TOTAL_VARS)

    for zi in range(NUM_ZONES):
        for ri, res in enumerate(RESOURCES):
            c[_zr_index(zi, ri)] = RESOURCE_COSTS[res]

    c[BATTERY_VAR] = BATTERY_COST
    c[FLEX_DEMAND_VAR] = FLEX_DEMAND_COST
    c[UNSERVED_VAR] = UNSERVED_PENALTY

    # --- Equality constraint: total dispatch + unserved = deficit ---
    A_eq = np.ones((1, TOTAL_VARS))
    b_eq = np.array([deficit])

    # --- Inequality constraints ---
    # 1) Per-zone, per-resource availability: x_zr <= available_zr
    # 2) Per-zone allocation cap: sum_r(x_zr) <= 0.40 * deficit
    # 3) Battery cap: x_battery <= battery_mw
    # 4) Flex demand cap: x_flex <= flex_demand_mw

    num_avail = NUM_ZONES * NUM_RESOURCES
    num_zone_caps = NUM_ZONES
    num_backup_caps = 2
    num_ineq = num_avail + num_zone_caps + num_backup_caps

    A_ub = np.zeros((num_ineq, TOTAL_VARS))
    b_ub = np.zeros(num_ineq)

    row = 0

    # Resource availability constraints
    for zi in range(NUM_ZONES):
        pool = resource_pools[zi]
        for ri, res in enumerate(RESOURCES):
            A_ub[row, _zr_index(zi, ri)] = 1.0
            b_ub[row] = pool[res]
            row += 1

    # Zone allocation cap: sum_r(x_zr) <= 0.40 * deficit
    zone_cap = MAX_ZONE_ALLOCATION_PERCENT * deficit
    for zi in range(NUM_ZONES):
        for ri in range(NUM_RESOURCES):
            A_ub[row, _zr_index(zi, ri)] = 1.0
        b_ub[row] = zone_cap
        row += 1

    # Battery cap
    A_ub[row, BATTERY_VAR] = 1.0
    b_ub[row] = battery_mw
    row += 1

    # Flexible demand cap
    A_ub[row, FLEX_DEMAND_VAR] = 1.0
    b_ub[row] = flex_demand_mw
    row += 1

    # --- Bounds ---
    bounds = [(0.0, None)] * TOTAL_VARS

    # --- Solve ---
    result = linprog(
        c,
        A_ub=A_ub,
        b_ub=b_ub,
        A_eq=A_eq,
        b_eq=b_eq,
        bounds=bounds,
        method="highs",
    )

    if not result.success:
        logger.warning("LP solver failed: %s", result.message)
        return None

    x = result.x

    # --- Extract solution ---
    zone_dispatches: Dict[str, Dict[str, float]] = {}
    total_dispatch = 0.0

    for zi in range(NUM_ZONES):
        zone = resource_pools[zi]["zone"]
        zone_dispatches[zone] = {}
        for ri, res in enumerate(RESOURCES):
            val = round(float(x[_zr_index(zi, ri)]), 3)
            zone_dispatches[zone][res] = val
            total_dispatch += val

    battery_used = round(float(x[BATTERY_VAR]), 3)
    flex_used = round(float(x[FLEX_DEMAND_VAR]), 3)
    unserved = round(float(x[UNSERVED_VAR]), 3)

    total_dispatch += battery_used + flex_used

    status = "DEFICIT_COVERED" if unserved <= 0.001 else "DEFICIT_REMAINS"

    return OptimizationResult(
        status=status,
        deficit=deficit,
        total_dispatch=round(total_dispatch, 3),
        remaining_gap=unserved,
        zone_dispatches=zone_dispatches,
        battery_mw=battery_used,
        flex_demand_mw=flex_used,
        objective_value=round(float(result.fun), 3),
    )


# =========================================================
# MAIN ENTRY POINT
# =========================================================

def optimize_mathematical(
    demand_mw: float,
    supply_mw: float,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[Dict[str, Any]] = None,
    waste_zones: Optional[Dict[str, Any]] = None,
    hydro_total_mw: float = 0.0,
    battery_mw: float = BATTERY_POWER_MW,
    flexible_demand_mw: float = FLEXIBLE_DEMAND_MW,
) -> Optional[OptimizationResult]:
    """Run mathematical optimization for LoadShield dispatch.

    Returns OptimizationResult if successful, None if it should
    fall back to the heuristic optimizer.
    """

    demand = max(0.0, safe_float(demand_mw))
    supply = max(0.0, safe_float(supply_mw))
    deficit = max(demand - supply, 0.0)

    if deficit <= 0:
        return OptimizationResult(
            status="SUPPLY_SUFFICIENT",
            deficit=0.0,
            total_dispatch=0.0,
            remaining_gap=0.0,
            zone_dispatches={},
            battery_mw=0.0,
            flex_demand_mw=0.0,
            objective_value=0.0,
        )

    try:
        resource_pools = _build_resource_pool(
            solar_data, wind_data, biomass_divisions, waste_zones
        )

        lp_result = _solve_lp(
            deficit, resource_pools, battery_mw, flexible_demand_mw
        )

        if lp_result is None:
            return None

        return lp_result

    except Exception as e:
        logger.exception("Mathematical optimization failed: %s", e)
        return None


# =========================================================
# CONVERT TO DICT FORMAT (for optimizer.py compatibility)
# =========================================================

def math_result_to_dict(
    result: OptimizationResult,
    solar_data: Dict[str, Any],
    wind_data: Dict[str, Any],
    biomass_divisions: Optional[Dict[str, Any]] = None,
    waste_zones: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Convert OptimizationResult to the dict format used by
    the heuristic optimizer for API compatibility."""

    zone_analysis = build_zone_analysis(
        solar_data, wind_data, biomass_divisions, waste_zones
    )

    deployment = []
    rank = 1

    if result.status == "SUPPLY_SUFFICIENT":
        return {
            "status": "SUPPLY_SUFFICIENT",
            "initial_deficit_mw": 0.0,
            "total_support_mw": 0.0,
            "remaining_gap_mw": 0.0,
            "zone_analysis": zone_analysis,
            "recommended_deployment": [],
        }

    for zone in BANGLADESH_ZONES:
        zone_d = result.zone_dispatches.get(zone, {})
        for res in RESOURCES:
            mw = zone_d.get(res, 0.0)
            if mw > 0.001:
                deployment.append({
                    "rank": rank,
                    "zone": zone,
                    "resource": res.capitalize(),
                    "support_mw": mw,
                    "recommended_installed_capacity_mw": 0.0,
                    "reason": f"Mathematical optimization: {res} dispatch in {zone}.",
                })
                rank += 1

    if result.battery_mw > 0.001:
        deployment.append({
            "rank": rank,
            "zone": "System-wide",
            "resource": "Battery",
            "support_mw": result.battery_mw,
            "recommended_installed_capacity_mw": result.battery_mw,
            "reason": "Battery dispatch via mathematical optimization.",
        })
        rank += 1

    if result.flex_demand_mw > 0.001:
        deployment.append({
            "rank": rank,
            "zone": "System-wide",
            "resource": "Flexible Demand",
            "support_mw": result.flex_demand_mw,
            "recommended_installed_capacity_mw": result.flex_demand_mw,
            "reason": "Flexible demand reduction via mathematical optimization.",
        })

    total_support = result.total_dispatch

    return {
        "status": result.status,
        "initial_deficit_mw": round(result.deficit, 3),
        "total_support_mw": round(total_support, 3),
        "remaining_gap_mw": result.remaining_gap,
        "zone_analysis": zone_analysis,
        "recommended_deployment": deployment,
    }
