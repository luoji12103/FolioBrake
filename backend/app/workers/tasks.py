import logging
from datetime import date, datetime

from app.workers.celery_app import celery_app
from app.db.base import SessionLocal
from app.data.sync import DataSyncService
from app.backtest.engine import BacktestEngine
from app.backtest.models import BacktestConfig
from app.strategy.models import StrategyConfig
from app.core.cache import invalidate_prefix

logger = logging.getLogger(__name__)

DEFAULT_SYMBOLS = ["510050", "510300", "510500", "159919", "159915"]


@celery_app.task(bind=True, name="workers.sync_data")
def sync_data(self, symbols: list[str] | None = None, start_date: str = "20220101") -> dict:
    db = SessionLocal()
    result = {"synced": 0, "quality_checks": 0, "errors": []}
    try:
        symbols = symbols or DEFAULT_SYMBOLS
        service = DataSyncService(db)
        total = len(symbols)
        for i, symbol in enumerate(symbols):
            try:
                self.update_state(
                    state="PROGRESS",
                    meta={"current": i + 1, "total": total, "symbol": symbol},
                )
                inst = service.sync_instrument(symbol)
                db.commit()
                count = service.sync_daily_bars(
                    inst.id, start_date, date.today().strftime("%Y%m%d"),
                )
                result["synced"] += count
                if count > 0:
                    service.run_quality_check(inst.id)
                    result["quality_checks"] += 1
            except Exception as e:
                result["errors"].append({"symbol": symbol, "error": str(e)})
        db.commit()
        invalidate_prefix("resp")
    except Exception as e:
        logger.exception("sync_data task failed")
        result["errors"].append({"fatal": str(e)})
    finally:
        db.close()
    return result


@celery_app.task(bind=True, name="workers.run_backtest")
def run_backtest(
    self,
    strategy_config_id: int,
    start_date: str,
    end_date: str,
    initial_capital: float = 100000.0,
    benchmark_symbol: str = "510050",
) -> dict:
    from sqlalchemy import select

    db = SessionLocal()
    try:
        strat_cfg = db.execute(
            select(StrategyConfig).where(StrategyConfig.id == strategy_config_id)
        ).scalar_one_or_none()
        if not strat_cfg:
            strat_cfg = StrategyConfig(
                name="risk_aware_etf_rotation_v1",
                version="v1",
                parameters={
                    "max_holdings": 5,
                    "max_concentration": 0.30,
                    "min_positions": 3,
                    "max_turnover": 0.50,
                },
            )
            db.add(strat_cfg)
            db.flush()

        config = BacktestConfig(
            strategy_config_id=strat_cfg.id,
            start_date=date.fromisoformat(start_date),
            end_date=date.fromisoformat(end_date),
            initial_capital=initial_capital,
            cost_model={"commission": 0.0003, "slippage": 0.001},
            benchmark_symbol=benchmark_symbol,
        )
        db.add(config)
        db.flush()

        self.update_state(state="PROGRESS", meta={"stage": "running_backtest"})

        engine = BacktestEngine(db)
        run = engine.run(config)
        db.commit()

        invalidate_prefix("resp")
        return {
            "run_id": run.id,
            "status": run.status,
            "config_hash": run.config_hash,
        }
    except Exception as e:
        logger.exception("run_backtest task failed")
        db.rollback()
        return {"error": str(e)}
    finally:
        db.close()


@celery_app.task(name="workers.daily_maintenance")
def daily_maintenance() -> dict:
    db = SessionLocal()
    try:
        from sqlalchemy import text
        db.execute(text("ANALYZE"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()

    invalidate_prefix("resp")
    return {"status": "done", "timestamp": datetime.utcnow().isoformat()}
