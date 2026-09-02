"""Phase 3 verification tests: mathematical optimization engine.

Tests for:
- Basic deficit scenario
- Supply sufficient scenario
- No renewable availability
- Zone cap constraint
- JSON serialization
- Fallback to heuristic optimizer
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from backend.optimizer_math import (
    OptimizationResult,
    optimize_mathematical,
    math_result_to_dict,
    _solve_lp,
    _build_resource_pool,
    RESOURCES,
    BATTERY_COST,
    FLEX_DEMAND_COST,
    UNSERVED_PENALTY,
    BATTERY_VAR,
    FLEX_DEMAND_VAR,
    UNSERVED_VAR,
    TOTAL_VARS,
    NUM_ZONES,
    NUM_RESOURCES,
    _zr_index,
)


# =========================================================
# FIXTURES
# =========================================================

def _make_solar_data(mw_per_1mw=0.15, zones=None):
    if zones is None:
        zones = [
            "Dhaka", "Chittagong", "Khulna", "Rajshahi",
            "Comilla", "Mymensingh", "Sylhet", "Barishal", "Rangpur",
        ]
    return {
        "current_hour_generation": {
            "mw_per_1mw_installed": mw_per_1mw,
        },
        "zone_ranking": [
            {"zone": z, "expected_energy_mwh_per_1mw_24h": 3.5}
            for z in zones
        ],
    }


def _make_wind_data(mw_per_1mw=0.20, zones=None):
    if zones is None:
        zones = [
            "Dhaka", "Chittagong", "Khulna", "Rajshahi",
            "Comilla", "Mymensingh", "Sylhet", "Barishal", "Rangpur",
        ]
    return {
        "current_hour_generation": {
            "mw_per_1mw_installed": mw_per_1mw,
        },
        "zone_ranking": [
            {"zone": z, "expected_energy_mwh_per_1mw_24h": 4.0}
            for z in zones
        ],
    }


def _empty_biomass():
    return {
        "Dhaka": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Chattogram": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Rajshahi": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Khulna": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Barishal": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Sylhet": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Rangpur": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
        "Mymensingh": {"average_potential_mw": 0, "dispatchable_mw": 0, "electricity_potential_mwh_year": 0},
    }


def _empty_waste():
    return {
        z: {"dispatchable_mw": 0, "available_mw": 0, "electricity_mwh_year": 0}
        for z in [
            "Dhaka", "Chittagong", "Khulna", "Rajshahi",
            "Comilla", "Mymensingh", "Sylhet", "Barishal", "Rangpur",
        ]
    }


# =========================================================
# BASIC DEFICIT SCENARIO
# =========================================================

class TestBasicDeficit:
    """Math optimizer should cover deficit using available resources."""

    def test_deficit_fully_covered(self):
        """LP should dispatch enough to close a 100 MW deficit."""
        result = optimize_mathematical(
            demand_mw=5000.0,
            supply_mw=4900.0,
            solar_data=_make_solar_data(0.15),
            wind_data=_make_wind_data(0.20),
            battery_mw=500.0,
            flexible_demand_mw=500.0,
        )
        assert result is not None
        assert result.status == "DEFICIT_COVERED"
        assert result.remaining_gap <= 0.01
        assert result.total_dispatch >= 99.0

    def test_deficit_larger_than_renewables(self):
        """When deficit exceeds renewables, battery and flex fill gap."""
        result = optimize_mathematical(
            demand_mw=5500.0,
            supply_mw=5000.0,
            solar_data=_make_solar_data(0.10),
            wind_data=_make_wind_data(0.10),
            battery_mw=500.0,
            flexible_demand_mw=500.0,
        )
        assert result is not None
        # deficit=500, renewables ~150, battery+flex=1000 -> covered
        assert result.status == "DEFICIT_COVERED"
        assert result.remaining_gap <= 0.01

    def test_large_deficit_with_no_backup(self):
        """Deficit beyond available resources leaves a gap."""
        result = optimize_mathematical(
            demand_mw=20000.0,
            supply_mw=15000.0,
            solar_data=_make_solar_data(0.01),
            wind_data=_make_wind_data(0.01),
            battery_mw=0.0,
            flexible_demand_mw=0.0,
        )
        assert result is not None
        assert result.status == "DEFICIT_REMAINS"
        assert result.remaining_gap > 0.0


# =========================================================
# SUPPLY SUFFICIENT SCENARIO
# =========================================================

class TestSupplySufficient:
    """No deficit should yield SUPPLY_SUFFICIENT with zero dispatch."""

    def test_no_deficit(self):
        result = optimize_mathematical(
            demand_mw=4000.0,
            supply_mw=5000.0,
            solar_data=_make_solar_data(),
            wind_data=_make_wind_data(),
        )
        assert result is not None
        assert result.status == "SUPPLY_SUFFICIENT"
        assert result.total_dispatch == 0.0
        assert result.remaining_gap == 0.0

    def test_exact_balance(self):
        result = optimize_mathematical(
            demand_mw=5000.0,
            supply_mw=5000.0,
            solar_data=_make_solar_data(),
            wind_data=_make_wind_data(),
        )
        assert result is not None
        assert result.status == "SUPPLY_SUFFICIENT"


# =========================================================
# NO RENEWABLE AVAILABILITY
# =========================================================

class TestNoRenewables:
    """When solar and wind output is zero, only backup resources dispatch."""

    def test_zero_solar_zero_wind(self):
        result = optimize_mathematical(
            demand_mw=5000.0,
            supply_mw=4500.0,
            solar_data=_make_solar_data(0.0),
            wind_data=_make_wind_data(0.0),
            biomass_divisions=_empty_biomass(),
            waste_zones=_empty_waste(),
            battery_mw=500.0,
            flexible_demand_mw=500.0,
        )
        assert result is not None
        assert result.status == "DEFICIT_COVERED"
        assert result.remaining_gap <= 0.01
        # Only battery and flex demand should be dispatched
        assert result.battery_mw > 0.0 or result.flex_demand_mw > 0.0

    def test_nighttime_solar_zero(self):
        """Solar current_hour=0 at night; only wind + backup."""
        solar_night = _make_solar_data(0.0)
        result = optimize_mathematical(
            demand_mw=5000.0,
            supply_mw=4800.0,
            solar_data=solar_night,
            wind_data=_make_wind_data(0.20),
            battery_mw=500.0,
            flexible_demand_mw=500.0,
        )
        assert result is not None
        assert result.status == "DEFICIT_COVERED"


# =========================================================
# ZONE CAP CONSTRAINT
# =========================================================

class TestZoneCap:
    """No single zone should dispatch more than 40% of deficit."""

    def test_zone_cap_respected(self):
        deficit = 1000.0
        result = optimize_mathematical(
            demand_mw=5000.0,
            supply_mw=4000.0,
            solar_data=_make_solar_data(0.50),
            wind_data=_make_wind_data(0.50),
            battery_mw=0.0,
            flexible_demand_mw=0.0,
        )
        assert result is not None
        zone_cap = 0.40 * deficit
        for zone, dispatches in result.zone_dispatches.items():
            total_zone = sum(dispatches.values())
            assert total_zone <= zone_cap + 0.01, (
                f"Zone {zone} dispatch {total_zone:.3f} "
                f"exceeds cap {zone_cap:.3f}"
            )

    def test_zone_cap_with_abundant_resource(self):
        """Even if one zone has huge solar, cap still applies."""
        deficit = 2000.0
        result = optimize_mathematical(
            demand_mw=6000.0,
            supply_mw=4000.0,
            solar_data=_make_solar_data(1.0),
            wind_data=_make_wind_data(1.0),
            battery_mw=0.0,
            flexible_demand_mw=0.0,
        )
        assert result is not None
        zone_cap = 0.40 * deficit
        for zone, dispatches in result.zone_dispatches.items():
            total_zone = sum(dispatches.values())
            assert total_zone <= zone_cap + 0.01


# =========================================================
# JSON SERIALIZATION
# =========================================================

class TestJsonSerialization:
    """OptimizationResult and conversion dict must be JSON-serializable."""

    def test_result_dataclass_to_dict(self):
        result = OptimizationResult(
            status="DEFICIT_COVERED",
            deficit=150.0,
            total_dispatch=150.0,
            remaining_gap=0.0,
            zone_dispatches={"Dhaka": {"solar": 100.0, "wind": 50.0}},
            battery_mw=0.0,
            flex_demand_mw=0.0,
            objective_value=500.0,
        )
        d = {
            "status": result.status,
            "deficit": result.deficit,
            "total_dispatch": result.total_dispatch,
            "remaining_gap": result.remaining_gap,
            "zone_dispatches": result.zone_dispatches,
            "battery_mw": result.battery_mw,
            "flex_demand_mw": result.flex_demand_mw,
            "objective_value": result.objective_value,
        }
        serialized = json.dumps(d)
        restored = json.loads(serialized)
        assert restored["status"] == "DEFICIT_COVERED"
        assert restored["zone_dispatches"]["Dhaka"]["solar"] == 100.0

    def test_math_result_to_dict_serializable(self):
        result = optimize_mathematical(
            demand_mw=5000.0,
            supply_mw=4900.0,
            solar_data=_make_solar_data(0.15),
            wind_data=_make_wind_data(0.20),
            battery_mw=500.0,
            flexible_demand_mw=500.0,
        )
        assert result is not None
        d = math_result_to_dict(
            result,
            _make_solar_data(0.15),
            _make_wind_data(0.20),
        )
        serialized = json.dumps(d)
        restored = json.loads(serialized)
        assert "status" in restored
        assert "recommended_deployment" in restored
        assert "zone_analysis" in restored

    def test_full_optimize_dict_serializable(self):
        from backend.optimizer import optimize
        d = optimize(
            demand_mw=5000.0,
            supply_mw=4900.0,
            solar_data=_make_solar_data(0.15),
            wind_data=_make_wind_data(0.20),
            battery_mw=500.0,
            flexible_demand_mw=500.0,
        )
        serialized = json.dumps(d)
        restored = json.loads(serialized)
        assert restored["status"] in (
            "DEFICIT_COVERED", "DEFICIT_REMAINS", "SUPPLY_SUFFICIENT"
        )


# =========================================================
# FALLBACK TO HEURISTIC
# =========================================================

class TestFallbackToHeuristic:
    """If math optimizer fails, heuristic should produce a result."""

    def test_fallback_on_solver_failure(self):
        """When linprog raises, optimize() still returns a result."""
        with patch(
            "backend.optimizer_math.linprog",
            side_effect=RuntimeError("solver crash"),
        ):
            from backend.optimizer import optimize
            d = optimize(
                demand_mw=5000.0,
                supply_mw=4900.0,
                solar_data=_make_solar_data(0.15),
                wind_data=_make_wind_data(0.20),
                battery_mw=500.0,
                flexible_demand_mw=500.0,
            )
            assert "status" in d
            assert d["status"] in (
                "DEFICIT_COVERED", "DEFICIT_REMAINS"
            )
            assert "remaining_gap_mw" in d

    def test_fallback_on_import_error(self):
        """When optimizer_math cannot be imported, heuristic runs."""
        import builtins
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "backend.optimizer_math":
                raise ImportError("no optimizer_math")
            return real_import(name, *args, **kwargs)

        with patch.object(builtins, "__import__", side_effect=mock_import):
            from backend.optimizer import optimize
            d = optimize(
                demand_mw=5000.0,
                supply_mw=4900.0,
                solar_data=_make_solar_data(0.15),
                wind_data=_make_wind_data(0.20),
                battery_mw=500.0,
                flexible_demand_mw=500.0,
            )
            assert "status" in d
            assert d["status"] in (
                "DEFICIT_COVERED", "DEFICIT_REMAINS"
            )

    def test_math_optimizer_returns_none_fallback(self):
        """When math optimizer returns None, heuristic is used."""
        with patch(
            "backend.optimizer_math.optimize_mathematical",
            return_value=None,
        ):
            from backend.optimizer import optimize
            d = optimize(
                demand_mw=5000.0,
                supply_mw=4900.0,
                solar_data=_make_solar_data(0.15),
                wind_data=_make_wind_data(0.20),
                battery_mw=500.0,
                flexible_demand_mw=500.0,
            )
            assert "status" in d
            assert d["status"] in (
                "DEFICIT_COVERED", "DEFICIT_REMAINS"
            )


# =========================================================
# LP STRUCTURE VALIDATION
# =========================================================

class TestLPStructure:
    """Validate LP variable indexing and cost structure."""

    def test_zr_index_covers_all_zones_resources(self):
        for zi in range(NUM_ZONES):
            for ri in range(NUM_RESOURCES):
                idx = _zr_index(zi, ri)
                assert 0 <= idx < NUM_ZONES * NUM_RESOURCES

    def test_total_vars_count(self):
        assert TOTAL_VARS == NUM_ZONES * NUM_RESOURCES + 3

    def test_backup_indices_are_last(self):
        assert BATTERY_VAR == NUM_ZONES * NUM_RESOURCES
        assert FLEX_DEMAND_VAR == NUM_ZONES * NUM_RESOURCES + 1
        assert UNSERVED_VAR == NUM_ZONES * NUM_RESOURCES + 2

    def test_renewables_are_zero_cost(self):
        from backend.optimizer_math import RESOURCE_COSTS
        assert RESOURCE_COSTS["solar"] == 0.0
        assert RESOURCE_COSTS["wind"] == 0.0

    def test_unserved_penalty_is_high(self):
        assert UNSERVED_PENALTY >= 1000.0

    def test_battery_and_flex_have_costs(self):
        assert BATTERY_COST > 0.0
        assert FLEX_DEMAND_COST > 0.0


# =========================================================
# EDGE CASES
# =========================================================

class TestEdgeCases:
    """Boundary conditions and zero-value inputs."""

    def test_zero_demand(self):
        result = optimize_mathematical(
            demand_mw=0.0,
            supply_mw=0.0,
            solar_data=_make_solar_data(),
            wind_data=_make_wind_data(),
        )
        assert result is not None
        assert result.status == "SUPPLY_SUFFICIENT"

    def test_negative_deficit_treated_as_zero(self):
        result = optimize_mathematical(
            demand_mw=3000.0,
            supply_mw=5000.0,
            solar_data=_make_solar_data(),
            wind_data=_make_wind_data(),
        )
        assert result is not None
        assert result.status == "SUPPLY_SUFFICIENT"

    def test_zero_battery_zero_flex(self):
        """With no backup, deficit may remain."""
        result = optimize_mathematical(
            demand_mw=50000.0,
            supply_mw=40000.0,
            solar_data=_make_solar_data(0.01),
            wind_data=_make_wind_data(0.01),
            battery_mw=0.0,
            flexible_demand_mw=0.0,
        )
        assert result is not None
        assert result.status == "DEFICIT_REMAINS"

    def test_build_resource_pool_length(self):
        pools = _build_resource_pool(
            _make_solar_data(),
            _make_wind_data(),
            None,
            None,
        )
        assert len(pools) == NUM_ZONES

    def test_build_resource_pool_has_all_resources(self):
        pools = _build_resource_pool(
            _make_solar_data(),
            _make_wind_data(),
            None,
            None,
        )
        for pool in pools:
            for res in RESOURCES:
                assert res in pool
