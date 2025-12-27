"""add_accounting_connections

Add accounting system connection models:
- accounting_connections: OAuth credentials and connection metadata for QuickBooks/Xero
- accounting_sync_logs: Sync history and results tracking

Revision ID: 20251212_accounting_connections
Revises: 20251212_social_recovery
Create Date: 2025-12-12 19:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_accounting_connections'
down_revision = '20251212_social_recovery'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create accounting_connections table
    op.create_table(
        'accounting_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('system', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('access_token', sa.Text(), nullable=False),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.Column('realm_id', sa.String(length=100), nullable=True),
        sa.Column('tenant_id', sa.String(length=100), nullable=True),
        sa.Column('sync_frequency', sa.String(length=20), nullable=False, server_default='manual'),
        sa.Column('last_sync_at', sa.DateTime(), nullable=True),
        sa.Column('next_sync_at', sa.DateTime(), nullable=True),
        sa.Column('account_mappings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_accounting_connections_id'), 'accounting_connections', ['id'], unique=False)
    op.create_index(op.f('ix_accounting_connections_user_id'), 'accounting_connections', ['user_id'], unique=False)
    op.create_index(op.f('ix_accounting_connections_system'), 'accounting_connections', ['system'], unique=False)
    op.create_index(op.f('ix_accounting_connections_status'), 'accounting_connections', ['status'], unique=False)
    op.create_index('idx_user_system', 'accounting_connections', ['user_id', 'system'], unique=True)
    
    # Create accounting_sync_logs table
    op.create_table(
        'accounting_sync_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('connection_id', sa.Integer(), nullable=False),
        sa.Column('sync_type', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('transactions_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('transactions_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['connection_id'], ['accounting_connections.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_accounting_sync_logs_id'), 'accounting_sync_logs', ['id'], unique=False)
    op.create_index(op.f('ix_accounting_sync_logs_connection_id'), 'accounting_sync_logs', ['connection_id'], unique=False)
    op.create_index(op.f('ix_accounting_sync_logs_status'), 'accounting_sync_logs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_accounting_sync_logs_status'), table_name='accounting_sync_logs')
    op.drop_index(op.f('ix_accounting_sync_logs_connection_id'), table_name='accounting_sync_logs')
    op.drop_index(op.f('ix_accounting_sync_logs_id'), table_name='accounting_sync_logs')
    op.drop_table('accounting_sync_logs')
    
    op.drop_index('idx_user_system', table_name='accounting_connections')
    op.drop_index(op.f('ix_accounting_connections_status'), table_name='accounting_connections')
    op.drop_index(op.f('ix_accounting_connections_system'), table_name='accounting_connections')
    op.drop_index(op.f('ix_accounting_connections_user_id'), table_name='accounting_connections')
    op.drop_index(op.f('ix_accounting_connections_id'), table_name='accounting_connections')
    op.drop_table('accounting_connections')
