import json
import logging
import concurrent.futures
import requests
import pandas as pd
import joblib

from datetime import datetime, timezone, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException

from database.connection import get_session
from database.models import AIPrediction

logger = logging.getLogger(__name__)

# Bangladesh Standard Time (UTC+6)
BANGLADESH_TZ = timezone(timedelta(hours=6))


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/solar",
    tags=["Solar"]
)


# =========================================================
# LOG AI PREDICTION TO POSTGRESQL
# =========================================================

def log_ai_prediction(
    model_type: str,
    zone: str,
    predicted_mw: float,
    features: dict = None,
    model_version: str = None,
) -> bool:

    try:
        session = get_session()
        try:
            now = datetime.now(timezone.utc)
            existing = (
                session.query(AIPrediction)
                .filter(
                    AIPrediction.model_type == model_type,
                    AIPrediction.zone == zone,
                    AIPrediction.timestamp >= now.replace(
                        hour=0, minute=0, second=0,
                        microsecond=0
                    ),
                )
                .first()
            )
            if existing:
                return False

            prediction = AIPrediction(
                timestamp=now,
                model_type=model_type,
                zone=zone,
                predicted_mw=round(predicted_mw, 4),
                features_json=features,
                model_version=model_version,
            )
            session.add(prediction)
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            logger.warning(
                "Failed to log AI prediction: %s", e
            )
            return False

        finally:
            session.close()

    except Exception as e:
        logger.warning(
            "Database unavailable for AI prediction: %s", e
        )
        return False


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


MODEL_FILE = (
    PROJECT_ROOT /
    "models/weather_only_solar_model.pkl"
)


# =========================================================
# SOLAR MODEL
# =========================================================

try:

    solar_model = joblib.load(
        MODEL_FILE
    )

    logger.info(
        "Solar module OK"
    )

except Exception as error:

    solar_model = None

    logger.warning(
        "Could not load solar model: %s",
        error
    )


# =========================================================
# BANGLADESH LOCATIONS
# =========================================================

LOCATIONS = {

    "Dhaka": (23.8103, 90.4125),

    "Chittagong": (22.3569, 91.7832),

    "Khulna": (22.8456, 89.5403),

    "Rajshahi": (24.3745, 88.6042),

    "Comilla": (23.4607, 91.1809),

    "Mymensingh": (24.7471, 90.4203),

    "Sylhet": (24.8949, 91.8687),

    "Barishal": (22.7010, 90.3535),

    "Rangpur": (25.7439, 89.2752),
}


# =========================================================
# LIVE SOLAR FORECAST
# =========================================================

