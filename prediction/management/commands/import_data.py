import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from prediction.models import Community, DailyFloodRisk

class Command(BaseCommand):
    help = 'Import data from CSV (train.csv or test.csv)'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before importing'
        )

    def handle(self, *args, **options):
        file_path = options['csv_file']
        clear_existing = options.get('clear', False)

        # Optional: Clear existing data
        if clear_existing:
            self.stdout.write(self.style.WARNING('Clearing existing predictions...'))
            DailyFloodRisk.objects.all().delete()

        count = 0
        skipped = 0

        with open(file_path, 'r') as f:
            # Detect delimiter (comma or semicolon)
            sample = f.read(1024)
            f.seek(0)
            delimiter = ';' if ';' in sample else ','

            reader = csv.DictReader(f, delimiter=delimiter)

            # Get column names (normalize to lowercase)
            columns = {k.lower().strip(): k for k in reader.fieldnames}

            for row in reader:
                try:
                    # Get community name
                    comm_name = row.get(columns.get('community', 'community')) or row.get(columns.get('name', 'name'))
                    if not comm_name:
                        skipped += 1
                        continue

                    # Get or create community
                    comm, created = Community.objects.get_or_create(
                        name=comm_name.strip(),
                        defaults={'latitude': 0.0, 'longitude': 0.0}  # You can update later
                    )

                    # Get date
                    date_str = row.get(columns.get('date', 'date'))
                    if not date_str:
                        skipped += 1
                        continue
                    date_obj = datetime.strptime(date_str.strip(), '%Y-%m-%d').date()

                    # Get values
                    rainfall = float(row.get(columns.get('rainfall_mm', 'rainfall'), 0) or 0)
                    temp = float(row.get(columns.get('temperature_c', 'temperature'), 0) or 0)
                    humidity = float(row.get(columns.get('humidity_percent', 'humidity'), 0) or 0)
                    soil = float(row.get(columns.get('soil_moisture', 'soil'), 0) or 0)

                    # Get flood_risk (handle different formats)
                    risk_val = row.get(columns.get('flood_risk', 'flood'), 'False')
                    flood_risk = str(risk_val).lower() in ('true', '1', 'yes', 't')

                    # Get confidence
                    conf = float(row.get(columns.get('confidence', 'confidence'), 0) or 0)

                    # Get risk_level
                    risk_level = row.get(columns.get('risk_level', 'risk'), 'LOW').upper()
                    if risk_level not in ['LOW', 'MODERATE', 'HIGH']:
                        risk_level = 'LOW'

                    # Create or update prediction
                    obj, created = DailyFloodRisk.objects.update_or_create(
                        community=comm,
                        date=date_obj,
                        defaults={
                            'rainfall_mm': rainfall,
                            'temperature_c': temp,
                            'humidity_percent': humidity,
                            'soil_moisture': soil,
                            'flood_risk': flood_risk,
                            'confidence': conf,
                            'risk_level': risk_level,
                        }
                    )

                    if created:
                        count += 1
                        self.stdout.write(self.style.SUCCESS(f'✅ Added: {comm_name} - {date_str}'))
                    else:
                        self.stdout.write(f'🔄 Updated: {comm_name} - {date_str}')

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'⚠️ Error on row: {row} - {str(e)}'))
                    skipped += 1

        self.stdout.write(self.style.SUCCESS(f'\n✅ Imported {count} records, skipped {skipped}'))

    def __str__(self):
        return self.name