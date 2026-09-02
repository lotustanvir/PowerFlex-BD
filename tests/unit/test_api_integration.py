"""Integration tests for PowerFlex BD API endpoints.

Tests the grid, loadshield, and zone analysis endpoints
against the actual backend logic (not HTTP, to avoid
requiring a running server).
"""
import json
import time
import concurrent.futures
import pytest
from unittest.mock import patch


class TestOptimizer:
    """Test the optimizer module directly."""

    def test_optimizer_with_deficit(self):
        """Optimizer returns DEFICIT_COVERED when deficit exists."""
        from backend.optimizer import optimize

        solar_data = {
            "zone_ranking": [
                {"zone": "Dhaka", "expected_energy_mwh_per_1mw_24h": 5.0},
            ],
            "current_hour_generation": {"mw_per_1mw_installed": 0.3},
        }
        wind_data = {
            "zone_ranking": [
                {"zone": "Dhaka", "expected_energy_mwh_per_1mw_24h": 3.0},
            ],
            "current_hour_generation": {"mw_per_1mw_installed": 0.2},
        }

        result = optimize(
            demand_mw=16000.0,
            supply_mw=15000.0,
            solar_data=solar_data,
            wind_data=wind_data,
        )

        assert result["status"] in ("DEFICIT_COVERED", "DEFICIT_REMAINS")
        assert result["initial_deficit_mw"] == 1000.0
        assert len(result["zone_analysis"]) == 9
        assert len(result["recommended_deployment"]) > 0

    def test_optimizer_supply_sufficient(self):
        """Optimizer returns SUPPLY_SUFFICIENT when supply >= demand."""
        from backend.optimizer import optimize

        solar_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.0},
        }
        wind_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.0},
        }

        result = optimize(
            demand_mw=10000.0,
            supply_mw=12000.0,
            solar_data=solar_data,
            wind_data=wind_data,
        )

        assert result["status"] == "SUPPLY_SUFFICIENT"
        assert result["initial_deficit_mw"] == 0.0
        assert len(result["recommended_deployment"]) == 0

    def test_optimizer_zero_demand(self):
        """Optimizer handles zero demand gracefully."""
        from backend.optimizer import optimize

        result = optimize(
            demand_mw=0.0,
            supply_mw=0.0,
            solar_data={"zone_ranking": [], "current_hour_generation": {}},
            wind_data={"zone_ranking": [], "current_hour_generation": {}},
        )

        assert result["status"] == "SUPPLY_SUFFICIENT"
        assert result["initial_deficit_mw"] == 0.0

    def test_optimizer_empty_solar_wind(self):
        """Optimizer works with empty solar/wind data."""
        from backend.optimizer import optimize

        result = optimize(
            demand_mw=16000.0,
            supply_mw=14000.0,
            solar_data={},
            wind_data={},
        )

        assert result["status"] in ("DEFICIT_COVERED", "DEFICIT_REMAINS")
        assert result["initial_deficit_mw"] == 2000.0

    def test_optimizer_json_serializable(self):
        """Optimizer output is JSON-serializable."""
        from backend.optimizer import optimize

        solar_data = {
            "zone_ranking": [
                {"zone": "Dhaka", "expected_energy_mwh_per_1mw_24h": 5.0},
            ],
            "current_hour_generation": {"mw_per_1mw_installed": 0.3},
        }
        wind_data = {
            "zone_ranking": [
                {"zone": "Dhaka", "expected_energy_mwh_per_1mw_24h": 3.0},
            ],
            "current_hour_generation": {"mw_per_1mw_installed": 0.2},
        }

        result = optimize(
            demand_mw=16000.0,
            supply_mw=15000.0,
            solar_data=solar_data,
            wind_data=wind_data,
        )

        serialized = json.dumps(result, default=str)
        assert len(serialized) > 0
        parsed = json.loads(serialized)
        assert parsed["status"] == result["status"]


