from django.core.management.base import BaseCommand
from datetime import date
import pickle
import os
from prediction.models import Community, DailyFloodRisk
from prediction.weather_fetcher import get_daily_weather

class Command(BaseCommand):
    help = 'Generate daily flood predictions using real‑time weather data'

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        model_path = os.path.join(base_dir, 'flood_model.pkl')
        encoder_path = os.path.join(base_dir, 'community_encoder.pkl')

        if not os.path.exists(model_path):
            self.stdout.write(self.style.ERROR("Model not found. Run train_ai.py first."))
            return

        model = pickle.load(open(model_path, 'rb'))
        encoder = pickle.load(open(encoder_path, 'rb'))

        communities = Community.objects.all()
        today = date.today()

        for comm in communities:
            try:
                weather = get_daily_weather(comm.latitude, comm.longitude, today)
                rainfall = weather['rainfall']
                temperature = weather['temperature']
                humidity = weather['humidity']
                soil_moisture = weather['soil_moisture']
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Weather fetch failed for {comm.name}: {e}. Using fallback."))
                rainfall = 0.0
                temperature = 28.0
                humidity = 70.0
                soil_moisture = 0.30

            try:
                comm_enc = encoder.transform([comm.name])[0]
            except:
                self.stdout.write(self.style.ERROR(f"Community {comm.name} not in encoder – skip"))
                continue

            input_data = [[comm_enc, rainfall, temperature, humidity, soil_moisture]]
            risk = model.predict(input_data)[0]          # 0 or 1
            proba = model.predict_proba(input_data)[0][1] # probability of flood (class 1)

            # Determine risk level from probability
            if proba >= 0.7:
                risk_level = 'HIGH'
            elif proba >= 0.3:
                risk_level = 'MODERATE'
            else:
                risk_level = 'LOW'

            DailyFloodRisk.objects.update_or_create(
                community=comm,
                date=today,
                defaults={
                    'rainfall_mm': rainfall,
                    'temperature_c': temperature,
                    'humidity_percent': humidity,
                    'soil_moisture': soil_moisture,
                    'flood_risk': bool(risk),
                    'confidence': float(proba * 100),
                    'risk_level': risk_level,
                }
            )
            self.stdout.write(f"Prediction for {comm.name}: {risk_level} ({proba*100:.1f}%) – rain={rainfall:.1f}mm")

        self.stdout.write(self.style.SUCCESS("✅ Daily predictions complete."))