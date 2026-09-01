import requests
import pandas as pd
from pathlib import Path


# ============================================
# BANGLADESH LOCATIONS
# ============================================

LOCATIONS = {
    "Dhaka": (23.8103, 90.4125),
    "Chittagong": (22.3569, 91.7832),
    "Khulna": (22.8456, 89.5403),
    "Rajshahi": (24.3745, 88.6042),
    "Comilla": (23.4607, 91.1809),
    "Mymensingh": (24.7471, 90.4203),
    "Sylhet": (24.8949, 91.8687),
    "Barishal": (22.7010, 90.3535),
    "Rangpur": (25.7439, 89.2752),
}


OUTPUT_FILE = Path(
    "data/raw/bpdb/live_forecast.csv"
)


# ============================================
# FETCH FORECAST
# ============================================

rows = []

for zone, (latitude, longitude) in LOCATIONS.items():

    print(f"Fetching current forecast for {zone}...")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m"
        ]),

        "hourly": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "cloud_cover",
            "wind_speed_10m",
            "wind_direction_10m",
            "shortwave_radiation"
        ]),

        "forecast_hours": 24,

        "timezone": "Asia/Dhaka"
    }

    response = requests.get(
        url,
        params=params,
        timeout=60
    )

    print("Status:", response.status_code)

    response.raise_for_status()

    data = response.json()

    hourly = data["hourly"]

    for i in range(len(hourly["time"])):

        rows.append({
            "zone": zone,
            "latitude": latitude,
            "longitude": longitude,
            "timestamp": hourly["time"][i],
            "temperature_c": hourly["temperature_2m"][i],
            "humidity_percent": hourly["relative_humidity_2m"][i],
            "precipitation_mm": hourly["precipitation"][i],
            "cloud_cover_percent": hourly["cloud_cover"][i],
            "wind_speed_kmh": hourly["wind_speed_10m"][i],
            "wind_direction_degree": hourly["wind_direction_10m"][i],
            "solar_radiation_wm2": hourly["shortwave_radiation"][i]
        })


# ============================================
# SAVE
# ============================================

df = pd.DataFrame(rows)

OUTPUT_FILE.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================
# RESULT
# ============================================

print("\n============================================")
print("POWERFLEX BD - LIVE FORECAST DATA")
print("============================================")

print("Total rows:", len(df))
print("Locations:", df["zone"].nunique())
print("Output:", OUTPUT_FILE)

print("\nFirst 10 rows:")
print(
    df.head(10).to_string(index=False)
)

print("\n============================================")
print("Forecast fetch completed!")
print("============================================")