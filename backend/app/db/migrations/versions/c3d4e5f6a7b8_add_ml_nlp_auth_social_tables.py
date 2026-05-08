"""add_ml_nlp_auth_social_tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, Sequence[str], None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ml_model_configs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=False),
        sa.Column('feature_set', postgresql.JSON(), nullable=True),
        sa.Column('hyperparameters', postgresql.JSON(), nullable=True),
        sa.Column('target_horizon', sa.Integer(), nullable=True),
        sa.Column('target_type', sa.String(30), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ml_training_runs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_config_id', sa.Integer(), sa.ForeignKey('ml_model_configs.id'), nullable=False),
        sa.Column('instrument_id', sa.Integer(), sa.ForeignKey('instruments.id'), nullable=True),
        sa.Column('train_start', sa.Date(), nullable=False),
        sa.Column('train_end', sa.Date(), nullable=False),
        sa.Column('test_start', sa.Date(), nullable=True),
        sa.Column('test_end', sa.Date(), nullable=True),
        sa.Column('train_score', sa.Float(), nullable=True),
        sa.Column('test_score', sa.Float(), nullable=True),
        sa.Column('feature_importance', postgresql.JSON(), nullable=True),
        sa.Column('model_path', sa.String(256), nullable=True),
        sa.Column('status', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'ml_predictions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('training_run_id', sa.Integer(), sa.ForeignKey('ml_training_runs.id'), nullable=False),
        sa.Column('instrument_id', sa.Integer(), sa.ForeignKey('instruments.id'), nullable=False),
        sa.Column('prediction_date', sa.Date(), nullable=False),
        sa.Column('predicted_value', sa.Float(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('features_used', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'news_articles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('url', sa.String(500), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('instrument_id', sa.Integer(), sa.ForeignKey('instruments.id'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'sentiment_results',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('article_id', sa.Integer(), sa.ForeignKey('news_articles.id'), nullable=True),
        sa.Column('instrument_id', sa.Integer(), sa.ForeignKey('instruments.id'), nullable=True),
        sa.Column('text_snippet', sa.Text(), nullable=False),
        sa.Column('label', sa.String(20), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('model_name', sa.String(100), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(128), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_username', 'users', ['username'], unique=True)
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_hash', sa.String(128), nullable=False),
        sa.Column('name', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('ix_api_keys_key_hash', 'api_keys', ['key_hash'], unique=True)

    op.create_table(
        'shared_strategies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_config_id', sa.Integer(), sa.ForeignKey('strategy_configs.id'), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('tags', postgresql.JSON(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=True),
        sa.Column('fork_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_shared_strategies_user_id', 'shared_strategies', ['user_id'])

    op.create_table(
        'strategy_performance_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shared_strategy_id', sa.Integer(), sa.ForeignKey('shared_strategies.id'), nullable=False),
        sa.Column('snapshot_date', sa.String(10), nullable=False),
        sa.Column('total_return', sa.Float(), nullable=True),
        sa.Column('sharpe_ratio', sa.Float(), nullable=True),
        sa.Column('max_drawdown', sa.Float(), nullable=True),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('trade_count', sa.Integer(), nullable=True),
        sa.Column('extra_metrics', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'strategy_comments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shared_strategy_id', sa.Integer(), sa.ForeignKey('shared_strategies.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_strategy_comments_user_id', 'strategy_comments', ['user_id'])

    op.create_table(
        'strategy_likes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('shared_strategy_id', sa.Integer(), sa.ForeignKey('shared_strategies.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_strategy_likes_user_id', 'strategy_likes', ['user_id'])

    op.create_table(
        'strategy_forks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('source_strategy_id', sa.Integer(), sa.ForeignKey('shared_strategies.id'), nullable=False),
        sa.Column('forked_strategy_id', sa.Integer(), sa.ForeignKey('shared_strategies.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_strategy_forks_user_id', 'strategy_forks', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_strategy_forks_user_id', table_name='strategy_forks', if_exists=True)
    op.drop_table('strategy_forks')
    op.drop_index('ix_strategy_likes_user_id', table_name='strategy_likes', if_exists=True)
    op.drop_table('strategy_likes')
    op.drop_index('ix_strategy_comments_user_id', table_name='strategy_comments', if_exists=True)
    op.drop_table('strategy_comments')
    op.drop_table('strategy_performance_snapshots')
    op.drop_index('ix_shared_strategies_user_id', table_name='shared_strategies', if_exists=True)
    op.drop_table('shared_strategies')
    op.drop_index('ix_api_keys_key_hash', table_name='api_keys', if_exists=True)
    op.drop_index('ix_api_keys_user_id', table_name='api_keys', if_exists=True)
    op.drop_table('api_keys')
    op.drop_index('ix_users_email', table_name='users', if_exists=True)
    op.drop_index('ix_users_username', table_name='users', if_exists=True)
    op.drop_table('users')
    op.drop_table('sentiment_results')
    op.drop_table('news_articles')
    op.drop_table('ml_predictions')
    op.drop_table('ml_training_runs')
    op.drop_table('ml_model_configs')
