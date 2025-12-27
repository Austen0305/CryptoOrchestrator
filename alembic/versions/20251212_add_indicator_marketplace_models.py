"""add_indicator_marketplace_models

Add indicator marketplace models:
- indicators: Custom indicators with versioning, pricing, ratings
- indicator_versions: Version tracking for indicators
- indicator_purchases: Purchase tracking with 70/30 revenue split
- indicator_ratings: User ratings for indicators

Revision ID: 20251212_indicator_marketplace
Revises: 20251212_marketplace
Create Date: 2025-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_indicator_marketplace'
down_revision = '20251212_marketplace'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create indicators table
    op.create_table(
        'indicators',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('developer_id', sa.Integer(), nullable=False),
        
        # Basic information
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        
        # Marketplace status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft'),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_featured', sa.Boolean(), nullable=False, server_default='false'),
        
        # Pricing
        sa.Column('price', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_free', sa.Boolean(), nullable=False, server_default='true'),
        
        # Technical details
        sa.Column('language', sa.String(length=20), nullable=False, server_default='python'),
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Versioning
        sa.Column('current_version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('latest_version_id', sa.Integer(), nullable=True),
        
        # Statistics
        sa.Column('download_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('purchase_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_ratings', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue', sa.Float(), nullable=False, server_default='0.0'),
        
        # Documentation
        sa.Column('documentation', sa.Text(), nullable=True),
        sa.Column('usage_examples', sa.Text(), nullable=True),
        sa.Column('changelog', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.ForeignKeyConstraint(['developer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for indicators
    op.create_index(op.f('ix_indicators_id'), 'indicators', ['id'], unique=False)
    op.create_index('ix_indicators_developer_id', 'indicators', ['developer_id'], unique=False)
    op.create_index('ix_indicators_status', 'indicators', ['status'], unique=False)
    op.create_index('ix_indicators_is_public', 'indicators', ['is_public'], unique=False)
    op.create_index('ix_indicators_category', 'indicators', ['category'], unique=False)
    op.create_index('ix_indicators_language', 'indicators', ['language'], unique=False)
    op.create_index('ix_indicators_download_count', 'indicators', ['download_count'], unique=False)
    op.create_index('ix_indicators_average_rating', 'indicators', ['average_rating'], unique=False)
    
    # Create indicator_versions table
    op.create_table(
        'indicator_versions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False),
        
        # Version information
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('version_name', sa.String(length=50), nullable=True),
        sa.Column('changelog', sa.Text(), nullable=True),
        
        # Code
        sa.Column('code', sa.Text(), nullable=False),
        sa.Column('parameters', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_breaking', sa.Boolean(), nullable=False, server_default='false'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for indicator_versions
    op.create_index(op.f('ix_indicator_versions_id'), 'indicator_versions', ['id'], unique=False)
    op.create_index('ix_indicator_versions_indicator_id', 'indicator_versions', ['indicator_id'], unique=False)
    op.create_index('ix_indicator_versions_version', 'indicator_versions', ['version'], unique=False)
    op.create_index('ix_indicator_versions_is_active', 'indicator_versions', ['is_active'], unique=False)
    # Composite index for indicator-version uniqueness
    op.create_index('ix_indicator_versions_indicator_version', 'indicator_versions', ['indicator_id', 'version'], unique=True)
    
    # Create indicator_purchases table
    op.create_table(
        'indicator_purchases',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # Purchase details
        sa.Column('price_paid', sa.Float(), nullable=False),
        sa.Column('platform_fee', sa.Float(), nullable=False),  # 30% to platform
        sa.Column('developer_payout', sa.Float(), nullable=False),  # 70% to developer
        
        # Version purchased
        sa.Column('version_id', sa.Integer(), nullable=False),
        
        # Status
        sa.Column('status', sa.String(length=20), nullable=False, server_default='completed'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['version_id'], ['indicator_versions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for indicator_purchases
    op.create_index(op.f('ix_indicator_purchases_id'), 'indicator_purchases', ['id'], unique=False)
    op.create_index('ix_indicator_purchases_indicator_id', 'indicator_purchases', ['indicator_id'], unique=False)
    op.create_index('ix_indicator_purchases_user_id', 'indicator_purchases', ['user_id'], unique=False)
    op.create_index('ix_indicator_purchases_version_id', 'indicator_purchases', ['version_id'], unique=False)
    op.create_index('ix_indicator_purchases_status', 'indicator_purchases', ['status'], unique=False)
    # Composite index for user-indicator uniqueness (one purchase per user per indicator)
    op.create_index('ix_indicator_purchases_user_indicator', 'indicator_purchases', ['user_id', 'indicator_id'], unique=False)
    
    # Create indicator_ratings table
    op.create_table(
        'indicator_ratings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('indicator_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        
        # Rating (1-5 stars)
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.ForeignKeyConstraint(['indicator_id'], ['indicators.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for indicator_ratings
    op.create_index(op.f('ix_indicator_ratings_id'), 'indicator_ratings', ['id'], unique=False)
    op.create_index('ix_indicator_ratings_indicator_id', 'indicator_ratings', ['indicator_id'], unique=False)
    op.create_index('ix_indicator_ratings_user_id', 'indicator_ratings', ['user_id'], unique=False)
    op.create_index('ix_indicator_ratings_rating', 'indicator_ratings', ['rating'], unique=False)
    # Composite index for user-indicator uniqueness (one rating per user per indicator)
    op.create_index('ix_indicator_ratings_user_indicator', 'indicator_ratings', ['user_id', 'indicator_id'], unique=True)


def downgrade() -> None:
    # Drop indicator_ratings table
    op.drop_index('ix_indicator_ratings_user_indicator', table_name='indicator_ratings')
    op.drop_index('ix_indicator_ratings_rating', table_name='indicator_ratings')
    op.drop_index('ix_indicator_ratings_user_id', table_name='indicator_ratings')
    op.drop_index('ix_indicator_ratings_indicator_id', table_name='indicator_ratings')
    op.drop_index(op.f('ix_indicator_ratings_id'), table_name='indicator_ratings')
    op.drop_table('indicator_ratings')
    
    # Drop indicator_purchases table
    op.drop_index('ix_indicator_purchases_user_indicator', table_name='indicator_purchases')
    op.drop_index('ix_indicator_purchases_status', table_name='indicator_purchases')
    op.drop_index('ix_indicator_purchases_version_id', table_name='indicator_purchases')
    op.drop_index('ix_indicator_purchases_user_id', table_name='indicator_purchases')
    op.drop_index('ix_indicator_purchases_indicator_id', table_name='indicator_purchases')
    op.drop_index(op.f('ix_indicator_purchases_id'), table_name='indicator_purchases')
    op.drop_table('indicator_purchases')
    
    # Drop indicator_versions table
    op.drop_index('ix_indicator_versions_indicator_version', table_name='indicator_versions')
    op.drop_index('ix_indicator_versions_is_active', table_name='indicator_versions')
    op.drop_index('ix_indicator_versions_version', table_name='indicator_versions')
    op.drop_index('ix_indicator_versions_indicator_id', table_name='indicator_versions')
    op.drop_index(op.f('ix_indicator_versions_id'), table_name='indicator_versions')
    op.drop_table('indicator_versions')
    
    # Drop indicators table
    op.drop_index('ix_indicators_average_rating', table_name='indicators')
    op.drop_index('ix_indicators_download_count', table_name='indicators')
    op.drop_index('ix_indicators_language', table_name='indicators')
    op.drop_index('ix_indicators_category', table_name='indicators')
    op.drop_index('ix_indicators_is_public', table_name='indicators')
    op.drop_index('ix_indicators_status', table_name='indicators')
    op.drop_index('ix_indicators_developer_id', table_name='indicators')
    op.drop_index(op.f('ix_indicators_id'), table_name='indicators')
    op.drop_table('indicators')
