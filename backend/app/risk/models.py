from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskProfile(Base):
    __tablename__ = "risk_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False)
    max_volatility: Mapped[float] = mapped_column(Float, nullable=False)
    max_concentration: Mapped[float] = mapped_column(Float, nullable=False)
    liquidity_threshold: Mapped[float] = mapped_column(Float, default=0.0)
    max_equity_exposure: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskStateRecord(Base):
    __tablename__ = "risk_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    state: Mapped[str] = mapped_column(String(20), nullable=False)
    transition_reason: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskRuleResultRecord(Base):
    __tablename__ = "risk_rule_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(100), nullable=False)
    triggered: Mapped[bool] = mapped_column(Boolean, default=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RiskOverlayDecisionRecord(Base):
    __tablename__ = "risk_overlay_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    original_targets: Mapped[dict] = mapped_column(JSON, default=dict)
    final_targets: Mapped[dict] = mapped_column(JSON, default=dict)
    suppressed_trades: Mapped[dict] = mapped_column(JSON, default=dict)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    decision: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
