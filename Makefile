.PHONY: help install pipeline sync train up down logs test clean

help:
	@echo "Feature Forge - Available Commands"
	@echo "-----------------------------------"
	@echo "make install     Install dependencies"
	@echo "make pipeline    Run feature engineering pipeline"
	@echo "make sync        Sync offline store to Redis"
	@echo "make train       Train and register models"
	@echo "make up          Start all services via Docker Compose"
	@echo "make down        Stop all services"
	@echo "make logs        Tail logs from all services"
	@echo "make test        Run test suite"
	@echo "make clean       Remove cached files"

install:
	pip install -r requirements.txt

pipeline:
	python -c "from src.offline_store.store import run_pipeline; run_pipeline()"

sync:
	python -c "from src.online_store.store import sync_to_online_store; sync_to_online_store()"

train:
	python -m src.serving.train

mlflow:
	mlflow ui --port 5000

up:
	cd docker && docker compose up --build

down:
	cd docker && docker compose down

logs:
	cd docker && docker compose logs -f

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".DS_Store" -delete