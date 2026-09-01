import pandas as pd
import joblib


# ============================================
# 1. LOAD TRAINED MODEL
# ============================================

MODEL_FILE = "solar_forecast_model.pkl"

print("Loading trained Solar AI model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully!")


# ============================================
# 2. BANGLADESH LOCATIONS
# ============================================

locations = {
    "Dhaka": {
        "latitude": 23.8103,
        "longitude": 90.4125
    },
    "Chittagong": {
        "latitude": 22.3569,
        "longitude": 91.7832
    },
    "Khulna": {
        "latitude": 22.8456,
        "longitude": 89.5403
    },
    "Rajshahi": {
        "latitude": 24.3745,
        "longitude": 88.6042
    },
    "Comilla": {
        "latitude": 23.4607,
        "longitude": 91.1809
    },
    "Mymensingh": {
        "latitude": 24.7471,
        "longitude": 90.4203
    },
    "Sylhet": {
        "latitude": 24.8949,
        "longitude": 91.8687
    },
    "Barishal": {
        "latitude": 22.7010,
        "longitude": 90.3535
    },
    "Rangpur": {
        "latitude": 25.7439,
        "longitude": 89.2752
    }
}


# ============================================
# 3. ONE WEATHER SCENARIO
# ============================================
# এই values শুধু model test করার জন্য।
# পরে real weather forecast API থেকে আসবে।

weather = {
    "temperature_c": 34,
    "humidity_percent": 65,
    "precipitation_mm": 0,
    "cloud_cover_percent": 15,
    "wind_speed_kmh": 15,
    "wind_direction_degree": 180,
    "solar_radiation_wm2": 700,
    "hour": 12,
    "day": 30,
    "month": 8,
    "day_of_week": 6,
    "is_daytime": 1
}


# ============================================
# 4. CREATE INPUT DATA
# ============================================

rows = []

for zone, location in locations.items():

    row = {
        "zone": zone,
        "latitude": location["latitude"],
        "longitude": location["longitude"],

        "temperature_c": weather["temperature_c"],
        "humidity_percent": weather["humidity_percent"],
        "precipitation_mm": weather["precipitation_mm"],
        "cloud_cover_percent": weather["cloud_cover_percent"],
        "wind_speed_kmh": weather["wind_speed_kmh"],
        "wind_direction_degree": weather["wind_direction_degree"],
        "solar_radiation_wm2": weather["solar_radiation_wm2"],

        "hour": weather["hour"],
        "day": weather["day"],
        "month": weather["month"],
        "day_of_week": weather["day_of_week"],
        "is_daytime": weather["is_daytime"]
    }

    rows.append(row)


input_data = pd.DataFrame(rows)


# ============================================
# 5. MAKE PREDICTION
# ============================================

predictions = model.predict(input_data)

# Negative prediction allow করব না
predictions = predictions.clip(min=0)


# ============================================
# 6. ADD PREDICTIONS
# ============================================

input_data["predicted_generation_mw_per_1mw"] = predictions


# ============================================
# 7. SORT BY PREDICTION
# ============================================

result = input_data[
    [
        "zone",
        "latitude",
        "longitude",
        "predicted_generation_mw_per_1mw"
    ]
].sort_values(
    by="predicted_generation_mw_per_1mw",
    ascending=False
)


# ============================================
# 8. SHOW RESULTS
# ============================================

print("\n==============================================")
print("   POWERFLEX BD - SOLAR ZONE RANKING")
print("==============================================")

print(
    result.to_string(index=False)
)


# ============================================
# 9. SAVE RESULTS
# ============================================

result.to_csv(
    "solar_zone_predictions.csv",
    index=False
)

print("\n----------------------------------------------")
print("Prediction completed!")
print("Saved as: solar_zone_predictions.csv")
print("----------------------------------------------")