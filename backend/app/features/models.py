from datetime import date, datetime
from sqlalchemy import JSON, Date, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FeatureDefinition(Base):
    __tablename__ = "feature_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    lookback_days: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeatureValue(Base):
    __tablename__ = "feature_values"
    __table_args__ = (
        UniqueConstraint("instrument_id", "feature_definition_id", "date", "config_hash",
                         name="uq_feature_value"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    feature_definition_id: Mapped[int] = mapped_column(ForeignKey("feature_definitions.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    instrument: Mapped["Instrument"] = relationship(back_populates="feature_values")
    feature_definition: Mapped["FeatureDefinition"] = relationship()


class FeatureRun(Base):
    __tablename__ = "feature_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    config_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    instrument_id: Mapped[int] = mapped_column(ForeignKey("instruments.id"), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
