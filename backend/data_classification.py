"""Centralized Data Classification System for PowerFlex BD v2.0.

Every important energy value returned by the backend must include
metadata indicating its classification, source, timestamp, and
methodology. This module provides the enum, helper functions, and
standardized response wrappers.

Classifications:
  OFFICIAL       - Verified data from government/institutional sources
  MEASURED       - Physical telemetry from operational sensors
  LIVE_FEED      - Near-real-time data from external feeds
  DELAYED        - Official data with significant time lag
  FORECAST       - Weather-driven or ML-driven predictions
  CALCULATED     - Engineering/physics-based calculations
  POTENTIAL      - Theoretical/geographic potential
  SCENARIO       - Explicit scenario assumptions
  PROJECT        - Planned/announced projects
  UNDER_CONSTRUCTION - Physically under construction
  UNDER_COMMISSIONING - Under commissioning/commissioning tests
  EXPERIMENTAL   - Research/prototype models not validated for production
  PROTOTYPE      - Placeholder values awaiting real data
  DATA_UNAVAILABLE - Data source unavailable or failed
  UNKNOWN        - Classification cannot be determined
"""

from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, Optional


class DataClassification(str, Enum):
    """Standardized data classification values."""

    OFFICIAL = "OFFICIAL"
    MEASURED = "MEASURED"
    LIVE_FEED = "LIVE_FEED"
    DELAYED = "DELAYED"
    FORECAST = "FORECAST"
    CALCULATED = "CALCULATED"
    POTENTIAL = "POTENTIAL"
    SCENARIO = "SCENARIO"
    PROJECT = "PROJECT"
    UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
    UNDER_COMMISSIONING = "UNDER_COMMISSIONING"
    EXPERIMENTAL = "EXPERIMENTAL"
    PROTOTYPE = "PROTOTYPE"
    DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


# Legacy aliases for backward compatibility
LEGACY_CLASSIFICATION_MAP = {
    "OFFICIAL_PGCB": DataClassification.OFFICIAL,
    "LIVE": DataClassification.LIVE_FEED,
    "MODEL_FORECAST": DataClassification.FORECAST,
    "CALCULATED_FROM_OFFICIAL_DATA": DataClassification.CALCULATED,
    "PROTOTYPE": DataClassification.PROTOTYPE,
    "DATA_UNAVAILABLE": DataClassification.DATA_UNAVAILABLE,
    "NOT_CONNECTED": DataClassification.DATA_UNAVAILABLE,
}


def normalize_classification(raw: str) -> DataClassification:
    """Map legacy classification strings to the standardized enum."""
    if raw is None:
        return DataClassification.UNKNOWN
    upper = raw.strip().upper()
    if upper in LEGACY_CLASSIFICATION_MAP:
        return LEGACY_CLASSIFICATION_MAP[upper]
    try:
        return DataClassification(upper)
    except ValueError:
        return DataClassification.UNKNOWN


# =========================================================
# CLASSIFICATION DISPLAY METADATA
# =========================================================

CLASSIFICATION_DISPLAY = {
    DataClassification.OFFICIAL: {
        "label": "Official",
        "badge_color": "emerald",
        "icon": "🏛️",
        "description": "Verified data from government or institutional sources.",
    },
    DataClassification.MEASURED: {
        "label": "Measured",
        "badge_color": "emerald",
        "icon": "📏",
        "description": "Physical telemetry from operational sensors.",
    },
    DataClassification.LIVE_FEED: {
        "label": "Live Feed",
        "badge_color": "sky",
        "icon": "📡",
        "description": "Near-real-time data from external API feeds.",
    },
    DataClassification.DELAYED: {
        "label": "Delayed",
        "badge_color": "amber",
        "icon": "⏳",
        "description": "Official data with significant time lag.",
    },
    DataClassification.FORECAST: {
        "label": "Forecast",
        "badge_color": "blue",
        "icon": "🔮",
        "description": "Weather-driven or ML-driven prediction.",
    },
    DataClassification.CALCULATED: {
        "label": "Calculated",
        "badge_color": "amber",
        "icon": "🧮",
        "description": "Engineering or physics-based calculation.",
    },
    DataClassification.POTENTIAL: {
        "label": "Potential",
        "badge_color": "purple",
        "icon": "📊",
        "description": "Theoretical or geographic potential estimate.",
    },
    DataClassification.SCENARIO: {
        "label": "Scenario",
        "badge_color": "slate",
        "icon": "📋",
        "description": "Explicit scenario assumption for analysis.",
    },
    DataClassification.PROJECT: {
        "label": "Project",
        "badge_color": "red",
        "icon": "🏗️",
        "description": "Planned or announced project.",
    },
    DataClassification.UNDER_CONSTRUCTION: {
        "label": "Under Construction",
        "badge_color": "red",
        "icon": "🚧",
        "description": "Physically under construction.",
    },
    DataClassification.UNDER_COMMISSIONING: {
        "label": "Commissioning",
        "badge_color": "orange",
        "icon": "⚙️",
        "description": "Under commissioning and testing.",
    },
    DataClassification.EXPERIMENTAL: {
        "label": "Experimental",
        "badge_color": "yellow",
        "icon": "🧪",
        "description": "Research/prototype model, not validated for production.",
    },
    DataClassification.PROTOTYPE: {
        "label": "Prototype",
        "badge_color": "slate",
        "icon": "🔧",
        "description": "Placeholder value awaiting real data.",
    },
    DataClassification.DATA_UNAVAILABLE: {
        "label": "Unavailable",
        "badge_color": "red",
        "icon": "❌",
        "description": "Data source unavailable or failed.",
    },
    DataClassification.UNKNOWN: {
        "label": "Unknown",
        "badge_color": "gray",
        "icon": "❓",
        "description": "Classification cannot be determined.",
    },
}


