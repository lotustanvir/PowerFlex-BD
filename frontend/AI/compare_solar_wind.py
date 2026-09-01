import pandas as pd
from pathlib import Path


# ============================================
# FILE PATHS
# ============================================

SOLAR_FILE = Path(
    "data/raw/bpdb/solar_zone_summary.csv"
)

WIND_FILE = Path(
    "data/processed/wind_zone_summary.csv"
)

OUTPUT_FILE = Path(
    "data/processed/renewable_zone_comparison.csv"
)


# ============================================
# LOAD DATA
# ============================================

print("Loading solar summary...")
solar = pd.read_csv(SOLAR_FILE)

print("Loading wind summary...")
wind = pd.read_csv(WIND_FILE)


# ============================================
# SELECT REQUIRED COLUMNS
# ============================================

solar = solar[
    [
        "zone",
        "average_generation_mw_per_1mw"
    ]
].rename(
    columns={
        "average_generation_mw_per_1mw":
        "solar_avg_generation_mw_per_1mw"
    }
)

wind = wind[
    [
        "zone",
        "average_generation_mw_per_1mw"
    ]
].rename(
    columns={
        "average_generation_mw_per_1mw":
        "wind_avg_generation_mw_per_1mw"
    }
)


# ============================================
# MERGE SOLAR + WIND
# ============================================

comparison = pd.merge(
    solar,
    wind,
    on="zone",
    how="inner"
)


# ============================================
# DETERMINE BEST RESOURCE
# ============================================

comparison["best_resource"] = comparison.apply(
    lambda row:
        "Solar"
        if row["solar_avg_generation_mw_per_1mw"]
        > row["wind_avg_generation_mw_per_1mw"]
        else "Wind",
    axis=1
)


# ============================================
# RENEWABLE RESOURCE SCORE
# ============================================
# This is NOT a national suitability score.
# It is only a simple comparison indicator
# based on our current simulated potentials.

comparison["combined_resource_score"] = (
    comparison["solar_avg_generation_mw_per_1mw"]
    + comparison["wind_avg_generation_mw_per_1mw"]
) / 2


# ============================================
# SORT
# ============================================

comparison = comparison.sort_values(
    "combined_resource_score",
    ascending=False
).reset_index(drop=True)

comparison["overall_rank"] = range(
    1,
    len(comparison) + 1
)


# ============================================
# SAVE
# ============================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

comparison.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================
# DISPLAY
# ============================================

print("\n==============================================")
print(" POWERFLEX BD - SOLAR + WIND COMPARISON")
print("==============================================\n")

print(
    comparison.to_string(index=False)
)


# ============================================
# BEST ZONE
# ============================================

best = comparison.iloc[0]

print("\n==============================================")
print("          BEST COMBINED RENEWABLE ZONE")
print("==============================================")

print("Zone:", best["zone"])

print(
    "Solar potential:",
    round(
        best["solar_avg_generation_mw_per_1mw"],
        4
    )
)

print(
    "Wind potential:",
    round(
        best["wind_avg_generation_mw_per_1mw"],
        4
    )
)

print(
    "Best individual resource:",
    best["best_resource"]
)

print(
    "Combined resource score:",
    round(
        best["combined_resource_score"],
        4
    )
)

print("==============================================")

print("\nSaved as:")
print(OUTPUT_FILE)