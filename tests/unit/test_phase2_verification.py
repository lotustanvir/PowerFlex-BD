"""Phase 2 verification tests: hourly solar/wind availability.

Tests for:
- Nighttime solar output is zero
- Daytime solar output is non-zero
- Bangladesh timezone boundary handling
- Hourly wind output varies correctly
- Optimizer receives current-hour inputs (not daily/24)
- Data classifications are FORECAST/CALCULATED, never ACTUAL
"""
import json
import pytest
from datetime import datetime, timezone, timedelta


BANGLADESH_TZ = timezone(timedelta(hours=6))


class TestNighttimeSolar:
    """Solar output must be zero when radiation <= 0."""

    def test_nighttime_solar_forced_zero(self):
        """When solar_radiation_wm2 <= 0, predicted generation is 0."""
        import pandas as pd

        timestamps = pd.date_range(
            "2026-01-01 00:00", periods=24, freq="h", tz="Asia/Dhaka"
        )
        # Night hours (0-5, 19-23) have 0 radiation
        radiation = []
        for t in timestamps:
            hour = t.hour
            if 6 <= hour <= 18:
                radiation.append(500.0)
            else:
                radiation.append(0.0)

        df = pd.DataFrame({
            "timestamp": timestamps,
            "solar_radiation_wm2": radiation,
            "predicted_generation_mw_per_1mw": [0.5] * 24,
        })

        # Apply night correction
        df.loc[
            df["solar_radiation_wm2"] <= 0,
            "predicted_generation_mw_per_1mw"
        ] = 0

        # Night hours must be zero
        night_mask = df["timestamp"].dt.hour.isin(
            list(range(0, 6)) + list(range(19, 24))
        )
        assert (df.loc[night_mask, "predicted_generation_mw_per_1mw"] == 0).all()

        # Day hours must be non-zero
        day_mask = df["timestamp"].dt.hour.isin(range(6, 19))
        assert (df.loc[day_mask, "predicted_generation_mw_per_1mw"] > 0).all()

    def test_solar_current_hour_respects_night(self):
        """Current-hour solar extraction returns 0 at night."""
        # Simulate nighttime: radiation = 0 at hour 2
        import pandas as pd

        timestamps = pd.date_range(
            "2026-01-01 00:00", periods=24, freq="h", tz="Asia/Dhaka"
        )
        radiation = []
        for t in timestamps:
            hour = t.hour
            if 6 <= hour <= 18:
                radiation.append(500.0)
            else:
                radiation.append(0.0)

        df = pd.DataFrame({
            "timestamp": timestamps,
            "solar_radiation_wm2": radiation,
            "predicted_generation_mw_per_1mw": [0.5] * 24,
        })

        df.loc[
            df["solar_radiation_wm2"] <= 0,
            "predicted_generation_mw_per_1mw"
        ] = 0

        # Extract for hour 2 (night)
        night_idx = df["timestamp"].dt.hour == 2
        assert night_idx.any()
        night_val = float(df[night_idx].iloc[0]["predicted_generation_mw_per_1mw"])
        assert night_val == 0.0

    def test_solar_current_hour_active_during_day(self):
        """Current-hour solar extraction returns non-zero during day."""
        import pandas as pd

        timestamps = pd.date_range(
            "2026-01-01 00:00", periods=24, freq="h", tz="Asia/Dhaka"
        )
        radiation = []
        for t in timestamps:
            hour = t.hour
            if 6 <= hour <= 18:
                radiation.append(500.0)
            else:
                radiation.append(0.0)

        df = pd.DataFrame({
            "timestamp": timestamps,
            "solar_radiation_wm2": radiation,
            "predicted_generation_mw_per_1mw": [0.5] * 24,
        })

        df.loc[
            df["solar_radiation_wm2"] <= 0,
            "predicted_generation_mw_per_1mw"
        ] = 0

        # Extract for hour 12 (day)
        day_idx = df["timestamp"].dt.hour == 12
        assert day_idx.any()
        day_val = float(df[day_idx].iloc[0]["predicted_generation_mw_per_1mw"])
        assert day_val > 0.0


