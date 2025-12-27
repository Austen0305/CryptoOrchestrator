"""add_marketplace_models

Add marketplace models for copy trading:
- signal_providers: Signal provider profiles with curator approval, performance metrics, reputation
- signal_provider_ratings: User ratings for signal providers (1-5 stars)
- payouts: Payout tracking with 80/20 revenue split

Revision ID: 20251212_marketplace
Revises: 20251208_hot_path_indexes
Create Date: 2025-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_marketplace'
down_revision = '20251208_hot_path_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if tables already exist (from direct table creation fallback)
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # Create signal_providers table
    if 'signal_providers' not in existing_tables:
        op.create_table(
            'signal_providers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            
            # Curator status
            sa.Column('curator_status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('curator_approved_at', sa.DateTime(), nullable=True),
            sa.Column('curator_notes', sa.Text(), nullable=True),
            
            # Performance metrics (updated daily)
            sa.Column('total_return', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('sharpe_ratio', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('win_rate', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('total_trades', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('winning_trades', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('total_profit', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('max_drawdown', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('profit_factor', sa.Float(), nullable=False, server_default='0.0'),
            
            # Reputation metrics
            sa.Column('average_rating', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('total_ratings', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('follower_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('subscriber_count', sa.Integer(), nullable=False, server_default='0'),
            
            # Marketplace settings
            sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('subscription_fee', sa.Float(), nullable=True),
            sa.Column('performance_fee_percentage', sa.Float(), nullable=False, server_default='0.0'),
            sa.Column('minimum_subscription_amount', sa.Float(), nullable=True),
            
            # Profile information
            sa.Column('profile_description', sa.Text(), nullable=True),
            sa.Column('trading_strategy', sa.Text(), nullable=True),
            sa.Column('risk_level', sa.String(length=20), nullable=True),
            
            # Statistics tracking
            sa.Column('last_metrics_update', sa.DateTime(), nullable=True),
            sa.Column('metrics_update_frequency', sa.String(length=20), nullable=False, server_default='daily'),
            
            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('user_id')
        )
        
        # Indexes for signal_providers
        op.create_index(op.f('ix_signal_providers_id'), 'signal_providers', ['id'], unique=False)
        op.create_index(op.f('ix_signal_providers_user_id'), 'signal_providers', ['user_id'], unique=True)
        op.create_index('ix_signal_providers_curator_status', 'signal_providers', ['curator_status'], unique=False)
        op.create_index('ix_signal_providers_is_public', 'signal_providers', ['is_public'], unique=False)
        op.create_index('ix_signal_providers_total_return', 'signal_providers', ['total_return'], unique=False)
        op.create_index('ix_signal_providers_sharpe_ratio', 'signal_providers', ['sharpe_ratio'], unique=False)
        op.create_index('ix_signal_providers_win_rate', 'signal_providers', ['win_rate'], unique=False)
        op.create_index('ix_signal_providers_average_rating', 'signal_providers', ['average_rating'], unique=False)
        op.create_index('ix_signal_providers_follower_count', 'signal_providers', ['follower_count'], unique=False)
    
    # Create signal_provider_ratings table
    if 'signal_provider_ratings' not in existing_tables:
        op.create_table(
            'signal_provider_ratings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('signal_provider_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            
            # Rating (1-5 stars)
            sa.Column('rating', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=True),
            
            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            
            sa.ForeignKeyConstraint(['signal_provider_id'], ['signal_providers.id'], ),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Indexes for signal_provider_ratings
        op.create_index(op.f('ix_signal_provider_ratings_id'), 'signal_provider_ratings', ['id'], unique=False)
        op.create_index('ix_signal_provider_ratings_signal_provider_id', 'signal_provider_ratings', ['signal_provider_id'], unique=False)
        op.create_index('ix_signal_provider_ratings_user_id', 'signal_provider_ratings', ['user_id'], unique=False)
        op.create_index('ix_signal_provider_ratings_rating', 'signal_provider_ratings', ['rating'], unique=False)
        # Composite index for user-provider uniqueness (one rating per user per provider)
        op.create_index('ix_signal_provider_ratings_user_provider', 'signal_provider_ratings', ['user_id', 'signal_provider_id'], unique=True)
    
    # Create payouts table
    if 'payouts' not in existing_tables:
        op.create_table(
            'payouts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('signal_provider_id', sa.Integer(), nullable=False),
            
            # Payout details
            sa.Column('period_start', sa.DateTime(), nullable=False),
            sa.Column('period_end', sa.DateTime(), nullable=False),
            sa.Column('total_revenue', sa.Float(), nullable=False),
            sa.Column('platform_fee', sa.Float(), nullable=False),  # 20% to platform
            sa.Column('provider_payout', sa.Float(), nullable=False),  # 80% to provider
            
            # Payout status
            sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
            sa.Column('payout_method', sa.String(length=50), nullable=True),
            sa.Column('transaction_hash', sa.String(length=100), nullable=True),
            
            # Timestamps
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            
            sa.ForeignKeyConstraint(['signal_provider_id'], ['signal_providers.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Indexes for payouts
        op.create_index(op.f('ix_payouts_id'), 'payouts', ['id'], unique=False)
        op.create_index('ix_payouts_signal_provider_id', 'payouts', ['signal_provider_id'], unique=False)
        op.create_index('ix_payouts_status', 'payouts', ['status'], unique=False)
        op.create_index('ix_payouts_period_start', 'payouts', ['period_start'], unique=False)
        op.create_index('ix_payouts_period_end', 'payouts', ['period_end'], unique=False)
        op.create_index('ix_payouts_created_at', 'payouts', ['created_at'], unique=False)


def downgrade() -> None:
    # Drop payouts table
    op.drop_index('ix_payouts_created_at', table_name='payouts')
    op.drop_index('ix_payouts_period_end', table_name='payouts')
    op.drop_index('ix_payouts_period_start', table_name='payouts')
    op.drop_index('ix_payouts_status', table_name='payouts')
    op.drop_index('ix_payouts_signal_provider_id', table_name='payouts')
    op.drop_index(op.f('ix_payouts_id'), table_name='payouts')
    op.drop_table('payouts')
    
    # Drop signal_provider_ratings table
    op.drop_index('ix_signal_provider_ratings_user_provider', table_name='signal_provider_ratings')
    op.drop_index('ix_signal_provider_ratings_rating', table_name='signal_provider_ratings')
    op.drop_index('ix_signal_provider_ratings_user_id', table_name='signal_provider_ratings')
    op.drop_index('ix_signal_provider_ratings_signal_provider_id', table_name='signal_provider_ratings')
    op.drop_index(op.f('ix_signal_provider_ratings_id'), table_name='signal_provider_ratings')
    op.drop_table('signal_provider_ratings')
    
    # Drop signal_providers table
    op.drop_index('ix_signal_providers_follower_count', table_name='signal_providers')
    op.drop_index('ix_signal_providers_average_rating', table_name='signal_providers')
    op.drop_index('ix_signal_providers_win_rate', table_name='signal_providers')
    op.drop_index('ix_signal_providers_sharpe_ratio', table_name='signal_providers')
    op.drop_index('ix_signal_providers_total_return', table_name='signal_providers')
    op.drop_index('ix_signal_providers_is_public', table_name='signal_providers')
    op.drop_index('ix_signal_providers_curator_status', table_name='signal_providers')
    op.drop_index(op.f('ix_signal_providers_user_id'), table_name='signal_providers')
    op.drop_index(op.f('ix_signal_providers_id'), table_name='signal_providers')
    op.drop_table('signal_providers')