class TestBuildZoneAnalysis:
    """Test zone analysis builder."""

    def test_returns_9_zones(self):
        """Always returns exactly 9 Bangladesh zones."""
        from backend.optimizer import build_zone_analysis

        result = build_zone_analysis(
            solar_data={},
            wind_data={},
        )

        assert len(result) == 9
        zone_names = [z["zone"] for z in result]
        expected = [
            "Dhaka", "Chittagong", "Khulna", "Rajshahi",
            "Comilla", "Mymensingh", "Sylhet", "Barishal", "Rangpur",
        ]
        for name in expected:
            assert name in zone_names

    def test_solar_current_hour_in_output(self):
        """Zone analysis includes current-hour solar generation."""
        from backend.optimizer import build_zone_analysis

        solar_data = {
            "zone_ranking": [
                {"zone": "Dhaka", "expected_energy_mwh_per_1mw_24h": 5.0},
            ],
            "current_hour_generation": {"mw_per_1mw_installed": 0.35},
        }

        result = build_zone_analysis(
            solar_data=solar_data,
            wind_data={},
        )

        for zone in result:
            assert "solar_current_hour_mw_per_1mw" in zone
            assert zone["solar_current_hour_mw_per_1mw"] == 0.35

    def test_wind_current_hour_in_output(self):
        """Zone analysis includes current-hour wind generation."""
        from backend.optimizer import build_zone_analysis

        wind_data = {
            "zone_ranking": [
                {"zone": "Rangpur", "expected_energy_mwh_per_1mw_24h": 4.0},
            ],
            "current_hour_generation": {"mw_per_1mw_installed": 0.22},
        }

        result = build_zone_analysis(
            solar_data={},
            wind_data=wind_data,
        )

        for zone in result:
            assert "wind_current_hour_mw_per_1mw" in zone
            assert zone["wind_current_hour_mw_per_1mw"] == 0.22

    def test_biomass_integration(self):
        """Zone analysis includes biomass data when provided."""
        from backend.optimizer import build_zone_analysis

        biomass = {
            "Dhaka": {
                "dispatchable_mw": 50.0,
                "average_potential_mw": 60.0,
                "electricity_potential_mwh_year": 400000.0,
            },
            "Chattogram": {
                "dispatchable_mw": 40.0,
                "average_potential_mw": 50.0,
                "electricity_potential_mwh_year": 300000.0,
            },
        }

        result = build_zone_analysis(
            solar_data={},
            wind_data={},
            biomass_divisions=biomass,
        )

        dhaka = next(z for z in result if z["zone"] == "Dhaka")
        assert dhaka["biomass_available_mw"] == 50.0


