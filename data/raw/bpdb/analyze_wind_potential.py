import pandas as pd
from pathlib import Path


# ============================================
# FILE PATHS
# ============================================

INPUT_FILE = Path(
    "wind_generation_potential.csv"
)

OUTPUT_FILE = Path(
    "data/processed/wind_zone_summary.csv"
)


# ============================================
# LOAD DATA
# ============================================

print("Loading wind generation data...")

df = pd.read_csv(INPUT_FILE)

print("Total rows:", len(df))


# ============================================
# ZONE-WISE ANALYSIS
# ============================================

summary = (
    df.groupby("zone")["wind_generation_mw_per_1mw"]
    .agg(
        average_generation_mw_per_1mw="mean",
        maximum_generation_mw_per_1mw="max"
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
print("      POWERFLEX BD - WIND ZONE RANKING")
print("==============================================\n")

print(
    summary.to_string(index=False)
)


# ============================================
# BEST ZONE
# ============================================

best_zone = summary.iloc[0]

print("\n==============================================")
print("             BEST WIND ZONE")
print("==============================================")

print("Zone:", best_zone["zone"])

print(
    "Average generation potential:",
    round(
        best_zone["average_generation_mw_per_1mw"],
        4
    ),
    "MW per 1 MW capacity"
)

print(
    "Maximum generation potential:",
    round(
        best_zone["maximum_generation_mw_per_1mw"],
        4
    ),
    "MW per 1 MW capacity"
)

print("==============================================")

print("\nSaved as:")
print(OUTPUT_FILE)