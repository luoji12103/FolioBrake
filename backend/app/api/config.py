from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth import verify_api_key
from app.core.config_center import config_center

router = APIRouter(tags=["configuration"])

ALLOWED_CONFIG_KEYS = {
    "risk_profile", "max_concentration", "max_holdings", "min_positions",
    "max_turnover", "commission", "slippage", "data_source", "monitoring_enabled",
}


class ConfigUpdate(BaseModel):
    key: str = Field(..., min_length=1, max_length=128)
    value: Any


class ConfigBulkUpdate(BaseModel):
    values: dict[str, Any] = Field(..., min_length=1, max_length=50)


class ConfigSnapshotOut(BaseModel):
    version: int
    timestamp: float
    checksum: str
    data: dict[str, Any]


@router.get("/")
def get_config(
    _: str = Depends(verify_api_key),
) -> dict[str, Any]:
    return config_center.load()


@router.put("/")
def update_config(
    payload: ConfigBulkUpdate,
    _: str = Depends(verify_api_key),
) -> dict[str, Any]:
    version = config_center.update(payload.values)
    return {"version": version, "updated_keys": list(payload.values.keys())}


@router.put("/item")
def set_config_item(
    payload: ConfigUpdate,
    _: str = Depends(verify_api_key),
) -> dict[str, Any]:
    version = config_center.set(payload.key, payload.value)
    return {"version": version, "key": payload.key}


@router.get("/history")
def get_config_history(
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(verify_api_key),
) -> list[ConfigSnapshotOut]:
    return [
        ConfigSnapshotOut(
            version=s.version,
            timestamp=s.timestamp,
            checksum=s.checksum,
            data=s.data,
        )
        for s in config_center.history(limit)
    ]


@router.post("/rollback/{version}")
def rollback_config(
    version: int,
    _: str = Depends(verify_api_key),
) -> ConfigSnapshotOut:
    snapshot = config_center.rollback(version)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"Version {version} not found")
    return ConfigSnapshotOut(
        version=snapshot.version,
        timestamp=snapshot.timestamp,
        checksum=snapshot.checksum,
        data=snapshot.data,
    )
