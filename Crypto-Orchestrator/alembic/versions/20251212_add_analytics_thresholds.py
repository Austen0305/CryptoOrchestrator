"""add_analytics_thresholds

Add analytics threshold notification system:
- analytics_thresholds: Configurable threshold alerts for marketplace analytics metrics

Revision ID: 20251212_analytics_thresholds
Revises: 20251212_indicator_marketplace
Create Date: 2025-12-12 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_analytics_thresholds'
down_revision = '20251212_indicator_marketplace'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create analytics_thresholds table
    op.create_table(
        'analytics_thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),  # None for global thresholds
        
        # Threshold configuration
        sa.Column('threshold_type', sa.String(length=50), nullable=False),
        sa.Column('metric', sa.String(length=100), nullable=False),
        sa.Column('operator', sa.String(length=20), nullable=False),
        sa.Column('threshold_value', sa.Float(), nullable=False),
        
        # Context (e.g., provider_id, developer_id for specific entity thresholds)
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Alert configuration
        sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('notification_channels', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Cooldown and frequency
        sa.Column('cooldown_minutes', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('last_triggered_at', sa.DateTime(), nullable=True),
        
        # Metadata
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for analytics_thresholds
    op.create_index(op.f('ix_analytics_thresholds_id'), 'analytics_thresholds', ['id'], unique=False)
    op.create_index('ix_analytics_thresholds_user_id', 'analytics_thresholds', ['user_id'], unique=False)
    op.create_index('ix_analytics_thresholds_threshold_type', 'analytics_thresholds', ['threshold_type'], unique=False)
    op.create_index('ix_analytics_thresholds_metric', 'analytics_thresholds', ['metric'], unique=False)
    op.create_index('ix_analytics_thresholds_enabled', 'analytics_thresholds', ['enabled'], unique=False)
    
    # Composite index for efficient threshold checking queries
    op.create_index(
        'ix_analytics_thresholds_enabled_type',
        'analytics_thresholds',
        ['enabled', 'threshold_type'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_analytics_thresholds_enabled_type', table_name='analytics_thresholds')
    op.drop_index('ix_analytics_thresholds_enabled', table_name='analytics_thresholds')
    op.drop_index('ix_analytics_thresholds_metric', table_name='analytics_thresholds')
    op.drop_index('ix_analytics_thresholds_threshold_type', table_name='analytics_thresholds')
    op.drop_index('ix_analytics_thresholds_user_id', table_name='analytics_thresholds')
    op.drop_index(op.f('ix_analytics_thresholds_id'), table_name='analytics_thresholds')
    
    # Drop table
    op.drop_table('analytics_thresholds')
