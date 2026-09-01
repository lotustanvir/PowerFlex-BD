import pandas as pd
import joblib
from pathlib import Path


# ============================================
# FILE PATHS
# ============================================

MODEL_FILE = Path("models/weather_only_solar_model.pkl")

FORECAST_FILE = Path(
    "data/raw/bpdb/weather_forecast_24h.csv"
)

OUTPUT_FILE = Path(
    "data/processed/weather_only_solar_forecast_24h.csv"
)


# ============================================
# LOAD MODEL
# ============================================

print("Loading Weather-Only Solar AI model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully!")


# ============================================
# LOAD WEATHER FORECAST
# ============================================

print("\nLoading real 24-hour weather forecast...")

df = pd.read_csv(FORECAST_FILE)

print("Forecast rows:", len(df))


# ============================================
# CONVERT TIMESTAMP
# ============================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)


# ============================================
# TIME FEATURES
# ============================================

df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day
df["month"] = df["timestamp"].dt.month
df["day_of_week"] = df["timestamp"].dt.dayofweek


# ============================================
# DAYTIME
# ============================================

df["is_daytime"] = (
    (df["hour"] >= 6) &
    (df["hour"] <= 18)
).astype(int)


# ============================================
# MODEL FEATURES
# ============================================

features = [
    "zone",
    "latitude",
    "longitude",
    "temperature_c",
    "humidity_percent",
    "precipitation_mm",
    "cloud_cover_percent",
    "wind_speed_kmh",
    "wind_direction_degree",
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_daytime"
]


# ============================================
# MAKE PREDICTIONS
# ============================================

print("\nPredicting solar generation...")

X = df[features]

predictions = model.predict(X)

# Remove negative predictions
predictions = predictions.clip(min=0)

df["predicted_generation_mw_per_1mw"] = predictions


# ============================================
# NIGHT OUTPUT CORRECTION
# ============================================
# If solar radiation forecast is zero,
# actual solar generation should be zero.
#
# NOTE:
# This does NOT enter the AI model.
# It is a physical post-processing rule.

df.loc[
    df["solar_radiation_wm2"] <= 0,
    "predicted_generation_mw_per_1mw"
] = 0


# ============================================
# SAVE RESULTS
# ============================================

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================
# DISPLAY RESULTS
# ============================================

print("\n==============================================")
print(" POWERFLEX BD - WEATHER-ONLY SOLAR FORECAST")
print("==============================================")

print(
    df[
        [
            "zone",
            "timestamp",
            "temperature_c",
            "cloud_cover_percent",
            "precipitation_mm",
            "predicted_generation_mw_per_1mw"
        ]
    ].head(40).to_string(index=False)
)


# ============================================
# BEST HOURLY OPPORTUNITY
# ============================================

best_row = df.loc[
    df["predicted_generation_mw_per_1mw"].idxmax()
]

print("\n==============================================")
print("        BEST SOLAR OPPORTUNITY")
print("==============================================")

print("Zone:", best_row["zone"])
print("Time:", best_row["timestamp"])

print(
    "Predicted generation:",
    round(
        best_row["predicted_generation_mw_per_1mw"],
        4
    ),
    "MW per 1 MW capacity"
)


# ============================================
# BEST DAILY ZONE
# ============================================

daily = (
    df.groupby("zone")[
        "predicted_generation_mw_per_1mw"
    ]
    .sum()
    .reset_index()
)

daily = daily.sort_values(
    "predicted_generation_mw_per_1mw",
    ascending=False
)

daily["rank"] = range(
    1,
    len(daily) + 1
)

daily = daily.rename(
    columns={
        "predicted_generation_mw_per_1mw":
        "expected_energy_mwh_per_1mw_24h"
    }
)

print("\n==============================================")
print("         DAILY SOLAR ZONE RANKING")
print("==============================================")

print(
    daily.to_string(index=False)
)


# ============================================
# SAVE DAILY RANKING
# ============================================

daily.to_csv(
    "data/processed/weather_only_solar_zone_ranking.csv",
    index=False
)


print("\n----------------------------------------------")
print("Forecast completed successfully!")
print("Total predictions:", len(df))
print("Forecast file:", OUTPUT_FILE)
print("Zone ranking: data/processed/weather_only_solar_zone_ranking.csv")
print("----------------------------------------------")