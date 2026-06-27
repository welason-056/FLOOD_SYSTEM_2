import pickle
from datetime import date
from django.core.management.base import BaseCommand
from django.db.models import Q
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score
import numpy as np
from prediction.models import Community, DailyFloodRisk

class Command(BaseCommand):
    help = 'Train the flood risk model using data from the database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Proportion of data to use as test set (default: 0.2)',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retraining even if model exists',
        )

    def handle(self, *args, **options):
        test_size = options['test_size']
        force = options['force']

        self.stdout.write(self.style.WARNING('🚀 Fetching data from database...'))

        # Get all predictions that have the required fields
        qs = DailyFloodRisk.objects.select_related('community').filter(
            Q(rainfall_mm__isnull=False) &
            Q(temperature_c__isnull=False) &
            Q(humidity_percent__isnull=False) &
            Q(soil_moisture__isnull=False) &
            Q(flood_risk__isnull=False)
        )

        if not qs.exists():
            self.stdout.write(self.style.ERROR('❌ No usable data found in the database. Please generate some predictions first.'))
            return

        self.stdout.write(f'🔍 Found {qs.count()} records')

        # Extract features and target
        communities = []
        rainfalls = []
        temps = []
        humidities = []
        soils = []
        flood_risks = []

        for record in qs:
            communities.append(record.community.name)
            rainfalls.append(record.rainfall_mm)
            temps.append(record.temperature_c)
            humidities.append(record.humidity_percent)
            soils.append(record.soil_moisture)
            flood_risks.append(int(record.flood_risk))  # Convert bool to int

        # Convert to numpy arrays
        communities = np.array(communities)
        rainfalls = np.array(rainfalls)
        temps = np.array(temps)
        humidities = np.array(humidities)
        soils = np.array(soils)
        flood_risks = np.array(flood_risks)

        # Encode community names
        encoder = LabelEncoder()
        communities_encoded = encoder.fit_transform(communities)

        # Build feature matrix
        X = np.column_stack([communities_encoded, rainfalls, temps, humidities, soils])
        y = flood_risks

        # Split into train/test (shuffle)
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        self.stdout.write(f'📊 Training on {len(X_train)} samples, testing on {len(X_test)} samples')

        # Train model
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)

        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        self.stdout.write(self.style.SUCCESS(f'✅ Model Accuracy: {accuracy:.2%}'))

        # Save model and encoder
        with open('flood_model.pkl', 'wb') as f:
            pickle.dump(model, f)

        with open('community_encoder.pkl', 'wb') as f:
            pickle.dump(encoder, f)

        self.stdout.write(self.style.SUCCESS('✅ Model and encoder saved successfully!'))

        # Feature importance
        feature_names = ['Community (encoded)', 'Rainfall', 'Temperature', 'Humidity', 'Soil moisture']
        importances = model.feature_importances_
        self.stdout.write('\n📈 Feature Importance:')
        for name, imp in zip(feature_names, importances):
            self.stdout.write(f'  {name}: {imp:.4f}')

        # Additional info
        self.stdout.write(f'\n📊 Classes: {len(model.classes_)} classes')
        self.stdout.write(f'  - Target distribution: {np.bincount(y)}')
