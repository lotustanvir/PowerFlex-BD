import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from backend.collectors.base import BaseCollector, CollectorResult
from backend.collectors.grid_collector import GridCollector
from backend.collectors.weather_collector import WeatherCollector, LOCATIONS
from backend.collectors.biomass_collector import BiomassCollector
from backend.collectors.waste_collector import WasteCollector
from backend.data_quality import (
    DataQualityReport,
    assess_grid_quality,
    assess_solar_quality,
    assess_wind_quality,
    generate_quality_report,
)


# =========================================================
# CollectorResult tests
# =========================================================

class TestCollectorResult:
    def test_success_result(self):
        result = CollectorResult(source="test", success=True, data={"key": "val"})
        assert result.success is True
        assert result.source == "test"
        assert result.error is None
        assert result.latency_ms is None
        assert result.record_count == 0
        assert result.timestamp is not None

    def test_failure_result(self):
        result = CollectorResult(source="test", success=False, error="timeout")
        assert result.success is False
        assert result.error == "timeout"

    def test_timestamp_is_iso(self):
        result = CollectorResult(source="t", success=True)
        dt = datetime.fromisoformat(result.timestamp)
        assert dt.tzinfo is not None


# =========================================================
# BaseCollector tests
# =========================================================

class TestBaseCollector:
    def test_validate_nonempty(self):
        class Dummy(BaseCollector):
            def collect(self):
                return CollectorResult(source="d", success=True)

        c = Dummy(name="d")
        assert c.validate({"a": 1}) is True

    def test_validate_empty(self):
        class Dummy(BaseCollector):
            def collect(self):
                return CollectorResult(source="d", success=True)

        c = Dummy(name="d")
        assert c.validate({}) is False
        assert c.validate(None) is False


# =========================================================
# GridCollector tests
# =========================================================

class TestGridCollector:
    def test_collect_success(self):
        collector = GridCollector(max_retries=1)
        mock_data = {
            "connected": True,
            "data": {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "current_demand_mw": 15000,
                "supply_mw": 14800,
                "load_shedding_mw": 200,
                "generation_breakdown": {"gas_mw": 8000},
                "imports": {"total_imports_mw": 1200},
            },
        }
        with patch(
            "backend.collectors.grid_collector.fetch_pgcb_grid_data",
            return_value=mock_data,
        ):
            result = collector.collect()
            assert result.success is True
            assert result.source == "PGCB_GRID"
            assert result.latency_ms is not None
            assert result.latency_ms >= 0

    def test_collect_failure(self):
        collector = GridCollector(max_retries=1)
        mock_data = {
            "connected": False,
            "message": "Network error",
        }
        with patch(
            "backend.collectors.grid_collector.fetch_pgcb_grid_data",
            return_value=mock_data,
        ):
            result = collector.collect()
            assert result.success is False
            assert "Network error" in result.error

    def test_collect_exception(self):
        collector = GridCollector(max_retries=1)
        with patch(
            "backend.collectors.grid_collector.fetch_pgcb_grid_data",
            side_effect=ConnectionError("refused"),
        ):
            result = collector.collect()
            assert result.success is False
            assert "refused" in result.error

    def test_stale_data_recorded(self):
        collector = GridCollector(max_retries=1)
        stale_time = "2020-01-01T00:00:00+00:00"
        mock_data = {
            "connected": True,
            "data": {
                "timestamp": stale_time,
                "current_demand_mw": 15000,
                "supply_mw": 14800,
                "load_shedding_mw": 200,
                "generation_breakdown": {"gas_mw": 8000},
                "imports": {"total_imports_mw": 1200},
            },
        }
        with patch(
            "backend.collectors.grid_collector.fetch_pgcb_grid_data",
            return_value=mock_data,
        ):
            result = collector.collect()
            assert result.success is True


# =========================================================
# WeatherCollector tests
# =========================================================

