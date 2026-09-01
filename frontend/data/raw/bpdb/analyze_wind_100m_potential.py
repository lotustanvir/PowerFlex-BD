import pandas as pd
from pathlib import Path


# ============================================
# PROJECT ROOT
# ============================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]


# ============================================
# FILE PATHS
# ============================================

INPUT_FILE = (
    PROJECT_ROOT /
    "wind_generation_100m_potential.csv"
)

OUTPUT_FILE = (
    PROJECT_ROOT /
    "data" /
    "processed" /
    "wind_100m_zone_summary.csv"
)


# ============================================
# LOAD DATA
# ============================================

print("Loading 100m wind generation data...")

df = pd.read_csv(INPUT_FILE)

print("Total rows:", len(df))


# ============================================
# VALIDATION
# ============================================

required_columns = [
    "zone",
    "wind_speed_100m_kmh",
    "wind_generation_mw_per_1mw"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        "Missing required columns: "
        + ", ".join(missing_columns)
    )


# ============================================
# ZONE-WISE ANALYSIS
# ============================================

summary = (
    df.groupby("zone")
    .agg(
        average_wind_speed_100m_kmh=(
            "wind_speed_100m_kmh",
            "mean"
        ),

        maximum_wind_speed_100m_kmh=(
            "wind_speed_100m_kmh",
            "max"
        ),

        average_generation_mw_per_1mw=(
            "wind_generation_mw_per_1mw",
            "mean"
        ),

        maximum_generation_mw_per_1mw=(
            "wind_generation_mw_per_1mw",
            "max"
        )
    )
    .reset_index()
)


# ============================================
# RANK ZONES
# ============================================

summary = summary.sort_values(
    "average_generation_mw_per_1mw",
    ascending=False
).reset_index(drop=True)


summary["rank"] = range(
    1,
    len(summary) + 1
)


# ============================================
# MODELED CAPACITY FACTOR
# ============================================

summary["modeled_capacity_factor_pct"] = (
    summary["average_generation_mw_per_1mw"]
    * 100
)


# ============================================
# COLUMN ORDER
# ============================================

summary = summary[
    [
        "rank",
        "zone",

        "average_wind_speed_100m_kmh",
        "maximum_wind_speed_100m_kmh",

        "average_generation_mw_per_1mw",
        "maximum_generation_mw_per_1mw",

        "modeled_capacity_factor_pct"
    ]
]


# ============================================
# SAVE RESULT
# ============================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

summary.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================
# DISPLAY
# ============================================

print("\n==============================================")
print("   POWERFLEX BD - 100m WIND ZONE ANALYSIS")
print("==============================================\n")

print(
    summary.to_string(index=False)
)


# ============================================
# BEST ZONE
# ============================================

best_zone = summary.iloc[0]

print("\n==============================================")
print("          BEST MODELED WIND ZONE")
print("==============================================")

print(
    "Zone:",
    best_zone["zone"]
)

print(
    "Average 100m wind speed:",
    round(
        best_zone[
            "average_wind_speed_100m_kmh"
        ],
        2
    ),
    "km/h"
)

print(
    "Average modeled generation:",
    round(
        best_zone[
            "average_generation_mw_per_1mw"
        ],
        4
    ),
    "MW per 1 MW capacity"
)

print(
    "Modeled capacity factor:",
    round(
        best_zone[
            "modeled_capacity_factor_pct"
        ],
        2
    ),
    "%"
)

print("==============================================")


print("\nSaved as:")
print(OUTPUT_FILE)