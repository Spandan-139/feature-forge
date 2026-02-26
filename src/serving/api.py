import os
import time
import mlflow
import mlflow.sklearn
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger
from src.online_store.store import get_online_features

mlflow.set_tracking_uri(os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000"))

app = FastAPI(title="Feature Forge Serving API", version="1.0.0")

FEATURE_NAMES = [
    "avg_trip_distance_7d",
    "avg_fare_7d",
    "trip_count_7d",
    "avg_trip_duration_minutes_7d"
]

model_cache = {"model": None, "version": None}


def load_production_model():
    if model_cache["model"] is not None:
        return model_cache["model"]
    logger.info("Loading production model from MLflow...")
    model = mlflow.sklearn.load_model("models:/feature-forge-random-forest/Production")
    model_cache["model"] = model
    logger.info("Production model loaded and cached")
    return model


class PredictionRequest(BaseModel):
    location_id: str


class PredictionResponse(BaseModel):
    location_id: str
    predicted_tip_rate: float
    features_used: dict
    latency_ms: float
    model: str = "feature-forge-random-forest/Production"


@app.on_event("startup")
def startup():
    load_production_model()


@app.post("/predict", response_model=PredictionResponse)
def predict(request: PredictionRequest):
    start = time.time()

    features = get_online_features(request.location_id, FEATURE_NAMES)
    if not features:
        raise HTTPException(
            status_code=404,
            detail=f"No features found for location_id: {request.location_id}"
        )

    X = np.array([[features[f] for f in FEATURE_NAMES]])

    model = load_production_model()
    prediction = model.predict(X)[0]

    latency_ms = (time.time() - start) * 1000
    logger.info(f"Prediction for location {request.location_id}: {prediction:.4f} | {latency_ms:.2f}ms")

    return PredictionResponse(
        location_id=request.location_id,
        predicted_tip_rate=round(float(prediction), 4),
        features_used=features,
        latency_ms=round(latency_ms, 2)
    )


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": model_cache["model"] is not None}


@app.get("/locations/sample")
def sample_locations():
    from src.online_store.store import get_online_store_stats
    stats = get_online_store_stats()
    return {
        "total_locations": stats["total_entities"],
        "sample_ids": [k.split(":")[-1] for k in stats["sample_keys"]]
    }