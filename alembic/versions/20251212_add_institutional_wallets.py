"""add_institutional_wallets

Add institutional wallet system:
- institutional_wallets: Multi-signature wallets, time-locked wallets, treasury management
- pending_transactions: Transactions requiring signatures
- institutional_wallet_transactions: Executed transactions
- wallet_access_logs: Audit trail for compliance
- wallet_signer_associations: Many-to-many relationship between wallets and signers

Revision ID: 20251212_institutional_wallets
Revises: 20251212_analytics_thresholds
Create Date: 2025-12-12 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_institutional_wallets'
down_revision = '20251212_analytics_thresholds'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create wallet_signer_associations table (association table)
    op.create_table(
        'wallet_signer_associations',
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['wallet_id'], ['institutional_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('wallet_id', 'user_id'),
    )
    op.create_index('idx_wallet_signer', 'wallet_signer_associations', ['wallet_id', 'user_id'])
    
    # Create institutional_wallets table
    op.create_table(
        'institutional_wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),  # Primary owner
        sa.Column('wallet_type', sa.String(length=50), nullable=False),
        sa.Column('wallet_address', sa.String(length=100), nullable=True),
        sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('multisig_type', sa.String(length=20), nullable=True),
        sa.Column('required_signatures', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('total_signers', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unlock_time', sa.DateTime(), nullable=True),
        sa.Column('lock_duration_days', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('balance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('last_balance_update', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_institutional_wallets_id'), 'institutional_wallets', ['id'], unique=False)
    op.create_index(op.f('ix_institutional_wallets_user_id'), 'institutional_wallets', ['user_id'], unique=False)
    op.create_index(op.f('ix_institutional_wallets_wallet_type'), 'institutional_wallets', ['wallet_type'], unique=False)
    op.create_index(op.f('ix_institutional_wallets_status'), 'institutional_wallets', ['status'], unique=False)
    op.create_index(op.f('ix_institutional_wallets_wallet_address'), 'institutional_wallets', ['wallet_address'], unique=False)
    
    # Create pending_transactions table
    op.create_table(
        'pending_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('to_address', sa.String(length=100), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('currency', sa.String(length=10), nullable=True),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('transaction_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('signatures', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('required_signatures', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['institutional_wallets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_pending_transactions_id'), 'pending_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_pending_transactions_wallet_id'), 'pending_transactions', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_pending_transactions_status'), 'pending_transactions', ['status'], unique=False)
    
    # Create institutional_wallet_transactions table
    op.create_table(
        'institutional_wallet_transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('pending_transaction_id', sa.Integer(), nullable=True),
        sa.Column('transaction_hash', sa.String(length=100), nullable=True),
        sa.Column('transaction_type', sa.String(length=50), nullable=False),
        sa.Column('from_address', sa.String(length=100), nullable=False),
        sa.Column('to_address', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=10), nullable=False),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('executed_by', sa.Integer(), nullable=False),
        sa.Column('signatures', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('block_number', sa.Integer(), nullable=True),
        sa.Column('confirmations', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('gas_used', sa.Integer(), nullable=True),
        sa.Column('gas_price', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['institutional_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pending_transaction_id'], ['pending_transactions.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['executed_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_institutional_wallet_transactions_id'), 'institutional_wallet_transactions', ['id'], unique=False)
    op.create_index(op.f('ix_institutional_wallet_transactions_wallet_id'), 'institutional_wallet_transactions', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_institutional_wallet_transactions_transaction_type'), 'institutional_wallet_transactions', ['transaction_type'], unique=False)
    op.create_index(op.f('ix_institutional_wallet_transactions_status'), 'institutional_wallet_transactions', ['status'], unique=False)
    op.create_index(op.f('ix_institutional_wallet_transactions_chain_id'), 'institutional_wallet_transactions', ['chain_id'], unique=False)
    op.create_index(op.f('ix_institutional_wallet_transactions_transaction_hash'), 'institutional_wallet_transactions', ['transaction_hash'], unique=False)
    
    # Create wallet_access_logs table
    op.create_table(
        'wallet_access_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['institutional_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_wallet_access_logs_id'), 'wallet_access_logs', ['id'], unique=False)
    op.create_index(op.f('ix_wallet_access_logs_wallet_id'), 'wallet_access_logs', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_wallet_access_logs_user_id'), 'wallet_access_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_wallet_access_logs_action'), 'wallet_access_logs', ['action'], unique=False)
    op.create_index(op.f('ix_wallet_access_logs_success'), 'wallet_access_logs', ['success'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_wallet_access_logs_success'), table_name='wallet_access_logs')
    op.drop_index(op.f('ix_wallet_access_logs_action'), table_name='wallet_access_logs')
    op.drop_index(op.f('ix_wallet_access_logs_user_id'), table_name='wallet_access_logs')
    op.drop_index(op.f('ix_wallet_access_logs_wallet_id'), table_name='wallet_access_logs')
    op.drop_index(op.f('ix_wallet_access_logs_id'), table_name='wallet_access_logs')
    op.drop_table('wallet_access_logs')
    
    op.drop_index(op.f('ix_institutional_wallet_transactions_transaction_hash'), table_name='institutional_wallet_transactions')
    op.drop_index(op.f('ix_institutional_wallet_transactions_chain_id'), table_name='institutional_wallet_transactions')
    op.drop_index(op.f('ix_institutional_wallet_transactions_status'), table_name='institutional_wallet_transactions')
    op.drop_index(op.f('ix_institutional_wallet_transactions_transaction_type'), table_name='institutional_wallet_transactions')
    op.drop_index(op.f('ix_institutional_wallet_transactions_wallet_id'), table_name='institutional_wallet_transactions')
    op.drop_index(op.f('ix_institutional_wallet_transactions_id'), table_name='institutional_wallet_transactions')
    op.drop_table('institutional_wallet_transactions')
    
    op.drop_index(op.f('ix_pending_transactions_status'), table_name='pending_transactions')
    op.drop_index(op.f('ix_pending_transactions_wallet_id'), table_name='pending_transactions')
    op.drop_index(op.f('ix_pending_transactions_id'), table_name='pending_transactions')
    op.drop_table('pending_transactions')
    
    op.drop_index(op.f('ix_institutional_wallets_wallet_address'), table_name='institutional_wallets')
    op.drop_index(op.f('ix_institutional_wallets_status'), table_name='institutional_wallets')
    op.drop_index(op.f('ix_institutional_wallets_wallet_type'), table_name='institutional_wallets')
    op.drop_index(op.f('ix_institutional_wallets_user_id'), table_name='institutional_wallets')
    op.drop_index(op.f('ix_institutional_wallets_id'), table_name='institutional_wallets')
    op.drop_table('institutional_wallets')
    
    op.drop_index('idx_wallet_signer', table_name='wallet_signer_associations')
    op.drop_table('wallet_signer_associations')
