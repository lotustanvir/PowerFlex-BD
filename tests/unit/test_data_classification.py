"""Unit tests for the data classification system."""

import pytest
from backend.data_classification import (
    DataClassification,
    normalize_classification,
    wrap_with_provenance,
    create_unavailable,
    CLASSIFICATION_DISPLAY,
    LEGACY_CLASSIFICATION_MAP,
)


class TestDataClassification:
    """Test the DataClassification enum."""

    def test_all_classifications_exist(self):
        """Verify all required classifications are defined."""
        required = [
            "OFFICIAL", "MEASURED", "LIVE_FEED", "DELAYED",
            "FORECAST", "CALCULATED", "POTENTIAL", "SCENARIO",
            "PROJECT", "UNDER_CONSTRUCTION", "UNDER_COMMISSIONING",
            "EXPERIMENTAL", "PROTOTYPE", "DATA_UNAVAILABLE", "UNKNOWN",
        ]
        for name in required:
            assert hasattr(DataClassification, name)

    def test_classification_is_string_enum(self):
        """Classifications should be usable as strings."""
        assert DataClassification.FORECAST == "FORECAST"
        assert DataClassification.OFFICIAL == "OFFICIAL"


class TestNormalizeClassification:
    """Test legacy classification normalization."""

    def test_official_pgcb_maps_to_official(self):
        result = normalize_classification("OFFICIAL_PGCB")
        assert result == DataClassification.OFFICIAL

    def test_live_maps_to_live_feed(self):
        result = normalize_classification("LIVE")
        assert result == DataClassification.LIVE_FEED

    def test_model_forecast_maps_to_forecast(self):
        result = normalize_classification("MODEL_FORECAST")
        assert result == DataClassification.FORECAST

    def test_calculated_maps_to_calculated(self):
        result = normalize_classification("CALCULATED_FROM_OFFICIAL_DATA")
        assert result == DataClassification.CALCULATED

    def test_prototype_maps_to_prototype(self):
        result = normalize_classification("PROTOTYPE")
        assert result == DataClassification.PROTOTYPE

    def test_unknown_raw_maps_to_unknown(self):
        result = normalize_classification("SOME_RANDOM_VALUE")
        assert result == DataClassification.UNKNOWN

    def test_none_maps_to_unknown(self):
        result = normalize_classification(None)
        assert result == DataClassification.UNKNOWN

    def test_case_insensitive(self):
        result = normalize_classification("official")
        assert result == DataClassification.OFFICIAL


class TestWrapWithProvenance:
    """Test provenance metadata wrapping."""

    def test_basic_wrap(self):
        result = wrap_with_provenance(
            value=123.45,
            unit="MW",
            classification=DataClassification.FORECAST,
            source="Test Source",
        )
        assert result["value"] == 123.45
        assert result["unit"] == "MW"
        assert result["classification"] == "FORECAST"
        assert result["source"] == "Test Source"
        assert result["timestamp"] is not None

    def test_wrap_with_all_metadata(self):
        result = wrap_with_provenance(
            value=100,
            unit="MWh",
            classification=DataClassification.CALCULATED,
            source="Engineering Model",
            timestamp="2025-01-01T00:00:00Z",
            last_verified="2025-01-01T00:00:00Z",
            confidence=0.85,
            methodology="Power curve lookup",
        )
        assert result["confidence"] == 0.85
        assert result["methodology"] == "Power curve lookup"
        assert result["last_verified"] == "2025-01-01T00:00:00Z"

    def test_wrap_includes_display_info(self):
        result = wrap_with_provenance(
            value=0,
            unit="MW",
            classification=DataClassification.DATA_UNAVAILABLE,
            source="Failed Source",
        )
        assert "classification_display" in result
        assert "classification_badge_color" in result
        assert "classification_icon" in result


class TestCreateUnavailable:
    """Test DATA_UNAVAILABLE response creation."""

    def test_unavailable_has_null_value(self):
        result = create_unavailable(
            unit="MW",
            source="Test Source",
            reason="Connection failed",
        )
        assert result["value"] is None
        assert result["classification"] == "DATA_UNAVAILABLE"
        assert result["error"] == "Connection failed"

    def test_unavailable_has_source(self):
        result = create_unavailable(
            unit="MW",
            source="PGCB ERP",
        )
        assert result["source"] == "PGCB ERP"


class TestClassificationDisplay:
    """Test classification display metadata."""

    def test_all_classifications_have_display(self):
        for cls in DataClassification:
            assert cls in CLASSIFICATION_DISPLAY, f"Missing display for {cls}"

    def test_display_has_required_fields(self):
        for cls, display in CLASSIFICATION_DISPLAY.items():
            assert "label" in display
            assert "badge_color" in display
            assert "icon" in display
            assert "description" in display
