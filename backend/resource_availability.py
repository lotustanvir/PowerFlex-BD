"""Unified Resource Availability Engine for PowerFlex BD.

Provides a single ResourceAvailability dataclass that every resource
(solar, wind, hydro, biomass, waste, battery, flexible demand) is
mapped into, enforcing clear separation between:

  - installed_capacity_mw   Total nameplate capacity
  - measured_mw             Actual real-time telemetry (None if unavailable)
  - forecast_mw             Model prediction for current hour
  - available_mw            What can actually be dispatched right now
  - potential_mw            Theoretical maximum
  - scenario_mw             Scenario/hypothetical values

KEY PRINCIPLE:
    POTENTIAL values must NEVER be treated as DISPATCHABLE.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from backend.prototype_config import SOLAR_INSTALLED_MW, WIND_INSTALLED_MW


# =========================================================
# DATA CLASSIFICATION CONSTANTS
# =========================================================

FORECAST = "FORECAST"
CALCULATED = "CALCULATED"
MEASURED = "MEASURED"
LIVE_FEED = "LIVE_FEED"
PROTOTYPE = "PROTOTYPE"
SCENARIO = "SCENARIO"
DATA_UNAVAILABLE = "DATA_UNAVAILABLE"
UNDER_COMMISSIONING = "UNDER_COMMISSIONING"


# =========================================================
# SCIENTIFIC DISCLAIMER
# =========================================================

SCIENTIFIC_DISCLAIMER = (
    "DISCLAIMER: This value is derived from weather-driven "
    "models, engineering estimates, or prototype assumptions. "
    "It is NOT measured grid telemetry and must not be treated "
    "as dispatchable generation without independent verification."
)


# =========================================================
# RESOURCE AVAILABILITY DATACLASS
# =========================================================

@dataclass
class ResourceAvailability:
    """Unified resource availability record.

    Every resource in the PowerFlex BD system is mapped into this
    dataclass so that consumers have a single, unambiguous
    interface for resource availability data.
    """

    resource_name: str
    installed_capacity_mw: float
    measured_mw: Optional[float]
    forecast_mw: Optional[float]
    available_mw: float
    potential_mw: float
    scenario_mw: float
    classification: str
    source: str
    timestamp: Optional[str]
    confidence: Optional[float]
    is_dispatchable: bool
    dispatch_note: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary (JSON-safe)."""
        return asdict(self)

    def summary(self) -> str:
        """One-line human-readable summary."""
        status = "DISPATCHABLE" if self.is_dispatchable else "NOT DISPATCHABLE"
        return (
            f"{self.resource_name}: {self.available_mw:.1f} MW available "
            f"/ {self.potential_mw:.1f} MW potential [{status}] "
            f"({self.classification})"
        )


# =========================================================
# SAFE HELPER
# =========================================================

def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# =========================================================
# SOLAR AVAILABILITY
# =========================================================

