import pandas as pd
import joblib

from datetime import datetime
from xgboost import XGBRegressor
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from database.connection import get_session
from database.models import ModelRegistry


# ==========================================================
# 1. FILE PATH
# ==========================================================

input_file = "data/processed/solar_training_data.csv"

model_file = "models/solar_forecast_model.pkl"


# ==========================================================
# 2. LOAD DATA
# ==========================================================

print("Loading solar training data...")

df = pd.read_csv(input_file)

print("Total rows:", len(df))


# ==========================================================
# 3. SORT BY TIME
# ==========================================================

print("Sorting data by time...")

# Convert timestamp
# If timestamp is not present in the training file,
# we will use the row order.
if "timestamp" in df.columns:
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")


# ==========================================================
# 4. FEATURES AND TARGET
# ==========================================================

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


X = df[features]
y = df[target]


# ==========================================================
# 5. TIME-BASED TRAIN / TEST SPLIT
# ==========================================================

print("Creating time-based train/test split...")

split_index = int(len(df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]


print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))


# ==========================================================
# 6. CATEGORICAL + NUMERICAL FEATURES
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
    "solar_radiation_wm2",
    "hour",
    "day",
    "month",
    "day_of_week",
    "is_daytime"
]


# ==========================================================
# 7. PREPROCESSING
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
# 8. XGBOOST MODEL
# ==========================================================

model = XGBRegressor(
    n_estimators=500,
    max_depth=8,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)


# ==========================================================
# 9. COMPLETE PIPELINE
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
# 10. TRAIN
# ==========================================================

print("\nTraining XGBoost model...")

pipeline.fit(
    X_train,
    y_train
)

print("Training completed!")


# ==========================================================
# 11. PREDICTION
# ==========================================================

print("\nMaking predictions...")

predictions = pipeline.predict(X_test)


# ==========================================================
# 12. MODEL EVALUATION
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


print("\n========== MODEL PERFORMANCE ==========")

print("MAE :", round(mae, 6))
print("RMSE:", round(rmse, 6))
print("R²  :", round(r2, 6))

print("=======================================\n")


# ==========================================================
# 13. SAVE MODEL
# ==========================================================

joblib.dump(
    pipeline,
    model_file
)

print("Model saved as:", model_file)


# ==========================================================
# 14. SHOW SOME ACTUAL VS PREDICTED VALUES
# ==========================================================

results = pd.DataFrame({
    "actual": y_test.values,
    "predicted": predictions
})

print("\n========== ACTUAL VS PREDICTED ==========\n")

print(
    results.head(20).to_string(index=False)
)

print("\nSolar AI model training completed successfully!")


# ==========================================================
# 15. LOG TO MODEL REGISTRY
# ==========================================================

try:
    session = get_session()
    with session:
        registry_entry = ModelRegistry(
            model_type="solar",
            model_path=model_file,
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