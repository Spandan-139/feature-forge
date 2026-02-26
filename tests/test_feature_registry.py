import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.feature_registry.database import init_db, get_connection
from src.feature_registry.registry import (
    register_feature, get_feature_by_name,
    list_features, update_feature_status, delete_feature
)
from src.feature_registry.models import FeatureCreate, FeatureType, FeatureStatus


@pytest.fixture(autouse=True)
def setup_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_registry.db"
    monkeypatch.setattr("src.feature_registry.database.DB_PATH", test_db)
    init_db()


def make_feature(name="test_feature"):
    return FeatureCreate(
        name=name,
        description="Test feature",
        data_type=FeatureType.FLOAT,
        entity="user_id",
        computation="mean(x) WHERE window=7d",
        owner="spandan",
        tags=["test"],
        status=FeatureStatus.EXPERIMENTAL
    )


def test_register_feature():
    feature = register_feature(make_feature())
    assert feature["name"] == "test_feature"
    assert feature["version"] == 1
    assert feature["status"] == "experimental"


def test_get_feature_by_name():
    register_feature(make_feature())
    feature = get_feature_by_name("test_feature")
    assert feature is not None
    assert feature["entity"] == "user_id"
    assert feature["owner"] == "spandan"


def test_duplicate_feature_raises():
    register_feature(make_feature())
    with pytest.raises(Exception):
        register_feature(make_feature())


def test_list_features():
    register_feature(make_feature("feature_a"))
    register_feature(make_feature("feature_b"))
    features = list_features()
    assert len(features) == 2


def test_list_features_by_entity():
    register_feature(make_feature("feature_a"))
    features = list_features(entity="user_id")
    assert all(f["entity"] == "user_id" for f in features)


def test_update_feature_status():
    register_feature(make_feature())
    updated = update_feature_status("test_feature", "active")
    assert updated["status"] == "active"
    assert updated["version"] == 2


def test_delete_feature():
    register_feature(make_feature())
    result = delete_feature("test_feature")
    assert result is True
    assert get_feature_by_name("test_feature") is None


def test_delete_nonexistent_feature():
    result = delete_feature("does_not_exist")
    assert result is False