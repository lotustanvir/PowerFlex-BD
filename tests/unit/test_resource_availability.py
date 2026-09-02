"""Unit tests for the Resource Availability Engine."""

import json
import pytest
from backend.resource_availability import (
    ResourceAvailability,
    get_solar_availability,
    get_wind_availability,
    get_biomass_availability,
    get_waste_availability,
    get_hydro_availability,
    get_nuclear_availability,
    get_battery_availability,
    get_flexible_demand_availability,
    get_all_availability,
    FORECAST,
    CALCULATED,
    SCENARIO,
    DATA_UNAVAILABLE,
    UNDER_COMMISSIONING,
    SCIENTIFIC_DISCLAIMER,
)


# =========================================================
# RESOURCE AVAILABILITY DATACLASS
# =========================================================

class TestResourceAvailabilityDataclass:

    def test_has_all_required_fields(self):
        ra = ResourceAvailability(
            resource_name="Test",
            installed_capacity_mw=100.0,
            measured_mw=None,
            forecast_mw=50.0,
            available_mw=50.0,
            potential_mw=100.0,
            scenario_mw=0.0,
            classification="FORECAST",
            source="Test Source",
            timestamp="2026-01-01T00:00:00Z",
            confidence=0.8,
            is_dispatchable=True,
            dispatch_note="Test note",
        )
        assert ra.resource_name == "Test"
        assert ra.installed_capacity_mw == 100.0
        assert ra.measured_mw is None
        assert ra.forecast_mw == 50.0
        assert ra.available_mw == 50.0
        assert ra.potential_mw == 100.0
        assert ra.scenario_mw == 0.0
        assert ra.classification == "FORECAST"
        assert ra.source == "Test Source"
        assert ra.timestamp == "2026-01-01T00:00:00Z"
        assert ra.confidence == 0.8
        assert ra.is_dispatchable is True
        assert ra.dispatch_note == "Test note"

    def test_to_dict_returns_all_keys(self):
        ra = ResourceAvailability(
            resource_name="X",
            installed_capacity_mw=0.0,
            measured_mw=None,
            forecast_mw=None,
            available_mw=0.0,
            potential_mw=0.0,
            scenario_mw=0.0,
            classification="DATA_UNAVAILABLE",
            source="none",
            timestamp=None,
            confidence=None,
            is_dispatchable=False,
            dispatch_note="none",
        )
        d = ra.to_dict()
        expected_keys = {
            "resource_name", "installed_capacity_mw",
            "measured_mw", "forecast_mw", "available_mw",
            "potential_mw", "scenario_mw", "classification",
            "source", "timestamp", "confidence",
            "is_dispatchable", "dispatch_note",
        }
        assert set(d.keys()) == expected_keys

    def test_to_dict_is_json_serializable(self):
        ra = ResourceAvailability(
            resource_name="JSON",
            installed_capacity_mw=100.0,
            measured_mw=None,
            forecast_mw=42.5,
            available_mw=42.5,
            potential_mw=100.0,
            scenario_mw=0.0,
            classification="FORECAST",
            source="Test",
            timestamp="2026-01-01T00:00:00Z",
            confidence=0.9,
            is_dispatchable=True,
            dispatch_note="Note",
        )
        json_str = json.dumps(ra.to_dict())
        restored = json.loads(json_str)
        assert restored["resource_name"] == "JSON"
        assert restored["forecast_mw"] == 42.5
        assert restored["is_dispatchable"] is True

    def test_summary_contains_resource_name(self):
        ra = ResourceAvailability(
            resource_name="Solar",
            installed_capacity_mw=1000.0,
            measured_mw=None,
            forecast_mw=300.0,
            available_mw=300.0,
            potential_mw=1000.0,
            scenario_mw=0.0,
            classification="FORECAST",
            source="Test",
            timestamp=None,
            confidence=0.7,
            is_dispatchable=True,
            dispatch_note="Test",
        )
        s = ra.summary()
        assert "Solar" in s
        assert "300.0" in s
        assert "DISPATCHABLE" in s


# =========================================================
# SOLAR AVAILABILITY
# =========================================================

