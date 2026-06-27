import csv
from prediction.models import FloodClimateData

def run():
    print("IMPORT STARTED")

    file_path = r'C:\Users\DJ WEHALU\OneDrive\Desktop\PROJECT\flood_system\ai_flood_dataset.csv'

    with open(file_path, 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)

        for row in reader:
            print("ROW:", row)

            FloodClimateData.objects.create(
                year=int(row['Year']),
                region=row['Region'],
                rainfall_mm=float(row['Rainfall Intensity (mm)']),
                temperature=float(row['Temperature (C)']),
                flood=str(row['Flood']).strip().lower() in ['true', '1', 'yes']
            )

    print("IMPORT FINISHED")