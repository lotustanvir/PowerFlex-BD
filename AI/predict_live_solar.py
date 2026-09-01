import pandas as pd
import joblib
from pathlib import Path


# ============================================
# FILE PATHS
# ============================================

MODEL_FILE = Path(
    "models/weather_only_solar_model.pkl"
)

FORECAST_FILE = Path(
    "data/raw/bpdb/live_forecast.csv"
)

OUTPUT_FILE = Path(
    "data/processed/live_solar_prediction.csv"
)

RANKING_FILE = Path(
    "data/processed/live_solar_ranking.csv"
)


# ============================================
# LOAD MODEL
# ============================================

print("Loading Weather-Only Solar AI model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully!")


# ============================================
# LOAD LIVE FORECAST
# ============================================

print("\nLoading latest forecast data...")

df = pd.read_csv(FORECAST_FILE)

print("Forecast rows:", len(df))


# ============================================
# TIME FEATURES
# ============================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

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
# AI INPUT FEATURES
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


X = df[features]


# ============================================
# AI PREDICTION
# ============================================

print("\nRunning Solar AI predictions...")

predictions = model.predict(X)

# Never allow negative solar output
predictions = predictions.clip(min=0)

df["predicted_generation_mw_per_1mw"] = predictions


# ============================================
# NIGHT CORRECTION
# ============================================
# If forecasted solar radiation is essentially zero,
# solar generation should be zero.

df.loc[
    df["solar_radiation_wm2"] <= 0,
    "predicted_generation_mw_per_1mw"
] = 0


# ============================================
# SAVE HOURLY PREDICTIONS
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
# DAILY ZONE RANKING
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
).reset_index(drop=True)

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


# ============================================
# BEST HOUR
# ============================================

best_hour = df.loc[
    df["predicted_generation_mw_per_1mw"].idxmax()
]


# ============================================
# SAVE RANKING
# ============================================

daily.to_csv(
    RANKING_FILE,
    index=False
)


# ============================================
# DISPLAY
# ============================================

print("\n==============================================")
print(" POWERFLEX BD - LIVE SOLAR AI FORECAST")
print("==============================================")

print("\nBest hourly opportunity:")
print(
    "Zone:",
    best_hour["zone"]
)

print(
    "Time:",
    best_hour["timestamp"]
)

print(
    "Predicted generation:",
    round(
        best_hour[
            "predicted_generation_mw_per_1mw"
        ],
        4
    ),
    "MW per 1 MW capacity"
)


print("\n==============================================")
print("        24-HOUR ZONE RANKING")
print("==============================================")

print(
    daily.to_string(index=False)
)


print("\n----------------------------------------------")
print("Live Solar AI prediction completed!")
print("Hourly predictions:", len(df))
print("Prediction file:", OUTPUT_FILE)
print("Ranking file:", RANKING_FILE)
print("----------------------------------------------")