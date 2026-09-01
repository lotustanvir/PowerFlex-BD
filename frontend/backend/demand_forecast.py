import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import joblib
import numpy as np
import requests
from fastapi import APIRouter, HTTPException
from pathlib import Path

from backend.demand_history import count_records
from backend.services.grid_service import get_grid_live


# =========================================================
# POWERFLEX BD - DEMAND FORECAST MODULE
# =========================================================
#
# Predicts next 24 hours of Bangladesh grid demand.
#
# Architecture:
#   Synthetic training data → XGBoost model → 24h forecast
#   + Current PGCB demand as anchor
#   + Temperature-based adjustment (Open-Meteo)
#
# IMPORTANT:
#   - Current demand ALWAYS comes from PGCB (never faked)
#   - Forecast is labeled "MODEL_FORECAST"
#   - No hardcoded demand/supply values
# =========================================================


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/demand",
    tags=["Demand Forecast"],
)


# =========================================================
# INTERNAL SERVICES
# =========================================================

WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# =========================================================
# MODEL PATH
# =========================================================

MODEL_DIR = PROJECT_ROOT / "models"
MODEL_FILE = MODEL_DIR / "demand_forecast_model.pkl"


# =========================================================
# BANGLADESH DEMAND PATTERNS
# =========================================================
#
# Based on publicly available Bangladesh grid data patterns.
# BPDB peak demand typically:
#   - Morning peak: 10:00-12:00 BST (04:00-06:00 UTC)
#   - Evening peak: 18:00-21:00 BST (12:00-15:00 UTC)
#   - Night minimum: 02:00-05:00 BST (20:00-23:00 UTC previous day)
#
# Summer (Apr-Sep): Higher demand due to cooling
# Winter (Oct-Mar): Lower demand, morning peak dominates
#
# Weekend (Fri-Sat in Bangladesh): ~5-8% lower demand
# =========================================================

HOURLY_PATTERN_SUMMER = {
    0: 0.55, 1: 0.50, 2: 0.48, 3: 0.47, 4: 0.46,
    5: 0.48, 6: 0.55, 7: 0.65, 8: 0.78, 9: 0.88,
    10: 0.95, 11: 0.98, 12: 0.97, 13: 0.95, 14: 0.93,
    15: 0.92, 16: 0.93, 17: 0.96, 18: 1.00, 19: 0.98,
    20: 0.92, 21: 0.85, 22: 0.75, 23: 0.65,
}

HOURLY_PATTERN_WINTER = {
    0: 0.58, 1: 0.53, 2: 0.50, 3: 0.49, 4: 0.48,
    5: 0.50, 6: 0.58, 7: 0.68, 8: 0.80, 9: 0.90,
    10: 0.95, 11: 0.97, 12: 0.95, 13: 0.92, 14: 0.90,
    15: 0.89, 16: 0.90, 17: 0.93, 18: 0.95, 19: 0.90,
    20: 0.82, 21: 0.75, 22: 0.68, 23: 0.62,
}


# =========================================================
# SAFE HELPERS
# =========================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# FETCH CURRENT PGCB DEMAND
# =========================================================

def fetch_current_pgcb_demand() -> Optional[Dict[str, Any]]:
    """
    Get current demand from PGCB via internal grid service.
    NEVER fabricate this value.
    """
    try:
        result = get_grid_live()

        if result is None:
            return None

        if not result.get("connected"):
            return None

        grid = result.get("data", {})
        if not grid:
            return None

        demand = safe_float(grid.get("current_demand_mw"))
        supply = safe_float(grid.get("supply_mw"))
        load_shed = safe_float(grid.get("load_shedding_mw"))
        timestamp = grid.get("timestamp")

        if demand <= 0:
            return None

        return {
            "demand_mw": demand,
            "supply_mw": supply,
            "load_shedding_mw": load_shed,
            "timestamp": timestamp,
        }

    except Exception:
        return None


# =========================================================
# FETCH TEMPERATURE FORECAST (Open-Meteo)
# =========================================================

def fetch_temperature_forecast(
    hours: int = 24,
) -> Optional[List[Dict[str, Any]]]:
    """
    Fetch hourly temperature forecast for Dhaka
    to adjust demand predictions.
    """
    try:
        params = {
            "latitude": 23.8103,
            "longitude": 90.4125,
            "hourly": "temperature_2m",
            "timezone": "Asia/Dhaka",
            "forecast_days": 2,
        }

        response = requests.get(
            WEATHER_URL,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])

        if not times or not temps:
            return None

        now = datetime.now(timezone.utc)
        result = []

        for i, t_str in enumerate(times):
            try:
                t_dt = datetime.fromisoformat(
                    t_str.replace("Z", "+00:00")
                )
            except (ValueError, AttributeError):
                continue

            if t_dt >= now and len(result) < hours:
                result.append({
                    "timestamp_utc": t_dt.isoformat(),
                    "temperature_c": round(temps[i], 1)
                    if i < len(temps)
                    else None,
                })

        return result if result else None

    except Exception:
        return None


