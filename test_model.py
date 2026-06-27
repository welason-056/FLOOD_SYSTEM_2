import pickle
import numpy as np

# Load model and encoder
with open('flood_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('community_encoder.pkl', 'rb') as f:
    encoder = pickle.load(f)

# Test communities
communities = ['Jangwani', 'Kigogo', 'Buguruni', 'Kawe']

print("🔍 Testing with real-world weather scenarios:\n")

# Scenario 1: High risk (heavy rain + high humidity + wet soil)
print("🌧️ Scenario 1: Heavy rain (200mm), 26°C, 90% humidity, 60% soil moisture")
rainfall = 200
temperature = 26
humidity = 90
soil_moisture = 60
print("-" * 50)
for comm in communities:
    try:
        encoded = encoder.transform([comm])[0]
    except ValueError:
        print(f"⚠️ Community '{comm}' not known by encoder. Skipping.")
        continue
    input_data = np.array([[encoded, rainfall, temperature, humidity, soil_moisture]])
    proba = model.predict_proba(input_data)[0][1]
    risk = "HIGH" if proba >= 0.7 else "MODERATE" if proba >= 0.3 else "LOW"
    print(f"{comm}: {risk} (probability: {proba:.2%})")

print("\n" + "=" * 50)

# Scenario 2: Low risk (light rain + dry)
print("\n☀️ Scenario 2: Light rain (10mm), 30°C, 50% humidity, 20% soil moisture")
rainfall = 10
temperature = 30
humidity = 50
soil_moisture = 20
print("-" * 50)
for comm in communities:
    try:
        encoded = encoder.transform([comm])[0]
    except ValueError:
        continue
    input_data = np.array([[encoded, rainfall, temperature, humidity, soil_moisture]])
    proba = model.predict_proba(input_data)[0][1]
    risk = "HIGH" if proba >= 0.7 else "MODERATE" if proba >= 0.3 else "LOW"
    print(f"{comm}: {risk} (probability: {proba:.2%})")

print("\n" + "=" * 50)

# Scenario 3: Borderline (medium conditions)
print("\n🌤️ Scenario 3: Medium rain (80mm), 28°C, 75% humidity, 40% soil moisture")
rainfall = 80
temperature = 28
humidity = 75
soil_moisture = 40
print("-" * 50)
for comm in communities:
    try:
        encoded = encoder.transform([comm])[0]
    except ValueError:
        continue
    input_data = np.array([[encoded, rainfall, temperature, humidity, soil_moisture]])
    proba = model.predict_proba(input_data)[0][1]
    risk = "HIGH" if proba >= 0.7 else "MODERATE" if proba >= 0.3 else "LOW"
    print(f"{comm}: {risk} (probability: {proba:.2%})")

print("\n✅ Test complete!")