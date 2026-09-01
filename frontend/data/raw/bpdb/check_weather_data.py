import pandas as pd

file_path = "weather_real.csv"

df = pd.read_csv(file_path)

print("\n========== WEATHER DATASET OVERVIEW ==========\n")

print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\nColumns:")
print(df.columns.tolist())

print("\n========== ZONE CHECK ==========\n")

print(df["zone"].value_counts())

print("\n========== MISSING VALUES ==========\n")

print(df.isnull().sum())

print("\n========== DUPLICATE ROWS ==========\n")

print("Duplicate rows:", df.duplicated().sum())

print("\n========== TEMPERATURE ==========\n")

print("Minimum:", df["temperature_c"].min())
print("Maximum:", df["temperature_c"].max())
print("Average:", df["temperature_c"].mean())

print("\n========== HUMIDITY ==========\n")

print("Minimum:", df["humidity_percent"].min())
print("Maximum:", df["humidity_percent"].max())
print("Average:", df["humidity_percent"].mean())

print("\n========== RAINFALL ==========\n")

print("Minimum:", df["precipitation_mm"].min())
print("Maximum:", df["precipitation_mm"].max())
print("Average:", df["precipitation_mm"].mean())

print("\n========== WIND SPEED ==========\n")

print("Minimum:", df["wind_speed_kmh"].min())
print("Maximum:", df["wind_speed_kmh"].max())
print("Average:", df["wind_speed_kmh"].mean())

print("\n========== CLOUD COVER ==========\n")

print("Minimum:", df["cloud_cover_percent"].min())
print("Maximum:", df["cloud_cover_percent"].max())
print("Average:", df["cloud_cover_percent"].mean())

print("\n========== SOLAR RADIATION ==========\n")

print("Minimum:", df["solar_radiation_wm2"].min())
print("Maximum:", df["solar_radiation_wm2"].max())
print("Average:", df["solar_radiation_wm2"].mean())

print("\n========== FIRST 10 ROWS ==========\n")

print(df.head(10))

print("\n========== DATA TYPES ==========\n")

print(df.dtypes)

print("\n====================================")
print("Weather dataset check completed!")
print("====================================")