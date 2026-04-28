from datetime import date, datetime
from typing import Optional

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Instrument(Base):
    __tablename__ = "instruments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    symbol: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    exchange: Mapped[str] = mapped_column(String(8), nullable=False, comment="SH or SZ")
    type: Mapped[str] = mapped_column(String(16), default="ETF")
    category: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )

    bars: Mapped[list["DailyBar"]] = relationship(
        "DailyBar", back_populates="instrument", lazy="selectin"
    )
    quality_reports: Mapped[list["DataQualityReport"]] = relationship(
        "DataQualityReport", back_populates="instrument", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Instrument(id={self.id}, symbol={self.symbol}, name={self.name})>"


class DailyBar(Base):
    __tablename__ = "daily_bars"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    trade_date: Mapped[date] = mapped_column(Date, nullable=False)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    adj_close: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    data_source: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )

    instrument: Mapped["Instrument"] = relationship(
        "Instrument", back_populates="bars"
    )

    __table_args__ = (
        UniqueConstraint("instrument_id", "trade_date", name="uq_instrument_trade_date"),
        Index("ix_daily_bars_trade_date", "trade_date"),
        Index("ix_daily_bars_instrument_date", "instrument_id", "trade_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<DailyBar(symbol={self.instrument_id}, "
            f"date={self.trade_date}, close={self.close})>"
        )


class TradingCalendar(Base):
    __tablename__ = "trading_calendar"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    is_trading_day: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<TradingCalendar(date={self.date}, trading={self.is_trading_day})>"


class DataQualityReport(Base):
    __tablename__ = "data_quality_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    instrument_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("instruments.id", ondelete="CASCADE"), nullable=False
    )
    check_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )
    missing_dates: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    price_jumps: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    zero_volume_dates: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    overall_status: Mapped[str] = mapped_column(
        String(16), nullable=False, default="OK"
    )

    instrument: Mapped["Instrument"] = relationship(
        "Instrument", back_populates="quality_reports"
    )

    __table_args__ = (
        Index("ix_quality_instrument_date", "instrument_id", "check_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<DataQualityReport(instrument={self.instrument_id}, "
            f"status={self.overall_status})>"
        )
