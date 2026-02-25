import mlflow
import mlflow.sklearn
import polars as pl
import json
import numpy as np
from pathlib import Path
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from loguru import logger

FEATURES_PATH = Path("data/processed/features.parquet")

FEATURE_COLUMNS = [
    "avg_trip_distance_7d",
    "avg_fare_7d",
    "tip_rate_7d",
    "trip_count_7d",
    "avg_trip_duration_minutes_7d"
]

TARGET = "tip_rate_7d"  # predicting tip rate for a zone

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("feature-forge-tip-prediction")


def load_training_data():
    df = pl.read_parquet(FEATURES_PATH)
    # Use all features except target to predict target
    # In real world you'd join with labels — here features ARE our dataset
    X = df.select([c for c in FEATURE_COLUMNS if c != TARGET]).to_numpy()
    y = df.select(TARGET).to_numpy().ravel()
    return X, y, [c for c in FEATURE_COLUMNS if c != TARGET]


def train_and_log(model, model_name: str, params: dict, X_train, X_test, y_train, y_test, feature_names):
    with mlflow.start_run(run_name=model_name):
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)

        mlflow.log_params(params)
        mlflow.log_metrics({"rmse": rmse, "mae": mae, "r2": r2})
        mlflow.log_dict({"features": feature_names, "target": TARGET}, "feature_schema.json")
        mlflow.sklearn.log_model(model, "model", registered_model_name=f"feature-forge-{model_name}")

        logger.info(f"{model_name} → RMSE: {rmse:.4f} | MAE: {mae:.4f} | R2: {r2:.4f}")
        return rmse, r2


def run_training():
    X, y, feature_names = load_training_data()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    logger.info(f"Training set: {X_train.shape} | Test set: {X_test.shape}")

    # Model 1 — Linear Regression (baseline)
    lr_rmse, lr_r2 = train_and_log(
        LinearRegression(),
        "linear-regression",
        {"model": "linear_regression"},
        X_train, X_test, y_train, y_test, feature_names
    )

    # Model 2 — Random Forest
    rf_rmse, rf_r2 = train_and_log(
        RandomForestRegressor(n_estimators=100, max_depth=5, random_state=42),
        "random-forest",
        {"model": "random_forest", "n_estimators": 100, "max_depth": 5},
        X_train, X_test, y_train, y_test, feature_names
    )

    logger.info("Training complete. Check MLflow at http://localhost:5000")
    logger.info(f"Best model: {'Random Forest' if rf_rmse < lr_rmse else 'Linear Regression'}")


if __name__ == "__main__":
    run_training()