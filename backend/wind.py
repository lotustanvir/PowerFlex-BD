import sys
import logging
import concurrent.futures
from datetime import datetime, timezone, timedelta
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException

from database.connection import get_session
from database.models import AIPrediction

logger = logging.getLogger(__name__)

# Bangladesh Standard Time (UTC+6)
BANGLADESH_TZ = timezone(timedelta(hours=6))


# =========================================================
# PROJECT PATH
# =========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# =========================================================
# SHARED WIND POWER CURVE
# =========================================================

from AI.wind_power_curve import wind_power_curve


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/wind",
    tags=["Wind"]
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
# LIVE WIND FORECAST
# =========================================================

@router.get("/live")
def live_wind_forecast():

    all_rows = []

    # -----------------------------------------------------
    # Fetch 24-hour forecast (PARALLEL)
    # -----------------------------------------------------

    def _fetch_zone(zone, latitude, longitude):
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": ",".join([
                "wind_speed_10m",
                "wind_speed_80m",
                "wind_speed_100m",
                "wind_speed_120m",
                "wind_direction_10m",
                "wind_direction_100m",
                "wind_direction_120m",
                "wind_gusts_10m",
                "temperature_2m",
                "pressure_msl"
            ]),
            "forecast_hours": 24,
            "timezone": "Asia/Dhaka",
            "wind_speed_unit": "kmh"
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
                        "wind_speed_10m_kmh":
                            hourly["wind_speed_10m"][i],
                        "wind_speed_80m_kmh":
                            hourly["wind_speed_80m"][i],
                        "wind_speed_100m_kmh":
                            hourly["wind_speed_100m"][i],
                        "wind_speed_120m_kmh":
                            hourly["wind_speed_120m"][i],
                        "wind_direction_10m_degree":
                            hourly["wind_direction_10m"][i],
                        "wind_direction_100m_degree":
                            hourly["wind_direction_100m"][i],
                        "wind_direction_120m_degree":
                            hourly["wind_direction_120m"][i],
                        "wind_gust_10m_kmh":
                            hourly["wind_gusts_10m"][i],
                        "temperature_c":
                            hourly["temperature_2m"][i],
                        "pressure_msl_hpa":
                            hourly["pressure_msl"][i]
                    })
                return rows
            except Exception as error:
                last_error = error
                if attempt < 1:
                    _time.sleep(1.0 * (attempt + 1))
                    continue
                raise
        raise last_error or RuntimeError(
            f"All retries exhausted for wind zone {zone}"
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
            "resource": "wind",
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


    # -----------------------------------------------------
    # WIND GENERATION
    # -----------------------------------------------------

    # Historical wind dataset is based on 100m.
    # Live forecast therefore uses the same 100m basis.

    for row in all_rows:

        row["wind_generation_mw_per_1mw"] = (
            wind_power_curve(
                row["wind_speed_100m_kmh"]
            )
        )


    # -----------------------------------------------------
    # DAILY ENERGY BY ZONE
    # -----------------------------------------------------

    daily = {}

    for row in all_rows:

        zone = row["zone"]

        if zone not in daily:
            daily[zone] = 0.0

        # MW × 1 hour = MWh

        daily[zone] += (
            row["wind_generation_mw_per_1mw"]
        )


    # -----------------------------------------------------
    # ZONE RANKING
    # -----------------------------------------------------

    ranking = []

    for zone, energy in daily.items():

        ranking.append({

            "zone": zone,

            "expected_energy_mwh_per_1mw_24h":
                round(energy, 4),

            "modeled_capacity_factor_pct":
                round(
                    (energy / 24.0) * 100,
                    2
                )
        })


    ranking.sort(
        key=lambda item:
        item["expected_energy_mwh_per_1mw_24h"],
        reverse=True
    )


    for rank, item in enumerate(
        ranking,
        start=1
    ):

        item["rank"] = rank


    # -----------------------------------------------------
    # CURRENT HOUR GENERATION
    # -----------------------------------------------------

    current_hour_bst = datetime.now(BANGLADESH_TZ).hour
    current_hour_rows = [
        row for row in all_rows
        if datetime.fromisoformat(row["timestamp"]).hour == current_hour_bst
    ]

    if current_hour_rows:
        current_generation_per_1mw = float(
            current_hour_rows[0]["wind_generation_mw_per_1mw"]
        )
        current_hour_timestamp = current_hour_rows[0]["timestamp"]
    else:
        current_generation_per_1mw = 0.0
        current_hour_timestamp = None

    # -----------------------------------------------------
    # BEST HOURLY OPPORTUNITY
    # -----------------------------------------------------

    best_row = max(
        all_rows,
        key=lambda row:
        row["wind_generation_mw_per_1mw"]
    )


    # -----------------------------------------------------
    # BEST FORECAST ZONE
    # -----------------------------------------------------

    best_zone = ranking[0]


    # -----------------------------------------------------
    # LOG PREDICTIONS TO DATABASE
    # -----------------------------------------------------

    for item in ranking:
        log_ai_prediction(
            model_type="wind",
            zone=item["zone"],
            predicted_mw=item[
                "expected_energy_mwh_per_1mw_24h"
            ],
            features={
                "forecast_hours": 24,
                "wind_height_m": 100,
                "model": "wind_power_curve",
            },
            model_version="wind_power_curve_v1",
        )


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "project":
            "PowerFlex BD v2.0",

        "resource":
            "Wind",

        "module":
            "Wind Power Curve Model",

        "forecast_basis":
            "100m wind speed",

        "data_source":
            "Open-Meteo forecast + PowerFlex Wind Power Curve",

        "data_classification":
            "CALCULATED",

        "classification_details": {
            "weather_data": "LIVE_FEED (Open-Meteo API)",
            "wind_generation": "CALCULATED (power curve lookup, not AI)",
            "is_measured_generation": False,
            "note": (
                "These are engineering model estimates based on wind speed "
                "and a simplified prototype turbine power curve. This is "
                "NOT measured wind farm generation data."
            ),
        },

        "methodology": {
            "model": "Simplified prototype 1MW turbine power curve",
            "wind_height_m": 100,
            "cut_in_speed_kmh": 3.0,
            "rated_speed_kmh": 12.0,
            "cut_out_speed_kmh": 25.0,
            "air_density_assumption": "Standard sea-level (1.225 kg/m³)",
            "validation_status": "EXPERIMENTAL — not validated against real Bangladesh wind turbine data",
        },

        "forecast_hours":
            24,

        "current_hour_generation": {
            "mw_per_1mw_installed": round(
                current_generation_per_1mw, 4
            ),
            "timestamp": current_hour_timestamp,
            "data_classification": "CALCULATED",
            "note": (
                "Hourly wind generation estimate for current hour "
                "based on power curve model. Varies with wind speed."
            ),
        },

        "turbine_assumption": {

            "rated_power_mw":
                1.0,

            "cut_in_speed_kmh":
                3.0,

            "rated_speed_kmh":
                12.0,

            "cut_out_speed_kmh":
                25.0,

            "wind_height_used_m":
                100,

            "model_type":
                "Simplified prototype turbine power curve"
        },

        "best_opportunity": {

            "zone":
                best_row["zone"],

            "timestamp":
                best_row["timestamp"],

            "wind_speed_100m_kmh":
                round(
                    float(
                        best_row[
                            "wind_speed_100m_kmh"
                        ]
                    ),
                    2
                ),

            "predicted_generation_mw_per_1mw":
                round(
                    float(
                        best_row[
                            "wind_generation_mw_per_1mw"
                        ]
                    ),
                    4
                )
        },

        "best_forecast_zone": {

            "zone":
                best_zone["zone"],

            "expected_energy_mwh_per_1mw_24h":
                best_zone[
                    "expected_energy_mwh_per_1mw_24h"
                ],

            "modeled_capacity_factor_pct":
                best_zone[
                    "modeled_capacity_factor_pct"
                ]
        },

        "zone_ranking":
            ranking
    }