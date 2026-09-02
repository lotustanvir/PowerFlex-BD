import logging
import os

import joblib

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.observability.logging import setup_structured_logging
from backend.security import validate_api_key

setup_structured_logging(level=os.getenv("LOG_LEVEL", "INFO"))
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
from backend.history_api import router as history_api_router

# v3 routers
from backend.routes_weather import router as weather_router
from backend.routes_location import router as location_router
from backend.routes_recommendation import router as recommendation_router
from backend.routes_sources import router as sources_router
from backend.routes_historical import router as historical_router

MAX_REQUEST_BODY_BYTES = 1 * 1024 * 1024  # 1 MB

APP_ENV = os.getenv("APP_ENV", "development")

TRUSTED_HOSTS = [
    h.strip()
    for h in os.getenv("TRUSTED_HOSTS", "localhost,127.0.0.1").split(",")
    if h.strip()
]

# Routes that are always public (no auth required)
PUBLIC_ROUTES = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}

# Route prefixes that are always public
PUBLIC_PREFIXES = [
    "/docs",
    "/redoc",
]

# Route prefixes that require auth in production
PROTECTED_PREFIXES = [
    "/api/v3/recommendation",
    "/api/v3/location",
    "/api/v3/historical",
    "/api/sources",
    "/api/security",
]



def is_route_public(path: str) -> bool:
    """Check if a route is public (no auth required)."""
    if path in PUBLIC_ROUTES:
        return True
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


def is_route_protected(path: str) -> bool:
    """Check if a route requires authentication in production."""
    for prefix in PROTECTED_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


app = FastAPI(
    title="PowerFlex BD API",
    description=(
        "PowerFlex BD v3.0 — Bangladesh Electricity Intelligence + "
        "Forecasting + Renewable Resource + Location Optimization + "
        "AI Planning Platform. Provides grid data, weather-driven "
        "forecasts, resource estimates, location intelligence, and "
        "scenario-based optimization. This platform does NOT operate, "
        "control, or issue dispatch commands to the Bangladesh national grid."
    ),
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
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

from backend.middleware.rate_limiter import RateLimitMiddleware

app.add_middleware(
    RateLimitMiddleware,
    requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    response.headers["Permissions-Policy"] = (
        "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
        "magnetometer=(), microphone=(), payment=(), usb=()"
    )
    return response


@app.middleware("http")
async def trusted_host_and_body_limit(request: Request, call_next):
    host_header = request.headers.get("host", "")
    if TRUSTED_HOSTS and host_header.split(":")[0] not in TRUSTED_HOSTS:
        return JSONResponse(
            status_code=400,
            content={"detail": "Invalid host header"},
        )

    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_REQUEST_BODY_BYTES:
        return JSONResponse(
            status_code=413,
            content={"detail": "Request body too large (max 1 MB)"},
        )

    response = await call_next(request)
    return response


@app.middleware("http")
async def api_key_authentication(request: Request, call_next):
    """API key authentication for production environment.
    
    In development: all routes are open.
    In production: protected routes require valid X-API-Key header.
    Health checks and docs are always public.
    """
    path = request.url.path
    
    # Always allow public routes
    if is_route_public(path):
        return await call_next(request)
    
    # In development mode, allow all routes without auth
    if APP_ENV != "production":
        return await call_next(request)
    
    # In production, check if route is protected
    if not is_route_protected(path):
        return await call_next(request)
    
    # Check for API key
    api_key = request.headers.get("X-API-Key", "")
    if not api_key:
        logger.warning("Missing API key for protected route: %s from %s", 
                      path, request.client.host if request.client else "unknown")
        return JSONResponse(
            status_code=401,
            content={"detail": "API key required. Send X-API-Key header."},
        )
    
    # Validate API key (constant-time comparison via security.validate_api_key)
    key_name = validate_api_key(api_key)
    if not key_name:
        logger.warning("Invalid API key for route: %s from %s", 
                      path, request.client.host if request.client else "unknown")
        return JSONResponse(
            status_code=403,
            content={"detail": "Invalid API key"},
        )
    
    # Store key name for request context
    request.state.key_name = key_name
    
    return await call_next(request)


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

app.include_router(
    history_api_router
)

# v3 routers
app.include_router(
    weather_router
)

app.include_router(
    location_router
)

app.include_router(
    recommendation_router
)

app.include_router(
    sources_router
)

app.include_router(
    historical_router
)


MODEL_FILE = Path(
    "models/weather_only_solar_model.pkl"
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


@app.get("/api/models")
def list_models():
    """Return the model registry with all registered models."""
    from backend.model_registry import get_model_registry
    registry = get_model_registry()
    return {
        "models": registry.to_dict(),
        "total": len(registry.list_all()),
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
    from database.connection import check_connection

    grid_status = get_grid_status()
    solar_status = get_solar_status()
    wind_status = get_wind_status()
    db_connected = check_connection()

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

    if not db_connected:
        overall = "degraded"
        degraded_count += 1

    if degraded_count >= 2:
        overall = "unhealthy"
    elif degraded_count >= 1 or solar_model is None:
        overall = "degraded"

    return {
        "status": overall,
        "solar_model_loaded": solar_model is not None,
        "database_connected": db_connected,
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


@app.get("/api/security/stats")
def security_stats():
    """Return security middleware statistics."""
    from backend.security import get_api_keys
    keys = get_api_keys()
    return {
        "api_keys_configured": len(keys),
        "rate_limit_rpm": int(os.getenv("RATE_LIMIT_RPM", "60")),
        "trusted_hosts": TRUSTED_HOSTS,
        "max_body_size_bytes": MAX_REQUEST_BODY_BYTES,
    }


@app.get("/api/data-collection/status")
def data_collection_status():
    """Return data collection service status with quality metrics."""
    from backend.data_collector import get_collection_status
    return get_collection_status()


@app.post("/api/data-collection/trigger")
def trigger_data_collection():
    """Manually trigger a data collection cycle."""
    from backend.data_collector import trigger_collection
    return trigger_collection()


@app.on_event("startup")
async def startup():
    logger.info("PowerFlex BD backend starting")
    
    # Start background data collection if enabled
    if os.getenv("ENABLE_DATA_COLLECTION", "false").lower() == "true":
        from backend.data_collector import start_data_collection
        status = start_data_collection()
        logger.info("Data collection service started: %s", status)
    else:
        logger.info(
            "Data collection service disabled. "
            "Set ENABLE_DATA_COLLECTION=true to enable."
        )