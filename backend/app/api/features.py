from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import get_db
from app.features.models import FeatureDefinition, FeatureValue
from app.features.registry import FeatureRegistry, VALID_TIMEFRAMES

router = APIRouter(tags=["features"])


class FeatureDefinitionOut(BaseModel):
    id: int
    name: str
    category: str
    lookback_days: int
    parameters: dict
    timeframe: str

    model_config = {"from_attributes": True}


class ComputeRequest(BaseModel):
    instrument_id: int
    as_of_date: str
    timeframe: str = "daily"


@router.get("/definitions", response_model=list[FeatureDefinitionOut])
def list_definitions(
    timeframe: str | None = Query(None, description="Filter by timeframe: daily, weekly, monthly"),
    db: Session = Depends(get_db),
):
    stmt = select(FeatureDefinition)
    if timeframe is not None:
        stmt = stmt.where(FeatureDefinition.timeframe == timeframe)
    return list(db.execute(stmt).scalars().all())


@router.post("/compute")
def compute_features(req: ComputeRequest, db: Session = Depends(get_db)):
    from datetime import date as date_type
    if req.timeframe not in VALID_TIMEFRAMES:
        return {"error": f"Invalid timeframe '{req.timeframe}'. Must be one of {VALID_TIMEFRAMES}"}
    registry = FeatureRegistry(db)
    as_of = date_type.fromisoformat(req.as_of_date)
    features = registry.compute_all(req.instrument_id, as_of, timeframe=req.timeframe)
    db.commit()
    return {"instrument_id": req.instrument_id, "as_of_date": req.as_of_date, "timeframe": req.timeframe, "features": features}


@router.get("/values")
def get_values(
    instrument_id: int = Query(...),
    date: str = Query(...),
    timeframe: str | None = Query(None, description="Filter by timeframe"),
    db: Session = Depends(get_db),
):
    from datetime import date as date_type
    d = date_type.fromisoformat(date)
    stmt = select(FeatureValue).where(
        FeatureValue.instrument_id == instrument_id,
        FeatureValue.date == d,
    )
    if timeframe is not None:
        stmt = stmt.join(FeatureDefinition).where(FeatureDefinition.timeframe == timeframe)
    values = list(db.execute(stmt).scalars().all())
    return [
        {
            "feature_name": v.feature_definition.name if v.feature_definition else str(v.feature_definition_id),
            "value": v.value,
            "config_hash": v.config_hash,
        }
        for v in values
    ]
