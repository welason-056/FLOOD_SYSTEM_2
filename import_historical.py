import os
import django
import pandas as pd
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_system.settings')
django.setup()

from prediction.models import Community, DailyFloodRisk

# Load CSV
df = pd.read_csv('train.csv')

# Show columns for confirmation
print("CSV columns:", df.columns.tolist())

# Map columns (exact matches)
community_col = 'Community'
date_col = 'Date'
rainfall_col = 'Rainfall'
temp_col = 'Temperature'
humidity_col = 'Humidity'
soil_col = 'Soil moisture'
flood_risk_col = 'Flood_Risk'

# Verify required columns exist
missing = []
for col in [community_col, date_col, rainfall_col, temp_col, humidity_col, soil_col, flood_risk_col]:
    if col not in df.columns:
        missing.append(col)
if missing:
    print(f"Missing columns: {missing}")
    exit(1)

count = 0
skipped = 0

for _, row in df.iterrows():
    community_name = str(row[community_col]).strip()
    
    # Find or skip community
    try:
        community = Community.objects.get(name=community_name)
    except Community.DoesNotExist:
        print(f"Community '{community_name}' not found in DB – skipping")
        skipped += 1
        continue
    
    # Parse date (assuming format YYYY-MM-DD)
    try:
        date_obj = datetime.strptime(str(row[date_col]), '%Y-%m-%d').date()
    except Exception as e:
        print(f"Invalid date {row[date_col]} – skipping")
        skipped += 1
        continue
    
    # Numeric values
    try:
        rainfall = float(row[rainfall_col])
        temperature = float(row[temp_col])
        humidity = float(row[humidity_col])
        soil_moisture = float(row[soil_col])
    except (ValueError, TypeError):
        print(f"Invalid numeric data for {community_name} on {date_obj} – skipping")
        skipped += 1
        continue
    
    # Flood risk: 1 or 0, or "High"/"Low"
    risk_raw = str(row[flood_risk_col]).strip().lower()
    if risk_raw in ['1', 'true', 'yes', 'high']:
        flood_risk = True
    elif risk_raw in ['0', 'false', 'no', 'low']:
        flood_risk = False
    else:
        # If it's text like "High"/"Low"
        flood_risk = risk_raw in ['high', 'moderate']   # adjust as needed
        # For safety, you might want to set based on threshold:
        # flood_risk = (float(risk_raw) > 0) if risk_raw.replace('.','').isdigit() else False
    
    # Create or update record
    DailyFloodRisk.objects.update_or_create(
        community=community,
        date=date_obj,
        defaults={
            'rainfall_mm': rainfall,
            'temperature_c': temperature,
            'humidity_percent': humidity,
            'soil_moisture': soil_moisture,
            'flood_risk': flood_risk,
            'confidence': 85.0,  # placeholder, update after training
        }
    )
    count += 1
    if count % 100 == 0:
        print(f"Processed {count} rows...")

print(f"✅ Imported {count} records. Skipped {skipped}.")