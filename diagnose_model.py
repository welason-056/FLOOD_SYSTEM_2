import pickle
import pandas as pd
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix

# Load model
with open('flood_model.pkl', 'rb') as f:
    model = pickle.load(f)
with open('community_encoder.pkl', 'rb') as f:
    encoder = pickle.load(f)

# Load test data
test_df = pd.read_csv('test.csv')

def map_risk_to_binary(risk):
    return 1 if risk in ['High', 'Medium'] else 0

test_df['Flood_Risk_Binary'] = test_df['Flood_Risk'].apply(map_risk_to_binary)
test_df['community_encoded'] = encoder.transform(test_df['Community'])

X_test = test_df[['community_encoded', 'Rainfall', 'Temperature', 'Humidity', 'Soil moisture']]
y_test = test_df['Flood_Risk_Binary']

# Get probabilities
probs = model.predict_proba(X_test)[:, 1]  # probability of flood

# See distribution of probabilities
print("📊 Probability distribution (flood class):")
print(f"  Min: {probs.min():.2%}")
print(f"  Max: {probs.max():.2%}")
print(f"  Mean: {probs.mean():.2%}")
print(f"  Median: {np.median(probs):.2%}")

# Check how many predictions are above different thresholds
thresholds = [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
print("\n📈 Predictions above thresholds:")
for t in thresholds:
    count = np.sum(probs >= t)
    print(f"  Probability ≥ {t:.0%}: {count} ({count/len(probs):.1%})")

# Compare with actual labels
print("\n📊 Actual vs Predicted:")
cm = confusion_matrix(y_test, probs >= 0.5)
print(cm)
print(classification_report(y_test, probs >= 0.5))