# =========================================================
# PROVENANCE WRAPPER
# =========================================================

def wrap_with_provenance(
    value: Any,
    unit: str,
    classification: DataClassification,
    source: str,
    timestamp: Optional[str] = None,
    last_verified: Optional[str] = None,
    confidence: Optional[float] = None,
    methodology: Optional[str] = None,
) -> Dict[str, Any]:
    """Wrap a value with standardized provenance metadata.

    Args:
        value: The numeric or string value.
        unit: Unit of measurement (e.g., "MW", "MWh", "km/h").
        classification: DataClassification enum value.
        source: Human-readable source description.
        timestamp: ISO-8601 timestamp of when this value was generated.
        last_verified: ISO-8601 timestamp of last official verification.
        confidence: Prediction confidence (0.0-1.0), if applicable.
        methodology: Brief description of how this value was produced.

    Returns:
        Dictionary with value + full provenance metadata.
    """
    now = datetime.now(timezone.utc).isoformat()
    display = CLASSIFICATION_DISPLAY.get(
        classification, CLASSIFICATION_DISPLAY[DataClassification.UNKNOWN]
    )

    result = {
        "value": value,
        "unit": unit,
        "classification": classification.value,
        "classification_display": display["label"],
        "classification_badge_color": display["badge_color"],
        "classification_icon": display["icon"],
        "classification_description": display["description"],
        "source": source,
        "timestamp": timestamp or now,
        "last_verified": last_verified,
        "confidence": confidence,
        "methodology": methodology,
    }

    return result


def create_unavailable(
    unit: str,
    source: str,
    reason: str = "Data source unavailable",
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a standardized DATA_UNAVAILABLE response.

    Use this instead of returning None, 0, or fake data
    when a data source fails.
    """
    now = datetime.now(timezone.utc).isoformat()
    display = CLASSIFICATION_DISPLAY[DataClassification.DATA_UNAVAILABLE]

    return {
        "value": None,
        "unit": unit,
        "classification": DataClassification.DATA_UNAVAILABLE.value,
        "classification_display": display["label"],
        "classification_badge_color": display["badge_color"],
        "classification_icon": display["icon"],
        "classification_description": display["description"],
        "source": source,
        "timestamp": timestamp or now,
        "last_verified": None,
        "confidence": None,
        "methodology": None,
        "error": reason,
    }


# =========================================================
# DATA SOURCE REGISTRY
# =========================================================

DATA_SOURCES = {
    "pgcb_erp": {
        "name": "PGCB ERP Portal",
        "url": "https://erp.powergrid.gov.bd",
        "type": "OFFICIAL",
        "classification": DataClassification.OFFICIAL,
        "update_frequency": "On-demand HTML scrape",
        "reliability": "HIGH (when accessible)",
        "description": (
            "Power Grid Company of Bangladesh Enterprise Resource Planning "
            "portal. Provides demand, supply, load-shedding, and generation "
            "breakdown data."
        ),
    },
    "open_meteo": {
        "name": "Open-Meteo Weather API",
        "url": "https://api.open-meteo.com",
        "type": "LIVE_FEED",
        "classification": DataClassification.LIVE_FEED,
        "update_frequency": "Hourly forecast updates",
        "reliability": "HIGH",
        "description": (
            "Open-source weather API providing hourly forecasts for "
            "temperature, irradiance, wind speed, and other meteorological "
            "variables."
        ),
    },
    "faostat": {
        "name": "FAOSTAT (UN FAO)",
        "url": "https://www.fao.org/faostat",
        "type": "DELAYED",
        "classification": DataClassification.DELAYED,
        "update_frequency": "Annual",
        "reliability": "HIGH (with lag)",
        "description": (
            "Food and Agriculture Organization of the United Nations "
            "statistical database. Used for crop production data for "
            "biomass potential calculations."
        ),
    },
    "powerflex_solar_ai": {
        "name": "PowerFlex Solar AI",
        "type": "FORECAST",
        "classification": DataClassification.FORECAST,
        "update_frequency": "On-demand (300s cache)",
        "reliability": "EXPERIMENTAL",
        "description": (
            "XGBoost model trained on synthetic targets derived from "
            "Open-Meteo irradiance. NOT validated against real solar "
            "generation data from Bangladesh."
        ),
    },
    "powerflex_wind_ai": {
        "name": "PowerFlex Wind Power Curve",
        "type": "CALCULATED",
        "classification": DataClassification.CALCULATED,
        "update_frequency": "On-demand (300s cache)",
        "reliability": "EXPERIMENTAL",
        "description": (
            "Engineering power curve model applied to Open-Meteo 100m wind "
            "speed data. Uses simplified prototype turbine parameters. "
            "NOT validated against real wind turbine telemetry."
        ),
    },
    "powerflex_demand_forecast": {
        "name": "PowerFlex Demand Forecast",
        "type": "FORECAST",
        "classification": DataClassification.FORECAST,
        "update_frequency": "On-demand (300s cache)",
        "reliability": "EXPERIMENTAL",
        "description": (
            "XGBoost model trained on SYNTHETIC demand profiles based on "
            "published Bangladesh load research patterns. Anchored to "
            "real-time PGCB current demand. NOT production-validated."
        ),
    },
}


def get_source_info(source_key: str) -> Dict[str, Any]:
    """Retrieve metadata for a registered data source."""
    return DATA_SOURCES.get(source_key, {
        "name": source_key,
        "type": "UNKNOWN",
        "classification": DataClassification.UNKNOWN,
        "description": "Unregistered data source.",
    })
