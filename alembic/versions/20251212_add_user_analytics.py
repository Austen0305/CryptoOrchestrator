"""Add user analytics tables

Revision ID: 20251212_user_analytics
Revises: 20251212_onboarding
Create Date: 2025-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_user_analytics'
down_revision = '20251212_onboarding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_events table
    op.create_table(
        'user_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('event_name', sa.String(length=200), nullable=False),
        sa.Column('event_category', sa.String(length=100), nullable=True),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('page_url', sa.String(length=500), nullable=True),
        sa.Column('page_title', sa.String(length=200), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('user_agent', sa.String(length=500), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('device_type', sa.String(length=50), nullable=True),
        sa.Column('browser', sa.String(length=100), nullable=True),
        sa.Column('os', sa.String(length=100), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_events_id'), 'user_events', ['id'], unique=False)
    op.create_index(op.f('ix_user_events_user_id'), 'user_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_events_session_id'), 'user_events', ['session_id'], unique=False)
    op.create_index(op.f('ix_user_events_event_type'), 'user_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_user_events_event_name'), 'user_events', ['event_name'], unique=False)
    op.create_index(op.f('ix_user_events_event_category'), 'user_events', ['event_category'], unique=False)
    op.create_index('idx_user_events_user_time', 'user_events', ['user_id', 'created_at'], unique=False)
    op.create_index('idx_user_events_type_time', 'user_events', ['event_type', 'created_at'], unique=False)
    op.create_index('idx_user_events_session', 'user_events', ['session_id', 'created_at'], unique=False)

    # Create feature_usage table
    op.create_table(
        'feature_usage',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('feature_name', sa.String(length=100), nullable=False),
        sa.Column('feature_category', sa.String(length=100), nullable=True),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=True),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_feature_usage_id'), 'feature_usage', ['id'], unique=False)
    op.create_index(op.f('ix_feature_usage_user_id'), 'feature_usage', ['user_id'], unique=False)
    op.create_index(op.f('ix_feature_usage_feature_name'), 'feature_usage', ['feature_name'], unique=False)
    op.create_index(op.f('ix_feature_usage_feature_category'), 'feature_usage', ['feature_category'], unique=False)
    op.create_index('idx_feature_usage_user_feature', 'feature_usage', ['user_id', 'feature_name', 'created_at'], unique=False)
    op.create_index('idx_feature_usage_feature_time', 'feature_usage', ['feature_name', 'created_at'], unique=False)

    # Create conversion_funnels table
    op.create_table(
        'conversion_funnels',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=True),
        sa.Column('funnel_name', sa.String(length=100), nullable=False),
        sa.Column('stage', sa.String(length=100), nullable=False),
        sa.Column('stage_order', sa.Integer(), nullable=False),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('dropped_at_stage', sa.String(length=100), nullable=True),
        sa.Column('time_to_stage_seconds', sa.Integer(), nullable=True),
        sa.Column('time_in_stage_seconds', sa.Integer(), nullable=True),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('source', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_conversion_funnels_id'), 'conversion_funnels', ['id'], unique=False)
    op.create_index(op.f('ix_conversion_funnels_user_id'), 'conversion_funnels', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversion_funnels_session_id'), 'conversion_funnels', ['session_id'], unique=False)
    op.create_index(op.f('ix_conversion_funnels_funnel_name'), 'conversion_funnels', ['funnel_name'], unique=False)
    op.create_index(op.f('ix_conversion_funnels_stage'), 'conversion_funnels', ['stage'], unique=False)
    op.create_index(op.f('ix_conversion_funnels_is_completed'), 'conversion_funnels', ['is_completed'], unique=False)
    op.create_index('idx_conversion_funnel_user', 'conversion_funnels', ['user_id', 'funnel_name', 'created_at'], unique=False)
    op.create_index('idx_conversion_funnel_stage', 'conversion_funnels', ['funnel_name', 'stage', 'created_at'], unique=False)

    # Create user_journeys table
    op.create_table(
        'user_journeys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=100), nullable=False),
        sa.Column('journey_type', sa.String(length=100), nullable=False),
        sa.Column('step_name', sa.String(length=200), nullable=False),
        sa.Column('step_order', sa.Integer(), nullable=False),
        sa.Column('previous_step', sa.String(length=200), nullable=True),
        sa.Column('next_step', sa.String(length=200), nullable=True),
        sa.Column('path', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('time_to_step_seconds', sa.Integer(), nullable=True),
        sa.Column('time_in_step_seconds', sa.Integer(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_journeys_id'), 'user_journeys', ['id'], unique=False)
    op.create_index(op.f('ix_user_journeys_user_id'), 'user_journeys', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_journeys_session_id'), 'user_journeys', ['session_id'], unique=False)
    op.create_index(op.f('ix_user_journeys_journey_type'), 'user_journeys', ['journey_type'], unique=False)
    op.create_index(op.f('ix_user_journeys_is_completed'), 'user_journeys', ['is_completed'], unique=False)
    op.create_index('idx_user_journey_session', 'user_journeys', ['session_id', 'created_at'], unique=False)
    op.create_index('idx_user_journey_user_type', 'user_journeys', ['user_id', 'journey_type', 'created_at'], unique=False)

    # Create user_satisfaction table
    op.create_table(
        'user_satisfaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('survey_type', sa.String(length=100), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('question', sa.String(length=500), nullable=True),
        sa.Column('response', sa.Text(), nullable=True),
        sa.Column('context', sa.String(length=200), nullable=True),
        sa.Column('properties', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_satisfaction_id'), 'user_satisfaction', ['id'], unique=False)
    op.create_index(op.f('ix_user_satisfaction_user_id'), 'user_satisfaction', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_satisfaction_survey_type'), 'user_satisfaction', ['survey_type'], unique=False)
    op.create_index('idx_user_satisfaction_user_type', 'user_satisfaction', ['user_id', 'survey_type', 'created_at'], unique=False)
    op.create_index('idx_user_satisfaction_score', 'user_satisfaction', ['survey_type', 'score', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_user_satisfaction_score', table_name='user_satisfaction')
    op.drop_index('idx_user_satisfaction_user_type', table_name='user_satisfaction')
    op.drop_index(op.f('ix_user_satisfaction_survey_type'), table_name='user_satisfaction')
    op.drop_index(op.f('ix_user_satisfaction_user_id'), table_name='user_satisfaction')
    op.drop_index(op.f('ix_user_satisfaction_id'), table_name='user_satisfaction')
    op.drop_table('user_satisfaction')
    op.drop_index('idx_user_journey_user_type', table_name='user_journeys')
    op.drop_index('idx_user_journey_session', table_name='user_journeys')
    op.drop_index(op.f('ix_user_journeys_is_completed'), table_name='user_journeys')
    op.drop_index(op.f('ix_user_journeys_journey_type'), table_name='user_journeys')
    op.drop_index(op.f('ix_user_journeys_session_id'), table_name='user_journeys')
    op.drop_index(op.f('ix_user_journeys_user_id'), table_name='user_journeys')
    op.drop_index(op.f('ix_user_journeys_id'), table_name='user_journeys')
    op.drop_table('user_journeys')
    op.drop_index('idx_conversion_funnel_stage', table_name='conversion_funnels')
    op.drop_index('idx_conversion_funnel_user', table_name='conversion_funnels')
    op.drop_index(op.f('ix_conversion_funnels_is_completed'), table_name='conversion_funnels')
    op.drop_index(op.f('ix_conversion_funnels_stage'), table_name='conversion_funnels')
    op.drop_index(op.f('ix_conversion_funnels_funnel_name'), table_name='conversion_funnels')
    op.drop_index(op.f('ix_conversion_funnels_session_id'), table_name='conversion_funnels')
    op.drop_index(op.f('ix_conversion_funnels_user_id'), table_name='conversion_funnels')
    op.drop_index(op.f('ix_conversion_funnels_id'), table_name='conversion_funnels')
    op.drop_table('conversion_funnels')
    op.drop_index('idx_feature_usage_feature_time', table_name='feature_usage')
    op.drop_index('idx_feature_usage_user_feature', table_name='feature_usage')
    op.drop_index(op.f('ix_feature_usage_feature_category'), table_name='feature_usage')
    op.drop_index(op.f('ix_feature_usage_feature_name'), table_name='feature_usage')
    op.drop_index(op.f('ix_feature_usage_user_id'), table_name='feature_usage')
    op.drop_index(op.f('ix_feature_usage_id'), table_name='feature_usage')
    op.drop_table('feature_usage')
    op.drop_index('idx_user_events_session', table_name='user_events')
    op.drop_index('idx_user_events_type_time', table_name='user_events')
    op.drop_index('idx_user_events_user_time', table_name='user_events')
    op.drop_index(op.f('ix_user_events_event_category'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_event_name'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_event_type'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_session_id'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_user_id'), table_name='user_events')
    op.drop_index(op.f('ix_user_events_id'), table_name='user_events')
    op.drop_table('user_events')
