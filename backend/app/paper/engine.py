from datetime import date
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.paper.models import PaperPortfolio, PaperPosition, PaperOrder, PaperLedger
from app.data.models import DailyBar


class PaperTradingEngine:
    def __init__(self, db: Session):
        self.db = db

    def create_portfolio(self, name: str, capital: float) -> PaperPortfolio:
        pf = PaperPortfolio(name=name, initial_capital=capital)
        self.db.add(pf)
        self.db.flush()  # populate pf.id
        self.db.add(PaperLedger(portfolio_id=pf.id, date=date.today(),
                                entry_type="DEPOSIT", amount=capital,
                                description=f"Initial capital: {capital}"))
        self.db.flush()
        return pf

    def apply_signal(self, portfolio_id: int, signal_date: date, target_weights: dict[int, float]) -> list[PaperOrder]:
        """Apply trading signals to paper portfolio.

        Validates portfolio exists, checks cash availability for buys,
        computes weighted avg cost, and removes positions that reach zero.
        Raises ValueError on invalid portfolio.
        """
        # Verify portfolio exists
        pf = self.db.execute(
            select(PaperPortfolio).where(PaperPortfolio.id == portfolio_id)
        ).scalar_one_or_none()
        if not pf:
            raise ValueError(f"Portfolio {portfolio_id} not found")

        # Get current positions keyed by instrument_id
        positions: dict[int, PaperPosition] = {
            p.instrument_id: p for p in self.db.execute(
                select(PaperPosition).where(PaperPosition.portfolio_id == portfolio_id)
            ).scalars().all()
        }

        # Get P&L for cash and total value
        pnl = self.get_pnl(portfolio_id)
        total_value = pnl["total_value"]
        available_cash = pnl["cash"]

        orders: list[PaperOrder] = []
        cash_spent = 0.0

        for inst_id, target_w in target_weights.items():
            # Get latest bar on or before signal_date
            bar = self.db.execute(
                select(DailyBar)
                .where(DailyBar.instrument_id == inst_id, DailyBar.trade_date <= signal_date)
                .order_by(desc(DailyBar.trade_date))
                .limit(1)
            ).scalar_one_or_none()
            if not bar or bar.close <= 0:
                continue

            current_price = bar.close
            target_value = total_value * target_w
            existing = positions.get(inst_id)
            current_shares = existing.quantity if existing else 0.0
            current_value = current_shares * current_price

            delta_value = target_value - current_value
            if abs(delta_value) < 1.0:
                continue  # Skip negligible trades

            target_shares = target_value / current_price
            delta_shares = target_shares - current_shares
            side = "BUY" if delta_shares > 0 else "SELL"

            if side == "BUY":
                buy_cost = abs(delta_shares) * current_price
                if available_cash - cash_spent < buy_cost:
                    continue  # Insufficient cash — skip this instrument

                order = PaperOrder(
                    portfolio_id=portfolio_id, date=signal_date,
                    instrument_id=inst_id, side="BUY",
                    quantity=abs(delta_shares), price=current_price, status="FILLED",
                )
                self.db.add(order)

                if existing:
                    # Weighted average cost
                    total_cost = existing.quantity * existing.avg_cost + abs(delta_shares) * current_price
                    existing.quantity += abs(delta_shares)
                    existing.avg_cost = total_cost / existing.quantity if existing.quantity > 0 else current_price
                else:
                    pos = PaperPosition(
                        portfolio_id=portfolio_id, instrument_id=inst_id,
                        quantity=abs(delta_shares), avg_cost=current_price,
                    )
                    self.db.add(pos)

                cash_spent += buy_cost
                self.db.add(PaperLedger(
                    portfolio_id=portfolio_id, date=signal_date,
                    entry_type="TRADE", amount=-buy_cost,
                    description=f"BUY {inst_id}: {abs(delta_shares):.2f} shares @ {current_price:.2f}",
                ))
                orders.append(order)

            elif side == "SELL" and existing:
                sell_quantity = min(abs(delta_shares), existing.quantity)
                if sell_quantity <= 0:
                    continue

                order = PaperOrder(
                    portfolio_id=portfolio_id, date=signal_date,
                    instrument_id=inst_id, side="SELL",
                    quantity=sell_quantity, price=current_price, status="FILLED",
                )
                self.db.add(order)

                existing.quantity -= sell_quantity
                if existing.quantity <= 0:
                    self.db.delete(existing)

                proceeds = sell_quantity * current_price
                self.db.add(PaperLedger(
                    portfolio_id=portfolio_id, date=signal_date,
                    entry_type="TRADE", amount=proceeds,
                    description=f"SELL {inst_id}: {sell_quantity:.2f} shares @ {current_price:.2f}",
                ))
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