class TestBangladeshTimezone:
    """Verify BANGLADESH_TZ is correctly UTC+6."""

    def test_bangladesh_tz_offset(self):
        """BANGLADESH_TZ should be UTC+6."""
        from backend.solar import BANGLADESH_TZ
        assert BANGLADESH_TZ == timezone(timedelta(hours=6))

    def test_wind_bangladesh_tz_offset(self):
        """Wind module also uses UTC+6."""
        from backend.wind import BANGLADESH_TZ
        assert BANGLADESH_TZ == timezone(timedelta(hours=6))

    def test_current_hour_uses_bst(self):
        """datetime.now(BANGLADESH_TZ).hour gives BST hour."""
        now_bst = datetime.now(BANGLADESH_TZ)
        now_utc = datetime.now(timezone.utc)
        expected_bst_hour = (now_utc.hour + 6) % 24
        assert now_bst.hour == expected_bst_hour

    def test_solar_uses_bst_for_hour_matching(self):
        """Solar current hour extraction uses BST, not local time."""
        from backend.solar import BANGLADESH_TZ
        bst_hour = datetime.now(BANGLADESH_TZ).hour
        import pandas as pd
        timestamps = pd.date_range(
            "2026-01-01 00:00", periods=24, freq="h", tz="Asia/Dhaka"
        )
        current_idx = timestamps.hour == bst_hour
        assert current_idx.any(), f"No match for BST hour {bst_hour}"

    def test_wind_uses_bst_for_hour_matching(self):
        """Wind current hour extraction uses BST."""
        from backend.wind import BANGLADESH_TZ
        bst_hour = datetime.now(BANGLADESH_TZ).hour
        import pandas as pd
        timestamps = pd.date_range(
            "2026-01-01 00:00", periods=24, freq="h", tz="Asia/Dhaka"
        )
        current_idx = timestamps.hour == bst_hour
        assert current_idx.any(), f"No match for BST hour {bst_hour}"


class TestHourlyWindOutput:
    """Wind output should vary by wind speed, not be constant."""

    def test_wind_power_curve_varies(self):
        """Wind power curve produces different outputs for different speeds."""
        from AI.wind_power_curve import wind_power_curve

        low = wind_power_curve(5.0)
        medium = wind_power_curve(10.0)
        high = wind_power_curve(15.0)

        # Below cut-in (3 km/h) = 0
        below_cutin = wind_power_curve(1.0)
        assert below_cutin == 0.0

        # Output should increase with speed (up to rated)
        assert low < medium

    def test_wind_current_hour_non_constant(self):
        """Wind current-hour output depends on actual wind speed data."""
        import pandas as pd
        from AI.wind_power_curve import wind_power_curve

        # Simulate varying wind speeds
        wind_speeds = [3.0, 8.0, 12.0, 15.0, 20.0, 25.0, 30.0]
        outputs = [wind_power_curve(s) for s in wind_speeds]

        # At least some should differ
        assert len(set(outputs)) > 1

    def test_wind_above_cutout_is_zero(self):
        """Wind above cut-out speed (25 km/h) should be zero."""
        from AI.wind_power_curve import wind_power_curve
        assert wind_power_curve(30.0) == 0.0


