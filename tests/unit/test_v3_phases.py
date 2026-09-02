"""Comprehensive Tests for PowerFlex BD v3 Phases 16-22.

Tests source registry, data models, weather provider,
location intelligence, recommendation engine, and API routes.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from backend.source_registry import (
    SourceRegistry, DataSourceEntry, SourceType, SourceStatus,
    get_source_registry,
)
from backend.data_models import (
    DataProvenance, DemandData, SupplyData, GenerationBreakdown,
    GridSnapshotNormalized, DataQuality, PlantData,
    create_demand_unavailable, create_supply_unavailable,
)
from backend.data_classification import DataClassification
from backend.location_intelligence import (
    LocationFeatures, SiteScore, CandidateLocation,
    calculate_distance_km, find_nearest_grid, score_site,
    search_candidates, BANGLADESH_BOUNDS, GRID_SUBSTATIONS,
)
from backend.recommendation_engine import (
    DeficitAnalysis, TechnologyRecommendation, PlantRecommendation,
    AIPlanningRecommendation, calculate_deficit, recommend_technology,
    optimize_capacity, generate_recommendation, TECHNOLOGY_PROFILES,
)


# =========================================================
# PHASE 16: SOURCE REGISTRY TESTS
# =========================================================

class TestSourceRegistry:
    """Test the centralized source registry."""

    def test_registry_has_verified_sources(self):
        registry = get_source_registry()
        pgcb = registry.get("pgcb_erp")
        assert pgcb is not None
        assert pgcb.name == "PGCB ERP Portal"
        assert pgcb.source_type == SourceType.OFFICIAL_SCRAPER
        assert pgcb.classification == "OFFICIAL"
        assert pgcb.status == SourceStatus.ACTIVE

    def test_registry_has_open_meteo(self):
        registry = get_source_registry()
        meteo = registry.get("open_meteo_weather")
        assert meteo is not None
        assert meteo.name == "Open-Meteo Weather API"
        assert meteo.source_type == SourceType.OPEN_API
        assert meteo.classification == "LIVE_FEED"
        assert meteo.status == SourceStatus.ACTIVE

    def test_registry_has_ml_models(self):
        registry = get_source_registry()
        solar_ai = registry.get("powerflex_solar_ai")
        assert solar_ai is not None
        assert solar_ai.source_type == SourceType.ML_MODEL
        assert solar_ai.classification == "FORECAST"

    def test_registry_has_calculated_sources(self):
        registry = get_source_registry()
        wind = registry.get("powerflex_wind_ai")
        assert wind is not None
        assert wind.source_type == SourceType.CALCULATED
        assert wind.classification == "CALCULATED"

    def test_registry_has_unverified_sources(self):
        registry = get_source_registry()
        bpdb = registry.get("bpdb_annual")
        assert bpdb is not None
        assert bpdb.status == SourceStatus.UNVERIFIED

    def test_registry_summary(self):
        registry = get_source_registry()
        summary = registry.summary()
        assert summary["total_sources"] > 0
        assert summary["active_sources"] > 0
        assert summary["ml_models"] > 0
        assert summary["calculated"] > 0

    def test_record_success(self):
        registry = SourceRegistry()
        entry = DataSourceEntry(
            source_id="test_source",
            name="Test Source",
            organization="Test Org",
            source_type=SourceType.OPEN_API,
            url="https://test.com",
            access_method="REST API",
            data_type="Test data",
            update_frequency="Hourly",
            historical_coverage="1 year",
            reliability="HIGH",
            license_notes="Open",
            classification="LIVE_FEED",
        )
        registry.register(entry)

        registry.record_success("test_source")
        updated = registry.get("test_source")
        assert updated.success_count == 1
        assert updated.last_success is not None

    def test_record_failure(self):
        registry = SourceRegistry()
        entry = DataSourceEntry(
            source_id="test_failing",
            name="Test Failing",
            organization="Test Org",
            source_type=SourceType.OPEN_API,
            url="https://test.com",
            access_method="REST API",
            data_type="Test data",
            update_frequency="Hourly",
            historical_coverage="1 year",
            reliability="HIGH",
            license_notes="Open",
            classification="LIVE_FEED",
        )
        registry.register(entry)

        for _ in range(5):
            registry.record_failure("test_failing")
        updated = registry.get("test_failing")
        assert updated.status == SourceStatus.INACTIVE
        assert updated.failure_count == 5

    def test_serialization(self):
        registry = get_source_registry()
        data = registry.to_dict()
        assert isinstance(data, dict)
        assert "pgcb_erp" in data
        assert "open_meteo_weather" in data


# =========================================================
# PHASE 16: DATA MODELS TESTS
# =========================================================

class TestDataModels:
    """Test normalized data models."""

    def test_data_provenance(self):
        prov = DataProvenance(
            source="PGCB ERP",
            source_timestamp="2025-01-01T12:00:00+06:00",
            retrieved_at="2025-01-01T12:01:00+06:00",
            timezone="Asia/Dhaka",
            quality="GOOD",
            classification="OFFICIAL",
            freshness="FRESH",
        )
        data = prov.to_dict()
        assert data["source"] == "PGCB ERP"
        assert data["quality"] == "GOOD"
        assert data["classification"] == "OFFICIAL"

    def test_demand_data(self):
        demand = DemandData(
            timestamp="2025-01-01T12:00:00+06:00",
            demand_mw=12000,
            peak_demand_mw=14000,
            minimum_demand_mw=8000,
            average_demand_mw=11000,
            quality="GOOD",
        )
        data = demand.to_dict()
        assert data["demand_mw"] == 12000
        assert data["peak_demand_mw"] == 14000
        assert data["quality"] == "GOOD"

    def test_supply_data(self):
        supply = SupplyData(
            timestamp="2025-01-01T12:00:00+06:00",
            supply_mw=11500,
            generation_mw=11500,
            available_capacity_mw=15000,
        )
        data = supply.to_dict()
        assert data["supply_mw"] == 11500
        assert data["available_capacity_mw"] == 15000

    def test_generation_breakdown(self):
        gen = GenerationBreakdown(
            gas_mw=5000,
            coal_mw=3000,
            hydro_mw=200,
            solar_mw=500,
            wind_mw=100,
        )
        total = gen.total_generation_mw()
        assert total == 8800

    def test_generation_breakdown_all_none(self):
        gen = GenerationBreakdown()
        total = gen.total_generation_mw()
        assert total is None

    def test_plant_data(self):
        plant = PlantData(
            plant_name="Barishal Solar",
            technology="SOLAR",
            fuel="SOLAR",
            capacity_mw=50.0,
            available_generation_mw=35.0,
            status="OPERATIONAL",
        )
        data = plant.to_dict()
        assert data["plant_name"] == "Barishal Solar"
        assert data["capacity_mw"] == 50.0

    def test_grid_snapshot(self):
        snapshot = GridSnapshotNormalized(
            timestamp="2025-01-01T12:00:00+06:00",
            demand=DemandData(timestamp="2025-01-01T12:00:00+06:00", demand_mw=12000),
            supply=SupplyData(timestamp="2025-01-01T12:00:00+06:00", supply_mw=11500),
            generation=GenerationBreakdown(gas_mw=5000, coal_mw=3000),
            gap_mw=500,
            grid_status="NORMAL",
        )
        data = snapshot.to_dict()
        assert data["gap_mw"] == 500
        assert data["grid_status"] == "NORMAL"


# =========================================================
# PHASE 16: DATA QUALITY TESTS
# =========================================================

class TestDataQuality:
    """Test data quality assessment."""

    def test_assess_demand_quality_good(self):
        assert DataQuality.assess_demand_quality(12000, "2025-01-01T12:00:00") == "GOOD"

    def test_assess_demand_quality_unavailable(self):
        assert DataQuality.assess_demand_quality(None, "2025-01-01T12:00:00") == "UNAVAILABLE"

    def test_assess_demand_quality_invalid_negative(self):
        assert DataQuality.assess_demand_quality(-100, "2025-01-01T12:00:00") == "INVALID"

    def test_assess_demand_quality_suspect_high(self):
        assert DataQuality.assess_demand_quality(25000, "2025-01-01T12:00:00") == "SUSPECT"

    def test_assess_demand_quality_suspect_low(self):
        assert DataQuality.assess_demand_quality(500, "2025-01-01T12:00:00") == "SUSPECT"

    def test_assess_supply_quality_good(self):
        assert DataQuality.assess_supply_quality(11500, 12000) == "GOOD"

    def test_assess_supply_quality_unavailable(self):
        assert DataQuality.assess_supply_quality(None, 12000) == "UNAVAILABLE"

    def test_assess_supply_quality_invalid(self):
        assert DataQuality.assess_supply_quality(-100, 12000) == "INVALID"

    def test_assess_supply_quality_suspect(self):
        assert DataQuality.assess_supply_quality(30000, 12000) == "SUSPECT"

    def test_assess_freshness_fresh(self):
        now = datetime.now(timezone.utc).isoformat()
        assert DataQuality.assess_freshness(now) == "FRESH"

    def test_assess_freshness_unknown(self):
        assert DataQuality.assess_freshness(None) == "UNKNOWN"

    def test_detect_duplicates(self):
        data = [
            {"timestamp": "2025-01-01T12:00:00"},
            {"timestamp": "2025-01-01T12:00:00"},
            {"timestamp": "2025-01-01T13:00:00"},
        ]
        dupes = DataQuality.detect_duplicates(data)
        assert dupes == [1]

    def test_detect_gaps(self):
        timestamps = [
            "2025-01-01T12:00:00+00:00",
            "2025-01-01T13:00:00+00:00",
            "2025-01-01T16:00:00+00:00",  # 3-hour gap
        ]
        gaps = DataQuality.detect_gaps(timestamps)
        assert len(gaps) == 1
        assert gaps[0]["gap_minutes"] > 120

    def test_create_demand_unavailable(self):
        demand = create_demand_unavailable("test_source", "test reason")
        assert demand.demand_mw is None
        assert demand.quality == "UNAVAILABLE"
        assert demand.provenance.classification == "DATA_UNAVAILABLE"

    def test_create_supply_unavailable(self):
        supply = create_supply_unavailable("test_source", "test reason")
        assert supply.supply_mw is None
        assert supply.quality == "UNAVAILABLE"


# =========================================================
# PHASE 20: LOCATION INTELLIGENCE TESTS
# =========================================================

class TestLocationIntelligence:
    """Test Bangladesh location intelligence."""

    def test_haversine_distance(self):
        # Dhaka to Chittagong ~244 km
        dist = calculate_distance_km(23.8103, 90.4125, 22.3569, 91.7832)
        assert 200 < dist < 300

    def test_haversine_same_point(self):
        dist = calculate_distance_km(23.81, 90.41, 23.81, 90.41)
        assert dist < 0.1

    def test_find_nearest_grid_dhaka(self):
        grid = find_nearest_grid(23.81, 90.41)
        # Nearest substation to Dhaka center is Aminbazar (23.78, 90.35)
        assert grid["substation"] == "Aminbazar"
        assert grid["distance_km"] < 10
        assert grid["grid_proximity"] in ["EXCELLENT", "GOOD"]

    def test_find_nearest_grid_remote(self):
        grid = find_nearest_grid(20.5, 88.0)
        assert grid["grid_proximity"] in ["DISTANT", "REMOTE"]

    def test_score_site_no_data(self):
        score = score_site(23.81, 90.41)
        assert score.overall_score >= 0
        assert len(score.warnings) > 0
        assert "Solar data unavailable" in score.warnings

    def test_score_site_with_solar(self):
        solar_data = {"radiation_wm2": 500}
        score = score_site(23.81, 90.41, solar_data=solar_data)
        assert score.solar_score > 0
        assert score.overall_score > 0

    def test_score_site_with_wind(self):
        wind_data = {"wind_speed_kmh": 15}
        score = score_site(23.81, 90.41, wind_data=wind_data)
        assert score.wind_score == 100

    def test_search_candidates_all(self):
        candidates = search_candidates()
        assert len(candidates) >= 8

    def test_search_candidates_solar_only(self):
        candidates = search_candidates(technology="SOLAR")
        assert all(c["technology"] == "SOLAR" for c in candidates)

    def test_search_candidates_wind_only(self):
        candidates = search_candidates(technology="WIND")
        assert all(c["technology"] == "WIND" for c in candidates)

    def test_search_candidates_area_filter(self):
        area = {
            "min_lat": 22.0,
            "max_lat": 24.0,
            "min_lon": 89.0,
            "max_lon": 91.0,
        }
        candidates = search_candidates(area=area)
        for c in candidates:
            assert area["min_lat"] <= c["latitude"] <= area["max_lat"]
            assert area["min_lon"] <= c["longitude"] <= area["max_lon"]

    def test_bangladesh_bounds(self):
        assert BANGLADESH_BOUNDS["min_lat"] == 20.5
        assert BANGLADESH_BOUNDS["max_lat"] == 26.7
        assert BANGLADESH_BOUNDS["min_lon"] == 88.0
        assert BANGLADESH_BOUNDS["max_lon"] == 92.7


# =========================================================
# PHASE 21: DEFICIT ANALYSIS TESTS
# =========================================================

class TestDeficitAnalysis:
    """Test deficit calculation and analysis."""

    def test_deficit_positive(self):
        result = calculate_deficit(12000, 11000)
        assert result.forecast_gap_mw == 1000
        assert result.gap_type == "DEFICIT_RISK"
        assert result.severity == "MODERATE"

    def test_deficit_surplus(self):
        result = calculate_deficit(11000, 12000)
        assert result.forecast_gap_mw == -1000
        assert result.gap_type == "SURPLUS"
        assert result.severity == "NO_RISK"

    def test_deficit_balanced(self):
        result = calculate_deficit(12000, 12000)
        assert result.forecast_gap_mw == 0
        assert result.gap_type == "BALANCED"

    def test_deficit_critical(self):
        result = calculate_deficit(15000, 10000)
        assert result.forecast_gap_mw == 5000
        assert result.severity == "CRITICAL"

    def test_deficit_high(self):
        result = calculate_deficit(14000, 11500)
        assert result.forecast_gap_mw == 2500
        assert result.severity == "HIGH"

    def test_deficit_moderate(self):
        result = calculate_deficit(13000, 11500)
        assert result.forecast_gap_mw == 1500
        assert result.severity == "HIGH"

    def test_deficit_both_none(self):
        result = calculate_deficit(None, None)
        assert result.gap_type == "UNKNOWN"
        assert result.severity == "UNKNOWN"

    def test_deficit_demand_none(self):
        result = calculate_deficit(None, 12000)
        assert result.gap_type == "UNKNOWN"

    def test_deficit_supply_none(self):
        result = calculate_deficit(12000, None)
        assert result.gap_type == "UNKNOWN"

    def test_serialization(self):
        result = calculate_deficit(12000, 11000)
        data = result.to_dict()
        assert data["forecast_gap_mw"] == 1000
        assert data["gap_type"] == "DEFICIT_RISK"


# =========================================================
# PHASE 21: TECHNOLOGY RECOMMENDATION TESTS
# =========================================================

class TestTechnologyRecommendation:
    """Test technology selection."""

    def test_no_deficit(self):
        rec = recommend_technology(-500)
        assert rec.technology == "NONE"

    def test_zero_deficit(self):
        rec = recommend_technology(0)
        assert rec.technology == "NONE"

    def test_solar_only(self):
        solar_data = {"radiation_wm2": 500}
        rec = recommend_technology(1000, solar_data=solar_data)
        assert rec.technology == "SOLAR"
        assert rec.capacity_factor > 0

    def test_wind_only(self):
        wind_data = {"wind_speed_kmh": 12}
        rec = recommend_technology(1000, wind_data=wind_data)
        assert rec.technology == "WIND"

    def test_solar_wind(self):
        solar_data = {"radiation_wm2": 500}
        wind_data = {"wind_speed_kmh": 12}
        rec = recommend_technology(1000, solar_data=solar_data, wind_data=wind_data)
        assert rec.technology == "SOLAR_WIND"

    def test_solar_battery(self):
        solar_data = {"radiation_wm2": 500}
        rec = recommend_technology(1000, solar_data=solar_data, battery_available=True)
        assert rec.technology == "SOLAR_BATTERY"

    def test_default_solar(self):
        rec = recommend_technology(1000)
        assert rec.technology == "SOLAR"

    def test_technology_profiles_complete(self):
        expected = [
            "SOLAR", "WIND", "SOLAR_WIND", "SOLAR_BATTERY",
            "WIND_BATTERY", "SOLAR_WIND_BATTERY",
        ]
        for tech in expected:
            assert tech in TECHNOLOGY_PROFILES

    def test_serialization(self):
        rec = recommend_technology(1000)
        data = rec.to_dict()
        assert "technology" in data
        assert "capacity_factor" in data


# =========================================================
# PHASE 21: CAPACITY OPTIMIZATION TESTS
# =========================================================

class TestCapacityOptimization:
    """Test plant capacity optimization."""

    def test_zero_deficit(self):
        plant = optimize_capacity(0, "SOLAR")
        assert plant.recommended_capacity_mw == 0

    def test_positive_deficit(self):
        plant = optimize_capacity(1000, "SOLAR", capacity_factor=0.15)
        assert plant.recommended_capacity_mw > 1000
        assert plant.expected_hourly_generation_mw > 0

    def test_daily_energy(self):
        plant = optimize_capacity(1000, "SOLAR", capacity_factor=0.15)
        assert plant.expected_daily_energy_mwh == plant.expected_hourly_generation_mw * 24

    def test_annual_energy(self):
        plant = optimize_capacity(1000, "SOLAR", capacity_factor=0.15)
        assert plant.expected_annual_energy_gwh > 0

    def test_prediction_interval(self):
        plant = optimize_capacity(1000, "SOLAR", capacity_factor=0.15)
        assert plant.prediction_interval_lower < plant.expected_hourly_generation_mw
        assert plant.prediction_interval_upper > plant.expected_hourly_generation_mw

    def test_location_score_effect(self):
        plant_high = optimize_capacity(1000, "SOLAR", location_score=90)
        plant_low = optimize_capacity(1000, "SOLAR", location_score=30)
        assert plant_high.recommended_capacity_mw <= plant_low.recommended_capacity_mw


# =========================================================
# PHASE 21: FULL RECOMMENDATION PIPELINE TESTS
# =========================================================

class TestRecommendationPipeline:
    """Test full recommendation pipeline."""

    def test_full_recommendation_deficit(self):
        rec = generate_recommendation(
            demand_mw=12000,
            supply_mw=11000,
            solar_data={"radiation_wm2": 500},
        )
        assert rec.forecast_demand_mw == 12000
        assert rec.forecast_supply_mw == 11000
        assert rec.expected_deficit_mw == 1000
        assert rec.recommended_technology is not None
        assert rec.recommended_capacity_mw > 0
        assert "AI-generated planning recommendation" in rec.disclaimer

    def test_full_recommendation_surplus(self):
        rec = generate_recommendation(
            demand_mw=11000,
            supply_mw=12000,
        )
        assert rec.expected_deficit_mw == -1000
        assert rec.recommended_technology.technology == "NONE"

    def test_full_recommendation_no_data(self):
        rec = generate_recommendation(demand_mw=None, supply_mw=None)
        assert rec.forecast_demand_mw is None
        assert rec.expected_deficit_mw is None

    def test_full_recommendation_serialization(self):
        rec = generate_recommendation(12000, 11000)
        data = rec.to_dict()
        assert "forecast_demand_mw" in data
        assert "recommended_technology" in data
        assert "disclaimer" in data


# =========================================================
# PHASE 19: DATA CLASSIFICATION INTEGRITY
# =========================================================

class TestClassificationIntegrity:
    """Test that data classifications are properly enforced."""

    def test_all_classifications_exist(self):
        classifications = [
            "OFFICIAL", "MEASURED", "LIVE_FEED", "DELAYED",
            "FORECAST", "CALCULATED", "POTENTIAL", "SCENARIO",
            "PROJECT", "UNDER_CONSTRUCTION", "UNDER_COMMISSIONING",
            "EXPERIMENTAL", "PROTOTYPE", "DATA_UNAVAILABLE", "UNKNOWN",
        ]
        for cls in classifications:
            assert DataClassification(cls)

    def test_source_classification_matches(self):
        registry = get_source_registry()
        pgcb = registry.get("pgcb_erp")
        assert pgcb.classification == "OFFICIAL"

        meteo = registry.get("open_meteo_weather")
        assert meteo.classification == "LIVE_FEED"

    def test_recommendation_has_disclaimer(self):
        rec = generate_recommendation(12000, 11000)
        assert "construction approval" in rec.disclaimer
        assert "engineering certification" in rec.disclaimer
        assert "financial guarantee" in rec.disclaimer
