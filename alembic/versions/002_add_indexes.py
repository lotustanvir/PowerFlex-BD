"""Add performance indexes

Revision ID: 002_add_indexes
Revises: 001_initial
Create Date: 2026-09-01

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002_add_indexes"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "idx_grid_snapshots_ts_btree",
        "grid_snapshots",
        ["timestamp"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_predictions_ts_model",
        "ai_predictions",
        ["timestamp", "model_type"],
    )
    op.create_index(
        "idx_dispatches_ts_btree",
        "loadshield_dispatches",
        ["timestamp"],
        postgresql_using="btree",
    )
    op.create_index(
        "idx_demand_history_ts_btree",
        "demand_history",
        ["timestamp"],
        postgresql_using="btree",
    )


def downgrade() -> None:
    op.drop_index("idx_demand_history_ts_btree", table_name="demand_history")
    op.drop_index("idx_dispatches_ts_btree", table_name="loadshield_dispatches")
    op.drop_index("idx_predictions_ts_model", table_name="ai_predictions")
    op.drop_index("idx_grid_snapshots_ts_btree", table_name="grid_snapshots")
