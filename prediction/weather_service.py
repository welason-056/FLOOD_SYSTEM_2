import requests
import json
import random
from datetime import datetime, timedelta


class WeatherService:
    REGION_COORDINATES = {
        "Arusha": {"lat": -3.3869, "lon": 36.6820},
        "Dar-es-salaam": {"lat": -6.7924, "lon": 39.2083},
        "Dodoma": {"lat": -6.1629, "lon": 35.7516},
        "Geita": {"lat": -2.8667, "lon": 32.1667},
        "Iringa": {"lat": -7.7725, "lon": 35.6847},
        "Kagera": {"lat": -1.8667, "lon": 31.3667},
        "Kaskazini Pemba": {"lat": -5.0271, "lon": 39.7755},
        "Kaskazini Unguja": {"lat": -5.9294, "lon": 39.2891},
        "Katavi": {"lat": -6.8500, "lon": 31.2500},
        "Kigoma": {"lat": -4.8833, "lon": 29.6333},
        "Kilimanjaro": {"lat": -3.0674, "lon": 37.3556},
        "Kusini Pemba": {"lat": -5.5167, "lon": 39.7333},
        "Kusini Unguja": {"lat": -6.2833, "lon": 39.3667},
        "Lindi": {"lat": -9.9896, "lon": 39.7105},
        "Manyara": {"lat": -4.3150, "lon": 36.9544},
        "Mara": {"lat": -1.4667, "lon": 34.4667},
        "Mbeya": {"lat": -8.9033, "lon": 33.4568},
        "Mjini Magharibi": {"lat": -6.1659, "lon": 39.2026},
        "Morogoro": {"lat": -6.8305, "lon": 37.6606},
        "Mtwara": {"lat": -10.3127, "lon": 40.1830},
        "Mwanza": {"lat": -2.5164, "lon": 32.9172},
        "Njombe": {"lat": -9.3333, "lon": 34.7667},
        "Pwani": {"lat": -7.3238, "lon": 38.8205},
        "Rukwa": {"lat": -8.0000, "lon": 31.5000},
        "Ruvuma": {"lat": -10.6833, "lon": 35.6500},
        "Shinyanga": {"lat": -3.6619, "lon": 33.4275},
        "Simiyu": {"lat": -2.8333, "lon": 34.0000},
        "Singida": {"lat": -4.8163, "lon": 34.7436},
        "Tabora": {"lat": -5.0333, "lon": 32.8000},
        "Tanga": {"lat": -5.0689, "lon": 39.0986}
    }
    
    def __init__(self):
        self.api_key = None
        self.use_mock = True
    
    def set_api_key(self, api_key):
        self.api_key = api_key
        self.use_mock = False
    
    def get_real_time_weather(self, region):
        if region not in self.REGION_COORDINATES:
            return self.get_mock_weather(region)
        
        coords = self.REGION_COORDINATES[region]
        
        if self.api_key and not self.use_mock:
            try:
                url = f"https://api.openweathermap.org/data/2.5/weather?lat={coords['lat']}&lon={coords['lon']}&appid={self.api_key}&units=metric"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    rainfall = 0
                    if 'rain' in data:
                        rainfall = data['rain'].get('1h', 0)
                    
                    return {
                        'region': region,
                        'rainfall': round(rainfall, 1),
                        'temperature': data['main']['temp'],
                        'humidity': data['main']['humidity'],
                        'timestamp': datetime.now().isoformat(),
                        'source': 'api'
                    }
            except Exception as e:
                print(f"API error for {region}: {e}")
        
        return self.get_mock_weather(region)
    
    def get_mock_weather(self, region):
        from prediction.models import FloodClimateData
        from django.db.models import Avg
        
        historical = FloodClimateData.objects.filter(region=region)
        
        if historical.exists():
            stats = historical.aggregate(
                avg_rain=Avg('rainfall'),
                avg_temp=Avg('temperature'),
                avg_humidity=Avg('humidity')
            )
            base_rain = stats['avg_rain'] or 15
            base_temp = stats['avg_temp'] or 25
            base_humidity = stats['avg_humidity'] or 65
        else:
            base_rain = 15
            base_temp = 25
            base_humidity = 65
        
        month = datetime.now().month
        is_rainy = month in [3, 4, 5, 10, 11, 12]
        
        if is_rainy:
            rainfall = base_rain * random.uniform(0.8, 2.0)
        else:
            rainfall = base_rain * random.uniform(0.3, 1.0)
        
        return {
            'region': region,
            'rainfall': round(rainfall, 1),
            'temperature': round(base_temp + random.uniform(-3, 5), 1),
            'humidity': round(base_humidity + random.uniform(-10, 15), 1),
            'timestamp': datetime.now().isoformat(),
            'source': 'mock'
        }
    
    def get_forecast(self, region, days=3):
        forecasts = []
        current = self.get_real_time_weather(region)
        forecasts.append(current)
        
        for i in range(1, days):
            forecast = current.copy()
            forecast['timestamp'] = (datetime.now() + timedelta(days=i)).isoformat()
            forecast['rainfall'] = round(forecast['rainfall'] * random.uniform(0.5, 1.5), 1)
            forecast['temperature'] = round(forecast['temperature'] + random.uniform(-2, 2), 1)
            forecasts.append(forecast)
        
        return forecasts


weather_service = WeatherService()