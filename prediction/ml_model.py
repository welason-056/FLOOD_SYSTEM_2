import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score
import joblib
import os
from datetime import datetime


class FloodPredictionModel:
    def __init__(self):
        self.model = None
        self.region_encoder = LabelEncoder()
        self.risk_encoder = LabelEncoder()
        self.scaler = StandardScaler()
        self.is_trained = False
        self.training_records = 0
        self.trained_regions = []

        self.feature_columns = [
            'region_encoded', 'year', 'month',
            'rainfall', 'temperature', 'humidity',
            'rainfall_temp_interaction', 'rainfall_humidity_interaction',
            'is_rainy_season', 'is_high_rainfall', 'is_high_temp'
        ]

    def prepare_data(self, data):
        df = pd.DataFrame(data)

        if 'date' not in df.columns:
            df['date'] = pd.to_datetime(df['year'].astype(str) + '-' + df['month'].astype(str) + '-01')

        df['date'] = pd.to_datetime(df['date'])
        df['region_encoded'] = self.region_encoder.fit_transform(df['region'].astype(str))
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df = df.sort_values(['region', 'date'])
        
        df['rainfall_7day_avg'] = df.groupby('region')['rainfall'].transform(
            lambda x: x.shift(1).rolling(7, min_periods=1).mean()
        ).fillna(df['rainfall'])
        
        df['rainfall_temp_interaction'] = df['rainfall'] * df['temperature']
        df['rainfall_humidity_interaction'] = df['rainfall'] * df['humidity']

        df['is_rainy_season'] = df['month'].isin([3, 4, 5, 10, 11, 12]).astype(int)
        df['is_high_rainfall'] = (df['rainfall'] > 50).astype(int)
        df['is_high_temp'] = (df['temperature'] > 30).astype(int)

        X = df[self.feature_columns].fillna(0)
        y = self.risk_encoder.fit_transform(df['flood_risk'])
        X_scaled = self.scaler.fit_transform(X)

        return X_scaled, y

    def train_from_database(self, region=None):
        from prediction.models import FloodClimateData
        
        print("\n🔄 Training AI from database records...")
        
        queryset = FloodClimateData.objects.all()
        if region:
            queryset = queryset.filter(region=region)
            print(f"📊 Training for region: {region}")
        
        total_records = queryset.count()
        if total_records < 30:
            print(f"⚠️ Only {total_records} records. Need at least 30 for training.")
            return False
        
        data = []
        for record in queryset:
            data.append({
                'region': record.region,
                'year': record.year,
                'month': record.month,
                'rainfall': record.rainfall,
                'temperature': record.temperature,
                'humidity': record.humidity,
                'flood_risk': record.flood_risk,
            })
        
        df = pd.DataFrame(data)
        X, y = self.prepare_data(df)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
        
        self.is_trained = True
        self.training_records = len(data)
        self.trained_regions = list(df['region'].unique())
        
        print(f"✅ Model trained on {self.training_records} records from {len(self.trained_regions)} regions")
        return True

    def predict_with_database_context(self, region, rainfall, temperature, humidity, date=None):
        from prediction.models import FloodClimateData
        from django.db.models import Avg, Count
        
        if not self.is_trained:
            if not self.load_model('flood_ai_model.pkl'):
                self.train_from_database(region)
        
        if not self.is_trained:
            return None
        
        historical = FloodClimateData.objects.filter(region=region)
        
        if historical.exists():
            total = historical.count()
            high_risk_count = historical.filter(flood_risk='High').count()
            moderate_risk_count = historical.filter(flood_risk='Moderate').count()
            
            historical_high_prob = (high_risk_count / total * 100) if total > 0 else 0
            historical_moderate_prob = (moderate_risk_count / total * 100) if total > 0 else 0
            avg_rainfall = historical.aggregate(Avg('rainfall'))['rainfall__avg'] or 0
        else:
            historical_high_prob = 0
            historical_moderate_prob = 0
            avg_rainfall = 0
        
        if date is None:
            date = datetime.now()
        
        ai_prediction = self.predict(region, rainfall, temperature, humidity, date)
        
        if ai_prediction:
            ai_prediction['historical_context'] = {
                'total_records': total if historical.exists() else 0,
                'historical_high_probability': round(historical_high_prob, 1),
                'historical_moderate_probability': round(historical_moderate_prob, 1),
                'avg_historical_rainfall': round(avg_rainfall, 1)
            }
        
        return ai_prediction

    def predict(self, region, rainfall, temperature, humidity, date=None):
        if not self.is_trained:
            raise Exception("Model not trained")

        if date is None:
            date = datetime.now()

        try:
            region_encoded = self.region_encoder.transform([region])[0]
        except ValueError:
            region_encoded = 0

        year = date.year
        month = date.month

        r_t = rainfall * temperature
        r_h = rainfall * humidity

        rainy = 1 if month in [3, 4, 5, 10, 11, 12] else 0
        high_rain = 1 if rainfall > 50 else 0
        high_temp = 1 if temperature > 30 else 0

        features_df = pd.DataFrame([[
            region_encoded, year, month,
            rainfall, temperature, humidity,
            r_t, r_h,
            rainy, high_rain, high_temp
        ]], columns=self.feature_columns)

        features_scaled = self.scaler.transform(features_df)
        prediction = self.model.predict(features_scaled)[0]
        risk = self.risk_encoder.inverse_transform([prediction])[0]

        prob_dict = {}
        if hasattr(self.model, "predict_proba"):
            probs = self.model.predict_proba(features_scaled)[0]
            for i, label in enumerate(self.risk_encoder.classes_):
                prob_dict[label] = round(float(probs[i]) * 100, 2)
            confidence = round(float(max(probs)) * 100, 2)
        else:
            confidence = 85.0
            prob_dict = {risk: confidence}

        return {
            "risk": risk,
            "confidence": confidence,
            "probabilities": prob_dict
        }

    def save_model(self, path="flood_ai_model.pkl"):
        save_data = {
            "model": self.model,
            "region_encoder": self.region_encoder,
            "risk_encoder": self.risk_encoder,
            "scaler": self.scaler,
            "is_trained": self.is_trained,
            "training_records": self.training_records,
            "trained_regions": self.trained_regions,
            "feature_columns": self.feature_columns
        }
        joblib.dump(save_data, path)
        print(f"✅ Model saved to {path}")

    def load_model(self, path="flood_ai_model.pkl"):
        if not os.path.exists(path):
            print(f"⚠️ Model file {path} not found")
            return False

        try:
            data = joblib.load(path)
            self.model = data["model"]
            self.region_encoder = data["region_encoder"]
            self.risk_encoder = data["risk_encoder"]
            self.scaler = data["scaler"]
            self.is_trained = data["is_trained"]
            self.training_records = data.get("training_records", 0)
            self.trained_regions = data.get("trained_regions", [])
            if "feature_columns" in data:
                self.feature_columns = data["feature_columns"]
            print(f"✅ Model loaded from {path} ({self.training_records} training records)")
            return True
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False


ai_model = FloodPredictionModel()