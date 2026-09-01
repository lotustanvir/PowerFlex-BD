import pandas as pd
import joblib

from datetime import datetime
from pathlib import Path
from xgboost import XGBRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from database.connection import get_session
from database.models import ModelRegistry


# ==========================================================
# 1. FILE PATHS
# ==========================================================

INPUT_FILE = Path(
    "data/raw/bpdb/solar_weather_combined.csv"
)

MODEL_FILE = Path(
    "models/weather_only_solar_model.pkl"
)


# ==========================================================
# 2. LOAD DATA
# ==========================================================

print("Loading Solar + Weather dataset...")

df = pd.read_csv(INPUT_FILE)

print("Total rows:", len(df))


# ==========================================================
# 3. TIMESTAMP
# ==========================================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

df = df.sort_values(
    ["timestamp", "zone"]
).reset_index(drop=True)


# ==========================================================
# 4. TIME FEATURES
# ==========================================================

df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.day
df["month"] = df["timestamp"].dt.month
df["day_of_week"] = df["timestamp"].dt.dayofweek


# ==========================================================
# 5. DAYTIME
# ==========================================================
# We use time only, not solar radiation,
# to determine approximate daytime.

df["is_daytime"] = (
    (df["hour"] >= 6) &
    (df["hour"] <= 18)
).astype(int)


# ==========================================================
# 6. TARGET
# ==========================================================
# Target comes from NASA solar-resource data.
# The model will NOT see solar irradiance as an input.

PERFORMANCE_RATIO = 0.85

df["solar_generation_mw_per_1mw"] = (
    (df["solar_irradiance_wh_m2"] / 1000)
    * PERFORMANCE_RATIO
)

df["solar_generation_mw_per_1mw"] = (
    df["solar_generation_mw_per_1mw"]
    .clip(lower=0)
)


# ==========================================================
# 7. WEATHER-ONLY FEATURES
# ==========================================================
# IMPORTANT:
# solar_irradiance and solar_radiation are intentionally
# NOT included.

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

target = "solar_generation_mw_per_1mw"


X = df[features]
y = df[target]


# ==========================================================
# 8. REMOVE MISSING VALUES
# ==========================================================

valid_rows = X.notna().all(axis=1) & y.notna()

X = X.loc[valid_rows].reset_index(drop=True)
y = y.loc[valid_rows].reset_index(drop=True)

print("Usable rows:", len(X))


# ==========================================================
# 9. TIME-BASED TRAIN / TEST SPLIT
# ==========================================================

split_index = int(len(X) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


# ==========================================================
# 10. FEATURES
# ==========================================================

categorical_features = [
    "zone"
]

numeric_features = [
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


# ==========================================================
# 11. PREPROCESSING
# ==========================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "zone_encoder",
            OneHotEncoder(
                handle_unknown="ignore"
            ),
            categorical_features
        )
    ],
    remainder="passthrough"
)


# ==========================================================
# 12. XGBOOST MODEL
# ==========================================================

model = XGBRegressor(
    n_estimators=600,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)


# ==========================================================
# 13. PIPELINE
# ==========================================================

pipeline = Pipeline(
    steps=[
        (
            "preprocessor",
            preprocessor
        ),
        (
            "model",
            model
        )
    ]
)


# ==========================================================
# 14. TRAIN
# ==========================================================

print("\nTraining Weather-Only Solar AI...")

pipeline.fit(
    X_train,
    y_train
)

print("Training completed!")


# ==========================================================
# 15. PREDICTION
# ==========================================================

print("\nMaking predictions...")

predictions = pipeline.predict(X_test)

# Solar output cannot be negative
predictions = predictions.clip(min=0)


# ==========================================================
# 16. EVALUATION
# ==========================================================

mae = mean_absolute_error(
    y_test,
    predictions
)

rmse = mean_squared_error(
    y_test,
    predictions
) ** 0.5

r2 = r2_score(
    y_test,
    predictions
)


print("\n========== WEATHER-ONLY MODEL ==========")

print("MAE :", round(mae, 6))
print("RMSE:", round(rmse, 6))
print("R²  :", round(r2, 6))

print("=========================================")


# ==========================================================
# 17. SAVE MODEL
# ==========================================================

joblib.dump(
    pipeline,
    MODEL_FILE
)

print("\nModel saved as:")
print(MODEL_FILE)


# ==========================================================
# 18. ACTUAL VS PREDICTED
# ==========================================================

results = pd.DataFrame({
    "actual": y_test.values,
    "predicted": predictions
})

print("\n========== ACTUAL VS PREDICTED ==========\n")

print(
    results.head(20).to_string(index=False)
)


print("\nWeather-Only Solar AI training completed!")


# ==========================================================
# 19. LOG TO MODEL REGISTRY
# ==========================================================

try:
    session = get_session()
    with session:
        registry_entry = ModelRegistry(
            model_type="weather_only_solar",
            model_path=str(MODEL_FILE),
            trained_at=datetime.now(),
            training_samples=len(X_train),
            mae=round(mae, 6),
            rmse=round(rmse, 6),
            r2=round(r2, 6),
            features=features,
            is_active=True,
        )
        session.add(registry_entry)
        session.commit()
        print("Model registry entry created successfully!")
except Exception as e:
    print(f"Failed to log model registry: {e}")