class TestSolarAvailability:

    def test_solar_forecast_classification(self):
        solar_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.75,
                "timestamp": "2026-06-15T12:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Dhaka",
                "expected_energy_mwh_per_1mw_24h": 4.5,
            },
        }
        ra = get_solar_availability(solar_data)
        assert ra.classification == FORECAST

    def test_solar_source_mentions_open_meteo(self):
        solar_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.5,
                "timestamp": "2026-06-15T10:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Chittagong",
                "expected_energy_mwh_per_1mw_24h": 3.0,
            },
        }
        ra = get_solar_availability(solar_data)
        assert "Open-Meteo" in ra.source

    def test_solar_none_data_returns_unavailable(self):
        ra = get_solar_availability(None)
        assert ra.classification == DATA_UNAVAILABLE
        assert ra.is_dispatchable is False
        assert ra.available_mw == 0.0

    def test_solar_dispatchable_only_when_forecast_positive(self):
        # Nighttime: 0 MW per 1mw
        solar_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.0,
                "timestamp": "2026-06-15T02:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Dhaka",
                "expected_energy_mwh_per_1mw_24h": 4.0,
            },
        }
        ra = get_solar_availability(solar_data)
        assert ra.is_dispatchable is False

    def test_solar_has_scientific_disclaimer(self):
        ra = get_solar_availability(None)
        assert "DISCLAIMER" in ra.dispatch_note

    def test_solar_never_has_measured_mw(self):
        solar_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.8,
                "timestamp": "2026-06-15T14:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Rajshahi",
                "expected_energy_mwh_per_1mw_24h": 5.0,
            },
        }
        ra = get_solar_availability(solar_data)
        assert ra.measured_mw is None

    def test_solar_available_mw_matches_forecast(self):
        solar_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.6,
                "timestamp": "2026-06-15T11:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Dhaka",
                "expected_energy_mwh_per_1mw_24h": 4.2,
            },
        }
        ra = get_solar_availability(solar_data)
        expected = round(0.6 * 1000.0, 4)
        assert ra.available_mw == expected
        assert ra.forecast_mw == expected


# =========================================================
# WIND AVAILABILITY
# =========================================================

class TestWindAvailability:

    def test_wind_calculated_classification(self):
        wind_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.45,
                "timestamp": "2026-06-15T12:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Cox's Bazar",
                "expected_energy_mwh_per_1mw_24h": 3.2,
            },
        }
        ra = get_wind_availability(wind_data)
        assert ra.classification == CALCULATED

    def test_wind_source_mentions_power_curve(self):
        wind_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.3,
                "timestamp": "2026-06-15T09:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Dhaka",
                "expected_energy_mwh_per_1mw_24h": 2.0,
            },
        }
        ra = get_wind_availability(wind_data)
        assert "Wind Power Curve" in ra.source

    def test_wind_none_data_returns_unavailable(self):
        ra = get_wind_availability(None)
        assert ra.classification == DATA_UNAVAILABLE
        assert ra.is_dispatchable is False

    def test_wind_has_scientific_disclaimer(self):
        ra = get_wind_availability(None)
        assert "DISCLAIMER" in ra.dispatch_note

    def test_wind_never_has_measured_mw(self):
        wind_data = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.5,
                "timestamp": "2026-06-15T12:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Dhaka",
                "expected_energy_mwh_per_1mw_24h": 3.0,
            },
        }
        ra = get_wind_availability(wind_data)
        assert ra.measured_mw is None


# =========================================================
# BIOMASS AVAILABILITY
# =========================================================

class TestBiomassAvailability:

    def test_biomass_not_dispatchable_without_real_data(self):
        ra = get_biomass_availability(None)
        assert ra.is_dispatchable is False

    def test_biomass_unavailable_classification(self):
        ra = get_biomass_availability(None)
        assert ra.classification == DATA_UNAVAILABLE

    def test_biomass_installed_capacity_zero_by_default(self):
        ra = get_biomass_availability(None)
        assert ra.installed_capacity_mw == 0.0

    def test_biomass_with_info_dict(self):
        info = {
            "installed_capacity_mw": 100.0,
            "available_capacity_mw": 50.0,
            "potential_mw": 200.0,
        }
        ra = get_biomass_availability(info)
        assert ra.installed_capacity_mw == 100.0
        assert ra.available_mw == 50.0
        assert ra.potential_mw == 200.0
        assert ra.is_dispatchable is False

    def test_biomass_has_scientific_disclaimer(self):
        ra = get_biomass_availability(None)
        assert "DISCLAIMER" in ra.dispatch_note

    def test_biomass_has_classification_and_source(self):
        ra = get_biomass_availability(None)
        assert ra.classification != ""
        assert ra.source != ""


# =========================================================
# WASTE AVAILABILITY
# =========================================================

class TestWasteAvailability:

    def test_waste_not_dispatchable_under_construction(self):
        ra = get_waste_availability(None)
        assert ra.is_dispatchable is False

    def test_waste_with_capacity_is_under_commissioning(self):
        info = {"installed_capacity_mw": 42.5}
        ra = get_waste_availability(info)
        assert ra.classification == UNDER_COMMISSIONING

    def test_waste_without_capacity_is_unavailable(self):
        ra = get_waste_availability(None)
        assert ra.classification == DATA_UNAVAILABLE

    def test_waste_has_scientific_disclaimer(self):
        ra = get_waste_availability(None)
        assert "DISCLAIMER" in ra.dispatch_note


# =========================================================
# HYDRO AVAILABILITY
# =========================================================

class TestHydroAvailability:

    def test_hydro_unavailable_without_telemetry(self):
        ra = get_hydro_availability()
        assert ra.classification == DATA_UNAVAILABLE

    def test_hydro_installed_capacity_230(self):
        ra = get_hydro_availability()
        assert ra.installed_capacity_mw == 230.0

    def test_hydro_not_dispatchable_without_telemetry(self):
        ra = get_hydro_availability()
        assert ra.is_dispatchable is False

    def test_hydro_has_scientific_disclaimer(self):
        ra = get_hydro_availability()
        assert "DISCLAIMER" in ra.dispatch_note

    def test_hydro_has_classification_and_source(self):
        ra = get_hydro_availability()
        assert ra.classification != ""
        assert ra.source != ""


