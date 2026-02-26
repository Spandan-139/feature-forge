import json
from datetime import datetime, timezone
from typing import List, Optional
from loguru import logger
from .database import get_connection, row_to_dict
from .models import FeatureCreate


def register_feature(feature: FeatureCreate) -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO features (name, description, data_type, entity, computation, owner, tags, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feature.name,
            feature.description,
            feature.data_type.value,
            feature.entity,
            feature.computation,
            feature.owner,
            json.dumps(feature.tags),
            feature.status.value
        ))
        conn.commit()
        feature_id = cursor.lastrowid
        logger.info(f"Registered feature: {feature.name} (id={feature_id})")
        return get_feature_by_id(feature_id)
    except Exception as e:
        logger.error(f"Failed to register feature {feature.name}: {e}")
        raise
    finally:
        conn.close()


def get_feature_by_id(feature_id: int) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM features WHERE id = ?", (feature_id,)).fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def get_feature_by_name(name: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    row = cursor.execute("SELECT * FROM features WHERE name = ?", (name,)).fetchone()
    conn.close()
    return row_to_dict(row) if row else None


def list_features(entity: Optional[str] = None, tag: Optional[str] = None) -> List[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    rows = cursor.execute("SELECT * FROM features").fetchall()
    conn.close()
    features = [row_to_dict(r) for r in rows]
    if entity:
        features = [f for f in features if f["entity"] == entity]
    if tag:
        features = [f for f in features if tag in f["tags"]]
    return features


def update_feature_status(name: str, status: str) -> Optional[dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE features
        SET status = ?, version = version + 1, updated_at = ?
        WHERE name = ?
    """, (status, datetime.now(timezone.utc), name))
    conn.commit()
    conn.close()
    logger.info(f"Updated feature {name} status to {status}")
    return get_feature_by_name(name)


def delete_feature(name: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM features WHERE name = ?", (name,))
    affected = cursor.rowcount
    conn.commit()
    conn.close()
    return affected > 0