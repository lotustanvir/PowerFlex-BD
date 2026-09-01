import pandas as pd
import joblib
from pathlib import Path


# ============================================
# FILE PATHS
# ============================================

MODEL_FILE = Path("models/solar_forecast_model.pkl")

FORECAST_FILE = Path(
    "data/raw/bpdb/weather_forecast_24h.csv"
)

OUTPUT_FILE = Path(
    "data/processed/solar_forecast_24h.csv"
)


# ============================================
# LOAD MODEL
# ============================================

print("Loading Solar AI model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully!")


# ============================================
# LOAD WEATHER FORECAST
# ============================================

print("\nLoading 24-hour weather forecast...")

df = pd.read_csv(FORECAST_FILE)

print("Forecast rows:", len(df))


# ============================================
# TIME FEATURES
# ============================================

df["timestamp"] = pd.to_datetime(df["timestamp"])

df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day
df["month"] = df["timestamp"].dt.month
df["day_of_week"] = df["timestamp"].dt.dayofweek

# Day/night
df["is_daytime"] = (
    df["solar_radiation_wm2"] > 0
).astype(int)


# ============================================
# FEATURES
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
    "solar_radiation_wm2",
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_daytime"
]


# ============================================
# PREPARE INPUT
# ============================================

X = df[features]


# ============================================
# AI PREDICTION
# ============================================

print("\nPredicting solar generation...")

predictions = model.predict(X)

# Solar generation cannot be negative
predictions = predictions.clip(min=0)

df["predicted_generation_mw_per_1mw"] = predictions


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
# SHOW RESULTS
# ============================================

print("\n==============================================")
print("      POWERFLEX BD - 24H SOLAR FORECAST")
print("==============================================")

print(
    df[
        [
            "zone",
            "timestamp",
            "predicted_generation_mw_per_1mw"
        ]
    ].head(30).to_string(index=False)
)

print("\n----------------------------------------------")
print("Forecast completed!")
print("Total predictions:", len(df))
print("Saved as:", OUTPUT_FILE)
print("----------------------------------------------")


# ============================================
# BEST LOCATION
# ============================================

best_row = df.loc[
    df["predicted_generation_mw_per_1mw"].idxmax()
]

print("\n========== BEST SOLAR OPPORTUNITY ==========")

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

print("=============================================")