@router.get("/live")
def live_solar_forecast():

    if solar_model is None:

        raise HTTPException(
            status_code=500,
            detail="Solar AI model could not be loaded."
        )


    all_rows = []


    # =====================================================
    # FETCH OPEN-METEO FORECAST (PARALLEL)
    # =====================================================

    def _fetch_zone(zone, latitude, longitude):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join([
                "temperature_2m",
                "relative_humidity_2m",
                "precipitation",
                "cloud_cover",
                "wind_speed_10m",
                "wind_direction_10m",
                "shortwave_radiation"
            ]),
            "forecast_hours": 24,
            "timezone": "Asia/Dhaka"
        }
        # Retry logic with backoff (max 2 retries to fail fast on rate limits)
        import time as _time
        last_error = None
        for attempt in range(2):
            try:
                response = requests.get(
                    url, params=params, timeout=15
                )
                if response.status_code == 429:
                    _time.sleep(1.0 * (attempt + 1))
                    last_error = requests.HTTPError(
                        f"429 Too Many Requests for {zone}"
                    )
                    continue
                response.raise_for_status()
                data = response.json()
                hourly = data["hourly"]
                rows = []
                for i in range(len(hourly["time"])):
                    rows.append({
                        "zone": zone,
                        "latitude": latitude,
                        "longitude": longitude,
                        "timestamp": hourly["time"][i],
                        "temperature_c":
                            hourly["temperature_2m"][i],
                        "humidity_percent":
                            hourly["relative_humidity_2m"][i],
                        "precipitation_mm":
                            hourly["precipitation"][i],
                        "cloud_cover_percent":
                            hourly["cloud_cover"][i],
                        "wind_speed_kmh":
                            hourly["wind_speed_10m"][i],
                        "wind_direction_degree":
                            hourly["wind_direction_10m"][i],
                        "solar_radiation_wm2":
                            hourly["shortwave_radiation"][i]
                    })
                return rows
            except Exception as error:
                last_error = error
                if attempt < 1:
                    _time.sleep(1.0 * (attempt + 1))
                    continue
                raise
        raise last_error or RuntimeError(
            f"All retries exhausted for solar zone {zone}"
        )

    zone_results = {}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=5
    ) as pool:
        futures = {
            pool.submit(
                _fetch_zone, z, lat, lon
            ): z
            for z, (lat, lon) in LOCATIONS.items()
        }
        for future in concurrent.futures.as_completed(
            futures
        ):
            z = futures[future]
            try:
                zone_results[z] = future.result()
            except Exception as error:
                logger.warning(
                    "Skipping zone %s: %s",
                    z, error
                )

    for zone in LOCATIONS:
        if zone in zone_results:
            all_rows.extend(zone_results[zone])

    if not all_rows:
        # Return structured DATA_UNAVAILABLE instead of 502
        return {
            "status": "DATA_UNAVAILABLE",
            "resource": "solar",
            "reason": "Weather provider unavailable for all zones",
            "data_classification": "DATA_UNAVAILABLE",
            "source": "open_meteo",
            "classification": "DATA_UNAVAILABLE",
            "zone_count": len(LOCATIONS),
            "successful_zones": 0,
            "forecast": [],
            "zone_ranking": [],
            "best_forecast_zone": None,
            "best_opportunity": None,
        }


    # =====================================================
    # DATAFRAME
    # =====================================================

    df = pd.DataFrame(
        all_rows
    )


    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )


    # =====================================================
    # TIME FEATURES
    # =====================================================

    df["hour"] = (
        df["timestamp"].dt.hour
    )

    df["day"] = (
        df["timestamp"].dt.day
    )

    df["month"] = (
        df["timestamp"].dt.month
    )

    df["day_of_week"] = (
        df["timestamp"].dt.dayofweek
    )


    df["is_daytime"] = (

        (
            df["hour"] >= 6
        )

        &

        (
            df["hour"] <= 18
        )

    ).astype(int)


    # =====================================================
    # MODEL FEATURES
    # =====================================================

    features = [

        "zone",

        "latitude",

        "longitude",

        "temperature_c",

        "humidity_percent",

        "precipitation_mm",

        "cloud_cover_percent",

        "wind_speed_kmh",

        "wind_direction_degree",

        "hour",

        "day",

        "month",

        "day_of_week",

        "is_daytime"
    ]


    # =====================================================
    # AI PREDICTION
    # =====================================================

    predictions = solar_model.predict(
        df[features]
    )


    predictions = predictions.clip(
        min=0
    )


    df[
        "predicted_generation_mw_per_1mw"
    ] = predictions


    # =====================================================
    # NIGHT CORRECTION
    # =====================================================

    df.loc[

        df[
            "solar_radiation_wm2"
        ] <= 0,

        "predicted_generation_mw_per_1mw"

    ] = 0


    # =====================================================
    # DAILY ZONE RANKING
    # =====================================================

    daily = (

        df.groupby(
            "zone"
        )[

            "predicted_generation_mw_per_1mw"

        ]

        .sum()

        .reset_index()
    )


    daily = daily.sort_values(

        "predicted_generation_mw_per_1mw",

        ascending=False

    ).reset_index(
        drop=True
    )


    daily["rank"] = range(

        1,

        len(daily) + 1
    )


    daily = daily.rename(

        columns={

            "predicted_generation_mw_per_1mw":

            "expected_energy_mwh_per_1mw_24h"
        }
    )


    # =====================================================
    # CURRENT HOUR GENERATION
    # =====================================================

    current_hour_bst = datetime.now(BANGLADESH_TZ).hour
    current_hour_idx = df["timestamp"].dt.hour == current_hour_bst
    if current_hour_idx.any():
        current_hour_data = df[current_hour_idx].iloc[0]
        current_generation_per_1mw = float(
            current_hour_data["predicted_generation_mw_per_1mw"]
        )
        current_hour_timestamp = current_hour_data["timestamp"].isoformat()
    else:
        current_generation_per_1mw = 0.0
        current_hour_timestamp = None

    # =====================================================
    # BEST HOURLY OPPORTUNITY
    # =====================================================

    best_hour = df.loc[

        df[
            "predicted_generation_mw_per_1mw"
        ].idxmax()
    ]


    # =====================================================
    # BEST FORECAST ZONE
    # =====================================================

    best_zone = daily.iloc[0]


    # =====================================================
    # LOG PREDICTIONS TO DATABASE
    # =====================================================

    for _, row in daily.iterrows():
        log_ai_prediction(
            model_type="solar",
            zone=row["zone"],
            predicted_mw=float(
                row["expected_energy_mwh_per_1mw_24h"]
            ),
            features={
                "forecast_hours": 24,
                "model": "weather_only_solar",
            },
            model_version="weather_only_solar_v1",
        )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "project":
            "PowerFlex BD v2.0",

        "resource":
            "Solar",

        "module":
            "Solar AI Forecast",

        "forecast_basis":
            "Weather forecast + Solar AI",

        "data_source":
            "Open-Meteo forecast + PowerFlex Solar AI",

        "data_classification":
            "FORECAST",

        "classification_details": {
            "weather_data": "LIVE_FEED (Open-Meteo API)",
            "solar_prediction": "FORECAST (XGBoost model trained on synthetic targets)",
            "is_measured_generation": False,
            "note": (
                "These are weather-driven solar generation forecasts, "
                "NOT actual plant telemetry. The model was trained on "
                "synthetic targets derived from irradiance formulas, "
                "not real Bangladesh solar farm output."
            ),
        },

        "methodology": {
            "model": "XGBoost regression (weather_only_solar_model.pkl)",
            "features": "GHI, DNI, DHI, temperature, humidity, cloud cover, wind, zenith angle",
            "training_target": "(irradiance / 1000) * 0.85 performance ratio — synthetic, not measured",
            "validation_status": "EXPERIMENTAL — not validated against real Bangladesh solar generation",
        },

        "forecast_hours":
            24,

        "current_hour_generation": {
            "mw_per_1mw_installed": round(
                current_generation_per_1mw, 4
            ),
            "timestamp": current_hour_timestamp,
            "data_classification": "FORECAST",
            "note": (
                "Hourly forecast for current hour. "
                "Nighttime values are zero (no solar generation)."
            ),
        },

        "best_opportunity": {

            "zone":
                best_hour["zone"],

            "timestamp":
                best_hour[
                    "timestamp"
                ].isoformat(),

            "solar_radiation_wm2":
                round(
                    float(
                        best_hour[
                            "solar_radiation_wm2"
                        ]
                    ),
                    2
                ),

            "predicted_generation_mw_per_1mw":
                round(
                    float(
                        best_hour[
                            "predicted_generation_mw_per_1mw"
                        ]
                    ),
                    4
                )
        },

        "best_forecast_zone": {

            "zone":
                best_zone["zone"],

            "expected_energy_mwh_per_1mw_24h":
                round(
                    float(
                        best_zone[
                            "expected_energy_mwh_per_1mw_24h"
                        ]
                    ),
                    4
                )
        },

        "zone_ranking": [

            {

                "rank":
                    int(row["rank"]),

                "zone":
                    row["zone"],

                "expected_energy_mwh_per_1mw_24h":
                    round(
                        float(
                            row[
                                "expected_energy_mwh_per_1mw_24h"
                            ]
                        ),
                        4
                    )
            }

            for _, row in daily.iterrows()
        ]
    }