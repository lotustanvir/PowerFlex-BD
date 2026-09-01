import pandas as pd
import joblib


# ============================================
# 1. LOAD TRAINED MODEL
# ============================================

MODEL_FILE = "models/solar_forecast_model.pkl"

print("Loading trained Solar AI model...")

model = joblib.load(MODEL_FILE)

print("Model loaded successfully!")


# ============================================
# 2. USER INPUT
# ============================================

print("\n========== SOLAR PREDICTION ==========\n")

zone = input("Enter Bangladesh zone: ")

temperature = float(
    input("Temperature (°C): ")
)

humidity = float(
    input("Humidity (%): ")
)

rainfall = float(
    input("Rainfall (mm): ")
)

cloud_cover = float(
    input("Cloud cover (%): ")
)

wind_speed = float(
    input("Wind speed (km/h): ")
)

wind_direction = float(
    input("Wind direction (degree): ")
)

solar_radiation = float(
    input("Solar radiation (W/m²): ")
)

latitude = float(
    input("Latitude: ")
)

longitude = float(
    input("Longitude: ")
)

hour = int(
    input("Hour (0-23): ")
)

day = int(
    input("Day (1-31): ")
)

month = int(
    input("Month (1-12): ")
)

day_of_week = int(
    input("Day of week (0=Monday, 6=Sunday): ")
)


# ============================================
# 3. DAYTIME
# ============================================

is_daytime = int(
    solar_radiation > 0
)


# ============================================
# 4. CREATE INPUT DATAFRAME
# ============================================

input_data = pd.DataFrame([
    {
        "zone": zone,
        "latitude": latitude,
        "longitude": longitude,
        "temperature_c": temperature,
        "humidity_percent": humidity,
        "precipitation_mm": rainfall,
        "cloud_cover_percent": cloud_cover,
        "wind_speed_kmh": wind_speed,
        "wind_direction_degree": wind_direction,
        "solar_radiation_wm2": solar_radiation,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week,
        "is_daytime": is_daytime
    }
])


# ============================================
# 5. AI PREDICTION
# ============================================

prediction = model.predict(input_data)[0]


# Solar generation cannot be negative
prediction = max(0, prediction)


# ============================================
# 6. RESULT
# ============================================

print("\n========================================")
print("        POWERFLEX SOLAR FORECAST")
print("========================================")

print("Zone:", zone)

print(
    "Predicted generation:",
    round(prediction, 4),
    "MW per 1 MW installed capacity"
)

print("========================================")