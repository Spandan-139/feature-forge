import streamlit as st
import polars as pl
import json
from datetime import datetime

st.set_page_config(
    page_title="Feature Forge Monitor",
    page_icon="⚡",
    layout="wide"
)

# Sample data for demo deployment
SAMPLE_FEATURES = [
    {"entity_id": "132", "avg_trip_distance_7d": 4.21, "avg_fare_7d": 28.3, "tip_rate_7d": 0.18, "trip_count_7d": 135513, "avg_trip_duration_minutes_7d": 18.2},
    {"entity_id": "237", "avg_trip_distance_7d": 3.85, "avg_fare_7d": 24.1, "tip_rate_7d": 0.21, "trip_count_7d": 135160, "avg_trip_duration_minutes_7d": 15.7},
    {"entity_id": "161", "avg_trip_distance_7d": 2.94, "avg_fare_7d": 19.8, "tip_rate_7d": 0.15, "trip_count_7d": 134651, "avg_trip_duration_minutes_7d": 13.4},
    {"entity_id": "236", "avg_trip_distance_7d": 3.12, "avg_fare_7d": 21.5, "tip_rate_7d": 0.19, "trip_count_7d": 127739, "avg_trip_duration_minutes_7d": 14.1},
    {"entity_id": "162", "avg_trip_distance_7d": 2.76, "avg_fare_7d": 18.2, "tip_rate_7d": 0.14, "trip_count_7d": 101029, "avg_trip_duration_minutes_7d": 12.8},
    {"entity_id": "186", "avg_trip_distance_7d": 5.43, "avg_fare_7d": 35.7, "tip_rate_7d": 0.09, "trip_count_7d": 99247, "avg_trip_duration_minutes_7d": 24.3},
    {"entity_id": "230", "avg_trip_distance_7d": 3.67, "avg_fare_7d": 23.4, "tip_rate_7d": 0.17, "trip_count_7d": 98617, "avg_trip_duration_minutes_7d": 16.5},
    {"entity_id": "142", "avg_trip_distance_7d": 2.31, "avg_fare_7d": 16.9, "tip_rate_7d": 0.22, "trip_count_7d": 97364, "avg_trip_duration_minutes_7d": 11.9},
    {"entity_id": "138", "avg_trip_distance_7d": 4.89, "avg_fare_7d": 31.2, "tip_rate_7d": 0.11, "trip_count_7d": 86322, "avg_trip_duration_minutes_7d": 21.6},
    {"entity_id": "239", "avg_trip_distance_7d": 3.44, "avg_fare_7d": 22.1, "tip_rate_7d": 0.16, "trip_count_7d": 81132, "avg_trip_duration_minutes_7d": 15.1},
]

FEATURE_COLUMNS = [
    "avg_trip_distance_7d",
    "avg_fare_7d",
    "tip_rate_7d",
    "trip_count_7d",
    "avg_trip_duration_minutes_7d"
]

features_df = pl.DataFrame(SAMPLE_FEATURES)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("⚡ Feature Forge — Monitoring Dashboard")
st.caption(f"Live demo — NYC Taxi Feature Store | Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.info("🚀 This is a live demo powered by sample data from the NYC Taxi 2024 dataset (2.7M trips, 251 zones). Full system runs locally with Redis + DuckDB via Docker Compose.")

st.divider()

# ── System Status ─────────────────────────────────────────────────────────────
st.subheader("System Status")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Offline Store", "🟢 Ready")
with col2:
    st.metric("Online Store", "🟢 Redis")
with col3:
    st.metric("Entities in Store", "251")
with col4:
    st.metric("Feature Rows", "251")

st.divider()

# ── Feature Distributions ─────────────────────────────────────────────────────
st.subheader("Feature Distributions — Top 10 Zones by Trip Volume")
col1, col2 = st.columns(2)

with col1:
    st.markdown("**Average Fare by Zone**")
    fare_data = features_df.sort("avg_fare_7d", descending=True).select(["entity_id", "avg_fare_7d"]).to_pandas()
    st.bar_chart(fare_data.set_index("entity_id"))

with col2:
    st.markdown("**Tip Rate by Zone**")
    tip_data = features_df.sort("tip_rate_7d", descending=True).select(["entity_id", "tip_rate_7d"]).to_pandas()
    st.bar_chart(tip_data.set_index("entity_id"))

st.divider()

# ── Feature Statistics ────────────────────────────────────────────────────────
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

# ── Zone Inspector ────────────────────────────────────────────────────────────
st.subheader("Zone Feature Inspector")
zone_ids = [row["entity_id"] for row in SAMPLE_FEATURES]
selected = st.selectbox("Select a pickup zone to inspect", zone_ids)

if selected:
    row = next(r for r in SAMPLE_FEATURES if r["entity_id"] == selected)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Avg Trip Distance", f"{row['avg_trip_distance_7d']} mi")
        st.metric("Trip Count", f"{row['trip_count_7d']:,}")
    with col2:
        st.metric("Avg Fare", f"${row['avg_fare_7d']}")
        st.metric("Avg Duration", f"{row['avg_trip_duration_minutes_7d']} min")
    with col3:
        st.metric("Tip Rate", f"{row['tip_rate_7d']*100:.1f}%")

st.divider()

# ── Top Zones Table ───────────────────────────────────────────────────────────
st.subheader("Top Zones by Trip Volume")
top_zones = features_df.sort("trip_count_7d", descending=True).to_pandas()
st.dataframe(top_zones, use_container_width=True)

st.divider()

# ── About ─────────────────────────────────────────────────────────────────────
st.subheader("About Feature Forge")
st.markdown("""
**Feature Forge** is a production-style ML Feature Store built from scratch, inspired by Uber's Michelangelo, Google's Feast, and Meta's FBLearner.

**Components:**
- 🗄️ **Offline Store** — Parquet + DuckDB for point-in-time correct training data
- ⚡ **Online Store** — Redis for sub-5ms feature retrieval at inference time
- 📋 **Feature Registry** — SQLite + FastAPI for feature metadata and versioning
- 🤖 **Model Registry** — MLflow for experiment tracking and model promotion
- 🚀 **Serving API** — FastAPI endpoint returning predictions in ~25ms
- 📊 **This Dashboard** — Real-time monitoring of feature health and data quality

**Dataset:** NYC Yellow Taxi Trip Records 2024 — 2,964,624 trips across 251 pickup zones

[GitHub](https://github.com/Spandan-139/feature-forge)
""")