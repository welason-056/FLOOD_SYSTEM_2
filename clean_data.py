import pandas as pd

# Load dataset
df = pd.read_csv("flood_prediction_dataset.csv")

# Show missing values before cleaning
print("Missing values before:")
print(df.isnull().sum())

# Replace missing rainfall values with average
df['Rainfall Intensity (mm)'] = df['Rainfall Intensity (mm)'].fillna(
    df['Rainfall Intensity (mm)'].mean()
)

# Replace missing temperature values with average
df['Temperature (C)'] = df['Temperature (C)'].fillna(
    df['Temperature (C)'].mean()
)

# Show missing values after cleaning
print("\nMissing values after:")
print(df.isnull().sum())

# Save cleaned file
df.to_csv("cleaned_flood_data.csv", index=False)

print("\nDataset cleaned successfully!")