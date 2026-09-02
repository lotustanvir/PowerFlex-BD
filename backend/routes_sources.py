"""Source Registry API Routes for PowerFlex BD v3.

Provides data source metadata, status, and health information.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException

from backend.source_registry import get_source_registry, SourceStatus

logger = logging.getLogger("powerflex.api.source_registry")

router = APIRouter(
    prefix="/api/v3/sources",
    tags=["Data Sources v3"],
)


@router.get("")
def list_sources():
    """List all registered data sources."""
    registry = get_source_registry()
    return {
        "status": "OK",
        "sources": registry.to_dict(),
        "summary": registry.summary(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/summary")
def get_summary():
    """Get summary of data source status."""
    registry = get_source_registry()
    return {
        "status": "OK",
        "summary": registry.summary(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{source_id}")
def get_source(source_id: str):
    """Get details for a specific data source."""
    registry = get_source_registry()
    source = registry.get(source_id)
    if source is None:
        raise HTTPException(
            status_code=404,
            detail=f"Source '{source_id}' not found"
        )
    return {
        "status": "OK",
        "source": source.to_dict(),
    }


@router.get("/active/list")
def list_active_sources():
    """List all active data sources."""
    registry = get_source_registry()
    active = registry.list_active()
    return {
        "status": "OK",
        "sources": [s.to_dict() for s in active],
        "count": len(active),
    }
