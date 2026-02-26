import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import MagicMock, patch


def test_get_online_features_returns_dict():
    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {
        "avg_trip_distance_7d": "3.02",
        "avg_fare_7d": "17.92",
        "tip_rate_7d": "0.12",
        "trip_count_7d": "1108.0",
        "avg_trip_duration_minutes_7d": "14.85",
        "feature_timestamp": "2026-02-26"
    }

    with patch("src.online_store.store.get_redis_client", return_value=mock_redis):
        from src.online_store.store import get_online_features
        result = get_online_features("146")
        assert isinstance(result, dict)
        assert "avg_fare_7d" in result
        assert result["avg_fare_7d"] == 17.92


def test_get_online_features_missing_entity():
    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {}

    with patch("src.online_store.store.get_redis_client", return_value=mock_redis):
        from src.online_store.store import get_online_features
        result = get_online_features("999")
        assert result == {}


def test_get_online_features_filtered():
    mock_redis = MagicMock()
    mock_redis.hgetall.return_value = {
        "avg_trip_distance_7d": "3.02",
        "avg_fare_7d": "17.92",
        "tip_rate_7d": "0.12",
        "trip_count_7d": "1108.0",
        "avg_trip_duration_minutes_7d": "14.85",
        "feature_timestamp": "2026-02-26"
    }

    with patch("src.online_store.store.get_redis_client", return_value=mock_redis):
        from src.online_store.store import get_online_features
        result = get_online_features("146", ["avg_fare_7d", "tip_rate_7d"])
        assert set(result.keys()) == {"avg_fare_7d", "tip_rate_7d"}


def test_online_store_stats():
    mock_redis = MagicMock()
    mock_redis.keys.return_value = [
        "features:PULocationID:1",
        "features:PULocationID:2",
        "features:PULocationID:3"
    ]

    with patch("src.online_store.store.get_redis_client", return_value=mock_redis):
        from src.online_store.store import get_online_store_stats
        stats = get_online_store_stats()
        assert stats["total_entities"] == 3