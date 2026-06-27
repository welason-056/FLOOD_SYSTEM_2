import joblib
from django.conf import settings

model = joblib.load(settings.BASE_DIR / "flood_model.pkl")

def predict_flood(rainfall, duration, affected, deaths):

    X = [[
        rainfall,
        duration,
        affected,
        deaths
    ]]

    result = model.predict(X)[0]

    probability = None
    if hasattr(model, "predict_proba"):
        probability = model.predict_proba(X)[0][1]

    return {
        "risk": "HIGH" if result == 1 else "LOW",
        "probability": probability
    }