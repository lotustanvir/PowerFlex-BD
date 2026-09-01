import pandas as pd

# Read processed solar data
file_path = "solar_generation_potential.csv"

df = pd.read_csv(file_path)

# Average generation potential by Bangladesh zone
zone_summary = (
    df.groupby("zone")["generation_mw_per_1mw_capacity"]
    .agg(["mean", "max"])
    .reset_index()
)

zone_summary.columns = [
    "zone",
    "average_generation_mw_per_1mw",
    "maximum_generation_mw_per_1mw"
]

# Sort from highest to lowest average potential
zone_summary = zone_summary.sort_values(
    "average_generation_mw_per_1mw",
    ascending=False
)

print("\n========== SOLAR POTENTIAL BY BANGLADESH ZONE ==========\n")

print(zone_summary.to_string(index=False))

# Save report
zone_summary.to_csv(
    "solar_zone_summary.csv",
    index=False
)

print("\n==============================================")
print("Solar zone analysis completed!")
print("Report saved as: solar_zone_summary.csv")
print("==============================================")