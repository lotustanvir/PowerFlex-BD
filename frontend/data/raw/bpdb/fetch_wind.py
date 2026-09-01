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
    "Rangpur": (25.7439, 89.2752)
}


# ============================================
# HISTORICAL PERIOD
# ============================================

START_DATE = "2024-01-01"
END_DATE = "2024-12-31"

OUTPUT_FILE = "wind_weather_real.csv"

rows = []


# ============================================
# DOWNLOAD WEATHER WIND DATA
# ============================================

for zone, (latitude, longitude) in locations.items():

    print(f"Downloading wind data for {zone}...")

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,

        "hourly": ",".join([
            "wind_speed_10m",
            "wind_direction_10m",
            "temperature_2m",
            "pressure_msl"
        ]),

        "timezone": "Asia/Dhaka"
    }

    response = requests.get(
        url,
        params=params,
        timeout=120
    )

    print("Status:", response.status_code)

    response.raise_for_status()

    data = response.json()

    hourly = data["hourly"]

    times = hourly["time"]
    wind_speed = hourly["wind_speed_10m"]
    wind_direction = hourly["wind_direction_10m"]
    temperature = hourly["temperature_2m"]
    pressure = hourly["pressure_msl"]

    for i in range(len(times)):

        rows.append([
            zone,
            latitude,
            longitude,
            times[i],
            wind_speed[i],
            wind_direction[i],
            temperature[i],
            pressure[i]
        ])


# ============================================
# SAVE CSV
# ============================================

print("Saving wind data...")

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
        "wind_speed_kmh",
        "wind_direction_degree",
        "temperature_c",
        "pressure_msl_hpa"
    ])

    writer.writerows(rows)


# ============================================
# RESULT
# ============================================

print("--------------------------------")
print("Wind weather data download completed!")
print("Total rows:", len(rows))
print("Saved as:", OUTPUT_FILE)
print("--------------------------------")