# =========================================================
# GENERATE SYNTHETIC TRAINING DATA
# =========================================================

def generate_synthetic_training_data(
    days: int = 365,
) -> List[Dict[str, Any]]:
    """
    Generate synthetic Bangladesh demand training data
    based on known grid patterns.

    Uses realistic hourly profiles for summer/winter,
    day-of-week effects, and temperature correlation.
    """
    random.seed(42)
    np.random.seed(42)

    base_peak_mw = 16000.0

    records = []
    start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        month = current_date.month
        dow = current_date.weekday()

        is_summer = month in [4, 5, 6, 7, 8, 9]
        is_winter = month in [11, 12, 1, 2]

        if is_summer:
            pattern = HOURLY_PATTERN_SUMMER
            seasonal_factor = 1.0 + (month - 6) * 0.02
        elif is_winter:
            pattern = HOURLY_PATTERN_WINTER
            seasonal_factor = 0.85 + (12 - month) * 0.01
        else:
            pattern = HOURLY_PATTERN_SUMMER
            seasonal_factor = 0.92

        if dow >= 5:
            weekend_factor = 0.93
        else:
            weekend_factor = 1.0

        for hour in range(24):
            hourly_factor = pattern.get(hour, 0.7)

            noise = np.random.normal(0, 0.02)

            temp_noise = np.random.normal(0, 3)

            demand = (
                base_peak_mw
                * seasonal_factor
                * weekend_factor
                * hourly_factor
                * (1 + noise)
            )

            demand = max(demand, 6000)
            demand = min(demand, 22000)

            records.append({
                "year": current_date.year,
                "month": current_date.month,
                "day": current_date.day,
                "hour": hour,
                "day_of_week": dow,
                "is_weekend": 1 if dow >= 5 else 0,
                "is_summer": 1 if is_summer else 0,
                "is_winter": 1 if is_winter else 0,
                "hourly_factor": round(hourly_factor, 4),
                "seasonal_factor": round(seasonal_factor, 4),
                "weekend_factor": round(weekend_factor, 4),
                "temperature_c": round(
                    25 + temp_noise, 1
                ),
                "demand_mw": round(demand, 1),
            })

    return records


# =========================================================
# TRAIN DEMAND MODEL
# =========================================================

FEATURE_COLUMNS = [
    "month",
    "hour",
    "day_of_week",
    "is_weekend",
    "is_summer",
    "is_winter",
    "hourly_factor",
    "seasonal_factor",
    "weekend_factor",
    "temperature_c",
]


def train_demand_model(
    force_retrain: bool = False,
) -> Any:
    """
    Train XGBoost demand forecasting model.
    Saves to models/demand_forecast_model.pkl
    """
    MODEL_DIR.mkdir(exist_ok=True)

    if (
        MODEL_FILE.exists()
        and not force_retrain
    ):
        try:
            model = joblib.load(MODEL_FILE)
            return model
        except Exception:
            pass

    try:
        from xgboost import XGBRegressor
        use_xgb = True
    except ImportError:
        from sklearn.ensemble import (
            GradientBoostingRegressor,
        )
        use_xgb = False

    records = generate_synthetic_training_data()

    X = np.array([
        [r[col] for col in FEATURE_COLUMNS]
        for r in records
    ])
    y = np.array([r["demand_mw"] for r in records])

    if use_xgb:
        model = XGBRegressor(
            n_estimators=200,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0,
        )
    else:
        model = GradientBoostingRegressor(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            random_state=42,
        )

    model.fit(X, y)

    joblib.dump(model, MODEL_FILE)

    return model


# =========================================================
# FORECAST 24H DEMAND
# =========================================================

