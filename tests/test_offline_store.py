import pytest
import polars as pl
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.offline_store.store import compute_location_features, save_features, get_training_dataset
from datetime import datetime


@pytest.fixture
def sample_df():
    return pl.DataFrame({
        "PULocationID": [1, 1, 2, 2, 3],
        "trip_distance": [2.5, 3.0, 1.5, 2.0, 5.0],
        "fare_amount": [10.0, 12.0, 8.0, 9.0, 20.0],
        "tip_amount": [2.0, 1.5, 0.5, 1.0, 3.0],
        "trip_duration_minutes": [10.0, 12.0, 8.0, 9.0, 25.0],
    })


def test_compute_location_features(sample_df):
    features = compute_location_features(sample_df)
    assert "avg_trip_distance_7d" in features.columns
    assert "avg_fare_7d" in features.columns
    assert "tip_rate_7d" in features.columns
    assert "trip_count_7d" in features.columns
    assert "avg_trip_duration_minutes_7d" in features.columns
    assert "entity_id" in features.columns
    assert "feature_timestamp" in features.columns


def test_feature_row_count(sample_df):
    features = compute_location_features(sample_df)
    # 3 unique PULocationIDs
    assert len(features) == 3


def test_no_null_features(sample_df):
    features = compute_location_features(sample_df)
    for col in ["avg_trip_distance_7d", "avg_fare_7d", "trip_count_7d"]:
        assert features[col].null_count() == 0


def test_save_and_load_features(sample_df, tmp_path, monkeypatch):
    test_path = tmp_path / "features.parquet"
    monkeypatch.setattr("src.offline_store.store.FEATURES_PATH", test_path)
    features = compute_location_features(sample_df)
    save_features(features)
    assert test_path.exists()
    loaded = pl.read_parquet(test_path)
    assert len(loaded) == len(features)


def test_trip_count_correct(sample_df):
    features = compute_location_features(sample_df)
    location_1 = features.filter(pl.col("entity_id") == "1")
    assert location_1["trip_count_7d"][0] == 2