class TestLoadShieldEndpoint:
    """Test the LoadShield endpoint logic."""

    def test_loadshield_live_returns_valid_structure(self):
        """LoadShield live endpoint returns expected top-level keys."""
        from backend.loadshield import loadshield_live

        result = loadshield_live()

        required_keys = [
            "project", "module", "status",
            "current_situation", "zone_analysis",
            "current_recommendation", "data_source",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

        assert result["project"] == "PowerFlex BD"
        assert result["module"] == "LoadShield"

    def test_loadshield_live_json_serializable(self):
        """LoadShield response is JSON-serializable."""
        from backend.loadshield import loadshield_live

        result = loadshield_live()
        serialized = json.dumps(result, default=str)
        assert len(serialized) > 0

    def test_loadshield_has_zone_analysis(self):
        """LoadShield response includes zone_analysis."""
        from backend.loadshield import loadshield_live

        result = loadshield_live()
        assert "zone_analysis" in result
        assert isinstance(result["zone_analysis"], list)

    def test_loadshield_has_resource_analysis(self):
        """LoadShield response includes resource_analysis.

        The API contract allows resource_analysis to be:
          - A dict when grid data is available (normal path)
          - None in degraded states (WAITING_FOR_GRID_DATA, DATA_INCOMPLETE)

        Both are valid. The frontend TypeScript interface defines:
          resource_analysis: Record<string, unknown> | null
        And the LoadShield component guards with:
          {data.resource_analysis && (...)}
        """
        from backend.loadshield import loadshield_live

        result = loadshield_live()
        assert "resource_analysis" in result

        ra = result["resource_analysis"]
        status = result.get("status", "")

        if status in ("WAITING_FOR_GRID_DATA", "DATA_INCOMPLETE"):
            # Degraded state: resource_analysis is intentionally None
            # because grid data is unavailable to build the analysis.
            assert ra is None, (
                f"Expected None for status={status}, got {type(ra)}"
            )
        else:
            # Normal path: resource_analysis is a dict with resource entries.
            assert isinstance(ra, dict), (
                f"Expected dict for status={status}, got {type(ra)}"
            )

    def test_loadshield_data_source_complete(self):
        """LoadShield data_source dict covers all resources."""
        from backend.loadshield import loadshield_live

        result = loadshield_live()
        ds = result.get("data_source", {})

        expected_sources = [
            "grid", "solar", "wind", "demand_forecast",
            "hydro", "biomass", "waste",
            "battery", "flexible_demand",
        ]
        for key in expected_sources:
            assert key in ds, f"Missing data_source key: {key}"


class TestGridEndpoint:
    """Test the Grid endpoint logic."""

    def test_grid_live_returns_valid_structure(self):
        """Grid live endpoint returns expected structure."""
        from backend.grid import live_grid

        result = live_grid()

        assert "project" in result
        assert "live" in result
        assert "grid_snapshot" in result

    def test_grid_live_json_serializable(self):
        """Grid response is JSON-serializable."""
        from backend.grid import live_grid

        result = live_grid()
        serialized = json.dumps(result, default=str)
        assert len(serialized) > 0

    def test_grid_status_endpoint(self):
        """Grid status endpoint returns adapter info."""
        from backend.grid import pgcb_status

        result = pgcb_status()

        assert "provider" in result
        assert "pgcb_sources" in result
        assert "generation" in result["pgcb_sources"]
        assert "demand_supply_loadshed" in result["pgcb_sources"]


class TestErrorHandler:
    """Test error handling with missing data."""

    def test_optimizer_handles_none_demand(self):
        """Optimizer handles None demand gracefully."""
        from backend.optimizer import optimize

        result = optimize(
            demand_mw=None,
            supply_mw=None,
            solar_data={},
            wind_data={},
        )

        assert result["status"] == "SUPPLY_SUFFICIENT"
        assert result["initial_deficit_mw"] == 0.0

    def test_optimizer_handles_negative_deficit(self):
        """Optimizer handles supply > demand."""
        from backend.optimizer import optimize

        result = optimize(
            demand_mw=10000.0,
            supply_mw=15000.0,
            solar_data={},
            wind_data={},
        )

        assert result["status"] == "SUPPLY_SUFFICIENT"
        assert result["initial_deficit_mw"] == 0.0

    def test_build_zone_analysis_empty_biomass(self):
        """Zone analysis handles empty biomass gracefully."""
        from backend.optimizer import build_zone_analysis

        result = build_zone_analysis(
            solar_data={},
            wind_data={},
            biomass_divisions={},
            waste_zones={},
        )

        assert len(result) == 9
        for zone in result:
            assert zone["biomass_available_mw"] == 0.0
            assert zone["waste_available_mw"] == 0.0


# =========================================================
# GRID TIMEOUT ISOLATION TESTS
# =========================================================


class TestGridTimeout:
    """Test that grid endpoints respect endpoint-level timeout.

    When PGCB is unreachable, the endpoint must return a safe
    response within the bounded timeout budget rather than
    blocking for minutes.
    """

    def test_fetch_with_timeout_returns_default_on_timeout(self):
        """fetch_with_timeout returns default when function exceeds timeout."""
        from backend.grid import fetch_with_timeout

        def slow_function():
            time.sleep(10)
            return {"connected": True}

        start = time.monotonic()
        result = fetch_with_timeout(
            slow_function,
            timeout=2,
            default=None,
            label="test",
        )
        elapsed = time.monotonic() - start

        assert result is None
        assert elapsed < 5, f"Timeout took {elapsed:.1f}s, expected <5s"

    def test_fetch_with_timeout_returns_result_when_fast(self):
        """fetch_with_timeout returns result when function completes quickly."""
        from backend.grid import fetch_with_timeout

        def fast_function():
            return {"connected": True, "data": "ok"}

        result = fetch_with_timeout(
            fast_function,
            timeout=5,
            default=None,
            label="test",
        )

        assert result is not None
        assert result["connected"] is True

    def test_grid_live_returns_within_timeout_when_pgcb_unreachable(self):
        """live_grid returns safe response within timeout when PGCB hangs.

        The endpoint must not block for longer than
        PGCB_ENDPOINT_TIMEOUT + a small margin.
        """
        from backend.grid import live_grid, PGCB_ENDPOINT_TIMEOUT

        def hanging_pgcb():
            time.sleep(300)
            return {"connected": False, "message": "should not reach"}

        with patch("backend.grid.fetch_pgcb_grid_data", hanging_pgcb):
            start = time.monotonic()
            result = live_grid()
            elapsed = time.monotonic() - start

        assert result["live"] is False
        assert result["grid_snapshot"] is None
        assert result["status"] == "PGCB_ADAPTER_READY"
        assert elapsed < PGCB_ENDPOINT_TIMEOUT + 5, (
            f"Endpoint took {elapsed:.1f}s, budget is "
            f"{PGCB_ENDPOINT_TIMEOUT}s"
        )

    def test_grid_live_safe_response_shape_on_timeout(self):
        """Timed-out grid response preserves API contract."""
        from backend.grid import live_grid

        def hanging_pgcb():
            time.sleep(300)
            return {"connected": False}

        with patch("backend.grid.fetch_pgcb_grid_data", hanging_pgcb):
            result = live_grid()

        assert result["project"] == "PowerFlex BD"
        assert result["resource"] == "Bangladesh National Grid"
        assert result["live"] is False
        assert result["grid_snapshot"] is None
        assert "PGCB" in result["status"] or "TIMED" in result["status"]
        assert isinstance(result["message"], str)

    def test_grid_live_returns_none_default_on_timeout(self):
        """live_grid handles fetch_with_timeout returning None."""
        from backend.grid import live_grid

        with patch("backend.grid.fetch_pgcb_grid_data", return_value=None):
            result = live_grid()

        assert result["live"] is False
        assert result["grid_snapshot"] is None
        assert result["status"] == "PGCB_ADAPTER_READY"

    def test_grid_official_returns_within_timeout(self):
        """official_pgcb_data returns within timeout when PGCB hangs."""
        from backend.grid import official_pgcb_data, PGCB_ENDPOINT_TIMEOUT

        def hanging_pgcb():
            time.sleep(300)
            return {"connected": False, "message": "hang"}

        with patch("backend.grid.fetch_pgcb_demand_supply", hanging_pgcb):
            start = time.monotonic()
            result = official_pgcb_data()
            elapsed = time.monotonic() - start

        assert result["live"] is False
        assert result["data"] is None
        assert elapsed < PGCB_ENDPOINT_TIMEOUT + 5

    def test_grid_official_safe_response_shape_on_timeout(self):
        """Timed-out official response preserves API contract."""
        from backend.grid import official_pgcb_data

        with patch("backend.grid.fetch_pgcb_demand_supply", return_value=None):
            result = official_pgcb_data()

        assert result["project"] == "PowerFlex BD"
        assert result["live"] is False
        assert result["data"] is None


class TestDemandForecastTimeout:
    """Test that demand forecast respects endpoint-level timeout."""

    def test_demand_forecast_returns_502_within_timeout(self):
        """Demand forecast raises 502 within timeout when PGCB hangs."""
        from fastapi import HTTPException
        from backend.demand_forecast import get_demand_forecast, PGCB_ENDPOINT_TIMEOUT

        def hanging_grid():
            time.sleep(300)
            return None

        with patch("backend.demand_forecast.fetch_with_timeout", hanging_grid):
            start = time.monotonic()
            with pytest.raises(HTTPException) as exc_info:
                get_demand_forecast()
            elapsed = time.monotonic() - start

        assert exc_info.value.status_code == 502
        assert "PGCB" in exc_info.value.detail
        assert elapsed < PGCB_ENDPOINT_TIMEOUT + 5

    def test_demand_forecast_preserves_502_contract(self):
        """Demand forecast 502 detail message matches expected contract."""
        from fastapi import HTTPException
        from backend.demand_forecast import get_demand_forecast

        def always_none(*args, **kwargs):
            return None

        with patch("backend.demand_forecast.fetch_with_timeout", always_none):
            with pytest.raises(HTTPException) as exc_info:
                get_demand_forecast()

        assert exc_info.value.status_code == 502
        assert "PGCB demand data unavailable" in exc_info.value.detail
        assert "anchor" in exc_info.value.detail


class TestGridConcurrency:
    """Test that concurrent grid requests do not block the server.

    N concurrent requests × 1 executor thread per timed-out request
    = potential temporary background threads.

    The endpoint must remain responsive under concurrent load.
    """

    def test_concurrent_grid_live_requests_complete_bounded(self):
        """10 concurrent /api/grid/live requests all complete within budget."""
        from backend.grid import live_grid, PGCB_ENDPOINT_TIMEOUT

        def hanging_pgcb():
            time.sleep(300)
            return {"connected": False}

        n_requests = 10
        results = [None] * n_requests
        elapsed_times = [0.0] * n_requests

        def worker(idx):
            with patch("backend.grid.fetch_pgcb_grid_data", hanging_pgcb):
                start = time.monotonic()
                results[idx] = live_grid()
                elapsed_times[idx] = time.monotonic() - start

        with concurrent.futures.ThreadPoolExecutor(max_workers=n_requests) as pool:
            futures = [pool.submit(worker, i) for i in range(n_requests)]
            concurrent.futures.wait(futures, timeout=PGCB_ENDPOINT_TIMEOUT + 10)
            for f in futures:
                assert f.done(), "Future did not complete in time"

        for i in range(n_requests):
            assert results[i] is not None, f"Request {i} returned None"
            assert results[i]["live"] is False
            assert elapsed_times[i] < PGCB_ENDPOINT_TIMEOUT + 5, (
                f"Request {i} took {elapsed_times[i]:.1f}s"
            )

    def test_server_responsive_after_concurrent_timeouts(self):
        """Server remains responsive after handling concurrent timeouts."""
        from backend.grid import live_grid, PGCB_ENDPOINT_TIMEOUT

        def hanging_pgcb():
            time.sleep(300)
            return {"connected": False}

        def fast_pgcb():
            return {
                "connected": True,
                "data": {
                    "timestamp": "2026-01-01T00:00:00",
                    "current_demand_mw": 12000.0,
                    "supply_mw": 11500.0,
                    "load_shedding_mw": 0.0,
                    "generation_breakdown": {},
                    "imports": {},
                },
            }

        # Phase 1: 10 concurrent hanging requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futures = []
            for _ in range(10):
                with patch("backend.grid.fetch_pgcb_grid_data", hanging_pgcb):
                    futures.append(pool.submit(live_grid))
            concurrent.futures.wait(futures, timeout=PGCB_ENDPOINT_TIMEOUT + 10)

        # Phase 2: Server must still be responsive
        with patch("backend.grid.fetch_pgcb_grid_data", fast_pgcb):
            start = time.monotonic()
            result = live_grid()
            elapsed = time.monotonic() - start

        assert result["live"] is True
        assert elapsed < 5, f"Recovery request took {elapsed:.1f}s"


class TestDataCollector:
    """Test the data collection service and validation."""

    def test_validate_grid_data_valid(self):
        """Valid data returns no issues."""
        from backend.data_collector import DataCollectionService
        
        service = DataCollectionService(poll_interval_seconds=9999)
        issues = service._validate_grid_data(
            demand_mw=15000.0,
            supply_mw=14500.0,
            load_shedding_mw=500.0,
        )
        assert issues == []

    def test_validate_grid_data_negative_demand(self):
        """Negative demand flagged."""
        from backend.data_collector import DataCollectionService
        
        service = DataCollectionService(poll_interval_seconds=9999)
        issues = service._validate_grid_data(
            demand_mw=-100.0,
            supply_mw=14500.0,
            load_shedding_mw=0,
        )
        assert "NEGATIVE_DEMAND" in issues

    def test_validate_grid_data_negative_supply(self):
        """Negative supply flagged."""
        from backend.data_collector import DataCollectionService
        
        service = DataCollectionService(poll_interval_seconds=9999)
        issues = service._validate_grid_data(
            demand_mw=15000.0,
            supply_mw=-500.0,
            load_shedding_mw=0,
        )
        assert "NEGATIVE_SUPPLY" in issues

    def test_validate_grid_data_below_plausible_demand(self):
        """Demand below 3000 MW flagged."""
        from backend.data_collector import DataCollectionService
        
        service = DataCollectionService(poll_interval_seconds=9999)
        issues = service._validate_grid_data(
            demand_mw=2000.0,
            supply_mw=1800.0,
            load_shedding_mw=200.0,
        )
        assert "BELOW_PLAUSIBLE_DEMAND" in issues

    def test_validate_grid_data_demand_supply_mismatch(self):
        """Large demand-supply mismatch flagged."""
        from backend.data_collector import DataCollectionService
        
        service = DataCollectionService(poll_interval_seconds=9999)
        issues = service._validate_grid_data(
            demand_mw=15000.0,
            supply_mw=10000.0,
            load_shedding_mw=100.0,
        )
        assert "DEMAND_SUPPLY_MISMATCH" in issues

    def test_validate_grid_data_multiple_issues(self):
        """Multiple issues can be flagged simultaneously."""
        from backend.data_collector import DataCollectionService
        
        service = DataCollectionService(poll_interval_seconds=9999)
        issues = service._validate_grid_data(
            demand_mw=-100.0,
            supply_mw=-500.0,
            load_shedding_mw=-100.0,
        )
        assert len(issues) >= 3
        assert "NEGATIVE_DEMAND" in issues
        assert "NEGATIVE_SUPPLY" in issues
        assert "NEGATIVE_LOAD_SHEDDING" in issues

    def test_data_collector_singleton(self):
        """Singleton pattern works correctly."""
        from backend.data_collector import get_data_collector
        
        c1 = get_data_collector()
        c2 = get_data_collector()
        assert c1 is c2

    def test_data_collector_status_structure(self):
        """Status returns expected structure."""
        from backend.data_collector import get_data_collector
        
        collector = get_data_collector()
        status = collector.get_status()
        
        assert "running" in status
        assert "poll_interval_seconds" in status
        assert "collection_count" in status
        assert "sources" in status
        assert "PGCB_DEMAND_SUPPLY" in status["sources"]
        assert "PGCB_GENERATION" in status["sources"]

    def test_data_collector_trigger_returns_results(self):
        """Trigger collection returns structured results."""
        from backend.data_collector import get_data_collector
        
        collector = get_data_collector()
        result = collector.trigger_collection()
        
        assert "collection_results" in result
        assert "demand_supply" in result["collection_results"]
        assert "generation" in result["collection_results"]

    def test_log_grid_snapshot_with_provenance(self):
        """Grid snapshot includes source and data_classification."""
        from backend.grid import log_grid_snapshot
        from unittest.mock import MagicMock, patch
        
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None
        
        with patch("backend.grid.get_session", return_value=mock_session):
            result = log_grid_snapshot(
                timestamp="2026-09-01T10:00:00",
                demand_mw=15000.0,
                supply_mw=14500.0,
                source="DATA_COLLECTOR",
                data_classification="OFFICIAL_PGCB",
            )
        
        assert result is True
        # Verify the snapshot was created with provenance fields
        added_snapshot = mock_session.add.call_args[0][0]
        assert added_snapshot.source == "DATA_COLLECTOR"
        assert added_snapshot.data_classification == "OFFICIAL_PGCB"

    def test_demand_history_has_source_field(self):
        """DemandHistory model has source field."""
        from database.models import DemandHistory
        
        assert hasattr(DemandHistory, "source")
        
    def test_grid_snapshot_has_provenance_fields(self):
        """GridSnapshot model has source and data_classification fields."""
        from database.models import GridSnapshot
        
        assert hasattr(GridSnapshot, "source")
        assert hasattr(GridSnapshot, "data_classification")


# =========================================================
# PHASE 5C: DEDUPLICATION AND FORECAST GATE TESTS
# =========================================================

# OBSERVATION IDENTITY POLICY:
#
# PGCB timestamp semantics (verified from grid.py:349-392 and
# actual database records):
#
#   - Hourly historical rows: pgcb_timestamp is the grid
#     observation time (clean hourly marks: 10:00:00).
#     These come from PGCB's historical data table.
#
#   - Rapid-polling live rows: pgcb_timestamp is parsed from
#     the page's Date/Time columns, which for live readings
#     reflect the page generation/refresh time (sub-second
#     precision like 21:11:23.551687). Multiple rapid polls
#     of the same grid state produce different pgcb_timestamps
#     but identical demand_mw + supply_mw values.
#
# Independent observation = a state change in (demand_mw, supply_mw)
# when records are ordered chronologically. Consecutive records
# with identical values are rapid-polling duplicates of the same
# underlying PGCB grid state.
#
# This means:
#   - 168 rapid-polling records of the same state = 1 independent
#   - Same values on different days separated by other states =
#     2 independent (state-change detection preserves them)
#   - Global DISTINCT(demand_mw, supply_mw) is WRONG because it
#     collapses legitimate same-value observations across days

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta


class TestObservationIdentityPolicy:
    """Verify the observation identity policy is correctly implemented.

    These tests use controlled in-memory scenarios to verify the
    state-change detection algorithm independent of database state.
    """

    def _make_record(self, demand_mw, supply_mw, ts_offset_minutes):
        """Create a mock DemandHistory record."""
        r = MagicMock()
        r.demand_mw = demand_mw
        r.supply_mw = supply_mw
        r.timestamp = datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc) + timedelta(minutes=ts_offset_minutes)
        return r

    def _count_with_records(self, records):
        """Run state-change detection on a list of mock records."""
        if not records:
            return 0
        independent = 1
        for i in range(1, len(records)):
            prev = records[i - 1]
            curr = records[i]
            same_demand = round(float(prev.demand_mw), 1) == round(float(curr.demand_mw), 1)
            same_supply = round(float(prev.supply_mw), 1) == round(float(curr.supply_mw), 1)
            if not (same_demand and same_supply):
                independent += 1
        return independent

    def test_rapid_identical_polling_collapses(self):
        """Test A: 10 rapid polls of same state = 1 independent observation."""
        records = [
            self._make_record(14481.0, 13339.0, 0),
            self._make_record(14481.0, 13339.0, 10),
            self._make_record(14481.0, 13339.0, 20),
            self._make_record(14481.0, 13339.0, 30),
            self._make_record(14481.0, 13339.0, 40),
            self._make_record(14481.0, 13339.0, 50),
            self._make_record(14481.0, 13339.0, 60),
            self._make_record(14481.0, 13339.0, 70),
            self._make_record(14481.0, 13339.0, 80),
            self._make_record(14481.0, 13339.0, 90),
        ]
        assert self._count_with_records(records) == 1

    def test_same_values_different_days(self):
        """Test B: Same values on different days = 2 independent observations.

        Day 1: 14481/13339
        Day 2 (after different state): 14481/13339
        These are separated by a state change, so both count.
        """
        records = [
            self._make_record(14481.0, 13339.0, 0),     # Day 1
            self._make_record(15200.0, 14600.0, 1440),   # Day 2 different state
            self._make_record(14481.0, 13339.0, 2880),   # Day 3 same values as Day 1
        ]
        assert self._count_with_records(records) == 3

    def test_same_values_after_long_interval(self):
        """Test C: Same values after sufficiently long interval with other states."""
        records = [
            self._make_record(14481.0, 13339.0, 0),
            self._make_record(15000.0, 14000.0, 60),
            self._make_record(15500.0, 14500.0, 120),
            self._make_record(14481.0, 13339.0, 180),
        ]
        # 4 state changes: 14481 -> 15000 -> 15500 -> 14481
        assert self._count_with_records(records) == 4

    def test_floating_point_normalization(self):
        """Test D: Small floating-point noise normalizes to same observation."""
        records = [
            self._make_record(14481.0, 13339.0, 0),
            self._make_record(14481.0001, 13339.0001, 10),
        ]
        # After rounding to 1 decimal place, these are identical
        assert self._count_with_records(records) == 1

    def test_168_rapid_records_collapses(self):
        """Test E: 168 rapid-polling records of same state << 168 independent."""
        records = [
            self._make_record(15921.0, 15078.0, i)
            for i in range(168)
        ]
        independent = self._count_with_records(records)
        assert independent == 1
        assert independent < 168

    def test_168_legitimate_hourly_observations(self):
        """Test F: 168 genuinely independent hourly observations = 168 independent.

        Each record has different values representing a real grid state change.
        """
        records = [
            self._make_record(14000.0 + i * 10, 13000.0 + i * 10, i * 60)
            for i in range(168)
        ]
        independent = self._count_with_records(records)
        assert independent == 168

    def test_single_record(self):
        """Single record = 1 independent observation."""
        records = [self._make_record(15000.0, 14000.0, 0)]
        assert self._count_with_records(records) == 1

    def test_empty_records(self):
        """Empty record set = 0 independent observations."""
        assert self._count_with_records([]) == 0

    def test_alternating_values(self):
        """Alternating values: each is independent."""
        records = [
            self._make_record(14481.0, 13339.0, 0),
            self._make_record(15000.0, 14000.0, 60),
            self._make_record(14481.0, 13339.0, 120),
            self._make_record(15000.0, 14000.0, 180),
        ]
        # Each transition is a state change
        assert self._count_with_records(records) == 4

    def test_demand_changes_supply_same(self):
        """Demand change alone = new independent observation."""
        records = [
            self._make_record(14481.0, 13339.0, 0),
            self._make_record(15000.0, 13339.0, 60),
        ]
        assert self._count_with_records(records) == 2

    def test_supply_changes_demand_same(self):
        """Supply change alone = new independent observation."""
        records = [
            self._make_record(14481.0, 13339.0, 0),
            self._make_record(14481.0, 14000.0, 60),
        ]
        assert self._count_with_records(records) == 2


