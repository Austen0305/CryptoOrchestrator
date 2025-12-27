"""add_dex_trading_models

Revision ID: c8d9e0f1a2b3
Revises: b2c3d4e5f6a7
Create Date: 2025-12-05 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c8d9e0f1a2b3'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create dex_trades table
    op.create_table('dex_trades',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('trade_type', sa.String(length=20), nullable=False),
    sa.Column('chain_id', sa.Integer(), nullable=False),
    sa.Column('aggregator', sa.String(length=50), nullable=False),
    sa.Column('sell_token', sa.String(length=100), nullable=False),
    sa.Column('sell_token_symbol', sa.String(length=20), nullable=False),
    sa.Column('buy_token', sa.String(length=100), nullable=False),
    sa.Column('buy_token_symbol', sa.String(length=20), nullable=False),
    sa.Column('sell_amount', sa.String(length=100), nullable=False),
    sa.Column('buy_amount', sa.String(length=100), nullable=False),
    sa.Column('sell_amount_decimal', sa.Float(), nullable=False),
    sa.Column('buy_amount_decimal', sa.Float(), nullable=False),
    sa.Column('price', sa.Float(), nullable=True),
    sa.Column('slippage_percentage', sa.Float(), nullable=False, server_default='0.5'),
    sa.Column('platform_fee_bps', sa.Integer(), nullable=False, server_default='20'),
    sa.Column('platform_fee_amount', sa.Float(), nullable=False, server_default='0.0'),
    sa.Column('aggregator_fee_amount', sa.Float(), nullable=False, server_default='0.0'),
    sa.Column('user_wallet_address', sa.String(length=100), nullable=True),
    sa.Column('recipient_address', sa.String(length=100), nullable=True),
    sa.Column('transaction_hash', sa.String(length=100), nullable=True),
    sa.Column('transaction_status', sa.String(length=20), nullable=False, server_default='pending'),
    sa.Column('block_number', sa.Integer(), nullable=True),
    sa.Column('gas_used', sa.Integer(), nullable=True),
    sa.Column('gas_price', sa.String(length=50), nullable=True),
    sa.Column('swap_calldata', sa.Text(), nullable=True),
    sa.Column('swap_target', sa.String(length=100), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
    sa.Column('success', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('quote_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('execution_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('executed_at', sa.DateTime(), nullable=True),
    sa.Column('confirmed_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('transaction_hash')
    )
    op.create_index(op.f('ix_dex_trades_id'), 'dex_trades', ['id'], unique=False)
    op.create_index(op.f('ix_dex_trades_user_id'), 'dex_trades', ['user_id'], unique=False)
    op.create_index(op.f('ix_dex_trades_trade_type'), 'dex_trades', ['trade_type'], unique=False)
    op.create_index(op.f('ix_dex_trades_chain_id'), 'dex_trades', ['chain_id'], unique=False)
    op.create_index(op.f('ix_dex_trades_aggregator'), 'dex_trades', ['aggregator'], unique=False)
    op.create_index(op.f('ix_dex_trades_user_wallet_address'), 'dex_trades', ['user_wallet_address'], unique=False)
    op.create_index(op.f('ix_dex_trades_transaction_hash'), 'dex_trades', ['transaction_hash'], unique=False)
    op.create_index(op.f('ix_dex_trades_transaction_status'), 'dex_trades', ['transaction_status'], unique=False)
    op.create_index(op.f('ix_dex_trades_status'), 'dex_trades', ['status'], unique=False)

    # Create trading_fees table
    op.create_table('trading_fees',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('trade_type', sa.String(length=20), nullable=False),
    sa.Column('dex_trade_id', sa.Integer(), nullable=True),
    sa.Column('cex_trade_id', sa.Integer(), nullable=True),
    sa.Column('fee_type', sa.String(length=20), nullable=False),
    sa.Column('fee_bps', sa.Integer(), nullable=False),
    sa.Column('fee_amount', sa.Float(), nullable=False),
    sa.Column('fee_currency', sa.String(length=20), nullable=False),
    sa.Column('trade_amount', sa.Float(), nullable=False),
    sa.Column('trade_currency', sa.String(length=20), nullable=False),
    sa.Column('user_tier', sa.String(length=20), nullable=False),
    sa.Column('monthly_volume', sa.Float(), nullable=False, server_default='0.0'),
    sa.Column('is_custodial', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
    sa.Column('collected_at', sa.DateTime(), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['dex_trade_id'], ['dex_trades.id'], ),
    sa.ForeignKeyConstraint(['cex_trade_id'], ['trades.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_trading_fees_id'), 'trading_fees', ['id'], unique=False)
    op.create_index(op.f('ix_trading_fees_user_id'), 'trading_fees', ['user_id'], unique=False)
    op.create_index(op.f('ix_trading_fees_trade_type'), 'trading_fees', ['trade_type'], unique=False)
    op.create_index(op.f('ix_trading_fees_dex_trade_id'), 'trading_fees', ['dex_trade_id'], unique=False)
    op.create_index(op.f('ix_trading_fees_cex_trade_id'), 'trading_fees', ['cex_trade_id'], unique=False)
    op.create_index(op.f('ix_trading_fees_fee_type'), 'trading_fees', ['fee_type'], unique=False)
    op.create_index(op.f('ix_trading_fees_user_tier'), 'trading_fees', ['user_tier'], unique=False)
    op.create_index(op.f('ix_trading_fees_is_custodial'), 'trading_fees', ['is_custodial'], unique=False)
    op.create_index(op.f('ix_trading_fees_status'), 'trading_fees', ['status'], unique=False)

    # Create wallet_nonces table
    op.create_table('wallet_nonces',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('wallet_address', sa.String(length=100), nullable=False),
    sa.Column('nonce', sa.Integer(), nullable=False),
    sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1'),
    sa.Column('used', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('used_at', sa.DateTime(), nullable=True),
    sa.Column('expires_at', sa.DateTime(), nullable=False),
    sa.Column('message_type', sa.String(length=50), nullable=False, server_default='trade'),
    sa.Column('message_hash', sa.String(length=100), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('wallet_address', 'nonce', 'chain_id', name='uq_wallet_nonce_chain')
    )
    op.create_index(op.f('ix_wallet_nonces_id'), 'wallet_nonces', ['id'], unique=False)
    op.create_index(op.f('ix_wallet_nonces_user_id'), 'wallet_nonces', ['user_id'], unique=False)
    op.create_index(op.f('ix_wallet_nonces_wallet_address'), 'wallet_nonces', ['wallet_address'], unique=False)
    op.create_index(op.f('ix_wallet_nonces_expires_at'), 'wallet_nonces', ['expires_at'], unique=False)
    op.create_index(op.f('ix_wallet_nonces_used'), 'wallet_nonces', ['used'], unique=False)
    op.create_index(op.f('ix_wallet_nonces_message_hash'), 'wallet_nonces', ['message_hash'], unique=False)
    op.create_index('ix_wallet_nonce_user_wallet', 'wallet_nonces', ['user_id', 'wallet_address'], unique=False)

    # Create user_wallets table
    op.create_table('user_wallets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('wallet_address', sa.String(length=100), nullable=False),
    sa.Column('chain_id', sa.Integer(), nullable=False),
    sa.Column('wallet_type', sa.String(length=20), nullable=False, server_default='custodial'),
    sa.Column('balance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('last_balance_update', sa.DateTime(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
    sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('label', sa.String(length=100), nullable=True),
    sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'wallet_address', 'chain_id', name='uq_user_wallet_chain')
    )
    op.create_index(op.f('ix_user_wallets_id'), 'user_wallets', ['id'], unique=False)
    op.create_index(op.f('ix_user_wallets_user_id'), 'user_wallets', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_wallets_wallet_address'), 'user_wallets', ['wallet_address'], unique=False)
    op.create_index(op.f('ix_user_wallets_chain_id'), 'user_wallets', ['chain_id'], unique=False)
    op.create_index(op.f('ix_user_wallets_wallet_type'), 'user_wallets', ['wallet_type'], unique=False)
    op.create_index(op.f('ix_user_wallets_is_active'), 'user_wallets', ['is_active'], unique=False)
    op.create_index(op.f('ix_user_wallets_is_verified'), 'user_wallets', ['is_verified'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_user_wallets_is_verified'), table_name='user_wallets')
    op.drop_index(op.f('ix_user_wallets_is_active'), table_name='user_wallets')
    op.drop_index(op.f('ix_user_wallets_wallet_type'), table_name='user_wallets')
    op.drop_index(op.f('ix_user_wallets_chain_id'), table_name='user_wallets')
    op.drop_index(op.f('ix_user_wallets_wallet_address'), table_name='user_wallets')
    op.drop_index(op.f('ix_user_wallets_user_id'), table_name='user_wallets')
    op.drop_index(op.f('ix_user_wallets_id'), table_name='user_wallets')
    op.drop_table('user_wallets')
    
    op.drop_index('ix_wallet_nonce_user_wallet', table_name='wallet_nonces')
    op.drop_index(op.f('ix_wallet_nonces_message_hash'), table_name='wallet_nonces')
    op.drop_index(op.f('ix_wallet_nonces_used'), table_name='wallet_nonces')
    op.drop_index(op.f('ix_wallet_nonces_expires_at'), table_name='wallet_nonces')
    op.drop_index(op.f('ix_wallet_nonces_wallet_address'), table_name='wallet_nonces')
    op.drop_index(op.f('ix_wallet_nonces_user_id'), table_name='wallet_nonces')
    op.drop_index(op.f('ix_wallet_nonces_id'), table_name='wallet_nonces')
    op.drop_table('wallet_nonces')
    
    op.drop_index(op.f('ix_trading_fees_status'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_is_custodial'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_user_tier'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_fee_type'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_cex_trade_id'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_dex_trade_id'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_trade_type'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_user_id'), table_name='trading_fees')
    op.drop_index(op.f('ix_trading_fees_id'), table_name='trading_fees')
    op.drop_table('trading_fees')
    
    op.drop_index(op.f('ix_dex_trades_status'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_transaction_status'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_transaction_hash'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_user_wallet_address'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_aggregator'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_chain_id'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_trade_type'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_user_id'), table_name='dex_trades')
    op.drop_index(op.f('ix_dex_trades_id'), table_name='dex_trades')
    op.drop_table('dex_trades')
