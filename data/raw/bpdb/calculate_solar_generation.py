import pandas as pd

# Input file
input_file = "solar_resources_real.csv"

# Output file
output_file = "solar_generation_potential.csv"

# Solar panel performance ratio
# This accounts for common system losses such as:
# temperature, inverter, wiring, dust, etc.
PERFORMANCE_RATIO = 0.85

# Read real NASA solar data
df = pd.read_csv(input_file)

# NASA hourly solar value is Wh/m².
# For an hourly interval, this is numerically usable
# as the average solar power equivalent in W/m².
#
# Approximate generation:
#
# Generation (MW) =
# Installed Capacity (MW)
# × Solar Irradiance / 1000
# × Performance Ratio
#
# Because we do not yet have actual installed capacity
# for every zone, we calculate generation potential
# assuming 1 MW of installed solar capacity.

df["generation_mw_per_1mw_capacity"] = (
    (df["solar_irradiance_wh_m2"] / 1000)
    * PERFORMANCE_RATIO
)

# Generation cannot be negative
df["generation_mw_per_1mw_capacity"] = (
    df["generation_mw_per_1mw_capacity"].clip(lower=0)
)

# Save processed data
df.to_csv(output_file, index=False)

print("--------------------------------")
print("Solar generation calculation completed!")
print("Total rows:", len(df))
print("Output file:", output_file)
print("--------------------------------")

print("\nGeneration potential statistics:")
print(
    df["generation_mw_per_1mw_capacity"].describe()
)