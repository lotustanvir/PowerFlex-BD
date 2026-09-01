import pandas as pd
from pathlib import Path

# ============================================
# FILE PATHS
# ============================================

input_file = Path(
    "data/processed/solar_forecast_24h.csv"
)

output_file = Path(
    "data/processed/solar_forecast_final_24h.csv"
)

summary_file = Path(
    "data/processed/solar_forecast_summary.csv"
)


# ============================================
# LOAD FORECAST DATA
# ============================================

print("Loading 24-hour solar forecast...")

df = pd.read_csv(input_file)

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

print("Total rows:", len(df))


# ============================================
# 1. NIGHT OUTPUT CORRECTION
# ============================================
# Solar output must be zero when solar radiation
# is zero or when the sun is below the useful range.

df.loc[
    df["solar_radiation_wm2"] <= 0,
    "predicted_generation_mw_per_1mw"
] = 0


# Prevent any negative prediction
df["predicted_generation_mw_per_1mw"] = (
    df["predicted_generation_mw_per_1mw"].clip(lower=0)
)


# ============================================
# 2. DATE FEATURE
# ============================================

df["date"] = df["timestamp"].dt.date


# ============================================
# 3. DAILY ENERGY POTENTIAL
# ============================================
# Since each prediction represents an hourly output
# for 1 MW installed capacity, summing the hourly
# values gives approximate daily MWh per MW capacity.

daily_summary = (
    df.groupby("zone")[
        "predicted_generation_mw_per_1mw"
    ]
    .sum()
    .reset_index()
)

daily_summary = daily_summary.rename(
    columns={
        "predicted_generation_mw_per_1mw":
        "expected_energy_mwh_per_1mw_24h"
    }
)

daily_summary = daily_summary.sort_values(
    "expected_energy_mwh_per_1mw_24h",
    ascending=False
)

daily_summary["rank"] = range(
    1,
    len(daily_summary) + 1
)


# ============================================
# 4. BEST SOLAR TIME FOR EACH ZONE
# ============================================

best_times = (
    df.loc[
        df.groupby("zone")[
            "predicted_generation_mw_per_1mw"
        ].idxmax()
    ][
        [
            "zone",
            "timestamp",
            "predicted_generation_mw_per_1mw"
        ]
    ]
    .rename(
        columns={
            "timestamp": "best_time",
            "predicted_generation_mw_per_1mw":
            "peak_generation_mw_per_1mw"
        }
    )
)


# ============================================
# 5. MERGE DAILY + PEAK INFORMATION
# ============================================

summary = pd.merge(
    daily_summary,
    best_times,
    on="zone",
    how="left"
)


# ============================================
# 6. BEST OVERALL ZONE
# ============================================

best_zone = summary.iloc[0]


# ============================================
# 7. SAVE FINAL DATA
# ============================================

df.to_csv(
    output_file,
    index=False
)

summary.to_csv(
    summary_file,
    index=False
)


# ============================================
# 8. DISPLAY RESULTS
# ============================================

print("\n==============================================")
print("       POWERFLEX BD - SOLAR SUMMARY")
print("==============================================")

print(
    summary.to_string(index=False)
)


print("\n==============================================")
print("             BEST SOLAR ZONE")
print("==============================================")

print(
    "Zone:",
    best_zone["zone"]
)

print(
    "24H expected energy:",
    round(
        best_zone[
            "expected_energy_mwh_per_1mw_24h"
        ],
        4
    ),
    "MWh per 1 MW capacity"
)

print(
    "Best time:",
    best_zone["best_time"]
)

print(
    "Peak generation:",
    round(
        best_zone[
            "peak_generation_mw_per_1mw"
        ],
        4
    ),
    "MW per 1 MW capacity"
)

print("==============================================")

print("\nFiles saved:")
print(output_file)
print(summary_file)