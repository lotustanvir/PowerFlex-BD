import logging
import os

import joblib

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("powerflex")

from backend.solar import router as solar_router
from backend.wind import router as wind_router
from backend.renewable import router as renewable_router
from backend.grid import router as grid_router
from backend.loadshield import router as loadshield_router
from backend.demand_forecast import router as demand_router
from backend.demand_history import router as history_router
from backend.resource_data import router as resource_router
from backend.biomass_data import router as biomass_router
from backend.waste_data import router as waste_router


app = FastAPI(
    title="PowerFlex BD API",
    description=(
        "Bangladesh-focused AI Energy Intelligence "
        "and Virtual Power Plant Platform"
    ),
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


app.include_router(
    solar_router
)

app.include_router(
    wind_router
)

app.include_router(
    renewable_router
)

app.include_router(
    grid_router
)

app.include_router(
    loadshield_router
)

app.include_router(
    demand_router
)

app.include_router(
    history_router
)

app.include_router(
    resource_router
)

app.include_router(
    biomass_router
)

app.include_router(
    waste_router
)


MODEL_FILE = Path(
    "weather_only_solar_model.pkl"
)


try:

    solar_model = joblib.load(
        MODEL_FILE
    )

    logger.info("Solar model loaded successfully")

except Exception as error:

    solar_model = None

    logger.warning(
        "Could not load solar model: %s",
        error
    )


@app.get("/")
def root():

    return {
        "project":
            "PowerFlex BD",

        "status":
            "online",

        "message":
            "PowerFlex BD backend is running",

        "architecture":
            (
                "PGCB Grid → LoadShield → "
                "Renewable + Flexibility Dispatch"
            )
    }


@app.get("/api/solar/forecast")
def solar_forecast_alias():
    """Alias for /api/solar/live for frontend compatibility."""
    from backend.services.solar_service import get_solar_live
    result = get_solar_live()
    if result is None:
        return {"forecasts": [], "source": None}
    return result


@app.get("/api/wind/forecast")
def wind_forecast_alias():
    """Alias for /api/wind/live for frontend compatibility."""
    from backend.services.wind_service import get_wind_live
    result = get_wind_live()
    if result is None:
        return {"forecasts": [], "source": None}
    return result


@app.get("/api/pgcb/status")
def pgcb_status_alias():
    """Alias for /api/grid/status for frontend compatibility."""
    from backend.services.grid_service import get_grid_status
    status = get_grid_status()
    status["live"] = True
    status["source"] = "PGCB ERP Portal"
    return status


@app.get("/health")
@app.get("/api/health")
def health():
    from backend.services.grid_service import get_grid_status
    from backend.services.solar_service import get_solar_status
    from backend.services.wind_service import get_wind_status

    grid_status = get_grid_status()
    solar_status = get_solar_status()
    wind_status = get_wind_status()

    services = {
        "grid": grid_status,
        "solar": solar_status,
        "wind": wind_status,
    }

    overall = "healthy"
    degraded_count = 0

    for svc_name, svc_data in services.items():
        cache_stats = svc_data.get("cache", {})
        miss_count = cache_stats.get("miss_count", 0)
        hit_count = cache_stats.get("hit_count", 0)
        if miss_count > 5 and hit_count == 0:
            degraded_count += 1

    if degraded_count >= 2:
        overall = "unhealthy"
    elif degraded_count >= 1 or solar_model is None:
        overall = "degraded"

    return {
        "status": overall,
        "solar_model_loaded": solar_model is not None,
        "services": services,
        "modules": {
            "solar": solar_model is not None,
            "wind": True,
            "hydro": True,
            "biomass": True,
            "waste": True,
            "gas": True,
            "liquid_fuel": True,
            "coal": True,
            "nuclear": True,
            "renewable": True,
            "grid": True,
            "loadshield": True,
            "demand_forecast": True,
            "demand_history": True,
            "resource_data": True,
            "biomass_data": True,
            "waste_data": True,
        },
    }


@app.on_event("startup")
async def startup():
    logger.info("PowerFlex BD backend starting")