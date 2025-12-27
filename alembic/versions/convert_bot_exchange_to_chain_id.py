"""Convert bot exchange field to chain_id

Revision ID: bot_exchange_to_chain_id_2025
Revises: a1b2c3d4e5f6
Create Date: 2025-12-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'bot_exchange_to_chain_id_2025'
down_revision = 'c8d9e0f1a2b3'  # add_dex_trading_models
branch_labels = None
depends_on = None

# Exchange name to chain_id mapping
EXCHANGE_TO_CHAIN_ID = {
    'ethereum': 1,
    'binance': 56,  # BNB Chain
    'binanceus': 56,
    'kraken': 1,  # Default to Ethereum
    'coinbase': 1,  # Default to Ethereum
    'kucoin': 1,  # Default to Ethereum
    'bybit': 1,  # Default to Ethereum
    '1': 1,  # Already a chain_id
    '8453': 8453,  # Base
    '42161': 42161,  # Arbitrum
    '137': 137,  # Polygon
    '10': 10,  # Optimism
    '43114': 43114,  # Avalanche
    '56': 56,  # BNB Chain
}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Bot tables that need chain_id migration
    bot_tables = ['grid_bots', 'trailing_bots', 'infinity_grids', 'futures_positions', 'dca_bots']
    
    for table_name in bot_tables:
        if table_name not in inspector.get_table_names():
            continue
        
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        
        # Add chain_id column if it doesn't exist
        if 'chain_id' not in existing_columns:
            op.add_column(
                table_name,
                sa.Column('chain_id', sa.Integer(), nullable=True)  # Nullable initially for migration
            )
        
        # Migrate exchange values to chain_id
        # If exchange is already a numeric string (chain_id), use it directly
        # Otherwise, map exchange name to chain_id
        connection = op.get_bind()
        
        # Get all rows with exchange values
        result = connection.execute(text(f"SELECT id, exchange FROM {table_name} WHERE exchange IS NOT NULL"))
        rows = result.fetchall()
        
        for row_id, exchange_value in rows:
            # Try to parse as chain_id first
            chain_id = None
            if exchange_value and str(exchange_value).isdigit():
                chain_id = int(exchange_value)
            elif exchange_value:
                # Map exchange name to chain_id
                exchange_lower = str(exchange_value).lower()
                chain_id = EXCHANGE_TO_CHAIN_ID.get(exchange_lower, 1)  # Default to Ethereum
            
            if chain_id:
                # Update chain_id
                connection.execute(
                    text(f"UPDATE {table_name} SET chain_id = :chain_id WHERE id = :id"),
                    {"chain_id": chain_id, "id": row_id}
                )
        
        # Set default chain_id for any remaining NULL values
        connection.execute(
            text(f"UPDATE {table_name} SET chain_id = 1 WHERE chain_id IS NULL")
        )
        
        # Make chain_id NOT NULL after migration
        op.alter_column(table_name, 'chain_id', nullable=False, server_default='1')
        
        # Keep exchange column for now (deprecated but kept for backward compatibility)
        # In a future migration, we can drop it after ensuring all code uses chain_id


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    bot_tables = ['grid_bots', 'trailing_bots', 'infinity_grids', 'futures_positions', 'dca_bots']
    
    for table_name in bot_tables:
        if table_name not in inspector.get_table_names():
            continue
        
        existing_columns = {col["name"] for col in inspector.get_columns(table_name)}
        
        # Remove chain_id column
        if 'chain_id' in existing_columns:
            op.drop_column(table_name, 'chain_id')
