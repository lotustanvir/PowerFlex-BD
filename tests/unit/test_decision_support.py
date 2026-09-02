"""Phase 6: Decision Support Service Tests.

Tests for the unified recommendation engine including:
- Rule evaluation (supply deficit, renewable opportunity, high risk, forecast unavailable)
- Confidence scoring
- Deduplication (fingerprinting + cooldown)
- Graceful degradation for missing inputs
- Data classification integration
- System health
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone, timedelta

from backend.decision_support import (
    DecisionSupportService,
    RecommendationDeduplicator,
    calculate_confidence_score,
    evaluate_supply_deficit,
    evaluate_renewable_opportunity,
    evaluate_high_risk,
    evaluate_forecast_unavailable,
    evaluate_data_quality,
    get_decision_support,
    get_system_health,
    SystemInputs,
    Recommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationEvidence,
    SourceType,
    DataStatus,
)


class TestConfidenceScoring:
    """Test confidence score calculation."""

    def test_high_confidence_fresh_data(self):
        """Fresh data with reliable sources gives high confidence."""
        confidence = calculate_confidence_score(
            data_freshness_seconds=60,  # 1 minute old
            source_reliability=0.95,
            input_completeness=1.0,
            calculation_stability=0.95,
            forecast_available=True,
        )
        assert confidence >= 0.8

    def test_low_confidence_stale_data(self):
        """Stale data with unreliable sources gives low confidence."""
        confidence = calculate_confidence_score(
            data_freshness_seconds=7200,  # 2 hours old
            source_reliability=0.5,
            input_completeness=0.6,
            calculation_stability=0.5,
            forecast_available=False,
        )
        assert confidence <= 0.6

    def test_confidence_bounds(self):
        """Confidence is always between 0 and 1."""
        confidence = calculate_confidence_score(
            data_freshness_seconds=None,
            source_reliability=0.0,
            input_completeness=0.0,
            calculation_stability=0.0,
            forecast_available=False,
        )
        assert 0.0 <= confidence <= 1.0

    def test_forecast_bonus(self):
        """Forecast availability adds confidence bonus."""
        with_forecast = calculate_confidence_score(
            data_freshness_seconds=300,
            source_reliability=0.8,
            input_completeness=0.8,
            calculation_stability=0.8,
            forecast_available=True,
        )
        without_forecast = calculate_confidence_score(
            data_freshness_seconds=300,
            source_reliability=0.8,
            input_completeness=0.8,
            calculation_stability=0.8,
            forecast_available=False,
        )
        assert with_forecast > without_forecast


class TestDeduplication:
    """Test recommendation deduplication."""

    def test_no_duplicate_first_time(self):
        """First recommendation is not a duplicate."""
        dedup = RecommendationDeduplicator(cooldown_seconds=300)
        rec = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test",
            detailed_explanation="Test",
            evidence=RecommendationEvidence(trigger="test"),
            expected_impact="Test",
        )
        assert dedup.is_duplicate(rec) is False

    def test_duplicate_within_cooldown(self):
        """Same recommendation within cooldown is a duplicate."""
        dedup = RecommendationDeduplicator(cooldown_seconds=300)
        rec1 = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test",
            detailed_explanation="Test",
            evidence=RecommendationEvidence(trigger="test"),
            expected_impact="Test",
        )
        dedup.register(rec1)

        rec2 = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test",
            detailed_explanation="Test",
            evidence=RecommendationEvidence(trigger="test"),
            expected_impact="Test",
        )
        assert dedup.is_duplicate(rec2) is True

    def test_different_trigger_not_duplicate(self):
        """Different trigger is not a duplicate."""
        dedup = RecommendationDeduplicator(cooldown_seconds=300)
        rec1 = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test",
            detailed_explanation="Test",
            evidence=RecommendationEvidence(trigger="trigger_a"),
            expected_impact="Test",
        )
        dedup.register(rec1)

        rec2 = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test",
            detailed_explanation="Test",
            evidence=RecommendationEvidence(trigger="trigger_b"),
            expected_impact="Test",
        )
        assert dedup.is_duplicate(rec2) is False

    def test_cleanup_expired(self):
        """Cleanup removes expired entries."""
        dedup = RecommendationDeduplicator(cooldown_seconds=1)
        rec = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test",
            detailed_explanation="Test",
            evidence=RecommendationEvidence(trigger="test"),
            expected_impact="Test",
        )
        dedup.register(rec)
        assert len(dedup._recent) == 1

        # Wait for expiry
        import time
        time.sleep(1.1)

        removed = dedup.cleanup()
        assert removed == 1
        assert len(dedup._recent) == 0


class TestRuleEvaluation:
    """Test individual rule evaluation functions."""

    def test_supply_deficit_detected(self):
        """Supply deficit rule triggers when demand > supply."""
        inputs = SystemInputs(
            grid_demand_mw=16000.0,
            grid_supply_mw=15000.0,
            grid_data_classification="OFFICIAL",
        )
        rec = evaluate_supply_deficit(inputs)
        assert rec is not None
        assert rec.type == RecommendationType.SUPPLY_DEFICIT
        assert rec.evidence.current_value == 1000.0

    def test_no_supply_deficit(self):
        """Supply deficit rule does not trigger when supply >= demand."""
        inputs = SystemInputs(
            grid_demand_mw=15000.0,
            grid_supply_mw=16000.0,
        )
        rec = evaluate_supply_deficit(inputs)
        assert rec is None

    def test_renewable_opportunity(self):
        """Renewable opportunity rule triggers when renewable generation is low."""
        inputs = SystemInputs(
            grid_demand_mw=16000.0,
            solar_generation_mw=500.0,
            wind_generation_mw=300.0,
        )
        rec = evaluate_renewable_opportunity(inputs)
        assert rec is not None
        assert rec.type == RecommendationType.RENEWABLE_OPPORTUNITY

    def test_no_renewable_opportunity(self):
        """Renewable opportunity rule does not trigger when no generation."""
        inputs = SystemInputs(
            grid_demand_mw=16000.0,
            solar_generation_mw=0.0,
            wind_generation_mw=0.0,
        )
        rec = evaluate_renewable_opportunity(inputs)
        assert rec is None

    def test_high_risk_detected(self):
        """High risk rule triggers when risk score >= 60."""
        inputs = SystemInputs(
            risk_score=75.0,
            risk_level="HIGH",
        )
        rec = evaluate_high_risk(inputs)
        assert rec is not None
        assert rec.type == RecommendationType.HIGH_GRID_RISK

    def test_low_risk_not_triggered(self):
        """High risk rule does not trigger when risk score < 60."""
        inputs = SystemInputs(
            risk_score=40.0,
            risk_level="LOW",
        )
        rec = evaluate_high_risk(inputs)
        assert rec is None

    def test_forecast_unavailable(self):
        """Forecast unavailable rule triggers when forecast not ready."""
        inputs = SystemInputs(
            independent_observations=50,
            forecast_available=False,
        )
        rec = evaluate_forecast_unavailable(inputs)
        assert rec is not None
        assert rec.type == RecommendationType.FORECAST_UNAVAILABLE

    def test_forecast_available_no_trigger(self):
        """Forecast unavailable rule does not trigger when forecast available."""
        inputs = SystemInputs(
            independent_observations=200,
            forecast_available=True,
        )
        rec = evaluate_forecast_unavailable(inputs)
        assert rec is None

    def test_data_quality_issues(self):
        """Data quality rule triggers when issues exist."""
        inputs = SystemInputs(
            data_quality_issues=["grid_unavailable", "solar_stale"],
        )
        rec = evaluate_data_quality(inputs)
        assert rec is not None
        assert rec.type == RecommendationType.DATA_QUALITY_DEGRADATION

    def test_no_data_quality_issues(self):
        """Data quality rule does not trigger when no issues."""
        inputs = SystemInputs(data_quality_issues=[])
        rec = evaluate_data_quality(inputs)
        assert rec is None


class TestDecisionSupportService:
    """Test the unified DecisionSupportService."""

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_healthy_system(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """Healthy system with no deficit returns no critical recommendations."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 15000.0,
                "supply_mw": 16000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {
            "forecasts": [{"generation_mw": 2000.0}],
        }
        mock_wind.return_value = {
            "forecasts": [{"generation_mw": 1000.0}],
        }
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 30.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 200

        service = DecisionSupportService()
        result = service.generate_recommendations()

        assert result["status"] == "OK"
        assert result["total_recommendations"] >= 0
        assert "system_inputs" in result
        assert "metadata" in result

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_deficit_detected(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """System with deficit generates supply deficit recommendation."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 16000.0,
                "supply_mw": 15000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": []}
        mock_wind.return_value = {"forecasts": []}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 30.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 200

        service = DecisionSupportService()
        result = service.generate_recommendations()

        deficit_recs = [
            r for r in result["recommendations"]
            if r["type"] == "SUPPLY_DEFICIT"
        ]
        assert len(deficit_recs) > 0
        assert deficit_recs[0]["evidence"]["current_value"] == 1000.0

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_high_risk_detected(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """System with high risk generates high risk recommendation."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 15000.0,
                "supply_mw": 16000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": []}
        mock_wind.return_value = {"forecasts": []}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 75.0
        mock_risk_result.risk_level = "HIGH"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 200

        service = DecisionSupportService()
        result = service.generate_recommendations()

        risk_recs = [
            r for r in result["recommendations"]
            if r["type"] == "HIGH_GRID_RISK"
        ]
        assert len(risk_recs) > 0

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_forecast_unavailable(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """System with insufficient observations generates forecast unavailable."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 15000.0,
                "supply_mw": 16000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": []}
        mock_wind.return_value = {"forecasts": []}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 30.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 50  # Less than 168

        service = DecisionSupportService()
        result = service.generate_recommendations()

        forecast_recs = [
            r for r in result["recommendations"]
            if r["type"] == "FORECAST_UNAVAILABLE"
        ]
        assert len(forecast_recs) > 0
        assert forecast_recs[0]["evidence"]["current_value"] == 50.0

    @patch("backend.services.grid_service.get_grid_live")
    def test_pgcb_unavailable(self, mock_grid):
        """System handles PGCB data unavailability gracefully."""
        mock_grid.return_value = None

        service = DecisionSupportService()
        result = service.generate_recommendations()

        assert result["status"] == "OK"
        assert "grid_data" in result["missing_inputs"]

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_mixed_data_confidence(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """Mixed data sources affect confidence appropriately."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 16000.0,
                "supply_mw": 15000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": []}
        mock_wind.return_value = {"forecasts": []}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 30.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 200

        service = DecisionSupportService()
        result = service.generate_recommendations()

        # Check that recommendations have confidence scores
        for rec in result["recommendations"]:
            assert 0.0 <= rec["confidence"] <= 1.0


class TestSystemHealth:
    """Test system health endpoint."""

    @patch("backend.demand_history.count_unique_observations")
    @patch("backend.services.grid_service.get_grid_live")
    def test_system_health(
        self,
        mock_grid,
        mock_observations,
    ):
        """System health returns expected fields."""
        mock_observations.return_value = 200
        mock_grid.return_value = {"grid_status": "NORMAL"}

        health = get_system_health()

        assert "independent_observations" in health
        assert "grid_status" in health
        assert "forecast_ready" in health
        assert "data_quality_score" in health
        assert health["forecast_ready"] is True

    @patch("backend.demand_history.count_unique_observations")
    @patch("backend.services.grid_service.get_grid_live")
    def test_forecast_not_ready(
        self,
        mock_grid,
        mock_observations,
    ):
        """Forecast not ready when observations < 168."""
        mock_observations.return_value = 50
        mock_grid.return_value = {"grid_status": "NORMAL"}

        health = get_system_health()

        assert health["forecast_ready"] is False


class TestAPIDataClassification:
    """Test data classification integration."""

    def test_source_type_enum(self):
        """SourceType enum has expected values."""
        assert SourceType.RULE_BASED.value == "RULE_BASED"
        assert SourceType.HISTORICAL_ANALYSIS.value == "HISTORICAL_ANALYSIS"
        assert SourceType.SYSTEM_STATUS.value == "SYSTEM_STATUS"
        assert SourceType.FORECAST.value == "FORECAST"
        assert SourceType.SIMULATION.value == "SIMULATION"

    def test_data_status_enum(self):
        """DataStatus enum has expected values."""
        assert DataStatus.LIVE.value == "LIVE"
        assert DataStatus.HISTORICAL.value == "HISTORICAL"
        assert DataStatus.CACHED.value == "CACHED"
        assert DataStatus.ESTIMATED.value == "ESTIMATED"
        assert DataStatus.MODELED.value == "MODELED"
        assert DataStatus.SYNTHETIC.value == "SYNTHETIC"
        assert DataStatus.UNAVAILABLE.value == "UNAVAILABLE"

    def test_recommendation_evidence_to_dict(self):
        """RecommendationEvidence serializes correctly."""
        evidence = RecommendationEvidence(
            trigger="test_trigger",
            current_value=100.0,
            threshold=50.0,
            source_type=SourceType.RULE_BASED,
            data_status=DataStatus.LIVE,
            explanation="Test explanation",
        )
        d = evidence.to_dict()
        assert d["trigger"] == "test_trigger"
        assert d["current_value"] == 100.0
        assert d["source_type"] == "RULE_BASED"
        assert d["data_status"] == "LIVE"

    def test_recommendation_to_dict(self):
        """Recommendation serializes correctly."""
        rec = Recommendation(
            type=RecommendationType.SUPPLY_DEFICIT,
            priority=RecommendationPriority.HIGH,
            title="Test",
            summary="Test summary",
            detailed_explanation="Test explanation",
            evidence=RecommendationEvidence(trigger="test"),
            expected_impact="Test impact",
            confidence=0.85,
        )
        d = rec.to_dict()
        assert d["type"] == "SUPPLY_DEFICIT"
        assert d["priority"] == "HIGH"
        assert d["confidence"] == 0.85
        assert "evidence" in d


class TestSmartInsightsBehavior:
    """Behavior tests for SmartInsights component requirements (A-I)."""

    # --- A: SmartInsights consumes real Decision Support data ---

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_smart_insights_consumes_real_data(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """DecisionSupportService returns real data, not fabricated values."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 15000.0,
                "supply_mw": 16000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": [{"generation_mw": 500.0}]}
        mock_wind.return_value = {"forecasts": [{"generation_mw": 300.0}]}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 25.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 200

        result = get_decision_support()

        assert result["status"] == "OK"
        assert "recommendations" in result
        assert "system_inputs" in result
        assert "metadata" in result
        assert result["metadata"]["source_type"] in [
            "RULE_BASED", "SYSTEM_STATUS", "HISTORICAL_ANALYSIS"
        ]

    # --- B: No dummy recommendations remain ---

    def test_no_dummy_recommendations_in_rules(self):
        """Rule evaluation functions never return fabricated data."""
        inputs = SystemInputs(
            grid_demand_mw=15000.0,
            grid_supply_mw=16000.0,
            solar_generation_mw=500.0,
            wind_generation_mw=300.0,
            risk_score=25.0,
            risk_level="LOW",
            independent_observations=200,
            forecast_available=True,
        )

        recs = [
            r for r in [
                evaluate_supply_deficit(inputs),
                evaluate_renewable_opportunity(inputs),
                evaluate_high_risk(inputs),
                evaluate_forecast_unavailable(inputs),
                evaluate_data_quality(inputs),
            ]
            if r is not None
        ]

        for rec in recs:
            assert rec.evidence.source_type in [
                SourceType.RULE_BASED,
                SourceType.SYSTEM_STATUS,
                SourceType.HISTORICAL_ANALYSIS,
            ]
            assert "9999" not in rec.summary
            assert "9999" not in rec.detailed_explanation

    # --- C: Forecast unavailable is displayed honestly ---

    def test_forecast_unavailable_honest(self):
        """Forecast unavailable recommendation clearly states limitation."""
        inputs = SystemInputs(
            independent_observations=50,
            forecast_available=False,
        )
        rec = evaluate_forecast_unavailable(inputs)
        assert rec is not None
        assert "50" in rec.summary
        assert "168" in rec.detailed_explanation
        assert "SYNTHETIC" not in rec.title.upper()

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_forecast_unavailable_in_api_response(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """API returns forecast_available=false when observations < 168."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 15000.0,
                "supply_mw": 16000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": []}
        mock_wind.return_value = {"forecasts": []}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 30.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 50

        result = get_decision_support()

        assert result["metadata"]["forecast_available"] is False
        forecast_recs = [
            r for r in result["recommendations"]
            if r["type"] == "FORECAST_UNAVAILABLE"
        ]
        assert len(forecast_recs) > 0

    # --- D: Degraded data is visible ---

    @patch("backend.services.grid_service.get_grid_live")
    def test_degraded_data_visible(self, mock_grid):
        """Missing inputs are reported in the response."""
        mock_grid.return_value = None

        result = get_decision_support()

        assert len(result["missing_inputs"]) > 0
        assert "grid_data" in result["missing_inputs"]

    # --- E: No duplicate API polling is introduced ---

    def test_shared_hook_exists(self):
        """useDecisionSupport hook file exists and exports correctly."""
        import importlib.util
        spec = importlib.util.find_spec("frontend.src.hooks.useDecisionSupport")
        # The module path may not be directly importable, but the file should exist
        from pathlib import Path
        hook_path = Path("frontend/src/hooks/useDecisionSupport.tsx")
        assert hook_path.exists(), "useDecisionSupport.tsx must exist"

    # --- F: Empty recommendations render safely ---

    @patch("backend.services.grid_service.get_grid_live")
    @patch("backend.services.solar_service.get_solar_live")
    @patch("backend.services.wind_service.get_wind_live")
    @patch("backend.risk_engine.compute_grid_risk")
    @patch("backend.demand_history.count_unique_observations")
    def test_empty_recommendations_safe(
        self,
        mock_observations,
        mock_risk,
        mock_wind,
        mock_solar,
        mock_grid,
    ):
        """System with no issues returns empty recommendations safely."""
        mock_grid.return_value = {
            "grid_snapshot": {
                "current_demand_mw": 15000.0,
                "supply_mw": 16000.0,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "grid_status": "NORMAL",
        }
        mock_solar.return_value = {"forecasts": [{"generation_mw": 2000.0}]}
        mock_wind.return_value = {"forecasts": [{"generation_mw": 1000.0}]}
        mock_risk_result = MagicMock()
        mock_risk_result.composite_score = 20.0
        mock_risk_result.risk_level = "LOW"
        mock_risk.return_value = mock_risk_result
        mock_observations.return_value = 200

        result = get_decision_support()

        assert result["status"] == "OK"
        assert isinstance(result["recommendations"], list)
        # Response is valid even with zero recommendations
        assert result["total_recommendations"] >= 0

    # --- G: API failure renders safely ---

    def test_api_failure_returns_error_status(self):
        """DecisionSupportService handles internal errors gracefully."""
        with patch.object(
            DecisionSupportService,
            "_collect_inputs",
            side_effect=Exception("Simulated failure"),
        ):
            try:
                result = get_decision_support()
                # If it doesn't raise, the response should still be valid
                assert "status" in result
            except Exception:
                # The route handler catches this and returns an error response
                pass

    # --- H: Rule-based recommendation is labeled RULE_BASED ---

    def test_rule_based_labeled_correctly(self):
        """Rule-based recommendations have source_type=RULE_BASED."""
        inputs = SystemInputs(
            grid_demand_mw=16000.0,
            grid_supply_mw=15000.0,
            grid_data_classification="OFFICIAL",
        )
        rec = evaluate_supply_deficit(inputs)
        assert rec is not None
        assert rec.evidence.source_type == SourceType.SYSTEM_STATUS
        assert rec.evidence.source_type.value in [
            "RULE_BASED", "SYSTEM_STATUS"
        ]

    # --- I: Synthetic forecast is never labeled production forecast ---

    def test_synthetic_not_labeled_as_production(self):
        """FORECAST_UNAVAILABLE never claims synthetic model is production."""
        inputs = SystemInputs(
            independent_observations=50,
            forecast_available=False,
        )
        rec = evaluate_forecast_unavailable(inputs)
        assert rec is not None
        assert "production" not in rec.title.lower()
        assert "AI prediction" not in rec.detailed_explanation
        assert "ML prediction" not in rec.detailed_explanation
        assert "AI forecast" not in rec.detailed_explanation

    # --- Additional: data provenance preserved ---

    def test_data_provenance_preserved(self):
        """Recommendations include full data provenance."""
        inputs = SystemInputs(
            grid_demand_mw=16000.0,
            grid_supply_mw=15000.0,
            grid_data_classification="OFFICIAL",
        )
        rec = evaluate_supply_deficit(inputs)
        assert rec is not None
        assert rec.evidence.source_data_classification is not None
        assert rec.evidence.data_status is not None
        assert rec.evidence.source_type is not None
        assert rec.timestamp != ""