def get_solar_availability(
    solar_data: Optional[Dict[str, Any]] = None,
) -> ResourceAvailability:
    """Build a ResourceAvailability for solar.

    Args:
        solar_data: Output from the live solar forecast endpoint.
                    If None or missing keys, graceful fallback.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    installed = SOLAR_INSTALLED_MW  # prototype scenario capacity

    if solar_data is None:
        return ResourceAvailability(
            resource_name="Solar",
            installed_capacity_mw=installed,
            measured_mw=None,
            forecast_mw=None,
            available_mw=0.0,
            potential_mw=installed,
            scenario_mw=0.0,
            classification=DATA_UNAVAILABLE,
            source="No solar data provided",
            timestamp=now_iso,
            confidence=None,
            is_dispatchable=False,
            dispatch_note=(
                "No solar forecast data available. "
                + SCIENTIFIC_DISCLAIMER
            ),
        )

    # Current-hour forecast from the AI model (mw per 1 mw installed)
    current_gen = solar_data.get("current_hour_generation", {})
    forecast_per_mw = _safe_float(
        current_gen.get("mw_per_1mw_installed"), 0.0
    )
    forecast_mw = forecast_per_mw * installed

    best_zone = solar_data.get("best_forecast_zone", {})
    best_energy = _safe_float(
        best_zone.get("expected_energy_mwh_per_1mw_24h"), 0.0
    )
    potential_mw = best_energy * installed

    is_daytime = forecast_mw > 0.0

    return ResourceAvailability(
        resource_name="Solar",
        installed_capacity_mw=installed,
        measured_mw=None,
        forecast_mw=round(forecast_mw, 4),
        available_mw=round(forecast_mw, 4),
        potential_mw=round(potential_mw, 4),
        scenario_mw=0.0,
        classification=FORECAST,
        source="Open-Meteo + PowerFlex Solar AI",
        timestamp=current_gen.get("timestamp") or now_iso,
        confidence=0.7 if is_daytime else 0.0,
        is_dispatchable=is_daytime,
        dispatch_note=(
            "Solar availability based on weather-driven AI forecast. "
            "No real-time plant telemetry available. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# WIND AVAILABILITY
# =========================================================

def get_wind_availability(
    wind_data: Optional[Dict[str, Any]] = None,
) -> ResourceAvailability:
    """Build a ResourceAvailability for wind.

    Args:
        wind_data: Output from the live wind forecast endpoint.
                   If None or missing keys, graceful fallback.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    installed = WIND_INSTALLED_MW  # prototype scenario capacity

    if wind_data is None:
        return ResourceAvailability(
            resource_name="Wind",
            installed_capacity_mw=installed,
            measured_mw=None,
            forecast_mw=None,
            available_mw=0.0,
            potential_mw=installed,
            scenario_mw=0.0,
            classification=DATA_UNAVAILABLE,
            source="No wind data provided",
            timestamp=now_iso,
            confidence=None,
            is_dispatchable=False,
            dispatch_note=(
                "No wind forecast data available. "
                + SCIENTIFIC_DISCLAIMER
            ),
        )

    current_gen = wind_data.get("current_hour_generation", {})
    current_mw_per_1mw = _safe_float(
        current_gen.get("mw_per_1mw_installed"), 0.0
    )
    forecast_mw = current_mw_per_1mw * installed

    best_zone = wind_data.get("best_forecast_zone", {})
    best_energy = _safe_float(
        best_zone.get("expected_energy_mwh_per_1mw_24h"), 0.0
    )
    potential_mw = best_energy * installed

    return ResourceAvailability(
        resource_name="Wind",
        installed_capacity_mw=installed,
        measured_mw=None,
        forecast_mw=round(forecast_mw, 4),
        available_mw=round(forecast_mw, 4),
        potential_mw=round(potential_mw, 4),
        scenario_mw=0.0,
        classification=CALCULATED,
        source="Open-Meteo + PowerFlex Wind Power Curve",
        timestamp=current_gen.get("timestamp") or now_iso,
        confidence=0.65,
        is_dispatchable=forecast_mw > 0.0,
        dispatch_note=(
            "Wind availability based on power-curve engineering model. "
            "No real-time turbine telemetry available. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# BIOMASS AVAILABILITY
# =========================================================

def get_biomass_availability(
    biomass_info: Optional[Dict[str, Any]] = None,
) -> ResourceAvailability:
    """Build a ResourceAvailability for biomass.

    Args:
        biomass_info: Optional dict with keys like
                      'installed_capacity_mw', 'available_capacity_mw'.
                      If None, uses reference defaults.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    installed = 0.0
    available = 0.0
    potential = 0.0

    if biomass_info is not None:
        installed = _safe_float(
            biomass_info.get("installed_capacity_mw"), 0.0
        )
        available = _safe_float(
            biomass_info.get("available_capacity_mw"), 0.0
        )
        potential = _safe_float(
            biomass_info.get("potential_mw"), installed
        )

    # No utility-scale grid-connected biomass plant is
    # operational in Bangladesh.
    is_dispatchable = False

    return ResourceAvailability(
        resource_name="Biomass",
        installed_capacity_mw=installed,
        measured_mw=None,
        forecast_mw=None,
        available_mw=available,
        potential_mw=potential if potential > 0 else installed,
        scenario_mw=0.0,
        classification=DATA_UNAVAILABLE,
        source="BPDB / SREDA / US Trade.gov (international reference)",
        timestamp=now_iso,
        confidence=None,
        is_dispatchable=is_dispatchable,
        dispatch_note=(
            "No utility-scale grid-connected biomass plant is "
            "operational in Bangladesh. Capacity values are "
            "prototype assumptions. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# WASTE AVAILABILITY
# =========================================================

def get_waste_availability(
    waste_info: Optional[Dict[str, Any]] = None,
) -> ResourceAvailability:
    """Build a ResourceAvailability for waste-to-energy.

    Args:
        waste_info: Optional dict with keys like
                    'installed_capacity_mw', 'status'.
                    If None, uses reference defaults.
    """
    now_iso = datetime.now(timezone.utc).isoformat()

    installed = 0.0
    available = 0.0

    if waste_info is not None:
        installed = _safe_float(
            waste_info.get("installed_capacity_mw"), 0.0
        )
        available = _safe_float(
            waste_info.get("available_capacity_mw"), 0.0
        )

    # Waste-to-energy plants are under construction in Bangladesh.
    is_dispatchable = False

    return ResourceAvailability(
        resource_name="Waste-to-Energy",
        installed_capacity_mw=installed,
        measured_mw=None,
        forecast_mw=None,
        available_mw=available,
        potential_mw=installed,
        scenario_mw=0.0,
        classification=UNDER_COMMISSIONING
        if installed > 0
        else DATA_UNAVAILABLE,
        source="AIIB / NDB / CMEC (international reference)",
        timestamp=now_iso,
        confidence=None,
        is_dispatchable=is_dispatchable,
        dispatch_note=(
            "Waste-to-energy plants are under construction "
            "(North Dhaka WtE, 42.5 MW). Not yet operational. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# HYDRO AVAILABILITY
# =========================================================

def get_hydro_availability() -> ResourceAvailability:
    """Build a ResourceAvailability for hydro.

    Kaptai Dam (Karnafuli) is the only hydro plant in Bangladesh.
    Without live telemetry, classification is DATA_UNAVAILABLE.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    installed = 230.0

    return ResourceAvailability(
        resource_name="Hydro",
        installed_capacity_mw=installed,
        measured_mw=None,
        forecast_mw=None,
        available_mw=0.0,
        potential_mw=installed,
        scenario_mw=0.0,
        classification=DATA_UNAVAILABLE,
        source="BPDB / BWDB (awaiting official plant data)",
        timestamp=now_iso,
        confidence=None,
        is_dispatchable=False,
        dispatch_note=(
            "Kaptai Dam (Karnafuli) - 230 MW installed. "
            "No live telemetry available. "
            "Awaiting official plant-level data from PGCB/BWDB. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# NUCLEAR AVAILABILITY (for test coverage)
# =========================================================

def get_nuclear_availability() -> ResourceAvailability:
    """Build a ResourceAvailability for nuclear.

    Rooppur Nuclear Power Plant (RNPP) is under commissioning.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    installed = 2400.0

    return ResourceAvailability(
        resource_name="Nuclear",
        installed_capacity_mw=installed,
        measured_mw=None,
        forecast_mw=None,
        available_mw=0.0,
        potential_mw=installed,
        scenario_mw=0.0,
        classification=UNDER_COMMISSIONING,
        source="World Nuclear Association / Rosatom",
        timestamp=now_iso,
        confidence=None,
        is_dispatchable=False,
        dispatch_note=(
            "Rooppur Nuclear Power Plant (RNPP). "
            "2 x VVER-1200, 2,400 MW gross. "
            "Under commissioning, not yet generating to grid. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# BATTERY (SCENARIO-ONLY)
# =========================================================

def get_battery_availability() -> ResourceAvailability:
    """Build a ResourceAvailability for battery storage.

    Battery values are scenario-only assumptions.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    power_capacity = 500.0
    soc_percent = 80.0

    return ResourceAvailability(
        resource_name="Battery",
        installed_capacity_mw=power_capacity,
        measured_mw=None,
        forecast_mw=None,
        available_mw=0.0,
        potential_mw=0.0,
        scenario_mw=round(power_capacity * soc_percent / 100, 4),
        classification=SCENARIO,
        source="Prototype configuration (no real storage asset data)",
        timestamp=now_iso,
        confidence=None,
        is_dispatchable=False,
        dispatch_note=(
            "Battery dispatch is scenario-only. "
            "Awaiting real storage asset data. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# FLEXIBLE DEMAND (SCENARIO-ONLY)
# =========================================================

def get_flexible_demand_availability() -> ResourceAvailability:
    """Build a ResourceAvailability for flexible/demand response.

    Values are scenario-only assumptions.
    """
    now_iso = datetime.now(timezone.utc).isoformat()
    capacity = 500.0

    return ResourceAvailability(
        resource_name="Flexible Demand",
        installed_capacity_mw=capacity,
        measured_mw=None,
        forecast_mw=None,
        available_mw=0.0,
        potential_mw=0.0,
        scenario_mw=capacity,
        classification=SCENARIO,
        source="Prototype configuration (no real DR program data)",
        timestamp=now_iso,
        confidence=None,
        is_dispatchable=False,
        dispatch_note=(
            "Flexible demand is demand reduction, not generation. "
            "Scenario-only. Awaiting real DR program data. "
            + SCIENTIFIC_DISCLAIMER
        ),
    )


# =========================================================
# GET ALL AVAILABILITY
# =========================================================

def get_all_availability(
    solar_data: Optional[Dict[str, Any]] = None,
    wind_data: Optional[Dict[str, Any]] = None,
    biomass: Optional[Dict[str, Any]] = None,
    waste: Optional[Dict[str, Any]] = None,
) -> Dict[str, ResourceAvailability]:
    """Return ResourceAvailability for every resource type.

    Args:
        solar_data: Live solar forecast output (or None).
        wind_data: Live wind forecast output (or None).
        biomass: Biomass info dict (or None).
        waste: Waste info dict (or None).

    Returns:
        Dict keyed by lowercase resource name.
    """
    return {
        "solar": get_solar_availability(solar_data),
        "wind": get_wind_availability(wind_data),
        "hydro": get_hydro_availability(),
        "biomass": get_biomass_availability(biomass),
        "waste": get_waste_availability(waste),
        "battery": get_battery_availability(),
        "flexible_demand": get_flexible_demand_availability(),
    }
