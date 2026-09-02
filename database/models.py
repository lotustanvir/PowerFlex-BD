from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    String,
    Text,
    Boolean,
    DateTime,
    JSON,
    Index,
)
from database.connection import Base


def _utcnow():
    return datetime.now(timezone.utc)


class DemandHistory(Base):
    __tablename__ = "demand_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    pgcb_timestamp = Column(DateTime(timezone=True))
    demand_mw = Column(Numeric(10, 2))
    supply_mw = Column(Numeric(10, 2))
    load_shedding_mw = Column(Numeric(10, 2))
    deficit_mw = Column(Numeric(10, 2))
    source = Column(String(50), default="pgcb")
    data_classification = Column(String(30), default="actual")
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_demand_history_ts", "timestamp", postgresql_using="btree"),
        Index("idx_demand_history_source", "source"),
    )


class GridSnapshot(Base):
    __tablename__ = "grid_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    collected_at = Column(DateTime(timezone=True), default=_utcnow)
    demand_mw = Column(Numeric(10, 2))
    supply_mw = Column(Numeric(10, 2))
    load_shedding_mw = Column(Numeric(10, 2))
    gas_mw = Column(Numeric(10, 2))
    liquid_fuel_mw = Column(Numeric(10, 2))
    coal_mw = Column(Numeric(10, 2))
    hydro_mw = Column(Numeric(10, 2))
    solar_mw = Column(Numeric(10, 2))
    wind_mw = Column(Numeric(10, 2))
    hvdc_mw = Column(Numeric(10, 2))
    import_mw = Column(Numeric(10, 2))
    grid_status = Column(String(20))
    risk_level = Column(String(20))
    source = Column(String(50), default="PGCB_ERP")
    data_classification = Column(String(30), default="OFFICIAL_PGCB")
    raw_html = Column(Text)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_grid_snapshots_ts", "timestamp", postgresql_using="btree"),
    )


class AIPrediction(Base):
    __tablename__ = "ai_predictions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    model_type = Column(String(30), nullable=False)
    zone = Column(String(50))
    predicted_mw = Column(Numeric(10, 2))
    actual_mw = Column(Numeric(10, 2))
    features_json = Column(JSON)
    model_version = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_predictions_ts", "timestamp", postgresql_using="btree"),
        Index("idx_predictions_model", "model_type", "zone"),
    )


class LoadshieldDispatch(Base):
    __tablename__ = "loadshield_dispatches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    demand_mw = Column(Numeric(10, 2))
    supply_mw = Column(Numeric(10, 2))
    deficit_mw = Column(Numeric(10, 2))
    solar_mw = Column(Numeric(10, 2))
    wind_mw = Column(Numeric(10, 2))
    hydro_mw = Column(Numeric(10, 2))
    biomass_mw = Column(Numeric(10, 2))
    waste_mw = Column(Numeric(10, 2))
    battery_mw = Column(Numeric(10, 2))
    flexible_mw = Column(Numeric(10, 2))
    remaining_gap = Column(Numeric(10, 2))
    status = Column(String(30))
    risk_level = Column(String(30))
    zone_breakdown = Column(JSON)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_dispatches_ts", "timestamp", postgresql_using="btree"),
    )


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type = Column(String(30), nullable=False)
    model_path = Column(String(255))
    trained_at = Column(DateTime(timezone=True))
    training_samples = Column(Integer)
    mae = Column(Numeric(10, 4))
    rmse = Column(Numeric(10, 4))
    r2 = Column(Numeric(6, 4))
    features = Column(JSON)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("idx_model_registry_type", "model_type"),
    )
