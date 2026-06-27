import os
import sys
import django
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score

# ADD PROJECT ROOT TO PATH
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# DJANGO SETTINGS
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flood_system.settings')

django.setup()

# IMPORT MODEL
from prediction.models import FloodClimateData

# LOAD DATA
data = FloodClimateData.objects.all().values()

# CONVERT TO DATAFRAME
df = pd.DataFrame(data)

print("DATABASE DATA:")
print(df.head())

# ENCODE REGION
encoder = LabelEncoder()
df['region'] = encoder.fit_transform(df['region'])

# FEATURES
X = df[['year', 'region', 'rainfall_mm', 'temperature']]

# TARGET
y = df['flood']

# SPLIT DATA
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# TRAIN MODEL
model = RandomForestClassifier()

model.fit(X_train, y_train)

# PREDICTIONS
predictions = model.predict(X_test)

# ACCURACY
accuracy = accuracy_score(y_test, predictions)

print(f"Model Accuracy: {accuracy * 100:.2f}%")

# SAVE MODEL
joblib.dump(model, 'flood_model.pkl')

# SAVE ENCODER
joblib.dump(encoder, 'region_encoder.pkl')

print("MODEL TRAINED SUCCESSFULLY")