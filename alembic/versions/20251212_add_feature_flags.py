"""Add feature flags and A/B testing

Revision ID: 20251212_feature_flags
Revises: 20251212_social_features
Create Date: 2025-12-12 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_feature_flags'
down_revision = '20251212_social_features'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create feature_flags table
    op.create_table(
        'feature_flags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flag_key', sa.String(length=100), nullable=False),
        sa.Column('flag_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('DISABLED', 'ENABLED', 'ROLLING_OUT', 'DEPRECATED', name='flagstatus'), nullable=False),
        sa.Column('rollout_percentage', sa.Integer(), nullable=False),
        sa.Column('target_users', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('target_segments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('target_conditions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('variants', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by_user_id', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('flag_key')
    )
    op.create_index(op.f('ix_feature_flags_id'), 'feature_flags', ['id'], unique=False)
    op.create_index(op.f('ix_feature_flags_flag_key'), 'feature_flags', ['flag_key'], unique=True)
    op.create_index(op.f('ix_feature_flags_status'), 'feature_flags', ['status'], unique=False)
    op.create_index('idx_feature_flags_status', 'feature_flags', ['status', 'created_at'], unique=False)

    # Create flag_evaluations table
    op.create_table(
        'flag_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flag_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('variant', sa.String(length=100), nullable=True),
        sa.Column('context', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flag_id'], ['feature_flags.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_flag_evaluations_id'), 'flag_evaluations', ['id'], unique=False)
    op.create_index(op.f('ix_flag_evaluations_flag_id'), 'flag_evaluations', ['flag_id'], unique=False)
    op.create_index(op.f('ix_flag_evaluations_user_id'), 'flag_evaluations', ['user_id'], unique=False)
    op.create_index(op.f('ix_flag_evaluations_enabled'), 'flag_evaluations', ['enabled'], unique=False)
    op.create_index('idx_flag_evaluations_flag_user', 'flag_evaluations', ['flag_id', 'user_id', 'created_at'], unique=False)
    op.create_index('idx_flag_evaluations_enabled', 'flag_evaluations', ['enabled', 'created_at'], unique=False)

    # Create ab_test_experiments table
    op.create_table(
        'ab_test_experiments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('flag_id', sa.Integer(), nullable=False),
        sa.Column('experiment_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('variants', postgresql.JSON(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('primary_metric', sa.String(length=100), nullable=False),
        sa.Column('results', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['flag_id'], ['feature_flags.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ab_test_experiments_id'), 'ab_test_experiments', ['id'], unique=False)
    op.create_index(op.f('ix_ab_test_experiments_flag_id'), 'ab_test_experiments', ['flag_id'], unique=False)
    op.create_index(op.f('ix_ab_test_experiments_is_active'), 'ab_test_experiments', ['is_active'], unique=False)
    op.create_index(op.f('ix_ab_test_experiments_start_date'), 'ab_test_experiments', ['start_date'], unique=False)
    op.create_index(op.f('ix_ab_test_experiments_end_date'), 'ab_test_experiments', ['end_date'], unique=False)
    op.create_index('idx_experiments_active', 'ab_test_experiments', ['is_active', 'start_date', 'end_date'], unique=False)

    # Create experiment_assignments table
    op.create_table(
        'experiment_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('experiment_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('variant', sa.String(length=100), nullable=False),
        sa.Column('assigned_at', sa.DateTime(), nullable=False),
        sa.Column('converted', sa.Boolean(), nullable=True),
        sa.Column('converted_at', sa.DateTime(), nullable=True),
        sa.Column('conversion_value', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['experiment_id'], ['ab_test_experiments.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_experiment_assignments_id'), 'experiment_assignments', ['id'], unique=False)
    op.create_index(op.f('ix_experiment_assignments_experiment_id'), 'experiment_assignments', ['experiment_id'], unique=False)
    op.create_index(op.f('ix_experiment_assignments_user_id'), 'experiment_assignments', ['user_id'], unique=False)
    op.create_index(op.f('ix_experiment_assignments_variant'), 'experiment_assignments', ['variant'], unique=False)
    op.create_index(op.f('ix_experiment_assignments_converted'), 'experiment_assignments', ['converted'], unique=False)
    op.create_index('idx_experiment_assignments_experiment_user', 'experiment_assignments', ['experiment_id', 'user_id'], unique=True)
    op.create_index('idx_experiment_assignments_variant', 'experiment_assignments', ['variant', 'converted', 'created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_experiment_assignments_variant', table_name='experiment_assignments')
    op.drop_index('idx_experiment_assignments_experiment_user', table_name='experiment_assignments')
    op.drop_index(op.f('ix_experiment_assignments_converted'), table_name='experiment_assignments')
    op.drop_index(op.f('ix_experiment_assignments_variant'), table_name='experiment_assignments')
    op.drop_index(op.f('ix_experiment_assignments_user_id'), table_name='experiment_assignments')
    op.drop_index(op.f('ix_experiment_assignments_experiment_id'), table_name='experiment_assignments')
    op.drop_index(op.f('ix_experiment_assignments_id'), table_name='experiment_assignments')
    op.drop_table('experiment_assignments')
    op.drop_index('idx_experiments_active', table_name='ab_test_experiments')
    op.drop_index(op.f('ix_ab_test_experiments_end_date'), table_name='ab_test_experiments')
    op.drop_index(op.f('ix_ab_test_experiments_start_date'), table_name='ab_test_experiments')
    op.drop_index(op.f('ix_ab_test_experiments_is_active'), table_name='ab_test_experiments')
    op.drop_index(op.f('ix_ab_test_experiments_flag_id'), table_name='ab_test_experiments')
    op.drop_index(op.f('ix_ab_test_experiments_id'), table_name='ab_test_experiments')
    op.drop_table('ab_test_experiments')
    op.drop_index('idx_flag_evaluations_enabled', table_name='flag_evaluations')
    op.drop_index('idx_flag_evaluations_flag_user', table_name='flag_evaluations')
    op.drop_index(op.f('ix_flag_evaluations_enabled'), table_name='flag_evaluations')
    op.drop_index(op.f('ix_flag_evaluations_user_id'), table_name='flag_evaluations')
    op.drop_index(op.f('ix_flag_evaluations_flag_id'), table_name='flag_evaluations')
    op.drop_index(op.f('ix_flag_evaluations_id'), table_name='flag_evaluations')
    op.drop_table('flag_evaluations')
    op.drop_index('idx_feature_flags_status', table_name='feature_flags')
    op.drop_index(op.f('ix_feature_flags_status'), table_name='feature_flags')
    op.drop_index(op.f('ix_feature_flags_flag_key'), table_name='feature_flags')
    op.drop_index(op.f('ix_feature_flags_id'), table_name='feature_flags')
    op.drop_table('feature_flags')
    op.execute("DROP TYPE flagstatus")
