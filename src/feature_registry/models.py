from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class FeatureType(str, Enum):
    FLOAT = "float"
    INT = "int"
    STRING = "string"
    BOOLEAN = "boolean"


class FeatureStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    EXPERIMENTAL = "experimental"


class FeatureCreate(BaseModel):
    name: str
    description: str
    data_type: FeatureType
    entity: str                          # e.g. "user_id", "driver_id"
    computation: str                     # human readable formula/logic
    owner: str
    tags: Optional[List[str]] = []
    status: FeatureStatus = FeatureStatus.EXPERIMENTAL


class FeatureResponse(BaseModel):
    id: int
    name: str
    description: str
    data_type: FeatureType
    entity: str
    computation: str
    owner: str
    tags: List[str]
    status: FeatureStatus
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True