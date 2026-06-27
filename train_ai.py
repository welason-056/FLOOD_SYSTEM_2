import pandas as pd
import pickle
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

# Load data
train_df = pd.read_csv('train.csv')
test_df = pd.read_csv('test.csv')

# Convert Flood_Risk to binary (1=Flood, 0=No Flood)
def map_risk_to_binary(risk):
    if risk in ['High', 'Medium']:
        return 1
    else:
        return 0

train_df['Flood_Risk_Binary'] = train_df['Flood_Risk'].apply(map_risk_to_binary)
test_df['Flood_Risk_Binary'] = test_df['Flood_Risk'].apply(map_risk_to_binary)

print("📊 Binary target distribution in training:")
print(train_df['Flood_Risk_Binary'].value_counts())

# Encode community
encoder = LabelEncoder()
train_df['community_encoded'] = encoder.fit_transform(train_df['Community'])
test_df['community_encoded'] = encoder.transform(test_df['Community'])

# Features
features = ['community_encoded', 'Rainfall', 'Temperature', 'Humidity', 'Soil moisture']
X_train = train_df[features]
y_train = train_df['Flood_Risk_Binary']
X_test = test_df[features]
y_test = test_df['Flood_Risk_Binary']

# Train with balanced class weights
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42,
    class_weight='balanced'   # ← FIX
)
scores = cross_val_score(model, X_train, y_train, cv=5, scoring='accuracy')
print(f"✅ Cross-validated accuracy: {scores.mean():.2%} (±{scores.std():.2%})")

model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(f"\nTest set accuracy: {accuracy_score(y_test, y_pred):.2%}")
print("\n📋 Classification Report:")
print(classification_report(y_test, y_pred))

# Feature importance
importances = model.feature_importances_
feature_names = ['Community', 'Rainfall', 'Temperature', 'Humidity', 'Soil moisture']
print("\n📈 Feature Importance:")
for name, imp in zip(feature_names, importances):
    print(f"  {name}: {imp:.4f}")

# Save
with open('flood_model.pkl', 'wb') as f:
    pickle.dump(model, f)
with open('community_encoder.pkl', 'wb') as f:
    pickle.dump(encoder, f)

print("\n✅ Model and encoder saved successfully!")