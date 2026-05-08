from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class MLModelConfig(Base):
    __tablename__ = "ml_model_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="random_forest, gradient_boosting, logistic")
    feature_set: Mapped[dict] = mapped_column(JSON, default=dict, comment="List of feature names to use")
    hyperparameters: Mapped[dict] = mapped_column(JSON, default=dict)
    target_horizon: Mapped[int] = mapped_column(Integer, default=5, comment="Prediction horizon in trading days")
    target_type: Mapped[str] = mapped_column(String(30), default="binary_up", comment="binary_up, binary_down, regression")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MLTrainingRun(Base):
    __tablename__ = "ml_training_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_config_id: Mapped[int] = mapped_column(ForeignKey("ml_model_configs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=True)
    train_start: Mapped[date] = mapped_column(Date, nullable=False)
    train_end: Mapped[date] = mapped_column(Date, nullable=False)
    test_start: Mapped[date] = mapped_column(Date, nullable=True)
    test_end: Mapped[date] = mapped_column(Date, nullable=True)
    train_score: Mapped[float] = mapped_column(Float, default=0.0)
    test_score: Mapped[float] = mapped_column(Float, default=0.0)
    feature_importance: Mapped[dict] = mapped_column(JSON, default=dict)
    model_path: Mapped[str] = mapped_column(String(256), nullable=True, comment="Path to saved model file")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MLPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    training_run_id: Mapped[int] = mapped_column(ForeignKey("ml_training_runs.id"), nullable=False)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    prediction_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_value: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    features_used: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
