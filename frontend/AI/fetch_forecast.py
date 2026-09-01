import requests
import csv

# ============================================
# BANGLADESH LOCATIONS
# ============================================

locations = {
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

# ============================================
# OUTPUT FILE
# ============================================

OUTPUT_FILE = "data/raw/bpdb/weather_forecast_24h.csv"

rows = []


# ============================================
# FETCH FORECAST
# ============================================

for zone, (latitude, longitude) in locations.items():

    print(f"Fetching forecast for {zone}...")

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": latitude,
        "longitude": longitude,

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

    times = hourly["time"]
    temperatures = hourly["temperature_2m"]
    humidity = hourly["relative_humidity_2m"]
    precipitation = hourly["precipitation"]
    cloud_cover = hourly["cloud_cover"]
    wind_speed = hourly["wind_speed_10m"]
    wind_direction = hourly["wind_direction_10m"]
    solar_radiation = hourly["shortwave_radiation"]

    for i in range(len(times)):

        rows.append([
            zone,
            latitude,
            longitude,
            times[i],
            temperatures[i],
            humidity[i],
            precipitation[i],
            cloud_cover[i],
            wind_speed[i],
            wind_direction[i],
            solar_radiation[i]
        ])


# ============================================
# SAVE CSV
# ============================================

print("Saving forecast data...")

with open(
    OUTPUT_FILE,
    "w",
    newline="",
    encoding="utf-8"
) as file:

    writer = csv.writer(file)

    writer.writerow([
        "zone",
        "latitude",
        "longitude",
        "timestamp",
        "temperature_c",
        "humidity_percent",
        "precipitation_mm",
        "cloud_cover_percent",
        "wind_speed_kmh",
        "wind_direction_degree",
        "solar_radiation_wm2"
    ])

    writer.writerows(rows)


# ============================================
# RESULT
# ============================================

print("--------------------------------")
print("24-hour forecast download completed!")
print("Total rows:", len(rows))
print("Saved as:", OUTPUT_FILE)
print("--------------------------------")