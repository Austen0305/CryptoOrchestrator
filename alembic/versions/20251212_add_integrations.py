"""Add webhooks and API keys

Revision ID: 20251212_integrations
Revises: 20251212_audit_logs
Create Date: 2025-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_integrations'
down_revision = '20251212_audit_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create webhooks table
    op.create_table(
        'webhooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=False),
        sa.Column('secret', sa.String(length=100), nullable=True),
        sa.Column('events', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_triggered', sa.DateTime(), nullable=True),
        sa.Column('config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhooks_id'), 'webhooks', ['id'], unique=False)
    op.create_index(op.f('ix_webhooks_user_id'), 'webhooks', ['user_id'], unique=False)
    op.create_index(op.f('ix_webhooks_is_active'), 'webhooks', ['is_active'], unique=False)
    op.create_index('idx_webhooks_user_active', 'webhooks', ['user_id', 'is_active', 'created_at'], unique=False)

    # Create webhook_deliveries table
    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('webhook_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('payload', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('attempted_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['webhook_id'], ['webhooks.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webhook_deliveries_id'), 'webhook_deliveries', ['id'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_webhook_id'), 'webhook_deliveries', ['webhook_id'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_event_type'), 'webhook_deliveries', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_deliveries_status'), 'webhook_deliveries', ['status'], unique=False)
    op.create_index('idx_webhook_deliveries_webhook_status', 'webhook_deliveries', ['webhook_id', 'status', 'created_at'], unique=False)
    op.create_index('idx_webhook_deliveries_event_type', 'webhook_deliveries', ['event_type', 'created_at'], unique=False)

    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('key_name', sa.String(length=200), nullable=False),
        sa.Column('key_prefix', sa.String(length=20), nullable=False),
        sa.Column('key_hash', sa.String(length=64), nullable=False),
        sa.Column('permissions', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rate_limit', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('request_count', sa.Integer(), nullable=True),
        sa.Column('last_ip_address', sa.String(length=45), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_hash')
    )
    op.create_index(op.f('ix_api_keys_id'), 'api_keys', ['id'], unique=False)
    op.create_index(op.f('ix_api_keys_user_id'), 'api_keys', ['user_id'], unique=False)
    op.create_index(op.f('ix_api_keys_key_hash'), 'api_keys', ['key_hash'], unique=True)
    op.create_index(op.f('ix_api_keys_is_active'), 'api_keys', ['is_active'], unique=False)
    op.create_index(op.f('ix_api_keys_expires_at'), 'api_keys', ['expires_at'], unique=False)
    op.create_index('idx_api_keys_user_active', 'api_keys', ['user_id', 'is_active', 'created_at'], unique=False)
    op.create_index('idx_api_keys_expires', 'api_keys', ['expires_at', 'is_active'], unique=False)

    # Create api_key_usage table
    op.create_table(
        'api_key_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.String(length=200), nullable=False),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_api_key_usage_id'), 'api_key_usage', ['id'], unique=False)
    op.create_index(op.f('ix_api_key_usage_api_key_id'), 'api_key_usage', ['id'], unique=False)
    op.create_index(op.f('ix_api_key_usage_endpoint'), 'api_key_usage', ['endpoint'], unique=False)
    op.create_index('idx_api_key_usage_key_timestamp', 'api_key_usage', ['api_key_id', 'created_at'], unique=False)
    op.create_index('idx_api_key_usage_endpoint', 'api_key_usage', ['endpoint', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_api_key_usage_endpoint', table_name='api_key_usage')
    op.drop_index('idx_api_key_usage_key_timestamp', table_name='api_key_usage')
    op.drop_index(op.f('ix_api_key_usage_endpoint'), table_name='api_key_usage')
    op.drop_index(op.f('ix_api_key_usage_api_key_id'), table_name='api_key_usage')
    op.drop_index(op.f('ix_api_key_usage_id'), table_name='api_key_usage')
    op.drop_table('api_key_usage')
    op.drop_index('idx_api_keys_expires', table_name='api_keys')
    op.drop_index('idx_api_keys_user_active', table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_expires_at'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_is_active'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_key_hash'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_user_id'), table_name='api_keys')
    op.drop_index(op.f('ix_api_keys_id'), table_name='api_keys')
    op.drop_table('api_keys')
    op.drop_index('idx_webhook_deliveries_event_type', table_name='webhook_deliveries')
    op.drop_index('idx_webhook_deliveries_webhook_status', table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_status'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_event_type'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_webhook_id'), table_name='webhook_deliveries')
    op.drop_index(op.f('ix_webhook_deliveries_id'), table_name='webhook_deliveries')
    op.drop_table('webhook_deliveries')
    op.drop_index('idx_webhooks_user_active', table_name='webhooks')
    op.drop_index(op.f('ix_webhooks_is_active'), table_name='webhooks')
    op.drop_index(op.f('ix_webhooks_user_id'), table_name='webhooks')
    op.drop_index(op.f('ix_webhooks_id'), table_name='webhooks')
    op.drop_table('webhooks')