class TestWeatherCollector:
    def test_collect_success(self):
        collector = WeatherCollector(timeout=5, forecast_hours=1)
        sample_rows = [
            {
                "zone": "Dhaka",
                "latitude": 23.8103,
                "longitude": 90.4125,
                "timestamp": "2025-06-01T12:00",
                "temperature_2m": 32.0,
                "cloud_cover": 20,
                "shortwave_radiation": 450.0,
                "wind_speed_10m": 12.0,
            }
        ]
        with patch(
            "backend.collectors.weather_collector._fetch_zone_weather",
            return_value=sample_rows,
        ):
            result = collector.collect()
            assert result.success is True
            assert result.source == "OPEN_METEO"
            assert result.record_count > 0

    def test_collect_all_zones_fail(self):
        collector = WeatherCollector(timeout=5, forecast_hours=1)
        with patch(
            "backend.collectors.weather_collector._fetch_zone_weather",
            side_effect=ConnectionError("timeout"),
        ):
            result = collector.collect()
            assert result.success is False
            assert "All weather zones failed" in result.error

    def test_locations_count(self):
        assert len(LOCATIONS) == 9


# =========================================================
# BiomassCollector tests
# =========================================================

class TestBiomassCollector:
    def test_collect_success(self):
        collector = BiomassCollector()
        mock_result = {
            "divisions": {"Dhaka": {"dispatchable_mw": 50.0}},
            "national": {"total_dispatchable_mw": 200.0},
        }
        with patch(
            "backend.collectors.biomass_collector.calculate_all_divisions",
            return_value=mock_result,
        ):
            result = collector.collect()
            assert result.success is True
            assert result.source == "BIOMASS_CALCULATOR"
            assert result.record_count == 1

    def test_collect_failure(self):
        collector = BiomassCollector()
        with patch(
            "backend.collectors.biomass_collector.calculate_all_divisions",
            side_effect=RuntimeError("data missing"),
        ):
            result = collector.collect()
            assert result.success is False
            assert "data missing" in result.error


# =========================================================
# WasteCollector tests
# =========================================================

class TestWasteCollector:
    def test_collect_success(self):
        collector = WasteCollector()
        mock_cities = {
            "cities": {"Dhaka": {"dispatchable_mw": 30.0}},
            "national": {"total_dispatchable_mw": 100.0},
            "conversion_factors": {},
        }
        mock_zones = {
            "Dhaka": {"dispatchable_mw": 30.0, "available_mw": 30.0, "electricity_mwh_year": 500.0},
        }
        with patch(
            "backend.collectors.waste_collector.calculate_all_cities",
            return_value=mock_cities,
        ), patch(
            "backend.collectors.waste_collector.map_waste_to_zones",
            return_value=mock_zones,
        ):
            result = collector.collect()
            assert result.success is True
            assert result.source == "WASTE_CALCULATOR"
            assert "zones" in result.data

    def test_collect_failure(self):
        collector = WasteCollector()
        with patch(
            "backend.collectors.waste_collector.calculate_all_cities",
            side_effect=KeyError("missing"),
        ):
            result = collector.collect()
            assert result.success is False


# =========================================================
# DataQualityReport tests
# =========================================================

class TestDataQualityReport:
    def test_report_creation(self):
        report = DataQualityReport(
            source="test",
            freshness="FRESH",
            completeness=0.9,
            accuracy_notes=["good"],
        )
        assert report.source == "test"
        assert report.freshness == "FRESH"
        assert report.completeness == 0.9
        assert report.timestamp is not None


# =========================================================
# assess_grid_quality tests
# =========================================================

