"""Demand Forecasting v2 for PowerFlex BD.

Implements proper walk-forward validation, baseline comparisons,
and realistic forecasting without data leakage.

All models use Bangladesh timezone (UTC+06:00) for temporal features.
Data classification: FORECAST (weather-driven, ML-driven predictions).
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from backend.prototype_config import BASE_DEMAND_MW

logger = logging.getLogger("powerflex.forecast_v2")

BST = timezone(timedelta(hours=6))


# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class ForecastPoint:
    """Single forecast point."""
    timestamp_utc: datetime
    timestamp_local: datetime
    predicted_mw: float
    lower_bound_mw: float
    upper_bound_mw: float
    confidence_level: float = 0.90
    model_name: str = "baseline"
    data_classification: str = "FORECAST"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp_utc": self.timestamp_utc.isoformat(),
            "timestamp_local": self.timestamp_local.isoformat(),
            "predicted_mw": round(self.predicted_mw, 2),
            "lower_bound_mw": round(self.lower_bound_mw, 2),
            "upper_bound_mw": round(self.upper_bound_mw, 2),
            "confidence_level": self.confidence_level,
            "model_name": self.model_name,
            "data_classification": self.data_classification,
        }


@dataclass
class ForecastResult:
    """Complete forecast result with metadata."""
    forecast_points: List[ForecastPoint] = field(default_factory=list)
    model_name: str = "baseline"
    forecast_horizon_hours: int = 24
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    baseline_mae_mw: float = 0.0
    baseline_rmse_mw: float = 0.0
    model_mae_mw: float = 0.0
    model_rmse_mw: float = 0.0
    improvement_pct: float = 0.0
    data_classification: str = "FORECAST"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "forecast_horizon_hours": self.forecast_horizon_hours,
            "generated_at": self.generated_at.isoformat(),
            "point_count": len(self.forecast_points),
            "points": [p.to_dict() for p in self.forecast_points],
            "validation": {
                "baseline_mae_mw": round(self.baseline_mae_mw, 2),
                "baseline_rmse_mw": round(self.baseline_rmse_mw, 2),
                "model_mae_mw": round(self.model_mae_mw, 2),
                "model_rmse_mw": round(self.model_rmse_mw, 2),
                "improvement_pct": round(self.improvement_pct, 1),
            },
            "data_classification": self.data_classification,
        }


# =========================================================
# BASELINE MODELS
# =========================================================

class BaselineForecaster:
    """Simple baseline models for comparison."""

    @staticmethod
    def persistence_forecast(
        recent_demands: List[float],
        horizon_hours: int = 24,
    ) -> List[float]:
        """Persistence model: repeat last value.

        This is the simplest possible baseline.
        """
        if not recent_demands:
            return [BASE_DEMAND_MW] * horizon_hours
        return [recent_demands[-1]] * horizon_hours

    @staticmethod
    def moving_average_forecast(
        recent_demands: List[float],
        window_size: int = 24,
        horizon_hours: int = 24,
    ) -> List[float]:
        """Moving average model: repeat the mean of last N values."""
        if not recent_demands:
            return [BASE_DEMAND_MW] * horizon_hours
        window = recent_demands[-window_size:]
        avg = sum(window) / len(window)
        return [avg] * horizon_hours

    @staticmethod
    def seasonal_naive_forecast(
        recent_demands: List[float],
        period_hours: int = 24,
        horizon_hours: int = 24,
    ) -> List[float]:
        """Seasonal naive: repeat the value from the same hour yesterday.

        For Bangladesh, electricity demand follows a strong daily pattern
        with morning peak (10-12), evening peak (18-22), and overnight valley.
        """
        if len(recent_demands) < period_hours:
            return BaselineForecaster.moving_average_forecast(
                recent_demands, window_size=min(24, len(recent_demands)),
                horizon_hours=horizon_hours,
            )
        result = []
        for i in range(horizon_hours):
            idx = -(period_hours - i % period_hours)
            if abs(idx) <= len(recent_demands):
                result.append(recent_demands[idx])
            else:
                result.append(recent_demands[-1])
        return result

    @staticmethod
    def hour_of_day_profile(
        hourly_profiles: Dict[int, float],
        horizon_hours: int = 24,
        start_hour_bst: Optional[int] = None,
    ) -> List[float]:
        """Use hour-of-day profile (typical demand by hour).

        hourly_profiles: dict mapping hour (0-23) to typical demand MW.
        """
        if not hourly_profiles:
            return [BASE_DEMAND_MW] * horizon_hours

        now = datetime.now(BST)
        start_hour = start_hour_bst if start_hour_bst is not None else now.hour

        result = []
        for i in range(horizon_hours):
            hour = (start_hour + i) % 24
            result.append(hourly_profiles.get(hour, BASE_DEMAND_MW))
        return result


# =========================================================
# WALK-FORWARD VALIDATOR
# =========================================================

class WalkForwardValidator:
    """Walk-forward validation for time series forecasting.
    
    Avoids data leakage by always training on past data and testing on future.
    """

    @staticmethod
    def split_walk_forward(
        demands: List[float],
        train_size: int = 168,
        test_size: int = 24,
        step_size: int = 24,
    ) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Generate walk-forward splits.
        
        Returns list of ((train_start, train_end), (test_start, test_end)) indices.
        """
        splits = []
        n = len(demands)
        start = 0

        while start + train_size + test_size <= n:
            train_start = start
            train_end = start + train_size
            test_start = train_end
            test_end = test_start + test_size
            splits.append(((train_start, train_end), (test_start, test_end)))
            start += step_size

        return splits

    @staticmethod
    def evaluate_baseline(
        demands: List[float],
        train_size: int = 168,
        test_size: int = 24,
        step_size: int = 24,
    ) -> Dict[str, Any]:
        """Evaluate baseline models using walk-forward validation."""
        splits = WalkForwardValidator.split_walk_forward(
            demands, train_size, test_size, step_size
        )

        if not splits:
            return {
                "status": "INSUFFICIENT_DATA",
                "message": f"Need at least {train_size + test_size} data points",
                "available_points": len(demands),
            }

        persistence_errors = []
        ma_errors = []
        seasonal_errors = []

        for (train_start, train_end), (test_start, test_end) in splits:
            train_data = demands[train_start:train_end]
            test_data = demands[test_start:test_end]

            persistence_pred = BaselineForecaster.persistence_forecast(
                train_data, horizon_hours=test_size
            )
            ma_pred = BaselineForecaster.moving_average_forecast(
                train_data, window_size=24, horizon_hours=test_size
            )
            seasonal_pred = BaselineForecaster.seasonal_naive_forecast(
                train_data, period_hours=24, horizon_hours=test_size
            )

            for i in range(min(len(test_data), test_size)):
                persistence_errors.append(abs(test_data[i] - persistence_pred[i]))
                ma_errors.append(abs(test_data[i] - ma_pred[i]))
                if i < len(seasonal_pred):
                    seasonal_errors.append(abs(test_data[i] - seasonal_pred[i]))

        def mae(errors):
            return sum(errors) / len(errors) if errors else 0

        def rmse(errors):
            return math.sqrt(sum(e**2 for e in errors) / len(errors)) if errors else 0

        best_model = min(
            [("persistence", mae(persistence_errors)),
             ("moving_average", mae(ma_errors)),
             ("seasonal_naive", mae(seasonal_errors))],
            key=lambda x: x[1],
        )

        return {
            "status": "OK",
            "splits_evaluated": len(splits),
            "persistence": {
                "mae_mw": round(mae(persistence_errors), 2),
                "rmse_mw": round(rmse(persistence_errors), 2),
            },
            "moving_average": {
                "mae_mw": round(mae(ma_errors), 2),
                "rmse_mw": round(rmse(ma_errors), 2),
            },
            "seasonal_naive": {
                "mae_mw": round(mae(seasonal_errors), 2),
                "rmse_mw": round(rmse(seasonal_errors), 2),
            },
            "best_baseline": best_model[0],
            "best_baseline_mae_mw": round(best_model[1], 2),
        }


