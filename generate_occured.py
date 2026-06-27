import pandas as pd

# Load your dataset
df = pd.read_csv("prediction/flood_data.csv")

# Create "occured" column based on rules
def determine_occured(row):
    if (
        row["rainfall_intensity_mm_per_day"] > 120
        or row["total_affected"] > 5000
        or row["total_deaths"] > 0
    ):
        return "Yes"
    else:
        return "No"

df["occured"] = df.apply(determine_occured, axis=1)

# Save new CSV
df.to_csv("prediction/flood_data_with_occured.csv", index=False)

print("occured column created successfully!")