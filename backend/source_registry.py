"""Centralized Source Registry for PowerFlex BD v3.

Every data source used by the platform is registered here with
metadata about its accessibility, reliability, update frequency,
and classification. This is the single source of truth for data
provenance across all modules.

DO NOT fabricate sources. Only register sources that have been
independently verified to exist and be accessible.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger("powerflex.source_registry")


class SourceType(str, Enum):
    """Classification of data source types."""
    OFFICIAL_API = "OFFICIAL_API"
    OFFICIAL_SCRAPER = "OFFICIAL_SCRAPER"
    OPEN_API = "OPEN_API"
    REFERENCE_DATA = "REFERENCE_DATA"
    CALCULATED = "CALCULATED"
    ML_MODEL = "ML_MODEL"
    UNKNOWN = "UNKNOWN"


class SourceStatus(str, Enum):
    """Current operational status of a data source."""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    RATE_LIMITED = "RATE_LIMITED"
    BLOCKED = "BLOCKED"
    UNVERIFIED = "UNVERIFIED"


@dataclass
class DataSourceEntry:
    """Metadata for a registered data source."""
    source_id: str
    name: str
    organization: str
    source_type: SourceType
    url: Optional[str]
    access_method: str
    data_type: str
    update_frequency: str
    historical_coverage: str
    reliability: str
    license_notes: str
    classification: str
    status: SourceStatus = SourceStatus.UNVERIFIED
    active: bool = True
    last_success: Optional[str] = None
    last_failure: Optional[str] = None
    failure_count: int = 0
    success_count: int = 0
    description: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "organization": self.organization,
            "source_type": self.source_type.value,
            "url": self.url,
            "access_method": self.access_method,
            "data_type": self.data_type,
            "update_frequency": self.update_frequency,
            "historical_coverage": self.historical_coverage,
            "reliability": self.reliability,
            "license_notes": self.license_notes,
            "classification": self.classification,
            "status": self.status.value,
            "active": self.active,
            "last_success": self.last_success,
            "last_failure": self.last_failure,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "description": self.description,
            "notes": self.notes,
        }


class SourceRegistry:
    """Global registry of all data sources used by PowerFlex BD."""

    def __init__(self):
        self._sources: Dict[str, DataSourceEntry] = {}
        self._register_verified_sources()

    def _register_verified_sources(self):
        """Register only independently verified data sources."""

        # =========================================================
        # VERIFIED SOURCES — Bangladesh Electricity
        # =========================================================

        self.register(DataSourceEntry(
            source_id="pgcb_erp",
            name="PGCB ERP Portal",
            organization="Power Grid Company of Bangladesh",
            source_type=SourceType.OFFICIAL_SCRAPER,
            url="https://erp.powergrid.gov.bd",
            access_method="HTML scraping with BeautifulSoup",
            data_type="Grid demand, supply, load-shedding, generation breakdown",
            update_frequency="On-demand (scraper invocation)",
            historical_coverage="Current snapshot only (no historical API)",
            reliability="HIGH (when accessible, intermittent downtime)",
            license_notes="Government portal, no public API terms",
            classification="OFFICIAL",
            status=SourceStatus.ACTIVE,
            description=(
                "Power Grid Company of Bangladesh ERP portal. "
                "Primary source for national grid demand, supply, "
                "load-shedding, and generation breakdown by fuel type."
            ),
            notes=(
                "HTML scraper with Bangla digit translation. "
                "Stale threshold: 2 hours. Retry with exponential backoff."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="open_meteo_weather",
            name="Open-Meteo Weather API",
            organization="Open-Meteo GmbH",
            source_type=SourceType.OPEN_API,
            url="https://api.open-meteo.com",
            access_method="REST API (free tier)",
            data_type="Weather forecasts: temperature, humidity, wind speed, cloud cover, solar irradiance",
            update_frequency="Hourly forecast updates",
            historical_coverage="Past 7 days to 16-day forecast",
            reliability="HIGH",
            license_notes="CC-BY 4.0 for attribution; free for non-commercial use",
            classification="LIVE_FEED",
            status=SourceStatus.ACTIVE,
            description=(
                "Open-source weather API providing hourly forecasts "
                "for meteorological variables. Used for solar irradiance, "
                "wind speed, temperature, and cloud cover across "
                "9 Bangladesh zones."
            ),
            notes=(
                "Rate limit: 10,000 requests/day on free tier. "
                "Variables used: temperature_2m, relative_humidity_2m, "
                "precipitation, cloud_cover, wind_speed_10m, "
                "wind_direction_10m, shortwave_radiation, "
                "direct_normal_irradiance, diffuse_radiation."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="faostat_crop",
            name="FAOSTAT Crop Production",
            organization="Food and Agriculture Organization (UN FAO)",
            source_type=SourceType.REFERENCE_DATA,
            url="https://www.fao.org/faostat",
            access_method="Bulk download / API",
            data_type="Crop production statistics by country",
            update_frequency="Annual (1-2 year lag)",
            historical_coverage="1961 to present",
            reliability="HIGH (with publication lag)",
            license_notes="Open data, CC-BY-4.0",
            classification="DELAYED",
            status=SourceStatus.ACTIVE,
            description=(
                "UN FAO statistical database. Used for crop residue "
                "data in biomass potential calculations for Bangladesh."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="powerflex_solar_ai",
            name="PowerFlex Solar AI Model",
            organization="PowerFlex BD (internal)",
            source_type=SourceType.ML_MODEL,
            url=None,
            access_method="In-memory XGBoost model inference",
            data_type="Solar generation forecast (MW per 1MW installed)",
            update_frequency="On-demand (300s cache)",
            historical_coverage="Next 24 hours",
            reliability="EXPERIMENTAL",
            license_notes="Internal model",
            classification="FORECAST",
            status=SourceStatus.ACTIVE,
            description=(
                "XGBoost model trained on synthetic targets derived from "
                "Open-Meteo irradiance formulas. NOT validated against "
                "real Bangladesh solar farm output."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="powerflex_wind_ai",
            name="PowerFlex Wind Power Curve",
            organization="PowerFlex BD (internal)",
            source_type=SourceType.CALCULATED,
            url=None,
            access_method="Engineering power curve calculation",
            data_type="Wind generation forecast (MW per 1MW installed)",
            update_frequency="On-demand (300s cache)",
            historical_coverage="Next 24 hours",
            reliability="EXPERIMENTAL",
            license_notes="Internal model",
            classification="CALCULATED",
            status=SourceStatus.ACTIVE,
            description=(
                "Engineering power curve model applied to Open-Meteo "
                "100m wind speed data. Uses simplified prototype turbine "
                "parameters. NOT validated against real turbine telemetry."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="powerflex_demand_forecast",
            name="PowerFlex Demand Forecast",
            organization="PowerFlex BD (internal)",
            source_type=SourceType.ML_MODEL,
            url=None,
            access_method="XGBoost model + PGCB anchor",
            data_type="Demand forecast (MW) for next 24 hours",
            update_frequency="On-demand (300s cache)",
            historical_coverage="Next 24 hours",
            reliability="EXPERIMENTAL",
            license_notes="Internal model",
            classification="FORECAST",
            status=SourceStatus.ACTIVE,
            description=(
                "XGBoost model trained on synthetic demand profiles. "
                "Anchored to real-time PGCB demand. "
                "NOT production-validated."
            ),
        ))

        # =========================================================
        # UNVERIFIED SOURCES — Documented but not confirmed accessible
        # =========================================================

        self.register(DataSourceEntry(
            source_id="bpdb_annual",
            name="BPDB Annual Report",
            organization="Bangladesh Power Development Board",
            source_type=SourceType.REFERENCE_DATA,
            url="https://www.bpdb.gov.bd",
            access_method="PDF report download",
            data_type="Annual generation statistics, plant capacity",
            update_frequency="Annual",
            historical_coverage="Multi-year",
            reliability="MEDIUM (PDF parsing required)",
            license_notes="Government publication",
            classification="DELAYED",
            status=SourceStatus.UNVERIFIED,
            description=(
                "BPDB publishes annual performance reports with "
                "generation statistics by plant and fuel type."
            ),
            notes="Requires PDF parsing. Not yet integrated.",
        ))

        self.register(DataSourceEntry(
            source_id="power_division_monthly",
            name="Power Division Monthly Statistics",
            organization="Ministry of Power, Energy and Mineral Resources",
            source_type=SourceType.REFERENCE_DATA,
            url="https://powerdivision.gov.bd",
            access_method="Web scraping / PDF",
            data_type="Monthly electricity statistics",
            update_frequency="Monthly",
            historical_coverage="Multi-year",
            reliability="LOW (website accessibility varies)",
            license_notes="Government publication",
            classification="DELAYED",
            status=SourceStatus.UNVERIFIED,
            description=(
                "Power Division publishes monthly electricity "
                "statistics including demand, generation, and imports."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="sreda_renewable",
            name="SREDA Renewable Data",
            organization="Sustainable and Renewable Energy Development Authority",
            source_type=SourceType.REFERENCE_DATA,
            url="https://ndre.sreda.gov.bd",
            access_method="Web portal",
            data_type="Renewable energy installations and policies",
            update_frequency="Irregular",
            historical_coverage="Policy documents and project lists",
            reliability="LOW-MEDIUM",
            license_notes="Government publication",
            classification="DELAYED",
            status=SourceStatus.UNVERIFIED,
            description=(
                "SREDA maintains the National Renewable Energy Policy "
                "data and lists of approved renewable energy projects."
            ),
        ))

        self.register(DataSourceEntry(
            source_id="bmd_weather",
            name="Bangladesh Meteorological Department",
            organization="Bangladesh Meteorological Department",
            source_type=SourceType.OFFICIAL_API,
            url="https://www.bmd.gov.bd",
            access_method="Web portal / API (if available)",
            data_type="Weather observations, forecasts, warnings",
            update_frequency="Hourly / Daily",
            historical_coverage="Historical observations",
            reliability="MEDIUM (website accessibility varies)",
            license_notes="Government service",
            classification="OFFICIAL",
            status=SourceStatus.UNVERIFIED,
            description=(
                "BMD is the official national meteorological service. "
                "May provide more localized weather data than global models."
            ),
            notes="API availability not confirmed. Open-Meteo used as primary.",
        ))

    def register(self, entry: DataSourceEntry) -> None:
        """Register or update a data source."""
        self._sources[entry.source_id] = entry
        logger.debug("Registered source: %s (%s)", entry.source_id, entry.status.value)

    def get(self, source_id: str) -> Optional[DataSourceEntry]:
        """Retrieve a registered source by ID."""
        return self._sources.get(source_id)

    def list_all(self) -> List[DataSourceEntry]:
        """List all registered sources."""
        return list(self._sources.values())

    def list_by_status(self, status: SourceStatus) -> List[DataSourceEntry]:
        """List sources filtered by status."""
        return [s for s in self._sources.values() if s.status == status]

    def list_active(self) -> List[DataSourceEntry]:
        """List all active sources."""
        return [s for s in self._sources.values() if s.active]

    def record_success(self, source_id: str) -> None:
        """Record a successful data retrieval."""
        entry = self._sources.get(source_id)
        if entry:
            entry.success_count += 1
            entry.last_success = datetime.now(timezone.utc).isoformat()
            if entry.status == SourceStatus.INACTIVE:
                entry.status = SourceStatus.ACTIVE

    def record_failure(self, source_id: str, error: str = "") -> None:
        """Record a failed data retrieval."""
        entry = self._sources.get(source_id)
        if entry:
            entry.failure_count += 1
            entry.last_failure = datetime.now(timezone.utc).isoformat()
            if entry.failure_count >= 5:
                entry.status = SourceStatus.INACTIVE
                logger.warning(
                    "Source %s marked INACTIVE after %d failures",
                    source_id, entry.failure_count,
                )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire registry."""
        return {
            source_id: entry.to_dict()
            for source_id, entry in self._sources.items()
        }

    def summary(self) -> Dict[str, Any]:
        """Return a summary of the registry status."""
        all_sources = self.list_all()
        active = self.list_active()
        verified = self.list_by_status(SourceStatus.ACTIVE)
        unverified = self.list_by_status(SourceStatus.UNVERIFIED)

        return {
            "total_sources": len(all_sources),
            "active_sources": len(active),
            "verified_sources": len([s for s in verified if s.source_type != SourceType.ML_MODEL and s.source_type != SourceType.CALCULATED]),
            "unverified_sources": len(unverified),
            "ml_models": len([s for s in all_sources if s.source_type == SourceType.ML_MODEL]),
            "calculated": len([s for s in all_sources if s.source_type == SourceType.CALCULATED]),
            "classification_summary": self._classification_summary(all_sources),
        }

    def _classification_summary(self, sources: List[DataSourceEntry]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for s in sources:
            summary[s.classification] = summary.get(s.classification, 0) + 1
        return summary


_registry: Optional[SourceRegistry] = None


def get_source_registry() -> SourceRegistry:
    """Get or create the global source registry singleton."""
    global _registry
    if _registry is None:
        _registry = SourceRegistry()
    return _registry
