import sys
import logging
import concurrent.futures
from pathlib import Path

import requests
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)


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
    # RESPONSE
    # -----------------------------------------------------

    return {

        "project":
            "PowerFlex BD",

        "resource":
            "Wind",

        "forecast_basis":
            "100m wind speed",

        "data_source":
            "Open-Meteo forecast + PowerFlex Wind Power Curve",

        "forecast_hours":
            24,

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