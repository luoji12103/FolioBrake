"""add_performance_indexes

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, Sequence[str], None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Feature values: fast lookup by instrument + date
    op.create_index(
        'ix_feature_values_instrument_date', 'feature_values',
        ['instrument_id', 'date'], if_not_exists=True,
    )

    # Strategy signals: fast lookup by run
    op.create_index(
        'ix_signals_run_id', 'signals',
        ['run_id'], if_not_exists=True,
    )
    op.create_index(
        'ix_target_portfolios_run_id', 'target_portfolios',
        ['run_id'], if_not_exists=True,
    )
    op.create_index(
        'ix_explanation_logs_run_id', 'explanation_logs',
        ['run_id'], if_not_exists=True,
    )

    # Paper trading: fast lookup by portfolio
    op.create_index(
        'ix_paper_positions_portfolio', 'paper_positions',
        ['portfolio_id'], if_not_exists=True,
    )
    op.create_index(
        'ix_paper_orders_portfolio', 'paper_orders',
        ['portfolio_id'], if_not_exists=True,
    )
    op.create_index(
        'ix_paper_ledger_portfolio', 'paper_ledger',
        ['portfolio_id'], if_not_exists=True,
    )

    # Backtest: fast lookup by run
    op.create_index(
        'ix_portfolio_snapshots_run_id', 'portfolio_snapshots',
        ['run_id'], if_not_exists=True,
    )
    op.create_index(
        'ix_simulated_trades_run_id', 'simulated_trades',
        ['run_id'], if_not_exists=True,
    )
    op.create_index(
        'ix_performance_metrics_run_id', 'performance_metrics',
        ['run_id'], if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index('ix_performance_metrics_run_id', table_name='performance_metrics', if_exists=True)
    op.drop_index('ix_simulated_trades_run_id', table_name='simulated_trades', if_exists=True)
    op.drop_index('ix_portfolio_snapshots_run_id', table_name='portfolio_snapshots', if_exists=True)
    op.drop_index('ix_paper_ledger_portfolio', table_name='paper_ledger', if_exists=True)
    op.drop_index('ix_paper_orders_portfolio', table_name='paper_orders', if_exists=True)
    op.drop_index('ix_paper_positions_portfolio', table_name='paper_positions', if_exists=True)
    op.drop_index('ix_explanation_logs_run_id', table_name='explanation_logs', if_exists=True)
    op.drop_index('ix_target_portfolios_run_id', table_name='target_portfolios', if_exists=True)
    op.drop_index('ix_signals_run_id', table_name='signals', if_exists=True)
    op.drop_index('ix_feature_values_instrument_date', table_name='feature_values', if_exists=True)
