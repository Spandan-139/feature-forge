# ⚡ Feature Forge

[![Live Demo](https://img.shields.io/badge/🤗%20Live%20Demo-Feature%20Forge-blue)](https://huggingface.co/spaces/Spandan-139/feature-forge)
[![CI](https://github.com/Spandan-139/feature-forge/actions/workflows/ci.yml/badge.svg)](https://github.com/Spandan-139/feature-forge/actions)

A production-style ML Feature Store with offline/online serving, model registry, and real-time monitoring — built from scratch.

Inspired by Uber's Michelangelo, Google's Feast, and Meta's FBLearner.

---

## Architecture
```
Raw Data (NYC Taxi 2.7M trips)
          │
          ▼
┌─────────────────────┐
│  Feature Pipeline   │  Polars + DuckDB
│  (Transformation)   │
└─────────────────────┘
          │
    ┌─────┴──────┐
    ▼            ▼
┌────────┐  ┌─────────────┐
│Offline │  │   Online    │
│ Store  │  │   Store     │
│Parquet │  │   Redis     │
│DuckDB  │  │  (<5ms)     │
└────────┘  └─────────────┘
    │            │
    ▼            ▼
┌────────┐  ┌─────────────┐
│Training│  │  Serving    │
│  Jobs  │  │    API      │
└────────┘  │  FastAPI    │
    │       └─────────────┘
    ▼
┌─────────────────────┐
│   Model Registry    │  MLflow
│  Staging→Production │
└─────────────────────┘
          │
          ▼
┌─────────────────────┐
│     Monitoring      │  Streamlit
│  Feature Stats      │
│  Data Quality       │
│  Online Store Check │
└─────────────────────┘
```

---

## Components

**Feature Registry** — Central metadata store for all features. Tracks name, description, data type, entity, computation logic, owner, tags, version, and status. Built with FastAPI + SQLite.

**Offline Store** — Historical feature values stored as Parquet files, queryable via DuckDB. Supports point-in-time correct joins to prevent data leakage during training.

**Online Store** — Latest feature values stored in Redis for sub-millisecond retrieval at inference time. Synced from the offline store on a schedule.

**Feature Pipeline** — Transformation layer built with Polars and Pandas. Reads raw NYC Taxi data, computes 5 location-based features, validates schema, and writes to both stores.

**Model Registry** — MLflow-powered experiment tracking and model versioning. Models are promoted through Staging → Production → Archived lifecycle.

**Serving API** — FastAPI endpoint that fetches features from Redis and serves predictions from the Production model in real time. Average latency ~25ms.

**Monitoring Dashboard** — Streamlit dashboard showing system status, feature distributions, feature statistics, data quality metrics, and online store spot checks.

---

## Features Engineered

| Feature | Description | Entity |
|---|---|---|
| `avg_trip_distance_7d` | Average trip distance per zone | PULocationID |
| `avg_fare_7d` | Average fare amount per zone | PULocationID |
| `tip_rate_7d` | Tip / fare ratio per zone | PULocationID |
| `trip_count_7d` | Number of trips per zone | PULocationID |
| `avg_trip_duration_minutes_7d` | Average trip duration per zone | PULocationID |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data Processing | Polars, Pandas, PyArrow |
| Offline Store | Parquet, DuckDB |
| Online Store | Redis |
| API | FastAPI, Uvicorn |
| ML & Tracking | Scikit-learn, XGBoost, MLflow |
| Monitoring | Streamlit, Evidently |
| Orchestration | Docker, Docker Compose |
| Dataset | NYC Taxi Trip Data 2024 (2.7M rows) |

---

## Quick Start

### Prerequisites
- Python 3.12
- Docker Desktop
- Git

### 1. Clone the repo
```bash
git clone https://github.com/Spandan-139/feature-forge.git
cd feature-forge
```

### 2. Set up Python environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
pip install -r requirements.txt
```

### 3. Download the dataset
```bash
Invoke-WebRequest -Uri "https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2024-01.parquet" -OutFile "data\raw\yellow_tripdata_2024-01.parquet"
```

### 4. Run the feature pipeline
```bash
python -c "from src.offline_store.store import run_pipeline; run_pipeline()"
```

### 5. Sync to online store
```bash
python -c "from src.online_store.store import sync_to_online_store; sync_to_online_store()"
```

### 6. Start MLflow
```bash
mlflow ui --port 5000
```

### 7. Train and register models
```bash
python -m src.serving.train
```

### 8. Start all services
```bash
cd docker
docker compose up --build
```

### 9. Access the services

| Service | URL |
|---|---|
| Feature Registry API | http://localhost:8000/docs |
| Serving API | http://localhost:8001/docs |
| Monitoring Dashboard | http://localhost:8501 |
| MLflow UI | http://localhost:5000 |

---

## API Usage

### Register a feature
```bash
curl -X POST http://localhost:8000/features \
  -H "Content-Type: application/json" \
  -d '{
    "name": "avg_fare_7d",
    "description": "Average fare per pickup zone over 7 days",
    "data_type": "float",
    "entity": "PULocationID",
    "computation": "mean(fare_amount) GROUP BY PULocationID WHERE window=7d",
    "owner": "spandan",
    "tags": ["location", "financial"],
    "status": "active"
  }'
```

### Get a prediction
```bash
curl -X POST http://localhost:8001/predict \
  -H "Content-Type: application/json" \
  -d '{"location_id": "146"}'
```

### Response
```json
{
  "location_id": "146",
  "predicted_tip_rate": 0.1571,
  "features_used": {
    "avg_trip_distance_7d": 3.023511,
    "avg_fare_7d": 17.924449,
    "trip_count_7d": 1108.0,
    "avg_trip_duration_minutes_7d": 14.857491
  },
  "latency_ms": 25.14,
  "model": "feature-forge-random-forest/Production"
}
```

---

## Project Structure
```
feature-forge/
├── src/
│   ├── feature_registry/    # Feature metadata API
│   ├── offline_store/       # Parquet + DuckDB layer
│   ├── online_store/        # Redis sync and retrieval
│   ├── pipeline/            # Feature transformation
│   ├── serving/             # Prediction API + training
│   └── monitoring/          # Streamlit dashboard
├── data/
│   ├── raw/                 # Raw NYC Taxi parquet
│   └── processed/           # Computed feature store
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml
├── tests/
├── notebooks/
├── .env
└── requirements.txt
```

---

## Key Design Decisions

**Why DuckDB for the offline store?** DuckDB runs embedded with no server, supports columnar Parquet queries at near-Spark speeds, and is free. For 2.7M rows it returns training datasets in milliseconds.

**Why Redis for the online store?** Redis hash sets give O(1) feature retrieval by entity key. At inference time, fetching all features for a location takes under 5ms — fast enough for real-time serving.

**Why separate offline and online stores?** This eliminates train-serve skew — the most common silent killer of production ML models. Features are defined once and computed consistently for both training and inference.

**Why MLflow for model registry?** MLflow's staging system (None → Staging → Production → Archived) mirrors how real ML teams manage model lifecycle. The serving API always loads from Production, making deployments explicit and auditable.

---

## Dataset

NYC Yellow Taxi Trip Records — January 2024
- Source: NYC Taxi & Limousine Commission
- Size: 2,964,624 trips → 2,713,346 after cleaning
- Features engineered over 251 unique pickup zones
- Download: https://www.nyc.gov/site/tlc/about/tlc-trip-record-data.page

---

## Author

**Spandan** — B.Tech CSE @ SRMIST  
GitHub: [@Spandan-139](https://github.com/Spandan-139)