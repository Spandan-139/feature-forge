import sqlite3
import json
from pathlib import Path
from loguru import logger

DB_PATH = Path("data/feature_registry.db")


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            data_type TEXT NOT NULL,
            entity TEXT NOT NULL,
            computation TEXT NOT NULL,
            owner TEXT NOT NULL,
            tags TEXT DEFAULT '[]',
            status TEXT DEFAULT 'experimental',
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()
    logger.info("Feature registry database initialized")


def row_to_dict(row):
    d = dict(row)
    d["tags"] = json.loads(d["tags"])
    return d