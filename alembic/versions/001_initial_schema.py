"""Initial database schema

Revision ID: 001_initial
Revises: 
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "demand_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pgcb_timestamp", sa.DateTime(timezone=True), nullable=True),
        sa.Column("demand_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("supply_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("load_shedding_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("deficit_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("source", sa.String(50), server_default="pgcb"),
        sa.Column("data_classification", sa.String(30), server_default="actual"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_demand_history_ts", "demand_history", ["timestamp"])
    op.create_index("idx_demand_history_source", "demand_history", ["source"])

    op.create_table(
        "grid_snapshots",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("demand_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("supply_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("load_shedding_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("gas_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("liquid_fuel_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("coal_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("hydro_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("solar_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("wind_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("hvdc_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("import_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("grid_status", sa.String(20), nullable=True),
        sa.Column("risk_level", sa.String(20), nullable=True),
        sa.Column("raw_html", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_grid_snapshots_ts", "grid_snapshots", ["timestamp"])

    op.create_table(
        "ai_predictions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("model_type", sa.String(30), nullable=False),
        sa.Column("zone", sa.String(50), nullable=True),
        sa.Column("predicted_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("actual_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("features_json", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_predictions_ts", "ai_predictions", ["timestamp"])
    op.create_index("idx_predictions_model", "ai_predictions", ["model_type", "zone"])

    op.create_table(
        "loadshield_dispatches",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("demand_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("supply_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("deficit_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("solar_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("wind_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("hydro_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("biomass_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("waste_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("battery_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("flexible_mw", sa.Numeric(10, 2), nullable=True),
        sa.Column("remaining_gap", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(30), nullable=True),
        sa.Column("risk_level", sa.String(30), nullable=True),
        sa.Column("zone_breakdown", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_dispatches_ts", "loadshield_dispatches", ["timestamp"])

    op.create_table(
        "model_registry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("model_type", sa.String(30), nullable=False),
        sa.Column("model_path", sa.String(255), nullable=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("training_samples", sa.Integer(), nullable=True),
        sa.Column("mae", sa.Numeric(10, 4), nullable=True),
        sa.Column("rmse", sa.Numeric(10, 4), nullable=True),
        sa.Column("r2", sa.Numeric(6, 4), nullable=True),
        sa.Column("features", sa.JSON(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_model_registry_type", "model_registry", ["model_type"])


def downgrade() -> None:
    op.drop_table("model_registry")
    op.drop_table("loadshield_dispatches")
    op.drop_table("ai_predictions")
    op.drop_table("grid_snapshots")
    op.drop_table("demand_history")