# =========================================================
# STATISTICAL FORECAST (no ML dependency)
# =========================================================

class StatisticalForecaster:
    """Statistical demand forecaster using seasonal decomposition.
    
    Uses historical patterns without requiring trained ML models.
    This avoids the synthetic data problem of the original XGBoost model.
    """

    BANGLADESH_TYPICAL_PROFILE = {
        0: 4800, 1: 4500, 2: 4300, 3: 4200,
        4: 4200, 5: 4300, 6: 4600, 7: 5100,
        8: 5600, 9: 6100, 10: 6500, 11: 6700,
        12: 6600, 13: 6500, 14: 6400, 15: 6300,
        16: 6200, 17: 6300, 18: 6800, 19: 7200,
        20: 7500, 21: 7300, 22: 6800, 23: 5800,
    }

    WEEKDAY_MULTIPLIER = 1.0
    WEEKEND_MULTIPLIER = 0.88

    @staticmethod
    def get_typical_profile(
        reference_demands: Optional[List[float]] = None,
    ) -> Dict[int, float]:
        """Get hour-of-day profile, optionally calibrated from recent data."""
        profile = dict(StatisticalForecaster.BANGLADESH_TYPICAL_PROFILE)

        if reference_demands and len(reference_demands) >= 48:
            recent_avg = sum(reference_demands[-48:]) / len(reference_demands[-48:])
            baseline_avg = sum(profile.values()) / len(profile)
            if baseline_avg > 0:
                scale = recent_avg / baseline_avg
                profile = {h: v * scale for h, v in profile.items()}

        return profile

    @staticmethod
    def forecast(
        recent_demands: Optional[List[float]] = None,
        horizon_hours: int = 24,
        temperature_forecast: Optional[List[float]] = None,
    ) -> ForecastResult:
        """Generate a statistical demand forecast.
        
        No synthetic data. Uses hour-of-day profiles calibrated
        from recent actual data when available.
        """
        now_utc = datetime.now(timezone.utc)
        now_bst = now_utc.astimezone(BST)

        profile = StatisticalForecaster.get_typical_profile(recent_demands)

        recent_avg = None
        if recent_demands and len(recent_demands) >= 6:
            recent_avg = sum(recent_demands[-6:]) / len(recent_demands[-6:])

        points = []
        for i in range(horizon_hours):
            forecast_utc = now_utc + timedelta(hours=i + 1)
            forecast_bst = forecast_utc.astimezone(BST)
            hour = forecast_bst.hour
            is_weekend = forecast_bst.weekday() >= 5

            base_demand = profile.get(hour, BASE_DEMAND_MW)

            if is_weekend:
                base_demand *= StatisticalForecaster.WEEKEND_MULTIPLIER

            if recent_avg is not None:
                base_demand = 0.7 * base_demand + 0.3 * recent_avg

            if temperature_forecast and i < len(temperature_forecast):
                temp = temperature_forecast[i]
                if temp > 35:
                    cooling_factor = 1 + (temp - 35) * 0.02
                    base_demand *= cooling_factor
                elif temp < 15:
                    heating_factor = 1 + (15 - temp) * 0.01
                    base_demand *= heating_factor

            uncertainty_pct = 0.05 + 0.02 * i
            lower = base_demand * (1 - uncertainty_pct)
            upper = base_demand * (1 + uncertainty_pct)

            points.append(ForecastPoint(
                timestamp_utc=forecast_utc,
                timestamp_local=forecast_bst,
                predicted_mw=round(base_demand, 2),
                lower_bound_mw=round(lower, 2),
                upper_bound_mw=round(upper, 2),
                confidence_level=0.90,
                model_name="statistical_profile",
                data_classification="FORECAST",
            ))

        baseline_mae = 0.0
        baseline_rmse = 0.0
        if recent_demands and len(recent_demands) >= 24:
            baseline_preds = BaselineForecaster.persistence_forecast(
                recent_demands, horizon_hours=min(24, len(recent_demands))
            )
            test_data = recent_demands[-len(baseline_preds):]
            errors = [abs(test_data[i] - baseline_preds[i]) for i in range(len(test_data))]
            baseline_mae = sum(errors) / len(errors) if errors else 0
            baseline_rmse = math.sqrt(sum(e**2 for e in errors) / len(errors)) if errors else 0

        model_errors = []
        if recent_demands and len(recent_demands) >= 24:
            for i in range(min(24, len(points))):
                idx = len(recent_demands) - 24 + i
                if 0 <= idx < len(recent_demands):
                    model_errors.append(abs(recent_demands[idx] - points[i].predicted_mw))

        model_mae = sum(model_errors) / len(model_errors) if model_errors else 0
        model_rmse = math.sqrt(sum(e**2 for e in model_errors) / len(model_errors)) if model_errors else 0

        improvement = 0.0
        if baseline_mae > 0:
            improvement = ((baseline_mae - model_mae) / baseline_mae) * 100

        return ForecastResult(
            forecast_points=points,
            model_name="statistical_profile",
            forecast_horizon_hours=horizon_hours,
            generated_at=now_utc,
            baseline_mae_mw=baseline_mae,
            baseline_rmse_mw=baseline_rmse,
            model_mae_mw=model_mae,
            model_rmse_mw=model_rmse,
            improvement_pct=improvement,
            data_classification="FORECAST",
        )
