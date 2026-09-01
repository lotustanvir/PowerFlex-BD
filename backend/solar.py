import logging
import concurrent.futures
import requests
import pandas as pd
import joblib

from pathlib import Path
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/solar",
    tags=["Solar"]
)


# =========================================================
# PROJECT ROOT
# =========================================================

PROJECT_ROOT = Path(
    __file__
).resolve().parents[1]


MODEL_FILE = (
    PROJECT_ROOT /
    "weather_only_solar_model.pkl"
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
        response = requests.get(
            url, params=params, timeout=30
        )
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
        raise HTTPException(
            status_code=502,
            detail="Weather API failed for all zones"
        )


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
    # RESPONSE
    # =====================================================

    return {

        "project":
            "PowerFlex BD",

        "resource":
            "Solar",

        "forecast_basis":
            "Weather forecast + Solar AI",

        "data_source":
            "Open-Meteo forecast + PowerFlex Solar AI",

        "forecast_hours":
            24,

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