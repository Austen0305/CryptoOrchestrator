"""Add DEX positions table

Revision ID: add_dex_positions_2025
Revises: bot_exchange_to_chain_id_2025
Create Date: 2025-12-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_dex_positions_2025'
down_revision = 'bot_exchange_to_chain_id_2025'  # Update to latest migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if table already exists
    if 'dex_positions' in inspector.get_table_names():
        return  # Table already exists
    
    # Create dex_positions table
    op.create_table('dex_positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('chain_id', sa.Integer(), nullable=False),
        sa.Column('token_address', sa.String(length=100), nullable=False),
        sa.Column('token_symbol', sa.String(length=20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('amount_usd', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('entry_trade_id', sa.Integer(), nullable=True),
        sa.Column('current_price', sa.Float(), nullable=False),
        sa.Column('current_value_usd', sa.Float(), nullable=False),
        sa.Column('unrealized_pnl', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('unrealized_pnl_percent', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('is_open', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('exit_trade_id', sa.Integer(), nullable=True),
        sa.Column('exit_price', sa.Float(), nullable=True),
        sa.Column('realized_pnl', sa.Float(), nullable=True),
        sa.Column('realized_pnl_percent', sa.Float(), nullable=True),
        sa.Column('metadata', sa.Text(), nullable=True),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['entry_trade_id'], ['dex_trades.id'], ),
        sa.ForeignKeyConstraint(['exit_trade_id'], ['dex_trades.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_dex_positions_id'), 'dex_positions', ['id'], unique=False)
    op.create_index(op.f('ix_dex_positions_user_id'), 'dex_positions', ['user_id'], unique=False)
    op.create_index(op.f('ix_dex_positions_chain_id'), 'dex_positions', ['chain_id'], unique=False)
    op.create_index(op.f('ix_dex_positions_token_address'), 'dex_positions', ['token_address'], unique=False)
    op.create_index(op.f('ix_dex_positions_is_open'), 'dex_positions', ['is_open'], unique=False)
    op.create_index(
        'ix_dex_positions_user_chain_open',
        'dex_positions',
        ['user_id', 'chain_id', 'is_open'],
        unique=False
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Drop indexes
    if 'dex_positions' in inspector.get_table_names():
        try:
            op.drop_index('ix_dex_positions_user_chain_open', table_name='dex_positions')
            op.drop_index(op.f('ix_dex_positions_is_open'), table_name='dex_positions')
            op.drop_index(op.f('ix_dex_positions_token_address'), table_name='dex_positions')
            op.drop_index(op.f('ix_dex_positions_chain_id'), table_name='dex_positions')
            op.drop_index(op.f('ix_dex_positions_user_id'), table_name='dex_positions')
            op.drop_index(op.f('ix_dex_positions_id'), table_name='dex_positions')
        except Exception:
            pass  # Indexes may not exist
        
        # Drop table
        op.drop_table('dex_positions')
