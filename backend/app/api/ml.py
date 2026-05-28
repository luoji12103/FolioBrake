from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.auth import verify_api_key
from app.db.base import get_db
from app.ml.models import MLModelConfig, MLTrainingRun, MLPrediction
from app.ml.engine import MLEngine

router = APIRouter(tags=["ml"])


class TrainRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    model_type: str = Field("random_forest", max_length=64)
    feature_set: list[str] = Field(..., min_length=1, max_length=100)
    hyperparameters: dict = Field(default_factory=dict)
    target_horizon: int = Field(5, ge=1, le=252)
    target_type: str = Field("binary_up", max_length=32)
    instrument_id: int | None = None
    train_start: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    train_end: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    test_split: float = Field(0.2, gt=0.0, lt=1.0)


class PredictRequest(BaseModel):
    training_run_id: int
    instrument_id: int
    prediction_date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


@router.post("/train")
def train_model(req: TrainRequest, db: Session = Depends(get_db), _: str = Depends(verify_api_key)):
    config = MLModelConfig(
        name=req.name,
        model_type=req.model_type,
        feature_set=req.feature_set,
        hyperparameters=req.hyperparameters,
        target_horizon=req.target_horizon,
        target_type=req.target_type,
    )
    db.add(config)
    db.flush()

    engine = MLEngine(db)
    result = engine.train(
        config={
            "model_type": req.model_type,
            "feature_set": req.feature_set,
            "hyperparameters": req.hyperparameters,
            "target_horizon": req.target_horizon,
            "target_type": req.target_type,
            "train_start": req.train_start,
            "train_end": req.train_end,
            "test_split": req.test_split,
        },
        instrument_id=req.instrument_id,
    )

    if result.get("status") == "failed":
        raise HTTPException(status_code=400, detail=result.get("error", "Training failed"))

    run = MLTrainingRun(
        model_config_id=config.id,
        instrument_id=req.instrument_id,
        train_start=date.fromisoformat(req.train_start),
        train_end=date.fromisoformat(req.train_end),
        train_score=result.get("metrics", {}).get("train_accuracy", 0.0),
        test_score=result.get("metrics", {}).get("test_accuracy", 0.0),
        feature_importance=result.get("feature_importance", {}),
        model_path=result.get("model_path"),
        status=result.get("status", "completed"),
    )
    db.add(run)
    db.commit()

    return {
        "training_run_id": run.id,
        "model_config_id": config.id,
        "status": run.status,
        "metrics": result.get("metrics", {}),
        "feature_importance": result.get("feature_importance", {}),
    }


@router.post("/predict")
def predict(req: PredictRequest, db: Session = Depends(get_db)):
    run = db.execute(
        select(MLTrainingRun).where(MLTrainingRun.id == req.training_run_id)
    ).scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Training run not found")

    config = db.execute(
        select(MLModelConfig).where(MLModelConfig.id == run.model_config_id)
    ).scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="Model config not found")

    if not run.model_path:
        raise HTTPException(status_code=400, detail="No saved model for this run")

    engine = MLEngine(db)
    result = engine.predict(
        model_path=run.model_path,
        instrument_id=req.instrument_id,
        as_of_date=date.fromisoformat(req.prediction_date),
        feature_names=list(config.feature_set) if isinstance(config.feature_set, list) else [],
    )

    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    pred = MLPrediction(
        training_run_id=run.id,
        instrument_id=req.instrument_id,
        prediction_date=date.fromisoformat(req.prediction_date),
        predicted_value=result["predicted_value"],
        confidence=result["confidence"],
        features_used=result.get("features_used", {}),
    )
    db.add(pred)
    db.commit()

    return {
        "prediction_id": pred.id,
        "predicted_value": pred.predicted_value,
        "confidence": pred.confidence,
        "features_used": pred.features_used,
    }


@router.get("/models")
def list_models(db: Session = Depends(get_db)):
    configs = list(db.execute(select(MLModelConfig).order_by(MLModelConfig.id.desc())).scalars().all())
    return [
        {
            "id": c.id,
            "name": c.name,
            "model_type": c.model_type,
            "feature_set": c.feature_set,
            "target_horizon": c.target_horizon,
            "created_at": str(c.created_at),
        }
        for c in configs
    ]


@router.get("/training-runs")
def list_training_runs(db: Session = Depends(get_db)):
    runs = list(db.execute(select(MLTrainingRun).order_by(MLTrainingRun.id.desc())).scalars().all())
    return [
        {
            "id": r.id,
            "model_config_id": r.model_config_id,
            "train_score": r.train_score,
            "test_score": r.test_score,
            "status": r.status,
            "created_at": str(r.created_at),
        }
        for r in runs
    ]


@router.get("/predictions/{training_run_id}")
def get_predictions(training_run_id: int, db: Session = Depends(get_db)):
    preds = list(
        db.execute(
            select(MLPrediction)
            .where(MLPrediction.training_run_id == training_run_id)
            .order_by(MLPrediction.prediction_date)
        ).scalars().all()
    )
    return [
        {
            "id": p.id,
            "instrument_id": p.instrument_id,
            "prediction_date": str(p.prediction_date),
            "predicted_value": p.predicted_value,
            "confidence": p.confidence,
        }
        for p in preds
    ]
