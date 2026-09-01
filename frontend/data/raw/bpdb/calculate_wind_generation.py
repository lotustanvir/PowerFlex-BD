import sys
from pathlib import Path

import pandas as pd


# ============================================
# PROJECT PATH
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
AI_FOLDER = PROJECT_ROOT / "AI"

if str(AI_FOLDER) not in sys.path:
    sys.path.insert(0, str(AI_FOLDER))


# ============================================
# SHARED WIND POWER CURVE
# ============================================

from wind_power_curve import wind_power_curve


# ============================================
# FILES
# ============================================

INPUT_FILE = (
    PROJECT_ROOT /
    "wind_weather_100m_real.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT /
    "wind_generation_100m_potential.csv"
)


# ============================================
# LOAD WIND DATA
# ============================================

print("==============================================")
print("   POWERFLEX BD - 100m WIND GENERATION")
print("==============================================")

print("\nLoading 100m wind data...")

df = pd.read_csv(INPUT_FILE)

print("Total rows:", len(df))


# ============================================
# VALIDATE REQUIRED COLUMN
# ============================================

REQUIRED_COLUMN = "wind_speed_100m_kmh"

if REQUIRED_COLUMN not in df.columns:

    raise ValueError(
        f"Required column '{REQUIRED_COLUMN}' "
        "was not found in the input dataset."
    )


# ============================================
# CALCULATE GENERATION
# ============================================

print("\nCalculating 100m wind generation potential...")

df["wind_generation_mw_per_1mw"] = (
    df[REQUIRED_COLUMN]
    .apply(wind_power_curve)
)


# ============================================
# SAVE
# ============================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================
# STATISTICS
# ============================================

print("\n==============================================")
print("      100m WIND GENERATION STATISTICS")
print("==============================================")

print(
    df["wind_generation_mw_per_1mw"]
    .describe()
)


# ============================================
# FIRST 20 ROWS
# ============================================

print("\n========== FIRST 20 ROWS ==========\n")

print(
    df[
        [
            "zone",
            "timestamp",
            "wind_speed_100m_kmh",
            "wind_generation_mw_per_1mw"
        ]
    ]
    .head(20)
    .to_string(index=False)
)


# ============================================
# ZONE SUMMARY
# ============================================

print("\n========== ZONE SUMMARY ==========\n")

zone_summary = (
    df.groupby("zone")[
        "wind_generation_mw_per_1mw"
    ]
    .agg(
        mean_generation_mw_per_1mw="mean",
        max_generation_mw_per_1mw="max"
    )
    .reset_index()
)

zone_summary = zone_summary.sort_values(
    "mean_generation_mw_per_1mw",
    ascending=False
)

print(
    zone_summary.to_string(index=False)
)


# ============================================
# RESULT
# ============================================

print("\n----------------------------------------------")
print("100m wind generation calculation completed!")
print("Output file:", OUTPUT_FILE)
print("----------------------------------------------")