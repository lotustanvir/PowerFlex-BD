import pandas as pd
from pathlib import Path

# Current folder: data/raw/bpdb
file_path = Path("solar_resources_real.csv")

# Load data
df = pd.read_csv(file_path)

print("\n========== DATASET OVERVIEW ==========\n")

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

print("\n========== SOLAR IRRADIANCE ==========\n")

print("Minimum:", df["solar_irradiance_wh_m2"].min())
print("Maximum:", df["solar_irradiance_wh_m2"].max())
print("Average:", df["solar_irradiance_wh_m2"].mean())

print("\n========== FIRST 10 ROWS ==========\n")

print(df.head(10))

print("\n========== DATA TYPES ==========\n")

print(df.dtypes)

print("\n====================================")
print("Solar dataset check completed!")
print("====================================")