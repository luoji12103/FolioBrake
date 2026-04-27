from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.paper.models import PaperPortfolio, PaperPosition, PaperOrder, PaperLedger
from app.data.models import DailyBar


class PaperTradingEngine:
    def __init__(self, db: Session):
        self.db = db

    def create_portfolio(self, name: str, capital: float) -> PaperPortfolio:
        pf = PaperPortfolio(name=name, initial_capital=capital)
        self.db.add(pf)
        self.db.add(PaperLedger(portfolio_id=pf.id, date=date.today(),
                                entry_type="DEPOSIT", amount=capital,
                                description=f"Initial capital: {capital}"))
        self.db.flush()
        return pf

    def apply_signal(self, portfolio_id: int, signal_date: date, target_weights: dict[int, float]) -> list[PaperOrder]:
        orders = []
        for inst_id, target_w in target_weights.items():
            bar = self.db.execute(
                select(DailyBar).where(DailyBar.instrument_id == inst_id, DailyBar.trade_date == signal_date)
            ).scalar_one_or_none()
            if not bar:
                continue

            existing = self.db.execute(
                select(PaperPosition).where(
                    PaperPosition.portfolio_id == portfolio_id,
                    PaperPosition.instrument_id == inst_id,
                )
            ).scalar_one_or_none()

            total_value = self._get_total_value(portfolio_id, signal_date)
            target_value = total_value * target_w
            target_shares = target_value / bar.close if bar.close > 0 else 0

            if existing:
                delta = target_shares - existing.quantity
                if abs(delta) > 0.01:
                    side = "BUY" if delta > 0 else "SELL"
                    order = PaperOrder(portfolio_id=portfolio_id, date=signal_date,
                                       instrument_id=inst_id, side=side,
                                       quantity=abs(delta), price=bar.close, status="FILLED")
                    self.db.add(order)
                    existing.quantity = target_shares
                    existing.avg_cost = bar.close
                    orders.append(order)
                    self.db.add(PaperLedger(portfolio_id=portfolio_id, date=signal_date,
                                           entry_type="TRADE",
                                           amount=-delta * bar.close,
                                           description=f"{side} {inst_id}: {abs(delta):.2f} shares @ {bar.close:.2f}"))
            else:
                if target_shares > 0:
                    order = PaperOrder(portfolio_id=portfolio_id, date=signal_date,
                                       instrument_id=inst_id, side="BUY",
                                       quantity=target_shares, price=bar.close, status="FILLED")
                    self.db.add(order)
                    pos = PaperPosition(portfolio_id=portfolio_id, instrument_id=inst_id,
                                        quantity=target_shares, avg_cost=bar.close)
                    self.db.add(pos)
                    self.db.add(PaperLedger(portfolio_id=portfolio_id, date=signal_date,
                                           entry_type="TRADE",
                                           amount=-target_shares * bar.close,
                                           description=f"BUY {inst_id}: {target_shares:.2f} shares @ {bar.close:.2f}"))
                    orders.append(order)

        self.db.flush()
        return orders

    def _get_total_value(self, portfolio_id: int, as_of_date: date) -> float:
        pf = self.db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one()
        positions = list(self.db.execute(
            select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
        ).scalars().all())

        ledger = list(self.db.execute(
            select(PaperLedger).where(PaperLedger.portfolio_id == portfolio_id)
        ).scalars().all())
        cash = sum(l.amount for l in ledger)

        holdings_value = 0.0
        for pos in positions:
            bar = self.db.execute(
                select(DailyBar).where(
                    DailyBar.instrument_id == pos.instrument_id,
                    DailyBar.trade_date <= as_of_date,
                ).order_by(DailyBar.trade_date.desc()).limit(1)
            ).scalar_one_or_none()
            if bar:
                holdings_value += pos.quantity * bar.close

        return cash + holdings_value

    def get_pnl(self, portfolio_id: int) -> dict:
        pf = self.db.execute(select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)).scalar_one()
        ledger = list(self.db.execute(
            select(PaperLedger).where(PaperLedger.portfolio_id == portfolio_id)
        ).scalars().all())
        cash = sum(l.amount for l in ledger)
        positions = list(self.db.execute(
            select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
        ).scalars().all())
        holdings_value = 0.0
        for pos in positions:
            bar = self.db.execute(
                select(DailyBar).where(DailyBar.instrument_id == pos.instrument_id)
                .order_by(DailyBar.trade_date.desc()).limit(1)
            ).scalar_one_or_none()
            if bar:
                holdings_value += pos.quantity * bar.close

        total_value = cash + holdings_value
        return {
            "initial_capital": pf.initial_capital,
            "total_value": total_value,
            "cash": cash,
            "invested": holdings_value,
            "pnl": total_value - pf.initial_capital,
            "pnl_pct": (total_value - pf.initial_capital) / pf.initial_capital * 100 if pf.initial_capital else 0,
        }