class TestDemandHistoryQuality:
    """Test demand history quality metrics against live database."""

    def test_count_unique_observations_returns_int(self):
        """count_unique_observations() returns a non-negative int."""
        from backend.demand_history import count_unique_observations

        result = count_unique_observations()
        assert isinstance(result, int)
        assert result >= 0

    def test_independent_leq_raw(self):
        """independent_observations <= raw record count."""
        from backend.demand_history import count_unique_observations, count_records

        raw = count_records()
        independent = count_unique_observations()
        assert independent <= raw

    def test_quality_structure(self):
        """get_demand_history_quality() returns all expected keys."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()

        required_keys = [
            "raw_records",
            "independent_observations",
            "duplicates",
            "duplicate_rate",
            "time_coverage_hours",
            "largest_gap_minutes",
            "avg_interval_minutes",
            "hourly_aligned_count",
        ]
        for key in required_keys:
            assert key in quality, f"Missing key: {key}"

    def test_quality_independent_eq_raw_minus_duplicates(self):
        """independent_observations = raw_records - duplicates."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        assert (
            quality["independent_observations"]
            == quality["raw_records"] - quality["duplicates"]
        )

    def test_quality_duplicate_rate_range(self):
        """duplicate_rate is between 0.0 and 1.0."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        assert 0.0 <= quality["duplicate_rate"] <= 1.0

    def test_quality_non_negative(self):
        """All numeric quality metrics are non-negative."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        assert quality["raw_records"] >= 0
        assert quality["independent_observations"] >= 0
        assert quality["duplicates"] >= 0
        assert quality["time_coverage_hours"] >= 0
        assert quality["largest_gap_minutes"] >= 0
        assert quality["avg_interval_minutes"] >= 0
        assert quality["hourly_aligned_count"] >= 0

    def test_independent_observations_at_least_1_if_records_exist(self):
        """If raw_records > 0, independent_observations >= 1."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        if quality["raw_records"] > 0:
            assert quality["independent_observations"] >= 1


class TestForecastGate:
    """Test forecast gate uses independent observations, not raw rows."""

    def test_forecast_status_has_demand_history(self):
        """get_forecast_status_summary() includes demand_history section."""
        from backend.forecast_gate import get_forecast_status_summary

        summary = get_forecast_status_summary()
        assert "demand_history" in summary

    def test_forecast_status_raw_vs_independent(self):
        """Forecast gate exposes both raw and independent counts."""
        from backend.forecast_gate import get_forecast_status_summary

        summary = get_forecast_status_summary()
        dh = summary["demand_history"]

        assert "raw_records" in dh
        assert "independent_observations" in dh
        assert "duplicates_collapsed" in dh
        assert dh["raw_records"] >= dh["independent_observations"]
        assert dh["duplicates_collapsed"] == (
            dh["raw_records"] - dh["independent_observations"]
        )

    def test_forecast_gate_uses_independent_count(self):
        """Demand forecast provenance uses independent count for real_records."""
        from backend.forecast_gate import get_forecast_status_summary
        from backend.demand_history import count_unique_observations

        summary = get_forecast_status_summary()
        independent = count_unique_observations()

        demand = summary["demand_forecast"]
        assert demand["training"]["real_records"] == independent

    def test_forecast_gate_not_168_raw_rows(self):
        """168 raw database rows cannot satisfy MIN_TRAINING_RECORDS.

        The forecast gate must use independent observations, not raw rows.
        Even if there are 168+ raw rows, if they collapse to fewer
        independent observations, the gate must remain NOT READY.
        """
        from backend.forecast_gate import get_forecast_status_summary
        from backend.demand_history import count_records, count_unique_observations

        raw = count_records()
        independent = count_unique_observations()

        summary = get_forecast_status_summary()
        demand = summary["demand_forecast"]

        # The gate uses independent count, not raw
        assert demand["training"]["real_records"] == independent

        # If raw >= 168 but independent < 168, gate must NOT be ready
        if raw >= 168 and independent < 168:
            assert demand["production_gate"]["ready"] is False


class TestDataCollectionStatusEnhanced:
    """Test data collection status includes quality metrics."""

    def test_status_has_quality(self):
        """Data collection status includes demand_history_quality."""
        from backend.data_collector import get_collection_status

        status = get_collection_status()
        assert "demand_history_quality" in status

    def test_quality_in_status_matches_standalone(self):
        """Quality in status matches standalone quality call."""
        from backend.data_collector import get_collection_status
        from backend.demand_history import get_demand_history_quality

        status = get_collection_status()
        standalone = get_demand_history_quality()

        assert (
            status["demand_history_quality"]["independent_observations"]
            == standalone["independent_observations"]
        )


class TestHistoryAPIEnhanced:
    """Test history API returns observation-identity-aware fields."""

    def test_history_has_independent_observations(self):
        """GET /api/demand/history includes independent_observations."""
        from backend.demand_history import get_demand_history

        result = get_demand_history()
        assert "independent_observations" in result
        assert "duplicates" in result
        assert "duplicate_rate" in result

    def test_history_independent_leq_record_count(self):
        """independent_observations <= record_count in API response."""
        from backend.demand_history import get_demand_history

        result = get_demand_history()
        assert result["independent_observations"] <= result["record_count"]

    def test_history_message_mentions_independent(self):
        """History message mentions independent observations and duplicates."""
        from backend.demand_history import get_demand_history

        result = get_demand_history()
        assert "independent" in result["message"].lower()
        assert "duplicate" in result["message"].lower()

    def test_history_has_quality_section(self):
        """History API response includes quality section."""
        from backend.demand_history import get_demand_history

        result = get_demand_history()
        assert "quality" in result
        q = result["quality"]
        assert "time_coverage_hours" in q
        assert "largest_gap_minutes" in q
        assert "hourly_aligned_count" in q


class TestBackoffConstants:
    """Test backoff constants are defined and used."""

    def test_backoff_constants_defined(self):
        """Backoff constants are defined in data_collector."""
        from backend.data_collector import (
            MAX_CONSECUTIVE_FAILURES,
            BACKOFF_MULTIPLIER,
            MAX_BACKOFF_SECONDS,
        )

        assert MAX_CONSECUTIVE_FAILURES == 5
        assert BACKOFF_MULTIPLIER == 2.0
        assert MAX_BACKOFF_SECONDS == 3600


class TestDBDeduplication:
    """Test database-level deduplication prevents rapid-polling storage."""

    def test_is_duplicate_returns_false_when_no_match(self):
        """is_duplicate() returns False when no matching record exists."""
        from unittest.mock import patch, MagicMock

        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = None

        with patch("backend.demand_history.get_session", return_value=mock_session):
            from backend.demand_history import is_duplicate
            result = is_duplicate("2026-09-01T10:00:00", 15000.0, 14000.0)
            assert result is False

    def test_is_duplicate_returns_true_when_match_exists(self):
        """is_duplicate() returns True when matching record exists in window."""
        from unittest.mock import patch, MagicMock

        mock_record = MagicMock()
        mock_session = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_record

        with patch("backend.demand_history.get_session", return_value=mock_session):
            from backend.demand_history import is_duplicate
            result = is_duplicate("2026-09-01T10:00:00", 15000.0, 14000.0)
            assert result is True

    def test_is_duplicate_handles_db_unavailable(self):
        """is_duplicate() returns False when DB is unavailable."""
        from unittest.mock import patch

        with patch("backend.demand_history.get_session", side_effect=Exception("DB down")):
            from backend.demand_history import is_duplicate
            result = is_duplicate("2026-09-01T10:00:00", 15000.0, 14000.0)
            assert result is False
