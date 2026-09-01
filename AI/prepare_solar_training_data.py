import pandas as pd
from pathlib import Path

# ============================================
# FILE PATHS
# ============================================

input_file = Path(
    "data/raw/bpdb/solar_weather_combined.csv"
)

output_file = Path(
    "data/processed/solar_training_data.csv"
)

# Make sure output folder exists
output_file.parent.mkdir(parents=True, exist_ok=True)


# ============================================
# LOAD DATA
# ============================================

print("Loading combined solar + weather data...")

df = pd.read_csv(input_file)

print("Rows loaded:", len(df))


# ============================================
# CONVERT TIMESTAMP
# ============================================

print("Converting timestamp...")

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
# DAY / NIGHT FEATURE
# ============================================

df["is_daytime"] = (
    df["solar_radiation_wm2"] > 0
).astype(int)


# ============================================
# TARGET
# ============================================

# We are currently estimating solar output
# for 1 MW installed solar capacity.

PERFORMANCE_RATIO = 0.85

df["solar_generation_mw_per_1mw"] = (
    (df["solar_irradiance_wh_m2"] / 1000)
    * PERFORMANCE_RATIO
)

# Prevent negative values
df["solar_generation_mw_per_1mw"] = (
    df["solar_generation_mw_per_1mw"].clip(lower=0)
)


# ============================================
# SELECT AI FEATURES
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

target = "solar_generation_mw_per_1mw"


# ============================================
# CREATE TRAINING DATASET
# ============================================

training_df = df[
    features + [target]
].copy()


# ============================================
# REMOVE INVALID DATA
# ============================================

training_df = training_df.dropna()

training_df = training_df[
    training_df["solar_generation_mw_per_1mw"] >= 0
]


# ============================================
# SAVE
# ============================================

training_df.to_csv(
    output_file,
    index=False
)


# ============================================
# REPORT
# ============================================

print("--------------------------------------------")
print("Solar AI training dataset created!")
print("Rows:", len(training_df))
print("Columns:", len(training_df.columns))
print("Saved to:", output_file)
print("--------------------------------------------")

print("\nTraining columns:")

for column in training_df.columns:
    print("-", column)

print("\nFirst 10 rows:")

print(
    training_df.head(10).to_string(index=False)
)