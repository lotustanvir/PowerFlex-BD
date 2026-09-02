"""Normalized Demand and Supply Data Models for PowerFlex BD v3.

All demand and supply data returned by the platform must conform
to these standardized models. This ensures consistent data quality,
provenance tracking, and classification across all modules.

NEVER fabricate data. If unavailable, use DATA_UNAVAILABLE.
If stale, use STALE. If estimated, use ESTIMATED.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.data_classification import DataClassification

logger = logging.getLogger("powerflex.data_models")


@dataclass
class DataProvenance:
    """Standardized provenance metadata for any data point."""
    source: str
    source_timestamp: Optional[str] = None
    retrieved_at: Optional[str] = None
    timezone: str = "Asia/Dhaka"
    quality: str = "GOOD"
    classification: str = "UNKNOWN"
    freshness: str = "UNKNOWN"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "source_timestamp": self.source_timestamp,
            "retrieved_at": self.retrieved_at,
            "timezone": self.timezone,
            "quality": self.quality,
            "classification": self.classification,
            "freshness": self.freshness,
            "notes": self.notes,
        }


@dataclass
class DemandData:
    """Normalized demand data point."""
    timestamp: str
    demand_mw: Optional[float]
    peak_demand_mw: Optional[float] = None
    minimum_demand_mw: Optional[float] = None
    average_demand_mw: Optional[float] = None
    provenance: Optional[DataProvenance] = None
    quality: str = "GOOD"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "timestamp": self.timestamp,
            "demand_mw": self.demand_mw,
            "peak_demand_mw": self.peak_demand_mw,
            "minimum_demand_mw": self.minimum_demand_mw,
            "average_demand_mw": self.average_demand_mw,
            "quality": self.quality,
            "notes": self.notes,
        }
        if self.provenance:
            result["provenance"] = self.provenance.to_dict()
        return result


@dataclass
class PlantData:
    """Normalized plant-level generation data."""
    plant_name: str
    technology: str
    fuel: str
    capacity_mw: Optional[float] = None
    available_generation_mw: Optional[float] = None
    actual_generation_mw: Optional[float] = None
    status: str = "UNKNOWN"
    provenance: Optional[DataProvenance] = None

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "plant_name": self.plant_name,
            "technology": self.technology,
            "fuel": self.fuel,
            "capacity_mw": self.capacity_mw,
            "available_generation_mw": self.available_generation_mw,
            "actual_generation_mw": self.actual_generation_mw,
            "status": self.status,
        }
        if self.provenance:
            result["provenance"] = self.provenance.to_dict()
        return result


@dataclass
class SupplyData:
    """Normalized supply/generation data point."""
    timestamp: str
    supply_mw: Optional[float] = None
    generation_mw: Optional[float] = None
    available_capacity_mw: Optional[float] = None
    plants: List[PlantData] = field(default_factory=list)
    provenance: Optional[DataProvenance] = None
    quality: str = "GOOD"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "timestamp": self.timestamp,
            "supply_mw": self.supply_mw,
            "generation_mw": self.generation_mw,
            "available_capacity_mw": self.available_capacity_mw,
            "plants": [p.to_dict() for p in self.plants],
            "quality": self.quality,
            "notes": self.notes,
        }
        if self.provenance:
            result["provenance"] = self.provenance.to_dict()
        return result


@dataclass
class GenerationBreakdown:
    """Breakdown of generation by fuel/technology type."""
    gas_mw: Optional[float] = None
    coal_mw: Optional[float] = None
    liquid_fuel_mw: Optional[float] = None
    hydro_mw: Optional[float] = None
    solar_mw: Optional[float] = None
    wind_mw: Optional[float] = None
    nuclear_mw: Optional[float] = None
    biomass_mw: Optional[float] = None
    waste_mw: Optional[float] = None
    import_mw: Optional[float] = None
    hvdc_mw: Optional[float] = None
    provenance: Optional[DataProvenance] = None

    def total_generation_mw(self) -> Optional[float]:
        """Calculate total generation from breakdown."""
        values = [
            self.gas_mw, self.coal_mw, self.liquid_fuel_mw,
            self.hydro_mw, self.solar_mw, self.wind_mw,
            self.nuclear_mw, self.biomass_mw, self.waste_mw,
        ]
        valid = [v for v in values if v is not None]
        if not valid:
            return None
        return sum(valid)

    def to_dict(self) -> Dict[str, Any]:
        result = {
            "gas_mw": self.gas_mw,
            "coal_mw": self.coal_mw,
            "liquid_fuel_mw": self.liquid_fuel_mw,
            "hydro_mw": self.hydro_mw,
            "solar_mw": self.solar_mw,
            "wind_mw": self.wind_mw,
            "nuclear_mw": self.nuclear_mw,
            "biomass_mw": self.biomass_mw,
            "waste_mw": self.waste_mw,
            "import_mw": self.import_mw,
            "hvdc_mw": self.hvdc_mw,
        }
        if self.provenance:
            result["provenance"] = self.provenance.to_dict()
        return result


@dataclass
class GridSnapshotNormalized:
    """Normalized complete grid snapshot."""
    timestamp: str
    demand: DemandData
    supply: SupplyData
    generation: GenerationBreakdown
    gap_mw: Optional[float] = None
    load_shedding_mw: Optional[float] = None
    frequency_hz: Optional[float] = None
    grid_status: str = "UNKNOWN"
    risk_level: str = "UNKNOWN"
    provenance: Optional[DataProvenance] = None
    data_quality: str = "GOOD"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "demand": self.demand.to_dict(),
            "supply": self.supply.to_dict(),
            "generation": self.generation.to_dict(),
            "gap_mw": self.gap_mw,
            "load_shedding_mw": self.load_shedding_mw,
            "frequency_hz": self.frequency_hz,
            "grid_status": self.grid_status,
            "risk_level": self.risk_level,
            "data_quality": self.data_quality,
            "provenance": self.provenance.to_dict() if self.provenance else None,
        }


# =========================================================
# DATA QUALITY ASSESSMENT
# =========================================================

class DataQuality:
    """Data quality assessment utilities."""

    @staticmethod
    def assess_demand_quality(demand_mw: Optional[float], timestamp: Optional[str]) -> str:
        """Assess the quality of demand data."""
        if demand_mw is None:
            return "UNAVAILABLE"
        if demand_mw < 0:
            return "INVALID"
        if demand_mw > 20000:
            return "SUSPECT"
        if demand_mw < 1000:
            return "SUSPECT"
        return "GOOD"

    @staticmethod
    def assess_supply_quality(supply_mw: Optional[float], demand_mw: Optional[float]) -> str:
        """Assess the quality of supply data."""
        if supply_mw is None:
            return "UNAVAILABLE"
        if supply_mw < 0:
            return "INVALID"
        if demand_mw and supply_mw > demand_mw * 2:
            return "SUSPECT"
        return "GOOD"

    @staticmethod
    def assess_freshness(timestamp_str: Optional[str], max_age_hours: float = 2.0) -> str:
        """Assess data freshness based on timestamp."""
        if not timestamp_str:
            return "UNKNOWN"
        try:
            if "T" in timestamp_str:
                dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            else:
                dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                dt = dt.replace(tzinfo=timezone.utc)

            now = datetime.now(timezone.utc)
            age = now - dt

            if age.total_seconds() < 0:
                return "FUTURE"
            if age.total_seconds() < 3600:
                return "FRESH"
            if age.total_seconds() < max_age_hours * 3600:
                return "RECENT"
            if age.total_seconds() < 24 * 3600:
                return "STALE"
            return "OLD"
        except (ValueError, TypeError):
            return "UNKNOWN"

    @staticmethod
    def detect_duplicates(data_points: List[Dict[str, Any]], key: str = "timestamp") -> List[int]:
        """Detect duplicate entries by timestamp."""
        seen = set()
        duplicates = []
        for i, point in enumerate(data_points):
            ts = point.get(key)
            if ts in seen:
                duplicates.append(i)
            seen.add(ts)
        return duplicates

    @staticmethod
    def detect_gaps(timestamps: List[str], expected_interval_minutes: int = 60) -> List[Dict[str, Any]]:
        """Detect missing timestamps in a time series."""
        if len(timestamps) < 2:
            return []

        sorted_ts = sorted(timestamps)
        gaps = []

        for i in range(1, len(sorted_ts)):
            try:
                prev = datetime.fromisoformat(sorted_ts[i - 1].replace("Z", "+00:00"))
                curr = datetime.fromisoformat(sorted_ts[i].replace("Z", "+00:00"))
                diff_minutes = (curr - prev).total_seconds() / 60
                if diff_minutes > expected_interval_minutes * 1.5:
                    gaps.append({
                        "after": sorted_ts[i - 1],
                        "before": sorted_ts[i],
                        "gap_minutes": diff_minutes,
                    })
            except (ValueError, TypeError):
                continue

        return gaps


def create_demand_unavailable(source: str, reason: str = "Data source unavailable") -> DemandData:
    """Create a standardized unavailable demand response."""
    now = datetime.now(timezone.utc).isoformat()
    return DemandData(
        timestamp=now,
        demand_mw=None,
        provenance=DataProvenance(
            source=source,
            retrieved_at=now,
            quality="UNAVAILABLE",
            classification="DATA_UNAVAILABLE",
            freshness="UNAVAILABLE",
            notes=reason,
        ),
        quality="UNAVAILABLE",
        notes=reason,
    )


def create_supply_unavailable(source: str, reason: str = "Data source unavailable") -> SupplyData:
    """Create a standardized unavailable supply response."""
    now = datetime.now(timezone.utc).isoformat()
    return SupplyData(
        timestamp=now,
        supply_mw=None,
        generation_mw=None,
        available_capacity_mw=None,
        provenance=DataProvenance(
            source=source,
            retrieved_at=now,
            quality="UNAVAILABLE",
            classification="DATA_UNAVAILABLE",
            freshness="UNAVAILABLE",
            notes=reason,
        ),
        quality="UNAVAILABLE",
        notes=reason,
    )
