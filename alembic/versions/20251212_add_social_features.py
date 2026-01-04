"""Add social and community features

Revision ID: 20251212_social_features
Revises: 20251212_user_analytics
Create Date: 2025-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20251212_social_features'
down_revision = '20251212_user_analytics'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Get database inspector to check existing tables
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # Create shared_strategies table (only if it doesn't exist)
    if 'shared_strategies' not in existing_tables:
        op.create_table(
        'shared_strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('strategy_config', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('visibility', sa.Enum('PRIVATE', 'PUBLIC', 'UNLISTED', name='strategyvisibility'), nullable=False),
        sa.Column('share_token', sa.String(length=100), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('like_count', sa.Integer(), nullable=False),
        sa.Column('copy_count', sa.Integer(), nullable=False),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_shared_strategies_id'), 'shared_strategies', ['id'], unique=False)
        op.create_index(op.f('ix_shared_strategies_user_id'), 'shared_strategies', ['user_id'], unique=False)
        op.create_index(op.f('ix_shared_strategies_share_token'), 'shared_strategies', ['share_token'], unique=True)
        op.create_index(op.f('ix_shared_strategies_category'), 'shared_strategies', ['category'], unique=False)
        op.create_index(op.f('ix_shared_strategies_is_featured'), 'shared_strategies', ['is_featured'], unique=False)
        op.create_index('idx_shared_strategies_user', 'shared_strategies', ['user_id', 'created_at'], unique=False)
        op.create_index('idx_shared_strategies_visibility', 'shared_strategies', ['visibility', 'created_at'], unique=False)
        op.create_index('idx_shared_strategies_featured', 'shared_strategies', ['is_featured', 'created_at'], unique=False)

    # Create strategy_likes table (only if it doesn't exist)
    if 'strategy_likes' not in existing_tables:
        op.create_table(
        'strategy_likes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['strategy_id'], ['shared_strategies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_strategy_likes_id'), 'strategy_likes', ['id'], unique=False)
        op.create_index(op.f('ix_strategy_likes_user_id'), 'strategy_likes', ['user_id'], unique=False)
        op.create_index(op.f('ix_strategy_likes_strategy_id'), 'strategy_likes', ['strategy_id'], unique=False)
        op.create_index('idx_strategy_likes_unique', 'strategy_likes', ['user_id', 'strategy_id'], unique=True)

    # Create strategy_comments table (only if it doesn't exist)
    if 'strategy_comments' not in existing_tables:
        op.create_table(
        'strategy_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('strategy_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('parent_comment_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['strategy_comments.id'], ),
        sa.ForeignKeyConstraint(['strategy_id'], ['shared_strategies.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_strategy_comments_id'), 'strategy_comments', ['id'], unique=False)
        op.create_index(op.f('ix_strategy_comments_user_id'), 'strategy_comments', ['user_id'], unique=False)
        op.create_index(op.f('ix_strategy_comments_strategy_id'), 'strategy_comments', ['strategy_id'], unique=False)
        op.create_index('idx_strategy_comments_strategy', 'strategy_comments', ['strategy_id', 'created_at'], unique=False)
        op.create_index('idx_strategy_comments_user', 'strategy_comments', ['user_id', 'created_at'], unique=False)

    # Create social_feed_events table (only if it doesn't exist)
    if 'social_feed_events' not in existing_tables:
        op.create_table(
        'social_feed_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_data', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_social_feed_events_id'), 'social_feed_events', ['id'], unique=False)
        op.create_index(op.f('ix_social_feed_events_user_id'), 'social_feed_events', ['user_id'], unique=False)
        op.create_index(op.f('ix_social_feed_events_event_type'), 'social_feed_events', ['event_type'], unique=False)
        op.create_index(op.f('ix_social_feed_events_is_public'), 'social_feed_events', ['is_public'], unique=False)
        op.create_index('idx_social_feed_user_time', 'social_feed_events', ['user_id', 'created_at'], unique=False)
        op.create_index('idx_social_feed_type_time', 'social_feed_events', ['event_type', 'created_at'], unique=False)
        op.create_index('idx_social_feed_public', 'social_feed_events', ['is_public', 'created_at'], unique=False)

    # Create user_profiles table (only if it doesn't exist)
    if 'user_profiles' not in existing_tables:
        op.create_table(
        'user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('website_url', sa.String(length=500), nullable=True),
        sa.Column('twitter_handle', sa.String(length=100), nullable=True),
        sa.Column('telegram_handle', sa.String(length=100), nullable=True),
        sa.Column('total_trades', sa.Integer(), nullable=True),
        sa.Column('win_rate', sa.Float(), nullable=True),
        sa.Column('total_pnl', sa.Float(), nullable=True),
        sa.Column('followers_count', sa.Integer(), nullable=True),
        sa.Column('following_count', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('show_trading_stats', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
        )
        op.create_index(op.f('ix_user_profiles_id'), 'user_profiles', ['id'], unique=False)
        op.create_index(op.f('ix_user_profiles_user_id'), 'user_profiles', ['user_id'], unique=True)
        op.create_index(op.f('ix_user_profiles_is_public'), 'user_profiles', ['is_public'], unique=False)
        op.create_index('idx_user_profiles_public', 'user_profiles', ['is_public', 'created_at'], unique=False)

    # Create achievements table (only if it doesn't exist)
    if 'achievements' not in existing_tables:
        op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('icon_url', sa.String(length=500), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('requirement_type', sa.String(length=100), nullable=False),
        sa.Column('requirement_value', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('rarity', sa.String(length=50), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
        )
        op.create_index(op.f('ix_achievements_id'), 'achievements', ['id'], unique=False)
        op.create_index(op.f('ix_achievements_category'), 'achievements', ['category'], unique=False)
        op.create_index(op.f('ix_achievements_rarity'), 'achievements', ['rarity'], unique=False)
        op.create_index('idx_achievements_category', 'achievements', ['category', 'rarity'], unique=False)

    # Create user_achievements table (only if it doesn't exist)
    if 'user_achievements' not in existing_tables:
        op.create_table(
            'user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.Integer(), nullable=False),
        sa.Column('progress', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['achievement_id'], ['achievements.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_user_achievements_id'), 'user_achievements', ['id'], unique=False)
        op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)
        op.create_index(op.f('ix_user_achievements_achievement_id'), 'user_achievements', ['achievement_id'], unique=False)
        op.create_index('idx_user_achievements_user', 'user_achievements', ['user_id', 'is_completed', 'completed_at'], unique=False)
        op.create_index('idx_user_achievements_unique', 'user_achievements', ['user_id', 'achievement_id'], unique=True)

    # Create community_challenges table
    op.create_table(
        'community_challenges',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('challenge_type', sa.String(length=100), nullable=False),
        sa.Column('rules', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('prizes', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('participant_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_community_challenges_id'), 'community_challenges', ['id'], unique=False)
        op.create_index(op.f('ix_community_challenges_created_by_user_id'), 'community_challenges', ['created_by_user_id'], unique=False)
        op.create_index(op.f('ix_community_challenges_challenge_type'), 'community_challenges', ['challenge_type'], unique=False)
        op.create_index(op.f('ix_community_challenges_start_date'), 'community_challenges', ['start_date'], unique=False)
        op.create_index(op.f('ix_community_challenges_end_date'), 'community_challenges', ['end_date'], unique=False)
        op.create_index(op.f('ix_community_challenges_is_active'), 'community_challenges', ['is_active'], unique=False)
        op.create_index(op.f('ix_community_challenges_is_featured'), 'community_challenges', ['is_featured'], unique=False)
        op.create_index('idx_challenges_active', 'community_challenges', ['is_active', 'start_date', 'end_date'], unique=False)
        op.create_index('idx_challenges_featured', 'community_challenges', ['is_featured', 'start_date'], unique=False)

    # Create challenge_participants table (only if it doesn't exist)
    if 'challenge_participants' not in existing_tables:
        op.create_table(
        'challenge_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('challenge_id', sa.Integer(), nullable=False),
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('rank', sa.Integer(), nullable=True),
        sa.Column('metrics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['challenge_id'], ['community_challenges.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_challenge_participants_id'), 'challenge_participants', ['id'], unique=False)
        op.create_index(op.f('ix_challenge_participants_user_id'), 'challenge_participants', ['user_id'], unique=False)
        op.create_index(op.f('ix_challenge_participants_challenge_id'), 'challenge_participants', ['challenge_id'], unique=False)
        op.create_index(op.f('ix_challenge_participants_score'), 'challenge_participants', ['score'], unique=False)
        op.create_index(op.f('ix_challenge_participants_rank'), 'challenge_participants', ['rank'], unique=False)
        op.create_index('idx_challenge_participants_challenge', 'challenge_participants', ['challenge_id', 'score', 'rank'], unique=False)
        op.create_index('idx_challenge_participants_user', 'challenge_participants', ['user_id', 'challenge_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_challenge_participants_user', table_name='challenge_participants')
    op.drop_index('idx_challenge_participants_challenge', table_name='challenge_participants')
    op.drop_index(op.f('ix_challenge_participants_rank'), table_name='challenge_participants')
    op.drop_index(op.f('ix_challenge_participants_score'), table_name='challenge_participants')
    op.drop_index(op.f('ix_challenge_participants_challenge_id'), table_name='challenge_participants')
    op.drop_index(op.f('ix_challenge_participants_user_id'), table_name='challenge_participants')
    op.drop_index(op.f('ix_challenge_participants_id'), table_name='challenge_participants')
    op.drop_table('challenge_participants')
    op.drop_index('idx_challenges_featured', table_name='community_challenges')
    op.drop_index('idx_challenges_active', table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_is_featured'), table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_is_active'), table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_end_date'), table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_start_date'), table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_challenge_type'), table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_created_by_user_id'), table_name='community_challenges')
    op.drop_index(op.f('ix_community_challenges_id'), table_name='community_challenges')
    op.drop_table('community_challenges')
    op.drop_index('idx_user_achievements_unique', table_name='user_achievements')
    op.drop_index('idx_user_achievements_user', table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_achievement_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_user_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_id'), table_name='user_achievements')
    op.drop_table('user_achievements')
    op.drop_index('idx_achievements_category', table_name='achievements')
    op.drop_index(op.f('ix_achievements_rarity'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_category'), table_name='achievements')
    op.drop_index(op.f('ix_achievements_id'), table_name='achievements')
    op.drop_table('achievements')
    op.drop_index('idx_user_profiles_public', table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_is_public'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_user_id'), table_name='user_profiles')
    op.drop_index(op.f('ix_user_profiles_id'), table_name='user_profiles')
    op.drop_table('user_profiles')
    op.drop_index('idx_social_feed_public', table_name='social_feed_events')
    op.drop_index('idx_social_feed_type_time', table_name='social_feed_events')
    op.drop_index('idx_social_feed_user_time', table_name='social_feed_events')
    op.drop_index(op.f('ix_social_feed_events_is_public'), table_name='social_feed_events')
    op.drop_index(op.f('ix_social_feed_events_event_type'), table_name='social_feed_events')
    op.drop_index(op.f('ix_social_feed_events_user_id'), table_name='social_feed_events')
    op.drop_index(op.f('ix_social_feed_events_id'), table_name='social_feed_events')
    op.drop_table('social_feed_events')
    op.drop_index('idx_strategy_comments_user', table_name='strategy_comments')
    op.drop_index('idx_strategy_comments_strategy', table_name='strategy_comments')
    op.drop_index(op.f('ix_strategy_comments_strategy_id'), table_name='strategy_comments')
    op.drop_index(op.f('ix_strategy_comments_user_id'), table_name='strategy_comments')
    op.drop_index(op.f('ix_strategy_comments_id'), table_name='strategy_comments')
    op.drop_table('strategy_comments')
    op.drop_index('idx_strategy_likes_unique', table_name='strategy_likes')
    op.drop_index(op.f('ix_strategy_likes_strategy_id'), table_name='strategy_likes')
    op.drop_index(op.f('ix_strategy_likes_user_id'), table_name='strategy_likes')
    op.drop_index(op.f('ix_strategy_likes_id'), table_name='strategy_likes')
    op.drop_table('strategy_likes')
    op.drop_index('idx_shared_strategies_featured', table_name='shared_strategies')
    op.drop_index('idx_shared_strategies_visibility', table_name='shared_strategies')
    op.drop_index('idx_shared_strategies_user', table_name='shared_strategies')
    op.drop_index(op.f('ix_shared_strategies_is_featured'), table_name='shared_strategies')
    op.drop_index(op.f('ix_shared_strategies_category'), table_name='shared_strategies')
    op.drop_index(op.f('ix_shared_strategies_share_token'), table_name='shared_strategies')
    op.drop_index(op.f('ix_shared_strategies_user_id'), table_name='shared_strategies')
    op.drop_index(op.f('ix_shared_strategies_id'), table_name='shared_strategies')
    op.drop_table('shared_strategies')
    op.execute("DROP TYPE strategyvisibility")
