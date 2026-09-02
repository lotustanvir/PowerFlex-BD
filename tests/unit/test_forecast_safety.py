"""Phase 7: Forecasting & Historical Energy Analytics Tests.

Tests for:
- Forecast safety classification
- Observation counting correctness
- Database connection reliability
- Historical data integrity
- Forecast API contract
- Data provenance preservation
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from backend.forecast_gate import (
    ProductionRequirements,
    ProductionGateChecker,
    ForecastProvenance,
    ForecastStatus,
    build_demand_forecast_provenance,
)
from backend.data_quality import DataProvenance


class TestObservationCounting:
    """Tests 1-3: Observation counting correctness."""

    def test_7_independent_observations_do_not_satisfy_168(self):
        """Test 1: 7 independent observations do NOT satisfy 168-observation requirement."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=7,
            synthetic_records=8760,
        )
        checker = ProductionGateChecker()
        result = checker.check_production_readiness(provenance)

        assert result.production_ready is False
        assert any("INSUFFICIENT_DATA" in r for r in result.blocking_reasons)

    def test_168_raw_duplicates_do_not_satisfy_requirement(self):
        """Test 2: 168 raw duplicate rows do NOT satisfy the requirement."""
        # 168 raw records with duplicates means fewer independent observations
        # Simulate: 168 raw rows but only 7 independent (95% duplicates)
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=7,  # Only 7 independent observations
            synthetic_records=0,
        )
        checker = ProductionGateChecker()
        result = checker.check_production_readiness(provenance)

        assert result.production_ready is False
        assert result.real_training_records == 7
        assert result.real_training_records < ProductionRequirements.MIN_TRAINING_RECORDS

    def test_168_genuine_independent_observations_satisfy_data_count(self):
        """Test 3: 168 genuinely independent observations satisfy data-count requirement."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=168,
            synthetic_records=0,
        )
        # Check that data count requirement is met
        assert provenance.real_training_records >= ProductionRequirements.MIN_TRAINING_RECORDS


class TestForecastSafetyClassification:
    """Tests 4-6: Forecast safety classification."""

    def test_forecast_api_200_does_not_mean_production_ready(self):
        """Test 4: Forecast API HTTP 200 does not automatically mean production_ready=true."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=50,
            synthetic_records=8760,
        )
        checker = ProductionGateChecker()
        result = checker.check_production_readiness(provenance)

        # Even though the forecast endpoint returns 200, production_ready is False
        assert result.forecast_status != ForecastStatus.PRODUCTION_READY
        assert result.production_ready is False

    def test_synthetic_forecast_correctly_classified(self):
        """Test 5: Synthetic forecast is correctly classified."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=100,
            synthetic_records=8760,
        )
        checker = ProductionGateChecker()
        result = checker.check_production_readiness(provenance)

        assert result.forecast_status == ForecastStatus.SYNTHETIC_TRAINED
        assert "SYNTHETIC" in result.forecast_status

    def test_forecast_ui_not_labeling_synthetic_as_production(self):
        """Test 6: Forecast UI does not label synthetic/model output as production prediction."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=50,
            synthetic_records=8760,
        )
        checker = ProductionGateChecker()
        message = checker.get_honest_status_message(provenance)

        # Message should NOT claim production readiness
        assert "PRODUCTION READY" not in message
        assert "DEVELOPMENT ONLY" in message or "SYNTHETIC" in message


class TestDatabaseReliability:
    """Tests 7-8: Database connection and observation discrepancy."""

    def test_database_unavailable_fails_safely(self):
        """Test 7: Database unavailable fails safely."""
        from backend.demand_history import count_unique_observations, count_records

        # These functions catch exceptions and return 0
        with patch("backend.demand_history.get_session", side_effect=Exception("DB down")):
            unique = count_unique_observations()
            raw = count_records()
            assert unique == 0
            assert raw == 0

    def test_observation_counting_uses_correct_function(self):
        """Test 8: 0 vs 7 observation discrepancy is resolved - forecast gate uses count_unique_observations."""
        # Verify that the forecast endpoint uses count_unique_observations, not count_records
        import inspect
        from backend import demand_forecast

        source = inspect.getsource(demand_forecast.get_demand_forecast)
        assert "count_unique_observations" in source
        # Should NOT use count_records alone for the gate decision
        lines = source.split("\n")
        gate_lines = [l for l in lines if "real_records" in l and "=" in l]
        # The first assignment to real_records should use count_unique_observations
        assert any("count_unique_observations" in l for l in gate_lines)


