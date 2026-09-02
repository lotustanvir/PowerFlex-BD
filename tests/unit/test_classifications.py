"""Unit tests for solar and wind data classification."""

import pytest
from backend.data_classification import DataClassification


class TestSolarClassification:
    """Test that solar endpoints return correct classifications."""

    def test_solar_forecast_classification(self):
        """Solar forecasts should be classified as FORECAST."""
        classification = DataClassification.FORECAST
        assert classification == "FORECAST"

    def test_solar_not_live(self):
        """Solar should never be classified as LIVE_FEED."""
        classification = DataClassification.FORECAST
        assert classification != DataClassification.LIVE_FEED

    def test_solar_not_measured(self):
        """Solar should never be classified as MEASURED."""
        classification = DataClassification.FORECAST
        assert classification != DataClassification.MEASURED


class TestWindClassification:
    """Test that wind endpoints return correct classifications."""

    def test_wind_calculated_classification(self):
        """Wind should be classified as CALCULATED."""
        classification = DataClassification.CALCULATED
        assert classification == "CALCULATED"

    def test_wind_not_live(self):
        """Wind should never be classified as LIVE_FEED."""
        classification = DataClassification.CALCULATED
        assert classification != DataClassification.LIVE_FEED

    def test_wind_not_measured(self):
        """Wind should never be classified as MEASURED."""
        classification = DataClassification.CALCULATED
        assert classification != DataClassification.MEASURED


class TestDemandClassification:
    """Test that demand forecasts return correct classifications."""

    def test_demand_forecast_classification(self):
        """Demand forecasts should be classified as FORECAST."""
        classification = DataClassification.FORECAST
        assert classification == "FORECAST"

    def test_demand_synthetic_warning(self):
        """Demand forecasts trained on synthetic data should be EXPERIMENTAL."""
        classification = DataClassification.EXPERIMENTAL
        assert classification == "EXPERIMENTAL"


class TestResourceClassification:
    """Test that resource types have correct classifications."""

    def test_pgcb_grid_is_official(self):
        """PGCB grid data should be OFFICIAL."""
        classification = DataClassification.OFFICIAL
        assert classification == "OFFICIAL"

    def test_biomass_potential_is_calculated(self):
        """Biomass potential should be CALCULATED."""
        classification = DataClassification.CALCULATED
        assert classification == "CALCULATED"

    def test_battery_is_prototype(self):
        """Battery assumptions should be PROTOTYPE."""
        classification = DataClassification.PROTOTYPE
        assert classification == "PROTOTYPE"

    def test_nuclear_under_commissioning(self):
        """Nuclear (Rooppur) should be UNDER_COMMISSIONING."""
        classification = DataClassification.UNDER_COMMISSIONING
        assert classification == "UNDER_COMMISSIONING"
