import pandas as pd

# ============================================
# LOAD DATA
# ============================================

file_path = "wind_weather_real.csv"

print("Loading wind dataset...")

df = pd.read_csv(file_path)

print("\n========== WIND DATASET OVERVIEW ==========\n")

print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())


# ============================================
# ZONE CHECK
# ============================================

print("\n========== ZONE CHECK ==========\n")

print(df["zone"].value_counts())


# ============================================
# MISSING VALUES
# ============================================

print("\n========== MISSING VALUES ==========\n")

print(df.isnull().sum())


# ============================================
# DUPLICATE ROWS
# ============================================

print("\n========== DUPLICATE ROWS ==========\n")

print("Duplicate rows:", df.duplicated().sum())


# ============================================
# WIND SPEED
# ============================================

print("\n========== WIND SPEED ==========\n")

print("Minimum:", df["wind_speed_kmh"].min())
print("Maximum:", df["wind_speed_kmh"].max())
print("Average:", df["wind_speed_kmh"].mean())


# ============================================
# WIND DIRECTION
# ============================================

print("\n========== WIND DIRECTION ==========\n")

print("Minimum:", df["wind_direction_degree"].min())
print("Maximum:", df["wind_direction_degree"].max())


# ============================================
# TEMPERATURE
# ============================================

print("\n========== TEMPERATURE ==========\n")

print("Minimum:", df["temperature_c"].min())
print("Maximum:", df["temperature_c"].max())
print("Average:", df["temperature_c"].mean())


# ============================================
# PRESSURE
# ============================================

print("\n========== PRESSURE ==========\n")

print("Minimum:", df["pressure_msl_hpa"].min())
print("Maximum:", df["pressure_msl_hpa"].max())
print("Average:", df["pressure_msl_hpa"].mean())


# ============================================
# FIRST 10 ROWS
# ============================================

print("\n========== FIRST 10 ROWS ==========\n")

print(df.head(10).to_string(index=False))


# ============================================
# DATA TYPES
# ============================================

print("\n========== DATA TYPES ==========\n")

print(df.dtypes)


print("\n====================================")
print("Wind dataset check completed!")
print("====================================")