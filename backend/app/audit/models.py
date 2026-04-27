from datetime import date, datetime
from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditRun(Base):
    __tablename__ = "audit_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_config_id: Mapped[int] = mapped_column(ForeignKey("strategy_configs.id"), nullable=False)
    backtest_config_id: Mapped[int] = mapped_column(ForeignKey("backtest_configs.id"), nullable=False)
    run_date: Mapped[date] = mapped_column(Date, nullable=False)
    grade: Mapped[str] = mapped_column(String(10), nullable=False, default="YELLOW")
    score: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditCheckResult(Base):
    __tablename__ = "audit_check_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_run_id: Mapped[int] = mapped_column(ForeignKey("audit_runs.id"), nullable=False)
    check_name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # PASS/WARN/FAIL
    score: Mapped[float] = mapped_column(Float, default=0.0)
    detail: Mapped[dict] = mapped_column(JSON, default=dict)
