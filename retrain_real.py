# retrain_real.py
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, accuracy_score
from sklearn.model_selection import train_test_split

print("=" * 70)
print("FLOODGUARD AI – REAL DATA TRAINING (BINARY: Low vs High)")
print("=" * 70)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
train_path = os.path.join(BASE_DIR, 'train.csv')
test_path = os.path.join(BASE_DIR, 'test.csv')

if not os.path.exists(train_path):
    print("❌ train.csv not found!")
    exit()

# Load data
train_df = pd.read_csv(train_path)

# Rename columns to match expected names
column_mapping = {
    'Rainfall': 'rainfall',
    'Temperature': 'temperature',
    'Humidity': 'humidity',
    'Soil moisture': 'soil_moisture',
    'Community': 'community',
    'Flood_Risk': 'flood_risk',
    'Date': 'date'
}
train_df.rename(columns=column_mapping, inplace=True)

# Convert flood_risk to numeric (Low=0, High=1) – discard Moderate if any (there are none)
risk_mapping = {'Low': 0, 'High': 1}
train_df['flood_risk'] = train_df['flood_risk'].map(risk_mapping)
train_df = train_df.dropna(subset=['flood_risk'])

print(f"\n📊 Class distribution:")
counts = train_df['flood_risk'].value_counts().sort_index()
print(f"   Low (0): {counts.get(0, 0)}")
print(f"   High (1): {counts.get(1, 0)}")

# Load test data if exists
if os.path.exists(test_path):
    test_df = pd.read_csv(test_path)
    test_df.rename(columns=column_mapping, inplace=True)
    test_df['flood_risk'] = test_df['flood_risk'].map(risk_mapping)
    test_df = test_df.dropna(subset=['flood_risk'])
    print(f"\n✅ Using separate test.csv with {len(test_df)} samples")
else:
    test_df = None

# Feature engineering
def add_features(df):
    df['rain_intensity'] = df['rainfall'] * df['humidity'] / 100
    df['soil_effect'] = df['soil_moisture'] * df['rainfall']
    df['heavy_rain'] = (df['rainfall'] > 50).astype(int)
    df['humidity_soil'] = df['humidity'] * df['soil_moisture'] / 100
    return df

train_df = add_features(train_df)
if test_df is not None:
    test_df = add_features(test_df)

# Encode communities
community_encoder = LabelEncoder()
train_df['community_encoded'] = community_encoder.fit_transform(train_df['community'])
if test_df is not None:
    test_df['community_encoded'] = community_encoder.transform(test_df['community'])

features = [
    'community_encoded',
    'rainfall', 'temperature', 'humidity', 'soil_moisture',
    'rain_intensity', 'soil_effect', 'heavy_rain', 'humidity_soil'
]

X_train = train_df[features]
y_train = train_df['flood_risk']

if test_df is not None:
    X_test = test_df[features]
    y_test = test_df['flood_risk']
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X_train, y_train, test_size=0.2, random_state=42
    )

print(f"\n📊 Training shape: {X_train.shape}, Testing shape: {X_test.shape}")

# Train model (with class balancing)
model = RandomForestClassifier(
    n_estimators=200,
    max_depth=25,
    min_samples_split=5,
    class_weight='balanced',
    random_state=42,
    n_jobs=-1
)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"\n✅ Accuracy: {accuracy_score(y_test, y_pred):.2f}")
print("\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=['Low', 'High']))

# Feature importance
print("\n🔑 Feature Importance:")
for name, imp in sorted(zip(features, model.feature_importances_), key=lambda x: x[1], reverse=True):
    print(f"   {name}: {imp:.3f}")

# Save
pickle.dump(model, open(os.path.join(BASE_DIR, 'flood_model.pkl'), 'wb'))
pickle.dump(community_encoder, open(os.path.join(BASE_DIR, 'community_encoder.pkl'), 'wb'))
pickle.dump(features, open(os.path.join(BASE_DIR, 'feature_columns.pkl'), 'wb'))

# Save label encoder for binary classes (Low=0, High=1)
label_encoder = LabelEncoder()
label_encoder.fit(['Low', 'High'])  # only two classes
pickle.dump(label_encoder, open(os.path.join(BASE_DIR, 'label_encoder.pkl'), 'wb'))

print("\n✅ Model and encoders saved successfully!")
print("\nNow restart the server and test predictions.")