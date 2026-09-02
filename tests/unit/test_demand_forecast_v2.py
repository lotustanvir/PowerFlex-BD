import pytest
from unittest.mock import patch, MagicMock
import numpy as np

from backend.demand_forecast_v2 import (
    DemandForecaster,
    ConfidenceInterval,
    ModelComparisonResult,
    WalkForwardFold,
    WalkForwardResult,
)


# =========================================================
# ConfidenceInterval tests
# =========================================================

class TestConfidenceInterval:
    def test_creation(self):
        ci = ConfidenceInterval(lower_mw=14000, upper_mw=16000, confidence_level=0.90)
        assert ci.lower_mw == 14000
        assert ci.upper_mw == 16000
        assert ci.confidence_level == 0.90

    def test_default_confidence(self):
        ci = ConfidenceInterval(lower_mw=100, upper_mw=200)
        assert ci.confidence_level == 0.90


# =========================================================
# ModelComparisonResult tests
# =========================================================

class TestModelComparisonResult:
    def test_creation(self):
        mcr = ModelComparisonResult(
            persistence_mae=500,
            xgboost_mae=300,
            persistence_rmse=600,
            xgboost_rmse=350,
            winner="xgboost",
            improvement_pct=40.0,
        )
        assert mcr.winner == "xgboost"
        assert mcr.improvement_pct == 40.0


# =========================================================
# WalkForwardFold tests
# =========================================================

class TestWalkForwardFold:
    def test_creation(self):
        fold = WalkForwardFold(fold=1, train_size=500, test_size=100, mae=250, rmse=300, mape=2.5)
        assert fold.fold == 1
        assert fold.mape == 2.5


# =========================================================
# WalkForwardResult tests
# =========================================================

class TestWalkForwardResult:
    def test_creation(self):
        folds = [WalkForwardFold(fold=1, train_size=500, test_size=100, mae=250, rmse=300, mape=2.5)]
        result = WalkForwardResult(folds=folds, mean_mae=250, mean_rmse=300, mean_mape=2.5)
        assert result.mean_mae == 250


# =========================================================
# DemandForecaster tests
# =========================================================

class TestDemandForecaster:
    def _make_mock_model(self):
        model = MagicMock()
        model.predict.return_value = np.array([15000.0] * 24)
        return model

    def test_init(self):
        forecaster = DemandForecaster()
        assert forecaster._model is None

    def test_persistence_forecast(self):
        forecaster = DemandForecaster()
        result = forecaster.persistence_forecast(15000.0, hours=24)
        assert len(result) == 24
        assert all(v == 15000.0 for v in result)

    def test_persistence_forecast_custom_hours(self):
        forecaster = DemandForecaster()
        result = forecaster.persistence_forecast(12000.0, hours=12)
        assert len(result) == 12

    def test_forecast_calls_model(self):
        mock_model = self._make_mock_model()
        forecaster = DemandForecaster(model=mock_model)

        with patch(
            "backend.demand_forecast_v2.forecast_24h_demand"
        ) as mock_fc, patch(
            "backend.demand_forecast_v2.fetch_temperature_forecast",
            return_value=None,
        ):
            mock_fc.return_value = {
                "hourly_forecast": [
                    {"predicted_demand_mw": 15000.0, "hour_bst": h}
                    for h in range(24)
                ],
                "forecast_peak_mw": 15000.0,
            }
            result = forecaster.forecast(15000.0)

            assert "hourly_forecast" in result
            assert len(result["hourly_forecast"]) == 24

            for entry in result["hourly_forecast"]:
                assert "confidence_interval" in entry
                ci = entry["confidence_interval"]
                assert "lower_mw" in ci
                assert "upper_mw" in ci
                assert ci["confidence_level"] == 0.90

            assert result["model_version"] == "v2_walk_forward"

    def test_compare_models(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = np.random.normal(15000, 200, 24)

        forecaster = DemandForecaster(model=mock_model)
        forecaster._training_data = [
            {
                "month": 6, "hour": h, "day_of_week": 0,
                "is_weekend": 0, "is_summer": 1, "is_winter": 0,
                "hourly_factor": 0.9, "seasonal_factor": 1.0,
                "weekend_factor": 1.0, "temperature_c": 30.0,
                "demand_mw": 15000 + np.random.normal(0, 300),
            }
            for h in range(48)
        ]

        result = forecaster.compare_models(test_hours=24)
        assert isinstance(result, ModelComparisonResult)
        assert result.persistence_mae >= 0
        assert result.xgboost_mae >= 0
        assert result.winner in ("xgboost", "persistence")

    def test_walk_forward_validation(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = np.random.normal(15000, 200, 50)

        forecaster = DemandForecaster(model=mock_model)
        forecaster._training_data = [
            {
                "month": 6, "hour": h % 24, "day_of_week": d,
                "is_weekend": 0, "is_summer": 1, "is_winter": 0,
                "hourly_factor": 0.9, "seasonal_factor": 1.0,
                "weekend_factor": 1.0, "temperature_c": 30.0,
                "demand_mw": 15000 + np.random.normal(0, 300),
            }
            for d in range(7)
            for h in range(24)
        ]

        result = forecaster.walk_forward_validation(n_splits=3)
        assert isinstance(result, WalkForwardResult)
        assert len(result.folds) >= 1
        assert result.mean_mae >= 0
        assert result.mean_rmse >= 0

    def test_forecast_with_validation(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = np.random.normal(15000, 200, 24)

        forecaster = DemandForecaster(model=mock_model)
        forecaster._training_data = [
            {
                "month": 6, "hour": h, "day_of_week": 0,
                "is_weekend": 0, "is_summer": 1, "is_winter": 0,
                "hourly_factor": 0.9, "seasonal_factor": 1.0,
                "weekend_factor": 1.0, "temperature_c": 30.0,
                "demand_mw": 15000 + np.random.normal(0, 300),
            }
            for h in range(200)
        ]

        with patch(
            "backend.demand_forecast_v2.forecast_24h_demand"
        ) as mock_fc, patch(
            "backend.demand_forecast_v2.fetch_temperature_forecast",
            return_value=None,
        ):
            mock_fc.return_value = {
                "hourly_forecast": [
                    {"predicted_demand_mw": 15000.0, "hour_bst": h}
                    for h in range(24)
                ],
                "forecast_peak_mw": 15000.0,
            }
            result = forecaster.forecast_with_validation(15000.0)

            assert "model_comparison" in result
            assert "walk_forward_validation" in result
            assert "training_data_note" in result
            assert "SYNTHETIC" in result["training_data_note"]
            assert result["model_comparison"]["winner"] in ("xgboost", "persistence")

    def test_insufficient_data_for_walk_forward(self):
        mock_model = MagicMock()
        mock_model.predict.return_value = np.array([15000.0] * 24)

        forecaster = DemandForecaster(model=mock_model)
        forecaster._training_data = [
            {
                "month": 6, "hour": h, "day_of_week": 0,
                "is_weekend": 0, "is_summer": 1, "is_winter": 0,
                "hourly_factor": 0.9, "seasonal_factor": 1.0,
                "weekend_factor": 1.0, "temperature_c": 30.0,
                "demand_mw": 15000.0,
            }
            for h in range(50)
        ]

        result = forecaster.walk_forward_validation(n_splits=10)
        assert isinstance(result, WalkForwardResult)
        assert result.mean_mae >= 0
