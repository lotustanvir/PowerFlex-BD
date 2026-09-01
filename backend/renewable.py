import logging

from fastapi import APIRouter, HTTPException

from backend.services.solar_service import get_solar_live
from backend.services.wind_service import get_wind_live

logger = logging.getLogger(__name__)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/api/renewable",
    tags=["Renewable Energy"]
)


# =========================================================
# COMBINED SOLAR + WIND
# =========================================================

@router.get("/live")
def live_renewable_forecast():

    # =====================================================
    # SOLAR
    # =====================================================

    try:
        solar_data = get_solar_live()
        if solar_data is None:
            solar_data = {}
    except Exception as error:
        logger.error("[renewable] Solar fetch failed: %s", error)
        raise HTTPException(
            status_code=502,
            detail=f"Solar service failed: {error}"
        )

    # =====================================================
    # WIND
    # =====================================================

    try:
        wind_data = get_wind_live()
        if wind_data is None:
            wind_data = {}
    except Exception as error:
        logger.error("[renewable] Wind fetch failed: %s", error)
        raise HTTPException(
            status_code=502,
            detail=f"Wind service failed: {error}"
        )


    # =====================================================
    # BEST FORECAST ZONES
    # =====================================================

    solar_best_zone = solar_data.get(
        "best_forecast_zone"
    )

    wind_best_zone = wind_data.get(
        "best_forecast_zone"
    )


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "project":
            "PowerFlex BD",

        "resource_layer":
            "Solar + Wind",

        "forecast_hours":
            24,

        "comparison_note":
            (
                "Solar and Wind are reported separately. "
                "Their MW/MW outputs should not be treated "
                "as a direct official resource ranking."
            ),

        # =================================================
        # SOLAR SUMMARY
        # =================================================

        "solar_summary": {

            "best_forecast_zone":
                (
                    solar_best_zone
                    if solar_best_zone
                    else None
                ),

            "best_opportunity":
                solar_data.get(
                    "best_opportunity"
                )
        },

        # =================================================
        # WIND SUMMARY
        # =================================================

        "wind_summary": {

            "best_forecast_zone":
                (
                    wind_best_zone
                    if wind_best_zone
                    else None
                ),

            "best_opportunity":
                wind_data.get(
                    "best_opportunity"
                )
        },

        # =================================================
        # FULL RESOURCE DATA
        # =================================================

        "solar":
            solar_data,

        "wind":
            wind_data
    }