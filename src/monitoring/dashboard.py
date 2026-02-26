import streamlit as st
import polars as pl
import duckdb
import redis
import json
from pathlib import Path
from datetime import datetime
import numpy as np

st.set_page_config(
    page_title="Feature Forge Monitor",
    page_icon="⚡",
    layout="wide"
)

FEATURES_PATH = Path("data/processed/features.parquet")

FEATURE_COLUMNS = [
    "avg_trip_distance_7d",
    "avg_fare_7d",
    "tip_rate_7d",
    "trip_count_7d",
    "avg_trip_duration_minutes_7d"
]


def get_redis_client():
    try:
        client = redis.Redis(host="localhost", port=6379, decode_responses=True)
        client.ping()
        return client
    except:
        return None


def load_features():
    if FEATURES_PATH.exists():
        return pl.read_parquet(FEATURES_PATH)
    return None


# ── Header ──────────────────────────────────────────────────────────────────
st.title("⚡ Feature Forge — Monitoring Dashboard")
st.caption(f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ── System Status ────────────────────────────────────────────────────────────
st.subheader("System Status")
col1, col2, col3, col4 = st.columns(4)

redis_client = get_redis_client()
features_df = load_features()

with col1:
    st.metric("Redis", "🟢 Online" if redis_client else "🔴 Offline")

with col2:
    st.metric("Offline Store", "🟢 Ready" if features_df is not None else "🔴 Missing")

with col3:
    total_entities = len(redis_client.keys("features:PULocationID:*")) if redis_client else 0
    st.metric("Entities in Online Store", total_entities)

with col4:
    total_features = len(features_df) if features_df is not None else 0
    st.metric("Feature Rows (Offline)", total_features)

st.divider()

# ── Feature Distributions ────────────────────────────────────────────────────
if features_df is not None:
    st.subheader("Feature Distributions")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Average Fare by Zone (top 20)**")
        top_fare = (
            features_df
            .sort("avg_fare_7d", descending=True)
            .head(20)
            .select(["entity_id", "avg_fare_7d"])
            .to_pandas()
        )
        st.bar_chart(top_fare.set_index("entity_id"))

    with col2:
        st.markdown("**Tip Rate Distribution**")
        tip_data = features_df.select("tip_rate_7d").to_pandas()
        st.bar_chart(tip_data["tip_rate_7d"].value_counts().sort_index())

    st.divider()

    # ── Feature Stats Table ───────────────────────────────────────────────────
    st.subheader("Feature Statistics")
    stats = {}
    for col in FEATURE_COLUMNS:
        series = features_df[col]
        stats[col] = {
            "mean": round(float(series.mean()), 4),
            "std": round(float(series.std()), 4),
            "min": round(float(series.min()), 4),
            "max": round(float(series.max()), 4),
            "null_count": int(series.null_count())
        }
    st.dataframe(pl.DataFrame(stats).transpose(include_header=True, header_name="feature"), use_container_width=True)

    st.divider()

    # ── Online Store Spot Check ───────────────────────────────────────────────
    st.subheader("Online Store Spot Check")
    location_id = st.text_input("Enter Location ID to inspect", value="146")
    if redis_client and location_id:
        key = f"features:PULocationID:{location_id}"
        data = redis_client.hgetall(key)
        if data:
            st.success(f"Features found for location {location_id}")
            st.json(data)
        else:
            st.warning(f"No features found in Redis for location: {location_id}")

    st.divider()

    # ── Data Quality ──────────────────────────────────────────────────────────
    st.subheader("Data Quality")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Null Counts per Feature**")
        null_data = {col: features_df[col].null_count() for col in FEATURE_COLUMNS}
        st.json(null_data)

    with col2:
        st.markdown("**Zones with highest trip volume**")
        top_zones = (
            features_df
            .sort("trip_count_7d", descending=True)
            .head(10)
            .select(["entity_id", "trip_count_7d"])
            .to_pandas()
        )
        st.dataframe(top_zones, use_container_width=True)

else:
    st.warning("No feature data found. Run the pipeline first.")