"""Remove exchanges, add chain_id

Revision ID: e7f8g9h0i1j2
Revises: a1b2c3d4e5f6
Create Date: 2025-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e7f8g9h0i1j2'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Check if tables/columns exist before modifying
    if 'trades' in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("trades")}
        
        # Add chain_id and transaction_hash to trades table
        if 'chain_id' not in existing_columns:
            op.add_column('trades', sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1'))
        if 'transaction_hash' not in existing_columns:
            op.add_column('trades', sa.Column('transaction_hash', sa.String(), nullable=True))
            op.create_index(op.f('ix_trades_transaction_hash'), 'trades', ['transaction_hash'], unique=False)
        
        # Remove exchange column from trades table
        if 'exchange' in existing_columns:
            op.drop_column('trades', 'exchange')
    
    # Update portfolios table
    if 'portfolios' in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("portfolios")}
        if 'chain_id' not in existing_columns:
            op.add_column('portfolios', sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1'))
        if 'exchange' in existing_columns:
            op.drop_column('portfolios', 'exchange')
    
    # Update orders table
    if 'orders' in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("orders")}
        if 'chain_id' not in existing_columns:
            op.add_column('orders', sa.Column('chain_id', sa.Integer(), nullable=False, server_default='1'))
        if 'transaction_hash' not in existing_columns:
            op.add_column('orders', sa.Column('transaction_hash', sa.String(), nullable=True))
            op.create_index(op.f('ix_orders_transaction_hash'), 'orders', ['transaction_hash'], unique=False)
        if 'exchange' in existing_columns:
            op.drop_column('orders', 'exchange')
    
    # Drop exchange_api_keys table (no longer needed)
    if 'exchange_api_keys' in inspector.get_table_names():
        op.drop_table('exchange_api_keys')


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Recreate exchange_api_keys table (simplified structure)
    if 'exchange_api_keys' not in inspector.get_table_names():
        op.create_table('exchange_api_keys',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('exchange', sa.String(), nullable=False),
            sa.Column('api_key', sa.String(), nullable=False),
            sa.Column('api_secret', sa.String(), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
    
    # Add exchange column back to trades, portfolios, orders
    if 'trades' in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("trades")}
        if 'exchange' not in existing_columns:
            op.add_column('trades', sa.Column('exchange', sa.String(), nullable=False, server_default='paper'))
        if 'chain_id' in existing_columns:
            op.drop_column('trades', 'chain_id')
        if 'transaction_hash' in existing_columns:
            op.drop_index(op.f('ix_trades_transaction_hash'), table_name='trades')
            op.drop_column('trades', 'transaction_hash')
    
    if 'portfolios' in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("portfolios")}
        if 'exchange' not in existing_columns:
            op.add_column('portfolios', sa.Column('exchange', sa.String(), nullable=False, server_default='paper'))
        if 'chain_id' in existing_columns:
            op.drop_column('portfolios', 'chain_id')
    
    if 'orders' in inspector.get_table_names():
        existing_columns = {col["name"] for col in inspector.get_columns("orders")}
        if 'exchange' not in existing_columns:
            op.add_column('orders', sa.Column('exchange', sa.String(), nullable=False, server_default='paper'))
        if 'chain_id' in existing_columns:
            op.drop_column('orders', 'chain_id')
        if 'transaction_hash' in existing_columns:
            op.drop_index(op.f('ix_orders_transaction_hash'), table_name='orders')
            op.drop_column('orders', 'transaction_hash')
