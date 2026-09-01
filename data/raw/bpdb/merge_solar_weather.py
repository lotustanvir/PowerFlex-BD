import pandas as pd

# ==============================
# FILE NAMES
# ==============================

solar_file = "solar_resources_real.csv"
weather_file = "weather_real.csv"

output_file = "solar_weather_combined.csv"


# ==============================
# LOAD DATA
# ==============================

print("Loading solar data...")
solar_df = pd.read_csv(solar_file)

print("Loading weather data...")
weather_df = pd.read_csv(weather_file)


# ==============================
# CONVERT TIMESTAMP
# ==============================

print("Converting timestamps...")

# Solar timestamp example:
# 2024010100
# Convert it to:
# 2024-01-01 00:00:00

solar_df["timestamp"] = pd.to_datetime(
    solar_df["timestamp"].astype(str),
    format="%Y%m%d%H"
)

# Weather timestamp example:
# 2024-01-01T00:00
# Convert to datetime
weather_df["timestamp"] = pd.to_datetime(
    weather_df["timestamp"]
)


# ==============================
# KEEP REQUIRED WEATHER COLUMNS
# ==============================

weather_df = weather_df[
    [
        "zone",
        "timestamp",
        "temperature_c",
        "humidity_percent",
        "precipitation_mm",
        "cloud_cover_percent",
        "wind_speed_kmh",
        "wind_direction_degree",
        "solar_radiation_wm2"
    ]
]


# ==============================
# MERGE
# ==============================

print("Merging solar + weather data...")

combined_df = pd.merge(
    solar_df,
    weather_df,
    on=["zone", "timestamp"],
    how="inner"
)


# ==============================
# REMOVE DUPLICATES
# ==============================

combined_df = combined_df.drop_duplicates(
    subset=["zone", "timestamp"]
)


# ==============================
# SORT
# ==============================

combined_df = combined_df.sort_values(
    by=["zone", "timestamp"]
)


# ==============================
# SAVE
# ==============================

combined_df.to_csv(
    output_file,
    index=False
)


# ==============================
# RESULT
# ==============================

print("--------------------------------")
print("Solar + Weather merge completed!")
print("Solar rows:", len(solar_df))
print("Weather rows:", len(weather_df))
print("Combined rows:", len(combined_df))
print("Output file:", output_file)
print("--------------------------------")

print("\nFirst 10 combined rows:\n")

print(
    combined_df.head(10).to_string(index=False)
)