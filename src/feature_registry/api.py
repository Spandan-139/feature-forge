from fastapi import FastAPI, HTTPException
from typing import Optional
from .models import FeatureCreate, FeatureResponse
from .registry import (
    register_feature, get_feature_by_name,
    list_features, update_feature_status, delete_feature
)
from .database import init_db

app = FastAPI(title="Feature Registry", version="1.0.0")


@app.on_event("startup")
def startup():
    init_db()


@app.post("/features", response_model=FeatureResponse)
def create_feature(feature: FeatureCreate):
    existing = get_feature_by_name(feature.name)
    if existing:
        raise HTTPException(status_code=409, detail=f"Feature '{feature.name}' already exists")
    return register_feature(feature)


@app.get("/features", response_model=list[FeatureResponse])
def get_features(entity: Optional[str] = None, tag: Optional[str] = None):
    return list_features(entity=entity, tag=tag)


@app.get("/features/{name}", response_model=FeatureResponse)
def get_feature(name: str):
    feature = get_feature_by_name(name)
    if not feature:
        raise HTTPException(status_code=404, detail=f"Feature '{name}' not found")
    return feature


@app.patch("/features/{name}/status")
def update_status(name: str, status: str):
    updated = update_feature_status(name, status)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Feature '{name}' not found")
    return updated


@app.delete("/features/{name}")
def remove_feature(name: str):
    success = delete_feature(name)
    if not success:
        raise HTTPException(status_code=404, detail=f"Feature '{name}' not found")
    return {"message": f"Feature '{name}' deleted"}