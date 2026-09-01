import requests
import csv

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

START_DATE = "20240101"
END_DATE = "20241231"

output_file = "solar_resources_real.csv"

rows = []

for zone, (latitude, longitude) in locations.items():

    print(f"Downloading solar data for {zone}...")

    url = "https://power.larc.nasa.gov/api/temporal/hourly/point"

    params = {
        "start": START_DATE,
        "end": END_DATE,
        "latitude": latitude,
        "longitude": longitude,
        "community": "RE",
        "parameters": "ALLSKY_SFC_SW_DWN",
        "format": "JSON"
    }

    response = requests.get(url, params=params, timeout=120)

    print("Status:", response.status_code)

    response.raise_for_status()

    data = response.json()

    solar_data = data["properties"]["parameter"]["ALLSKY_SFC_SW_DWN"]

    for timestamp, value in solar_data.items():

        rows.append([
            timestamp,
            zone,
            latitude,
            longitude,
            value
        ])

print("Saving data...")

with open(output_file, "w", newline="", encoding="utf-8") as file:

    writer = csv.writer(file)

    writer.writerow([
        "timestamp",
        "zone",
        "latitude",
        "longitude",
        "solar_irradiance_wh_m2"
    ])

    writer.writerows(rows)

print("--------------------------------")
print("Solar data download completed!")
print("Total rows:", len(rows))
print("Saved as:", output_file)
print("--------------------------------")