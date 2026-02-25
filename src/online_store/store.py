import redis
import json
import polars as pl
from pathlib import Path
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed

FEATURES_PATH = Path("data/processed/features.parquet")

FEATURE_COLUMNS = [
    "avg_trip_distance_7d",
    "avg_fare_7d",
    "tip_rate_7d",
    "trip_count_7d",
    "avg_trip_duration_minutes_7d"
]


def get_redis_client():
    return redis.Redis(host="localhost", port=6379, decode_responses=True)


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def sync_to_online_store():
    logger.info("Syncing offline store → online store (Redis)...")
    df = pl.read_parquet(FEATURES_PATH)
    client = get_redis_client()

    synced = 0
    for row in df.iter_rows(named=True):
        entity_id = row["entity_id"]
        feature_data = {col: round(float(row[col]), 6) for col in FEATURE_COLUMNS}
        feature_data["feature_timestamp"] = str(row["feature_timestamp"])

        client.hset(f"features:PULocationID:{entity_id}", mapping=feature_data)
        synced += 1

    logger.info(f"Synced {synced} entities to Redis")
    return synced


def get_online_features(entity_id: str, feature_names: list[str] = None) -> dict:
    client = get_redis_client()
    key = f"features:PULocationID:{entity_id}"
    data = client.hgetall(key)

    if not data:
        logger.warning(f"No features found in online store for entity: {entity_id}")
        return {}

    if feature_names:
        data = {k: v for k, v in data.items() if k in feature_names}

    return {k: float(v) if k != "feature_timestamp" else v for k, v in data.items()}


def get_online_store_stats() -> dict:
    client = get_redis_client()
    keys = client.keys("features:PULocationID:*")
    return {
        "total_entities": len(keys),
        "sample_keys": keys[:5]
    }