class TestAssessGridQuality:
    def test_no_data(self):
        report = assess_grid_quality(None)
        assert report.freshness == "UNKNOWN"
        assert report.completeness == 0.0

    def test_complete_fresh(self):
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "timestamp": now,
            "current_demand_mw": 15000,
            "supply_mw": 14800,
            "load_shedding_mw": 200,
            "generation_breakdown": {"gas_mw": 8000},
            "imports": {"total_imports_mw": 1200},
        }
        report = assess_grid_quality(data)
        assert report.freshness == "FRESH"
        assert report.completeness == 1.0

    def test_stale_data(self):
        data = {
            "timestamp": "2020-01-01T00:00:00+00:00",
            "current_demand_mw": 15000,
            "supply_mw": 14800,
            "load_shedding_mw": 200,
            "generation_breakdown": {},
            "imports": {},
        }
        report = assess_grid_quality(data)
        assert report.freshness == "STALE"

    def test_partial_completeness(self):
        now = datetime.now(timezone.utc).isoformat()
        data = {
            "timestamp": now,
            "current_demand_mw": 15000,
        }
        report = assess_grid_quality(data)
        assert report.completeness < 1.0
        assert any("Missing" in n for n in report.accuracy_notes)


# =========================================================
# assess_solar_quality tests
# =========================================================

class TestAssessSolarQuality:
    def test_no_data(self):
        report = assess_solar_quality(None)
        assert report.freshness == "UNKNOWN"
        assert report.completeness == 0.0

    def test_complete_data(self):
        data = {
            "hourly_data": [{"temperature_2m": 30, "cloud_cover": 10, "shortwave_radiation": 500, "wind_speed_10m": 10}],
            "zones_succeeded": 9,
        }
        report = assess_solar_quality(data)
        assert report.freshness == "FRESH"
        assert report.completeness == 1.0

    def test_partial_zones(self):
        data = {
            "hourly_data": [{"temperature_2m": 30, "cloud_cover": 10, "shortwave_radiation": 500, "wind_speed_10m": 10}],
            "zones_succeeded": 5,
        }
        report = assess_solar_quality(data)
        assert report.completeness == 1.0
        assert any("zones failed" in n for n in report.accuracy_notes)


# =========================================================
# assess_wind_quality tests
# =========================================================

class TestAssessWindQuality:
    def test_no_data(self):
        report = assess_wind_quality(None)
        assert report.freshness == "UNKNOWN"

    def test_complete_data(self):
        data = {
            "hourly_data": [{"wind_speed_100m": 15, "wind_direction_100m": 180, "wind_gusts_10m": 25, "pressure_msl": 1013}],
            "zones_succeeded": 9,
        }
        report = assess_wind_quality(data)
        assert report.freshness == "FRESH"
        assert report.completeness == 1.0


# =========================================================
# generate_quality_report tests
# =========================================================

class TestGenerateQualityReport:
    def test_all_none(self):
        report = generate_quality_report(None, None, None, None, None)
        assert report["overall_freshness"] == "STALE"
        assert report["overall_completeness"] == 0.0
        assert len(report["sources"]) == 5

    def test_all_present(self):
        now = datetime.now(timezone.utc).isoformat()
        grid = {
            "timestamp": now,
            "current_demand_mw": 15000,
            "supply_mw": 14800,
            "load_shedding_mw": 200,
            "generation_breakdown": {"gas_mw": 8000},
            "imports": {"total_imports_mw": 1200},
        }
        solar = {
            "hourly_data": [{"temperature_2m": 30, "cloud_cover": 10, "shortwave_radiation": 500, "wind_speed_10m": 10}],
            "zones_succeeded": 9,
        }
        wind = {
            "hourly_data": [{"wind_speed_100m": 15, "wind_direction_100m": 180, "wind_gusts_10m": 25, "pressure_msl": 1013}],
            "zones_succeeded": 9,
        }
        biomass = {"national": {"total_dispatchable_mw": 200}}
        waste = {"national": {"total_dispatchable_mw": 100}}

        report = generate_quality_report(grid, solar, wind, biomass, waste)
        assert report["overall_freshness"] == "FRESH"
        assert report["overall_completeness"] > 0.5

    def test_mixed_sources(self):
        grid = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "current_demand_mw": 15000,
            "supply_mw": 14800,
            "load_shedding_mw": 200,
            "generation_breakdown": {},
            "imports": {},
        }
        report = generate_quality_report(grid, None, None, None, None)
        assert report["overall_freshness"] == "PARTIAL"
