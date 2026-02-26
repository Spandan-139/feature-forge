import polars as pl
import duckdb
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta, timezone

RAW_DATA_PATH = Path("data/raw/yellow_tripdata_2024-01.parquet")
PROCESSED_PATH = Path("data/processed")
FEATURES_PATH = PROCESSED_PATH / "features.parquet"


def load_raw_data() -> pl.DataFrame:
    logger.info("Loading raw NYC taxi data...")
    df = pl.read_parquet(RAW_DATA_PATH)
    # Basic cleaning
    df = df.filter(
        (pl.col("fare_amount") > 0) &
        (pl.col("trip_distance") > 0) &
        (pl.col("passenger_count") > 0) &
        (pl.col("tpep_pickup_datetime").is_not_null()) &
        (pl.col("tpep_dropoff_datetime").is_not_null())
    )
    # Add trip duration in minutes
    df = df.with_columns([
        ((pl.col("tpep_dropoff_datetime") - pl.col("tpep_pickup_datetime"))
         .dt.total_seconds() / 60).alias("trip_duration_minutes")
    ])
    df = df.filter(
        (pl.col("trip_duration_minutes") > 1) &
        (pl.col("trip_duration_minutes") < 180)
    )
    logger.info(f"Cleaned data shape: {df.shape}")
    return df


def compute_location_features(df: pl.DataFrame) -> pl.DataFrame:
    logger.info("Computing location-based features...")
    features = df.group_by("PULocationID").agg([
        pl.col("trip_distance").mean().alias("avg_trip_distance_7d"),
        pl.col("fare_amount").mean().alias("avg_fare_7d"),
        (pl.col("tip_amount") / pl.col("fare_amount")).mean().alias("tip_rate_7d"),
        pl.col("trip_distance").count().alias("trip_count_7d"),
        pl.col("trip_duration_minutes").mean().alias("avg_trip_duration_minutes_7d"),
    ]).with_columns([
        pl.lit(datetime.now(timezone.utc)).alias("feature_timestamp"),
        pl.col("PULocationID").cast(pl.Utf8).alias("entity_id"),
        pl.lit("PULocationID").alias("entity_type"),
    ])
    return features


def save_features(features: pl.DataFrame):
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    features.write_parquet(FEATURES_PATH)
    logger.info(f"Saved {len(features)} feature rows to {FEATURES_PATH}")


def get_training_dataset(feature_names: list[str]) -> pl.DataFrame:
    logger.info("Generating training dataset from offline store...")
    conn = duckdb.connect()
    cols = ", ".join(["entity_id", "feature_timestamp"] + feature_names)
    query = f"SELECT {cols} FROM read_parquet('{FEATURES_PATH}')"
    result = conn.execute(query).pl()
    conn.close()
    logger.info(f"Training dataset shape: {result.shape}")
    return result


def run_pipeline():
    df = load_raw_data()
    features = compute_location_features(df)
    save_features(features)
    return features