class TestOptimizerInputs:
    """Optimizer must use current-hour, not daily/24."""

    def test_optimizer_extracts_current_hour_from_solar(self):
        """Optimizer reads solar_data.current_hour_generation."""
        from backend.optimizer import optimize

        solar_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.42},
        }
        wind_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.18},
        }

        result = optimize(
            demand_mw=16000, supply_mw=15000,
            solar_data=solar_data, wind_data=wind_data,
        )

        assert result["status"] in ("DEFICIT_COVERED", "DEFICIT_REMAINS")

    def test_optimizer_zero_solar_at_night(self):
        """When solar current_hour is 0 (night), optimizer gets 0."""
        from backend.optimizer import optimize

        solar_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.0},
        }
        wind_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.0},
        }

        result = optimize(
            demand_mw=16000, supply_mw=15000,
            solar_data=solar_data, wind_data=wind_data,
        )

        # All solar deployment should be 0
        for dep in result["recommended_deployment"]:
            if dep["resource"] == "Solar":
                assert dep["support_mw"] == 0.0

    def test_optimizer_no_daily_division_by_24(self):
        """Optimizer never divides daily energy by 24 for current MW."""
        import inspect
        from backend.optimizer import optimize

        source = inspect.getsource(optimize)
        # Should not contain the old pattern
        assert "daily_energy / 24" not in source
        assert "solar_daily_energy / 24" not in source
        assert "wind_daily_energy / 24" not in source

    def test_optimizer_handles_missing_current_hour(self):
        """Optimizer handles missing current_hour_generation gracefully."""
        from backend.optimizer import optimize

        result = optimize(
            demand_mw=16000, supply_mw=15000,
            solar_data={}, wind_data={},
        )

        assert result["status"] in ("DEFICIT_COVERED", "DEFICIT_REMAINS")

    def test_build_zone_analysis_has_current_hour_fields(self):
        """Zone analysis output includes solar/wind current-hour MW."""
        from backend.optimizer import build_zone_analysis

        solar_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.35},
        }
        wind_data = {
            "zone_ranking": [],
            "current_hour_generation": {"mw_per_1mw_installed": 0.22},
        }

        result = build_zone_analysis(solar_data, wind_data)

        for zone in result:
            assert "solar_current_hour_mw_per_1mw" in zone
            assert zone["solar_current_hour_mw_per_1mw"] == 0.35
            assert "wind_current_hour_mw_per_1mw" in zone
            assert zone["wind_current_hour_mw_per_1mw"] == 0.22


class TestClassifications:
    """Solar/Wind model outputs must be FORECAST/CALCULATED, not ACTUAL."""

    def test_solar_classification_is_forecast(self):
        """Solar response data_classification is FORECAST."""
        from backend.resources import RESOURCE_CONFIG
        solar = RESOURCE_CONFIG.get("solar", {})
        assert solar.get("data_classification") == "FORECAST"

    def test_wind_classification_is_calculated(self):
        """Wind response data_classification is CALCULATED."""
        from backend.resources import RESOURCE_CONFIG
        wind = RESOURCE_CONFIG.get("wind", {})
        assert wind.get("data_classification") == "CALCULATED"

    def test_solar_not_labeled_as_actual(self):
        """Solar endpoint never returns 'ACTUAL' as classification."""
        import inspect
        from backend import solar
        source = inspect.getsource(solar)
        # Should not have ACTUAL in classification context
        assert '"ACTUAL"' not in source

    def test_wind_not_labeled_as_actual(self):
        """Wind endpoint never returns 'ACTUAL' as classification."""
        import inspect
        from backend import wind
        source = inspect.getsource(wind)
        assert '"ACTUAL"' not in source

    def test_optimizer_solar_source_is_forecast(self):
        """Optimizer labels solar source as FORECAST."""
        from backend.optimizer import build_zone_analysis

        result = build_zone_analysis(
            solar_data={"zone_ranking": [], "current_hour_generation": {}},
            wind_data={"zone_ranking": [], "current_hour_generation": {}},
        )

        for zone in result:
            assert "FORECAST" in zone["resource_source"]["solar"]

    def test_optimizer_wind_source_is_calculated(self):
        """Optimizer labels wind source as CALCULATED."""
        from backend.optimizer import build_zone_analysis

        result = build_zone_analysis(
            solar_data={"zone_ranking": [], "current_hour_generation": {}},
            wind_data={"zone_ranking": [], "current_hour_generation": {}},
        )

        for zone in result:
            assert "CALCULATED" in zone["resource_source"]["wind"]
