from datetime import datetime
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SharedStrategy(Base):
    __tablename__ = "shared_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    strategy_config_id: Mapped[int] = mapped_column(ForeignKey("strategy_configs.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    tags: Mapped[dict] = mapped_column(JSON, default=list)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    fork_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StrategyPerformanceSnapshot(Base):
    __tablename__ = "strategy_performance_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_strategy_id: Mapped[int] = mapped_column(ForeignKey("shared_strategies.id"), nullable=False)
    snapshot_date: Mapped[str] = mapped_column(String(10), nullable=False)
    total_return: Mapped[float] = mapped_column(Float, default=0.0)
    sharpe_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    max_drawdown: Mapped[float] = mapped_column(Float, default=0.0)
    win_rate: Mapped[float] = mapped_column(Float, default=0.0)
    trade_count: Mapped[int] = mapped_column(Integer, default=0)
    extra_metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StrategyComment(Base):
    __tablename__ = "strategy_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_strategy_id: Mapped[int] = mapped_column(ForeignKey("shared_strategies.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StrategyLike(Base):
    __tablename__ = "strategy_likes"
    __table_args__ = (
        {"comment": "One like per user per strategy"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shared_strategy_id: Mapped[int] = mapped_column(ForeignKey("shared_strategies.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StrategyFork(Base):
    __tablename__ = "strategy_forks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source_strategy_id: Mapped[int] = mapped_column(ForeignKey("shared_strategies.id"), nullable=False)
    forked_strategy_id: Mapped[int] = mapped_column(ForeignKey("shared_strategies.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