# =========================================================
# NUCLEAR AVAILABILITY
# =========================================================

class TestNuclearAvailability:

    def test_nuclear_not_dispatchable(self):
        ra = get_nuclear_availability()
        assert ra.is_dispatchable is False

    def test_nuclear_under_commissioning(self):
        ra = get_nuclear_availability()
        assert ra.classification == UNDER_COMMISSIONING

    def test_nuclear_installed_capacity_2400(self):
        ra = get_nuclear_availability()
        assert ra.installed_capacity_mw == 2400.0

    def test_nuclear_available_mw_zero(self):
        ra = get_nuclear_availability()
        assert ra.available_mw == 0.0

    def test_nuclear_has_scientific_disclaimer(self):
        ra = get_nuclear_availability()
        assert "DISCLAIMER" in ra.dispatch_note


# =========================================================
# BATTERY AVAILABILITY
# =========================================================

class TestBatteryAvailability:

    def test_battery_is_scenario_only(self):
        ra = get_battery_availability()
        assert ra.classification == SCENARIO

    def test_battery_not_dispatchable(self):
        ra = get_battery_availability()
        assert ra.is_dispatchable is False

    def test_battery_available_mw_zero(self):
        ra = get_battery_availability()
        assert ra.available_mw == 0.0

    def test_battery_scenario_mw_nonzero(self):
        ra = get_battery_availability()
        assert ra.scenario_mw > 0.0

    def test_battery_has_scientific_disclaimer(self):
        ra = get_battery_availability()
        assert "DISCLAIMER" in ra.dispatch_note

    def test_battery_potential_mw_zero(self):
        """Battery potential is 0 because it's scenario-only."""
        ra = get_battery_availability()
        assert ra.potential_mw == 0.0


# =========================================================
# FLEXIBLE DEMAND AVAILABILITY
# =========================================================

class TestFlexibleDemandAvailability:

    def test_flexible_demand_is_scenario(self):
        ra = get_flexible_demand_availability()
        assert ra.classification == SCENARIO

    def test_flexible_demand_not_dispatchable(self):
        ra = get_flexible_demand_availability()
        assert ra.is_dispatchable is False

    def test_flexible_demand_potential_mw_zero(self):
        ra = get_flexible_demand_availability()
        assert ra.potential_mw == 0.0

    def test_flexible_demand_scenario_mw_nonzero(self):
        ra = get_flexible_demand_availability()
        assert ra.scenario_mw > 0.0

    def test_flexible_demand_has_scientific_disclaimer(self):
        ra = get_flexible_demand_availability()
        assert "DISCLAIMER" in ra.dispatch_note


# =========================================================
# GET ALL AVAILABILITY
# =========================================================

class TestGetAllAvailability:

    def test_all_resources_have_classification_and_source(self):
        result = get_all_availability()
        for name, ra in result.items():
            assert ra.classification != "", (
                f"{name} missing classification"
            )
            assert ra.source != "", (
                f"{name} missing source"
            )

    def test_all_resources_have_dispatch_note(self):
        result = get_all_availability()
        for name, ra in result.items():
            assert ra.dispatch_note != "", (
                f"{name} missing dispatch_note"
            )
            assert "DISCLAIMER" in ra.dispatch_note, (
                f"{name} dispatch_note missing DISCLAIMER"
            )

    def test_returns_seven_resource_types(self):
        result = get_all_availability()
        expected = {
            "solar", "wind", "hydro", "biomass",
            "waste", "battery", "flexible_demand",
        }
        assert set(result.keys()) == expected

    def test_potential_never_treated_as_dispatchable(self):
        """Ensure no resource with only potential data is dispatchable."""
        result = get_all_availability()
        for name, ra in result.items():
            if ra.available_mw == 0.0 and ra.forecast_mw is None:
                assert ra.is_dispatchable is False, (
                    f"{name} should not be dispatchable "
                    f"with only potential data"
                )

    def test_passing_data_through(self):
        solar = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.7,
                "timestamp": "2026-06-15T12:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Dhaka",
                "expected_energy_mwh_per_1mw_24h": 4.0,
            },
        }
        wind = {
            "current_hour_generation": {
                "mw_per_1mw_installed": 0.4,
                "timestamp": "2026-06-15T12:00:00+06:00",
            },
            "best_forecast_zone": {
                "zone": "Rajshahi",
                "expected_energy_mwh_per_1mw_24h": 2.5,
            },
        }
        result = get_all_availability(
            solar_data=solar, wind_data=wind
        )
        assert result["solar"].available_mw == round(
            0.7 * 1000.0, 4
        )
        assert result["wind"].available_mw == round(
            0.4 * 500.0, 4
        )
        assert result["solar"].is_dispatchable is True
        assert result["wind"].is_dispatchable is True

    def test_all_values_json_serializable(self):
        result = get_all_availability()
        serializable = {
            k: v.to_dict() for k, v in result.items()
        }
        json_str = json.dumps(serializable)
        restored = json.loads(json_str)
        assert len(restored) == 7
