# prediction/weather_fetcher.py
import requests
from datetime import date

def get_daily_weather(lat, lng, pred_date):
    """
    Fetch weather data from wttr.in (no API key required).
    """
    try:
        url = f'https://wttr.in/{lat},{lng}?format=j1'
        response = requests.get(url, timeout=10)
        
        if response.status_code != 200:
            return _get_default_weather()
        
        data = response.json()
        current = data.get('current_condition', [{}])[0]
        
        temperature = float(current.get('temp_C', 28))
        humidity = float(current.get('humidity', 70))
        wind_speed = float(current.get('windSpeedKmph', 20))
        rainfall = float(current.get('precipMM', 0))
        
        # Estimate soil moisture
        soil_moisture = _estimate_soil_moisture(rainfall, humidity)
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'rainfall': round(rainfall, 1),
            'soil_moisture': round(soil_moisture, 3),
            'wind_speed': round(wind_speed, 1),
        }
        
    except Exception as e:
        print(f"Weather fetch error: {e}")
        return _get_default_weather()

def _estimate_soil_moisture(rainfall, humidity):
    base = 0.2 + (humidity / 100) * 0.3
    rain_factor = min(rainfall / 50, 0.4)
    return min(base + rain_factor, 1.0)

def _get_default_weather():
    return {
        'temperature': 28.0,
        'humidity': 70.0,
        'rainfall': 0.0,
        'soil_moisture': 0.5,
        'wind_speed': 20.0,
    }