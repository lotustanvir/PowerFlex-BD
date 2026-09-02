import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np

from backend.demand_forecast import (
    FEATURE_COLUMNS,
    generate_synthetic_training_data,
    fetch_temperature_forecast,
    train_demand_model,
    forecast_24h_demand,
)

logger = logging.getLogger("powerflex.demand_forecast_v2")


@dataclass
class ConfidenceInterval:
    lower_mw: float
    upper_mw: float
    confidence_level: float = 0.90


@dataclass
class ModelComparisonResult:
    persistence_mae: float
    xgboost_mae: float
    persistence_rmse: float
    xgboost_rmse: float
    winner: str
    improvement_pct: float


@dataclass
class WalkForwardFold:
    fold: int
    train_size: int
    test_size: int
    mae: float
    rmse: float
    mape: float


@dataclass
class WalkForwardResult:
    folds: List[WalkForwardFold]
    mean_mae: float
    mean_rmse: float
    mean_mape: float


class DemandForecaster:
    def __init__(self, model: Any = None):
        self._model = model
        self._training_data: Optional[List[Dict[str, Any]]] = None

    @property
    def model(self) -> Any:
        if self._model is None:
            self._model = train_demand_model()
        return self._model

    def _ensure_training_data(self) -> List[Dict[str, Any]]:
        if self._training_data is None:
            self._training_data = generate_synthetic_training_data()
        return self._training_data

    def forecast(
        self,
        current_demand_mw: float,
    ) -> Dict[str, Any]:
        forecast_result = forecast_24h_demand(
            current_demand_mw, self.model
        )

        hourly = forecast_result.get("hourly_forecast", [])
        predictions = [h["predicted_demand_mw"] for h in hourly]

        if predictions:
            prediction_std = float(np.std(predictions)) if len(predictions) > 1 else 0.0
        else:
            prediction_std = 0.0

        hourly_with_ci = []
        for entry in hourly:
            pred = entry["predicted_demand_mw"]
            ci = ConfidenceInterval(
                lower_mw=round(pred - 1.65 * prediction_std, 1),
                upper_mw=round(pred + 1.65 * prediction_std, 1),
                confidence_level=0.90,
            )
            hourly_with_ci.append({
                **entry,
                "confidence_interval": {
                    "lower_mw": ci.lower_mw,
                    "upper_mw": ci.upper_mw,
                    "confidence_level": ci.confidence_level,
                },
            })

        forecast_result["hourly_forecast"] = hourly_with_ci
        forecast_result["prediction_variance"] = round(prediction_std ** 2, 2)
        forecast_result["model_version"] = "v2_walk_forward"

        return forecast_result

    def persistence_forecast(
        self,
        current_demand_mw: float,
        hours: int = 24,
    ) -> List[float]:
        return [current_demand_mw] * hours

    def compare_models(
        self,
        test_hours: int = 24,
    ) -> ModelComparisonResult:
        records = self._ensure_training_data()

        split_idx = max(0, len(records) - test_hours)
        train_records = records[:split_idx]
        test_records = records[split_idx:]

        if not test_records:
            return ModelComparisonResult(
                persistence_mae=0.0,
                xgboost_mae=0.0,
                persistence_rmse=0.0,
                xgboost_rmse=0.0,
                winner="xgboost",
                improvement_pct=0.0,
            )

        X_test = np.array([
            [r[col] for col in FEATURE_COLUMNS]
            for r in test_records
        ])
        y_test = np.array([r["demand_mw"] for r in test_records])

        # Train a FRESH model on training data only (no data leakage)
        X_train = np.array([
            [r[col] for col in FEATURE_COLUMNS]
            for r in train_records
        ])
        y_train = np.array([r["demand_mw"] for r in train_records])
        
        try:
            from sklearn.ensemble import GradientBoostingRegressor
            fresh_model = GradientBoostingRegressor(
                n_estimators=100,
                max_depth=4,
                learning_rate=0.1,
                random_state=42,
            )
            fresh_model.fit(X_train, y_train)
            xgb_preds = fresh_model.predict(X_test)
        except Exception as e:
            logger.warning("Fresh model training failed: %s", e)
            xgb_preds = np.full(len(test_records), np.mean(y_train))

        base_demand = train_records[-1]["demand_mw"] if train_records else 16000.0
        persistence_preds = np.full(len(test_records), base_demand)

        persistence_errors = np.abs(y_test - persistence_preds)
        xgb_errors = np.abs(y_test - xgb_preds)

        persistence_mae = float(np.mean(persistence_errors))
        xgb_mae = float(np.mean(xgb_errors))

        persistence_rmse = float(np.sqrt(np.mean((y_test - persistence_preds) ** 2)))
        xgb_rmse = float(np.sqrt(np.mean((y_test - xgb_preds) ** 2)))

        if persistence_mae > 0:
            improvement_pct = ((persistence_mae - xgb_mae) / persistence_mae) * 100
        else:
            improvement_pct = 0.0

        winner = "xgboost" if xgb_mae <= persistence_mae else "persistence"

        return ModelComparisonResult(
            persistence_mae=round(persistence_mae, 2),
            xgboost_mae=round(xgb_mae, 2),
            persistence_rmse=round(persistence_rmse, 2),
            xgboost_rmse=round(xgb_rmse, 2),
            winner=winner,
            improvement_pct=round(improvement_pct, 2),
        )

    def walk_forward_validation(
        self,
        n_splits: int = 5,
        min_train_size: int = 100,
    ) -> WalkForwardResult:
        records = self._ensure_training_data()
        total_size = len(records)
        min_test_size = 24

        available = total_size - min_train_size
        if available < min_test_size * n_splits:
            n_splits = max(1, available // min_test_size)

        step = available // n_splits if n_splits > 0 else available
        if step < min_test_size:
            step = min_test_size

        folds: List[WalkForwardFold] = []

        for fold_idx in range(n_splits):
            train_end = min_train_size + fold_idx * step
            test_end = min(train_end + step, total_size)

            if train_end >= total_size:
                break

            train_records = records[:train_end]
            test_records = records[train_end:test_end]

            if not test_records:
                continue

            X_train = np.array([
                [r[col] for col in FEATURE_COLUMNS]
                for r in train_records
            ])
            y_train = np.array([
                r["demand_mw"] for r in train_records
            ])

            X_test = np.array([
                [r[col] for col in FEATURE_COLUMNS]
                for r in test_records
            ])
            y_test = np.array([
                r["demand_mw"] for r in test_records
            ])

            try:
                from xgboost import XGBRegressor
                fold_model = XGBRegressor(
                    n_estimators=200,
                    max_depth=6,
                    learning_rate=0.1,
                    subsample=0.8,
                    colsample_bytree=0.8,
                    random_state=42,
                    verbosity=0,
                )
            except ImportError:
                from sklearn.ensemble import (
                    GradientBoostingRegressor,
                )
                fold_model = GradientBoostingRegressor(
                    n_estimators=200,
                    max_depth=5,
                    learning_rate=0.1,
                    subsample=0.8,
                    random_state=42,
                )

            fold_model.fit(X_train, y_train)
            preds = fold_model.predict(X_test)

            errors = np.abs(y_test - preds)
            mae = float(np.mean(errors))
            rmse = float(np.sqrt(np.mean((y_test - preds) ** 2)))

            nonzero = y_test != 0
            if nonzero.any():
                mape = float(np.mean(np.abs((y_test[nonzero] - preds[nonzero]) / y_test[nonzero])) * 100)
            else:
                mape = 0.0

            folds.append(WalkForwardFold(
                fold=fold_idx + 1,
                train_size=len(train_records),
                test_size=len(test_records),
                mae=round(mae, 2),
                rmse=round(rmse, 2),
                mape=round(mape, 2),
            ))

        if not folds:
            return WalkForwardResult(
                folds=[],
                mean_mae=0.0,
                mean_rmse=0.0,
                mean_mape=0.0,
            )

        return WalkForwardResult(
            folds=folds,
            mean_mae=round(float(np.mean([f.mae for f in folds])), 2),
            mean_rmse=round(float(np.mean([f.rmse for f in folds])), 2),
            mean_mape=round(float(np.mean([f.mape for f in folds])), 2),
        )

    def forecast_with_validation(
        self,
        current_demand_mw: float,
    ) -> Dict[str, Any]:
        forecast_result = self.forecast(current_demand_mw)

        comparison = self.compare_models()
        walk_forward = self.walk_forward_validation()

        forecast_result["model_comparison"] = {
            "persistence_mae": comparison.persistence_mae,
            "xgboost_mae": comparison.xgboost_mae,
            "persistence_rmse": comparison.persistence_rmse,
            "xgboost_rmse": comparison.xgboost_rmse,
            "winner": comparison.winner,
            "improvement_pct": comparison.improvement_pct,
        }

        forecast_result["walk_forward_validation"] = {
            "n_folds": len(walk_forward.folds),
            "mean_mae": walk_forward.mean_mae,
            "mean_rmse": walk_forward.mean_rmse,
            "mean_mape": walk_forward.mean_mape,
            "fold_details": [
                {
                    "fold": f.fold,
                    "train_size": f.train_size,
                    "test_size": f.test_size,
                    "mae": f.mae,
                    "rmse": f.rmse,
                    "mape": f.mape,
                }
                for f in walk_forward.folds
            ],
        }

        forecast_result["training_data_note"] = (
            "SYNTHETIC — based on published Bangladesh load patterns, "
            "NOT real historical PGCB demand curves. Model is anchored "
            "to real-time PGCB demand but forecast shape is synthetic."
        )

        return forecast_result