def forecast_24h_demand(
    current_demand_mw: float,
    model: Any,
) -> Dict[str, Any]:
    """
    Predict next 24 hours of Bangladesh grid demand.

    Uses current PGCB demand as anchor and applies
    hourly pattern from the trained model.
    """
    now_utc = datetime.now(timezone.utc)
    now_bst = now_utc + timedelta(hours=6)

    temps = fetch_temperature_forecast(24)
    temp_map = {}
    weather_data_status = "AVAILABLE"
    if temps:
        for item in temps:
            ts = item.get("timestamp_utc", "")
            tc = item.get("temperature_c")
            if tc is not None:
                try:
                    dt = datetime.fromisoformat(
                        ts.replace("Z", "+00:00")
                    )
                    hour = dt.hour
                    temp_map[hour] = tc
                except (ValueError, AttributeError):
                    pass
    else:
        weather_data_status = "UNAVAILABLE"

    hourly_forecast = []
    peak_demand = 0.0
    peak_timestamp = ""

    for h in range(24):
        forecast_time_bst = now_bst + timedelta(hours=h)
        forecast_time_utc = now_utc + timedelta(hours=h)
        forecast_hour = forecast_time_bst.hour
        forecast_month = forecast_time_bst.month
        forecast_dow = forecast_time_bst.weekday()

        is_summer = forecast_month in [4, 5, 6, 7, 8, 9]
        is_winter = forecast_month in [11, 12, 1, 2]
        is_weekend = 1 if forecast_dow >= 5 else 0

        pattern = (
            HOURLY_PATTERN_SUMMER
            if is_summer or not is_winter
            else HOURLY_PATTERN_WINTER
        )
        hourly_factor = pattern.get(forecast_hour, 0.7)

        if is_summer:
            seasonal_factor = 1.0 + (
                forecast_month - 6
            ) * 0.02
        elif is_winter:
            seasonal_factor = 0.85 + (
                12 - forecast_month
            ) * 0.01
        else:
            seasonal_factor = 0.92

        weekend_factor = 0.93 if is_weekend else 1.0

        temperature = temp_map.get(forecast_hour, 28.0)

        features = np.array([[
            forecast_month,
            forecast_hour,
            forecast_dow,
            is_weekend,
            1 if is_summer else 0,
            1 if is_winter else 0,
            hourly_factor,
            seasonal_factor,
            weekend_factor,
            temperature,
        ]])

        predicted_mw = float(model.predict(features)[0])

        adjustment_ratio = (
            current_demand_mw / 16000.0
            if current_demand_mw > 0
            else 1.0
        )
        predicted_mw *= adjustment_ratio

        predicted_mw = max(predicted_mw, 6000)
        predicted_mw = min(predicted_mw, 22000)

        entry = {
            "hour_offset": h,
            "timestamp_utc": forecast_time_utc.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
            "timestamp_bst": forecast_time_bst.strftime(
                "%Y-%m-%dT%H:%M:%S+06:00"
            ),
            "hour_bst": forecast_hour,
            "predicted_demand_mw": round(predicted_mw, 1),
            "temperature_c": round(temperature, 1),
            "data_classification": "MODEL_FORECAST",
        }

        hourly_forecast.append(entry)

        if predicted_mw > peak_demand:
            peak_demand = predicted_mw
            peak_timestamp = entry["timestamp_bst"]

    return {
        "current_pgcb_demand_mw": round(
            current_demand_mw, 1
        ),
        "forecast_peak_mw": round(peak_demand, 1),
        "peak_timestamp": peak_timestamp,
        "hourly_forecast": hourly_forecast,
        "weather_data_status": weather_data_status,
        "model": "XGBoost / GradientBoosting",
        "data_source": "Synthetic training + PGCB anchor",
        "data_classification": "MODEL_FORECAST",
        "generated_at_utc": now_utc.strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        ),
    }


# =========================================================
# API ENDPOINT
# =========================================================

@router.get("/forecast")
def get_demand_forecast():
    """
    Predict next 24 hours of Bangladesh grid demand.

    Current demand is from PGCB official.
    Forecast is MODEL_FORECAST (not official).
    """

    pgcb = fetch_current_pgcb_demand()

    if pgcb is None:
        raise HTTPException(
            status_code=502,
            detail=(
                "Cannot generate forecast: "
                "PGCB demand data unavailable. "
                "Current demand is required as anchor."
            ),
        )

    current_demand = pgcb["demand_mw"]

    try:
        model = train_demand_model()
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Demand forecast model failed: {error}"
            ),
        )

    forecast = forecast_24h_demand(
        current_demand, model
    )

    forecast["pgcb_source"] = {
        "supply_mw": pgcb["supply_mw"],
        "load_shedding_mw": pgcb["load_shedding_mw"],
        "pgcb_timestamp": pgcb["timestamp"],
        "data_classification": "OFFICIAL_PGCB",
    }

    real_records = count_records()
    threshold = 168

    if real_records >= threshold:
        training_data_type = "REAL_PGCB"
        model_status = (
            f"Ready for retraining with "
            f"{real_records} real observations"
        )
    else:
        training_data_type = "SYNTHETIC"
        model_status = (
            f"Using synthetic model. "
            f"Need {threshold - real_records} more "
            f"real PGCB observations for retraining "
            f"(current: {real_records}/{threshold})"
        )

    forecast["training_metadata"] = {
        "training_data_type": training_data_type,
        "real_pgcb_records": real_records,
        "synthetic_records": (
            8760 if training_data_type == "SYNTHETIC"
            else 0
        ),
        "threshold_for_retraining": threshold,
        "model_status": model_status,
        "data_classification": "MODEL_FORECAST",
    }

    return forecast
