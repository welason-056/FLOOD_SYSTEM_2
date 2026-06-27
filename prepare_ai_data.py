import pandas as pd

# Load cleaned dataset
df = pd.read_csv("cleaned_flood_data.csv")

# Create flood labels
df['Flood'] = df['Rainfall Intensity (mm)'].apply(
    lambda x: 1 if x > 150 else 0
)

# Save AI-ready dataset
df.to_csv("ai_flood_dataset.csv", index=False)

print(df.head())

print("\nAI dataset created successfully!")