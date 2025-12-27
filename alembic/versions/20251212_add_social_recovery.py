"""add_social_recovery

Add social recovery system for institutional wallets:
- social_recovery_guardians: Guardians who can approve recovery requests
- recovery_requests: Recovery requests with time-locked recovery windows
- recovery_approvals: Guardian approvals for recovery requests

Revision ID: 20251212_social_recovery
Revises: 20251212_institutional_wallets
Create Date: 2025-12-12 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251212_social_recovery'
down_revision = '20251212_institutional_wallets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create social_recovery_guardians table
    op.create_table(
        'social_recovery_guardians',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('guardian_user_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('verification_token', sa.String(length=100), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('added_by', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['institutional_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guardian_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['added_by'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_social_recovery_guardians_id'), 'social_recovery_guardians', ['id'], unique=False)
    op.create_index(op.f('ix_social_recovery_guardians_wallet_id'), 'social_recovery_guardians', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_social_recovery_guardians_guardian_user_id'), 'social_recovery_guardians', ['guardian_user_id'], unique=False)
    op.create_index(op.f('ix_social_recovery_guardians_email'), 'social_recovery_guardians', ['email'], unique=False)
    op.create_index(op.f('ix_social_recovery_guardians_status'), 'social_recovery_guardians', ['status'], unique=False)
    op.create_index(op.f('ix_social_recovery_guardians_verification_token'), 'social_recovery_guardians', ['verification_token'], unique=False)
    op.create_index('idx_wallet_guardian', 'social_recovery_guardians', ['wallet_id', 'guardian_user_id'], unique=True)
    
    # Create recovery_requests table
    op.create_table(
        'recovery_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('required_approvals', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('current_approvals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('time_lock_days', sa.Integer(), nullable=False, server_default='7'),
        sa.Column('unlock_time', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('executed_by', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['wallet_id'], ['institutional_wallets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['executed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recovery_requests_id'), 'recovery_requests', ['id'], unique=False)
    op.create_index(op.f('ix_recovery_requests_wallet_id'), 'recovery_requests', ['wallet_id'], unique=False)
    op.create_index(op.f('ix_recovery_requests_requester_id'), 'recovery_requests', ['requester_id'], unique=False)
    op.create_index(op.f('ix_recovery_requests_status'), 'recovery_requests', ['status'], unique=False)
    op.create_index(op.f('ix_recovery_requests_unlock_time'), 'recovery_requests', ['unlock_time'], unique=False)
    op.create_index(op.f('ix_recovery_requests_expires_at'), 'recovery_requests', ['expires_at'], unique=False)
    
    # Create recovery_approvals table
    op.create_table(
        'recovery_approvals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recovery_request_id', sa.Integer(), nullable=False),
        sa.Column('guardian_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=False),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('verification_method', sa.String(length=20), nullable=True),
        sa.Column('verification_code', sa.String(length=50), nullable=True),
        sa.Column('ip_address', sa.String(length=50), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['recovery_request_id'], ['recovery_requests.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guardian_id'], ['social_recovery_guardians.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recovery_approvals_id'), 'recovery_approvals', ['id'], unique=False)
    op.create_index(op.f('ix_recovery_approvals_recovery_request_id'), 'recovery_approvals', ['recovery_request_id'], unique=False)
    op.create_index(op.f('ix_recovery_approvals_guardian_id'), 'recovery_approvals', ['guardian_id'], unique=False)
    op.create_index(op.f('ix_recovery_approvals_approver_id'), 'recovery_approvals', ['approver_id'], unique=False)
    op.create_index('idx_recovery_guardian', 'recovery_approvals', ['recovery_request_id', 'guardian_id'], unique=True)


def downgrade() -> None:
    op.drop_index('idx_recovery_guardian', table_name='recovery_approvals')
    op.drop_index(op.f('ix_recovery_approvals_approver_id'), table_name='recovery_approvals')
    op.drop_index(op.f('ix_recovery_approvals_guardian_id'), table_name='recovery_approvals')
    op.drop_index(op.f('ix_recovery_approvals_recovery_request_id'), table_name='recovery_approvals')
    op.drop_index(op.f('ix_recovery_approvals_id'), table_name='recovery_approvals')
    op.drop_table('recovery_approvals')
    
    op.drop_index(op.f('ix_recovery_requests_expires_at'), table_name='recovery_requests')
    op.drop_index(op.f('ix_recovery_requests_unlock_time'), table_name='recovery_requests')
    op.drop_index(op.f('ix_recovery_requests_status'), table_name='recovery_requests')
    op.drop_index(op.f('ix_recovery_requests_requester_id'), table_name='recovery_requests')
    op.drop_index(op.f('ix_recovery_requests_wallet_id'), table_name='recovery_requests')
    op.drop_index(op.f('ix_recovery_requests_id'), table_name='recovery_requests')
    op.drop_table('recovery_requests')
    
    op.drop_index('idx_wallet_guardian', table_name='social_recovery_guardians')
    op.drop_index(op.f('ix_social_recovery_guardians_verification_token'), table_name='social_recovery_guardians')
    op.drop_index(op.f('ix_social_recovery_guardians_status'), table_name='social_recovery_guardians')
    op.drop_index(op.f('ix_social_recovery_guardians_email'), table_name='social_recovery_guardians')
    op.drop_index(op.f('ix_social_recovery_guardians_guardian_user_id'), table_name='social_recovery_guardians')
    op.drop_index(op.f('ix_social_recovery_guardians_wallet_id'), table_name='social_recovery_guardians')
    op.drop_index(op.f('ix_social_recovery_guardians_id'), table_name='social_recovery_guardians')
    op.drop_table('social_recovery_guardians')
