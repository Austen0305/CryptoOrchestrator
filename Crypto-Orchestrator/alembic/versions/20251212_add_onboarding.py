"""add_onboarding

Add user onboarding system models:
- onboarding_progress: Step tracking and completion
- user_achievements: Achievement system
- feature_access: Feature unlocking

Revision ID: 20251212_onboarding
Revises: 20251212_accounting_connections
Create Date: 2025-12-12 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_onboarding'
down_revision = '20251212_accounting_connections'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create onboarding_progress table
    op.create_table(
        'onboarding_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('current_step', sa.String(length=50), nullable=True),
        sa.Column('completed_steps', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('skipped_steps', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_steps', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_onboarding_progress_id'), 'onboarding_progress', ['id'], unique=False)
    op.create_index(op.f('ix_onboarding_progress_user_id'), 'onboarding_progress', ['user_id'], unique=True)
    op.create_index(op.f('ix_onboarding_progress_is_completed'), 'onboarding_progress', ['is_completed'], unique=False)
    
    # Create user_achievements table
    op.create_table(
        'user_achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('achievement_id', sa.String(length=50), nullable=False),
        sa.Column('achievement_name', sa.String(length=100), nullable=False),
        sa.Column('achievement_description', sa.Text(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_progress', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('unlocked_at', sa.DateTime(), nullable=True),
        sa.Column('is_unlocked', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_user_achievements_id'), 'user_achievements', ['id'], unique=False)
    op.create_index(op.f('ix_user_achievements_user_id'), 'user_achievements', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_achievements_achievement_id'), 'user_achievements', ['achievement_id'], unique=False)
    op.create_index(op.f('ix_user_achievements_unlocked_at'), 'user_achievements', ['unlocked_at'], unique=False)
    op.create_index(op.f('ix_user_achievements_is_unlocked'), 'user_achievements', ['is_unlocked'], unique=False)
    op.create_index('idx_user_achievement', 'user_achievements', ['user_id', 'achievement_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_user_achievement', table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_is_unlocked'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_unlocked_at'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_achievement_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_user_id'), table_name='user_achievements')
    op.drop_index(op.f('ix_user_achievements_id'), table_name='user_achievements')
    op.drop_table('user_achievements')
    
    op.drop_index(op.f('ix_onboarding_progress_is_completed'), table_name='onboarding_progress')
    op.drop_index(op.f('ix_onboarding_progress_user_id'), table_name='onboarding_progress')
    op.drop_index(op.f('ix_onboarding_progress_id'), table_name='onboarding_progress')
    op.drop_table('onboarding_progress')
