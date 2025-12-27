"""add_orders_table_with_advanced_fields

Revision ID: a1b2c3d4e5f6
Revises: f49a0f90e8a9
Create Date: 2025-01-XX 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f49a0f90e8a9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create orders table with all advanced order type fields
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('bot_id', sa.String(length=50), nullable=True),
        
        # Order details
        sa.Column('exchange', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('pair', sa.String(), nullable=False),
        sa.Column('side', sa.String(), nullable=False),  # 'buy' or 'sell'
        sa.Column('order_type', sa.String(), nullable=False),  # OrderType enum
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),  # OrderStatus enum
        
        # Amount and price
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('price', sa.Float(), nullable=True),  # Limit price
        sa.Column('stop_price', sa.Float(), nullable=True),  # Stop price for stop-limit orders
        sa.Column('take_profit_price', sa.Float(), nullable=True),  # Take profit price
        
        # Trailing stop settings
        sa.Column('trailing_stop_percent', sa.Float(), nullable=True),  # Trailing stop percentage
        sa.Column('trailing_stop_amount', sa.Float(), nullable=True),  # Trailing stop amount
        sa.Column('highest_price', sa.Float(), nullable=True),  # Highest price reached (for trailing stops)
        sa.Column('lowest_price', sa.Float(), nullable=True),  # Lowest price reached (for trailing stops)
        
        # Execution
        sa.Column('filled_amount', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('average_fill_price', sa.Float(), nullable=True),
        sa.Column('exchange_order_id', sa.String(), nullable=True),
        
        # Time in force
        sa.Column('time_in_force', sa.String(length=20), nullable=False, server_default='GTC'),  # GTC, IOC, FOK
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        
        # Mode
        sa.Column('mode', sa.String(), nullable=False, server_default='paper'),  # 'paper' or 'real'
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['bot_id'], ['bots.id'], ondelete='SET NULL'),
    )
    
    # Create indexes for performance
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)
    op.create_index(op.f('ix_orders_bot_id'), 'orders', ['bot_id'], unique=False)
    op.create_index(op.f('ix_orders_symbol'), 'orders', ['symbol'], unique=False)
    op.create_index(op.f('ix_orders_pair'), 'orders', ['pair'], unique=False)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'], unique=False)
    op.create_index(op.f('ix_orders_mode'), 'orders', ['mode'], unique=False)
    op.create_index(op.f('ix_orders_order_type'), 'orders', ['order_type'], unique=False)
    op.create_index(op.f('ix_orders_exchange_order_id'), 'orders', ['exchange_order_id'], unique=False)
    op.create_index(op.f('ix_orders_created_at'), 'orders', ['created_at'], unique=False)
    
    # Composite index for common queries
    op.create_index('ix_orders_user_status', 'orders', ['user_id', 'status'], unique=False)
    op.create_index('ix_orders_user_mode', 'orders', ['user_id', 'mode'], unique=False)
    op.create_index('ix_orders_symbol_status', 'orders', ['symbol', 'status'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_orders_symbol_status', table_name='orders')
    op.drop_index('ix_orders_user_mode', table_name='orders')
    op.drop_index('ix_orders_user_status', table_name='orders')
    op.drop_index(op.f('ix_orders_created_at'), table_name='orders')
    op.drop_index(op.f('ix_orders_exchange_order_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_order_type'), table_name='orders')
    op.drop_index(op.f('ix_orders_mode'), table_name='orders')
    op.drop_index(op.f('ix_orders_status'), table_name='orders')
    op.drop_index(op.f('ix_orders_pair'), table_name='orders')
    op.drop_index(op.f('ix_orders_symbol'), table_name='orders')
    op.drop_index(op.f('ix_orders_bot_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_user_id'), table_name='orders')
    op.drop_index(op.f('ix_orders_id'), table_name='orders')
    
    # Drop table
    op.drop_table('orders')

