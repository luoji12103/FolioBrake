from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.base import get_db
from app.features.models import FeatureDefinition, FeatureValue
from app.features.registry import FeatureRegistry

router = APIRouter(tags=["features"])


class FeatureDefinitionOut(BaseModel):
    id: int
    name: str
    category: str
    lookback_days: int
    parameters: dict

    model_config = {"from_attributes": True}


class ComputeRequest(BaseModel):
    instrument_id: int
    as_of_date: str


@router.get("/definitions", response_model=list[FeatureDefinitionOut])
def list_definitions(db: Session = Depends(get_db)):
    return list(db.execute(select(FeatureDefinition)).scalars().all())


@router.post("/compute")
def compute_features(req: ComputeRequest, db: Session = Depends(get_db)):
    from datetime import date as date_type
    registry = FeatureRegistry(db)
    as_of = date_type.fromisoformat(req.as_of_date)
    features = registry.compute_all(req.instrument_id, as_of)
    return {"instrument_id": req.instrument_id, "as_of_date": req.as_of_date, "features": features}


@router.get("/values")
def get_values(instrument_id: int = Query(...), date: str = Query(...), db: Session = Depends(get_db)):
    from datetime import date as date_type
    d = date_type.fromisoformat(date)
    values = list(db.execute(
        select(FeatureValue).where(
            FeatureValue.instrument_id == instrument_id,
            FeatureValue.date == d,
        )
    ).scalars().all())
    return [
        {
            "feature_name": v.feature_definition.name if v.feature_definition else str(v.feature_definition_id),
            "value": v.value,
            "config_hash": v.config_hash,
        }
        for v in values
    ]
