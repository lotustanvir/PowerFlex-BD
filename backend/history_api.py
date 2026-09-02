import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from database.connection import get_session
from database.models import (
    GridSnapshot,
    AIPrediction,
    LoadshieldDispatch,
    ModelRegistry,
)

logger = logging.getLogger("powerflex.history_api")


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    tags=["Historical Data"],
)


# =========================================================
# GET /api/grid/history
# =========================================================

@router.get("/api/grid/history")
def get_grid_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Retrieve historical grid snapshots from PostgreSQL."""

    try:
        session = get_session()
        try:
            query = session.query(GridSnapshot)

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.filter(
                        GridSnapshot.timestamp >= start_dt
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid start_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS",
                    )

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.filter(
                        GridSnapshot.timestamp <= end_dt
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid end_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS",
                    )

            total = query.count()
            records = (
                query.order_by(GridSnapshot.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            data = []
            for r in records:
                data.append({
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "collected_at": r.collected_at.isoformat() if r.collected_at else None,
                    "demand_mw": float(r.demand_mw) if r.demand_mw else None,
                    "supply_mw": float(r.supply_mw) if r.supply_mw else None,
                    "load_shedding_mw": float(r.load_shedding_mw) if r.load_shedding_mw else None,
                    "deficit_mw": round(
                        float(r.demand_mw - r.supply_mw), 2
                    ) if r.demand_mw and r.supply_mw else None,
                    "gas_mw": float(r.gas_mw) if r.gas_mw else None,
                    "liquid_fuel_mw": float(r.liquid_fuel_mw) if r.liquid_fuel_mw else None,
                    "coal_mw": float(r.coal_mw) if r.coal_mw else None,
                    "hydro_mw": float(r.hydro_mw) if r.hydro_mw else None,
                    "solar_mw": float(r.solar_mw) if r.solar_mw else None,
                    "wind_mw": float(r.wind_mw) if r.wind_mw else None,
                    "hvdc_mw": float(r.hvdc_mw) if r.hvdc_mw else None,
                    "import_mw": float(r.import_mw) if r.import_mw else None,
                    "grid_status": r.grid_status,
                    "risk_level": r.risk_level,
                    "source": r.source,
                    "data_classification": r.data_classification,
                })

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": data,
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch grid history: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve grid history",
        )


# =========================================================
# GET /api/predictions/history
# =========================================================

@router.get("/api/predictions/history")
def get_predictions_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    model_type: Optional[str] = Query(None),
    zone: Optional[str] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Retrieve historical AI predictions from PostgreSQL."""

    try:
        session = get_session()
        try:
            query = session.query(AIPrediction)

            if model_type:
                query = query.filter(
                    AIPrediction.model_type == model_type
                )

            if zone:
                query = query.filter(
                    AIPrediction.zone == zone
                )

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.filter(
                        AIPrediction.timestamp >= start_dt
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid start_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS",
                    )

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.filter(
                        AIPrediction.timestamp <= end_dt
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid end_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS",
                    )

            total = query.count()
            records = (
                query.order_by(AIPrediction.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            data = []
            for r in records:
                data.append({
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "model_type": r.model_type,
                    "zone": r.zone,
                    "predicted_mw": float(r.predicted_mw) if r.predicted_mw else None,
                    "actual_mw": float(r.actual_mw) if r.actual_mw else None,
                    "model_version": r.model_version,
                })

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": data,
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch predictions history: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve predictions history",
        )


# =========================================================
# GET /api/loadshield/history
# =========================================================

@router.get("/api/loadshield/history")
def get_loadshield_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Retrieve historical LoadShield dispatches from PostgreSQL."""

    try:
        session = get_session()
        try:
            query = session.query(LoadshieldDispatch)

            if start_date:
                try:
                    start_dt = datetime.fromisoformat(start_date)
                    query = query.filter(
                        LoadshieldDispatch.timestamp >= start_dt
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid start_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS",
                    )

            if end_date:
                try:
                    end_dt = datetime.fromisoformat(end_date)
                    query = query.filter(
                        LoadshieldDispatch.timestamp <= end_dt
                    )
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid end_date format. Use ISO format: YYYY-MM-DDTHH:MM:SS",
                    )

            total = query.count()
            records = (
                query.order_by(LoadshieldDispatch.timestamp.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            data = []
            for r in records:
                data.append({
                    "id": r.id,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                    "demand_mw": float(r.demand_mw) if r.demand_mw else None,
                    "supply_mw": float(r.supply_mw) if r.supply_mw else None,
                    "deficit_mw": float(r.deficit_mw) if r.deficit_mw else None,
                    "solar_mw": float(r.solar_mw) if r.solar_mw else None,
                    "wind_mw": float(r.wind_mw) if r.wind_mw else None,
                    "hydro_mw": float(r.hydro_mw) if r.hydro_mw else None,
                    "biomass_mw": float(r.biomass_mw) if r.biomass_mw else None,
                    "waste_mw": float(r.waste_mw) if r.waste_mw else None,
                    "battery_mw": float(r.battery_mw) if r.battery_mw else None,
                    "flexible_mw": float(r.flexible_mw) if r.flexible_mw else None,
                    "remaining_gap": float(r.remaining_gap) if r.remaining_gap else None,
                    "status": r.status,
                    "risk_level": r.risk_level,
                    "zone_breakdown": r.zone_breakdown,
                })

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": data,
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch loadshield history: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve loadshield history",
        )


# =========================================================
# GET /api/models/history
# =========================================================

@router.get("/api/models/history")
def get_model_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    model_type: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
):
    """Retrieve registered ML models from PostgreSQL."""

    try:
        session = get_session()
        try:
            query = session.query(ModelRegistry)

            if model_type:
                query = query.filter(
                    ModelRegistry.model_type == model_type
                )

            if is_active is not None:
                query = query.filter(
                    ModelRegistry.is_active == is_active
                )

            total = query.count()
            records = (
                query.order_by(ModelRegistry.trained_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            data = []
            for r in records:
                data.append({
                    "id": r.id,
                    "model_type": r.model_type,
                    "model_path": r.model_path,
                    "trained_at": r.trained_at.isoformat() if r.trained_at else None,
                    "training_samples": r.training_samples,
                    "mae": float(r.mae) if r.mae else None,
                    "rmse": float(r.rmse) if r.rmse else None,
                    "r2": float(r.r2) if r.r2 else None,
                    "features": r.features,
                    "is_active": r.is_active,
                })

            return {
                "total": total,
                "limit": limit,
                "offset": offset,
                "data": data,
            }
        finally:
            session.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch model registry: %s", e)
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve model registry",
        )
