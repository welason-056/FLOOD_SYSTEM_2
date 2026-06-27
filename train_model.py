# prediction/train_model.py (new version for Dar communities)
import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report

# Paths – files are in the project root (one level above prediction/)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
train_path = os.path.join(BASE_DIR, 'train.csv')
test_path = os.path.join(BASE_DIR, 'test.csv')

print("Loading data...")
train_df = pd.read_csv(train_path)
test_df = pd.read_csv(test_path)

# Encode community names
community_encoder = LabelEncoder()
train_df['community_encoded'] = community_encoder.fit_transform(train_df['community'])
test_df['community_encoded'] = community_encoder.transform(test_df['community'])

# Features – exactly the columns we have
features = ['community_encoded', 'rainfall', 'temperature', 'humidity', 'soil_moisture']
X_train = train_df[features]
y_train = train_df['flood_risk']
X_test = test_df[features]
y_test = test_df['flood_risk']

print("Training Random Forest...")
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)
print(f"Accuracy: {acc:.2f}")
print(classification_report(y_test, y_pred))

# Save everything in the project root
model_path = os.path.join(BASE_DIR, 'flood_model.pkl')
encoder_path = os.path.join(BASE_DIR, 'community_encoder.pkl')
features_path = os.path.join(BASE_DIR, 'feature_columns.pkl')

pickle.dump(model, open(model_path, 'wb'))
pickle.dump(community_encoder, open(encoder_path, 'wb'))
pickle.dump(features, open(features_path, 'wb'))

print("✅ Model, community encoder, and feature columns saved.")
print(f"Communities: {list(community_encoder.classes_)}")