"""Add source, data_classification, collected_at to grid_snapshots

Revision ID: 003_add_grid_snapshot_provenance
Revises: 002_add_indexes
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003_add_grid_snapshot_provenance"
down_revision: Union[str, Sequence[str], None] = "002_add_indexes"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "grid_snapshots",
        sa.Column("collected_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "grid_snapshots",
        sa.Column("source", sa.String(50), server_default="PGCB_ERP", nullable=True),
    )
    op.add_column(
        "grid_snapshots",
        sa.Column("data_classification", sa.String(30), server_default="OFFICIAL_PGCB", nullable=True),
    )


def downgrade() -> None:
    op.drop_column("grid_snapshots", "data_classification")
    op.drop_column("grid_snapshots", "source")
    op.drop_column("grid_snapshots", "collected_at")