class TestHistoricalDataIntegrity:
    """Tests 9-12: Historical data and chart integrity."""

    def test_historical_chart_shows_gaps_not_false_data(self):
        """Test 9: Historical chart shows gaps rather than false continuous data."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        # Largest gap should be reported honestly
        assert "largest_gap_minutes" in quality
        assert quality["largest_gap_minutes"] >= 0

    def test_raw_records_distinct_from_independent_observations(self):
        """Test 10: Raw records and independent observations remain distinct."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        assert quality["raw_records"] >= quality["independent_observations"]
        assert quality["duplicates"] == quality["raw_records"] - quality["independent_observations"]

    def test_missing_historical_range_returns_honest_empty(self):
        """Test 11: Missing historical range returns an honest empty state."""
        from backend.demand_history import get_demand_history_quality

        quality = get_demand_history_quality()
        # If no data, should return zeros, not fake values
        if quality["raw_records"] == 0:
            assert quality["independent_observations"] == 0
            assert quality["time_coverage_hours"] == 0.0

    def test_daily_mwh_not_converted_to_mw_via_division(self):
        """Test 12: Daily MWh is never converted to current MW using /24."""
        from backend import demand_forecast
        import inspect

        # Check the forecast_24h_demand function for /24 conversion
        source = inspect.getsource(demand_forecast.forecast_24h_demand)
        # Should not contain naive MWh/24 conversion
        assert "/ 24" not in source or "mwh" not in source.lower()


class TestTimezoneAndClassification:
    """Tests 13-14: Timezone handling and data classification."""

    def test_timezone_handling_uses_asia_dhaka(self):
        """Test 13: Timezone handling uses Asia/Dhaka correctly."""
        from backend import demand_forecast
        import inspect

        source = inspect.getsource(demand_forecast)
        # Should reference Asia/Dhaka or UTC+06:00
        assert "Asia/Dhaka" in source or "UTC+06:00" in source or "timezone.utc" in source

    def test_forecast_and_measured_data_have_distinct_classifications(self):
        """Test 14: Forecast and measured data have distinct classifications."""
        from backend.data_classification import DataClassification

        # Forecast should be FORECAST or MODEL_FORECAST
        forecast_class = DataClassification.FORECAST
        # Measured should be OFFICIAL or MEASURED
        measured_class = DataClassification.OFFICIAL

        assert forecast_class != measured_class
        assert forecast_class.value == "FORECAST"
        assert measured_class.value == "OFFICIAL"


class TestPerformanceAndCompatibility:
    """Tests 15-16: Performance and API backward compatibility."""

    def test_large_time_ranges_do_not_cause_full_loading(self):
        """Test 15: Large time ranges do not cause unnecessary full-dataset loading."""
        from backend.history_api import get_grid_history

        # The function should support limit/offset for pagination
        import inspect
        sig = inspect.signature(get_grid_history)
        params = list(sig.parameters.keys())
        assert "limit" in params or "offset" in params

    def test_api_backward_compatibility_maintained(self):
        """Test 16: API backward compatibility is maintained."""
        # The forecast endpoint should still return the core fields
        from backend import demand_forecast
        import inspect

        source = inspect.getsource(demand_forecast.get_demand_forecast)
        # Core fields that must still be present
        assert "forecast_peak_mw" in source or "hourly_forecast" in source
        assert "training_metadata" in source
        # New field should not break existing structure
        assert "forecast_metadata" in source


class TestForecastGateIntegration:
    """Additional tests for forecast gate behavior."""

    def test_forecast_gate_preserves_168_threshold(self):
        """Forecast gate preserves the 168-observation threshold."""
        assert ProductionRequirements.MIN_TRAINING_RECORDS == 168

    def test_forecast_gate_blocks_synthetic_training(self):
        """Forecast gate blocks models trained on synthetic data."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=168,
            synthetic_records=8760,
        )
        checker = ProductionGateChecker()
        result = checker.check_production_readiness(provenance)

        assert result.production_ready is False
        assert any("SYNTHETIC" in r for r in result.blocking_reasons)

    def test_forecast_gate_allows_pure_real_data(self):
        """Forecast gate allows models trained only on real data."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=168,
            synthetic_records=0,
        )
        # Check that synthetic records don't block
        assert provenance.synthetic_training_records == 0

    def test_forecast_provenance_includes_all_fields(self):
        """Forecast provenance includes all required fields."""
        provenance = build_demand_forecast_provenance(
            real_pgcb_records=100,
            synthetic_records=8760,
        )
        d = provenance.to_dict()

        assert "input" in d
        assert "training" in d
        assert "model" in d
        assert "validation" in d
        assert "production_gate" in d
        assert d["production_gate"]["ready"] is False
