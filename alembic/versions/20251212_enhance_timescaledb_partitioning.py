"""enhance_timescaledb_partitioning

Enhance TimescaleDB partitioning for 1B+ rows:
- Add additional hypertables for high-volume tables
- Configure retention policies
- Add compression policies
- Optimize chunk sizes

Revision ID: 20251212_enhance_timescaledb
Revises: 20251212_institutional_wallets
Create Date: 2025-12-12 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251212_enhance_timescaledb'
down_revision = '20251212_institutional_wallets'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    
    # Only run for PostgreSQL databases
    if bind.dialect.name != 'postgresql':
        print("TimescaleDB enhancement skipped (not PostgreSQL)")
        return
    
    # Check if TimescaleDB extension is available (Railway doesn't have it)
    try:
        result = bind.execute(sa.text("""
            SELECT COUNT(*) FROM pg_available_extensions 
            WHERE name = 'timescaledb'
        """))
        if result.scalar() == 0:
            print("⚠️  TimescaleDB extension not available - SKIPPING all enhancements")
            print("    This is normal for Railway/managed PostgreSQL without TimescaleDB")
            print("    Your app will work fine with regular PostgreSQL!")
            return
    except Exception as e:
        print(f"⚠️  Cannot check for TimescaleDB - SKIPPING: {e}")
        return
    
    # Check if TimescaleDB extension is enabled
    result = bind.execute(sa.text("""
        SELECT COUNT(*) FROM pg_extension WHERE extname = 'timescaledb'
    """))
    if result.scalar() == 0:
        print("⚠️  TimescaleDB extension not enabled - SKIPPING enhancements")
        return
    
    # Convert additional high-volume tables to hypertables
    tables_to_convert = [
        ('wallet_transactions', 'created_at'),
        ('institutional_wallet_transactions', 'created_at'),
        ('pending_transactions', 'created_at'),
        ('wallet_access_logs', 'created_at'),
    ]
    
    for table_name, time_column in tables_to_convert:
        # Check if table exists
        result = bind.execute(sa.text(f"""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = '{table_name}'
        """))
        if result.scalar() == 0:
            print(f"Table {table_name} does not exist, skipping")
            continue
        
        # Check if already a hypertable
        result = bind.execute(sa.text(f"""
            SELECT COUNT(*) FROM timescaledb_information.hypertables 
            WHERE hypertable_name = '{table_name}'
        """))
        if result.scalar() == 0:
            try:
                op.execute(sa.text(f"""
                    SELECT create_hypertable('{table_name}', '{time_column}', 
                        if_not_exists => TRUE,
                        chunk_time_interval => INTERVAL '1 day'
                    )
                """))
                print(f"Converted {table_name} to TimescaleDB hypertable")
            except Exception as e:
                print(f"Failed to convert {table_name}: {e}")
        else:
            print(f"{table_name} already a hypertable")
    
    # Configure retention policies (keep data for 1 year)
    retention_tables = ['trades', 'candles', 'wallet_transactions']
    for table_name in retention_tables:
        result = bind.execute(sa.text(f"""
            SELECT COUNT(*) FROM timescaledb_information.hypertables 
            WHERE hypertable_name = '{table_name}'
        """))
        if result.scalar() > 0:
            try:
                # Add retention policy (drop data older than 1 year)
                op.execute(sa.text(f"""
                    SELECT add_retention_policy('{table_name}', INTERVAL '1 year', if_not_exists => TRUE)
                """))
                print(f"Added retention policy for {table_name}")
            except Exception as e:
                print(f"Failed to add retention policy for {table_name}: {e}")
    
    # Configure compression policies (compress data older than 7 days)
    compression_tables = ['trades', 'candles', 'wallet_transactions']
    for table_name in compression_tables:
        result = bind.execute(sa.text(f"""
            SELECT COUNT(*) FROM timescaledb_information.hypertables 
            WHERE hypertable_name = '{table_name}'
        """))
        if result.scalar() > 0:
            try:
                # Enable compression
                op.execute(sa.text(f"""
                    ALTER TABLE {table_name} SET (
                        timescaledb.compress,
                        timescaledb.compress_segmentby = 'id'
                    )
                """))
                
                # Add compression policy
                op.execute(sa.text(f"""
                    SELECT add_compression_policy('{table_name}', INTERVAL '7 days', if_not_exists => TRUE)
                """))
                print(f"Added compression policy for {table_name}")
            except Exception as e:
                print(f"Failed to add compression policy for {table_name}: {e}")
    
    # Optimize chunk sizes for better performance
    # Smaller chunks for high-frequency data, larger for historical
    op.execute(sa.text("""
        SELECT set_chunk_time_interval('trades', INTERVAL '1 day')
        WHERE EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'trades'
        )
    """))
    
    op.execute(sa.text("""
        SELECT set_chunk_time_interval('candles', INTERVAL '7 days')
        WHERE EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables 
            WHERE hypertable_name = 'candles'
        )
    """))


def downgrade() -> None:
    bind = op.get_bind()
    
    if bind.dialect.name != 'postgresql':
        return
    
    # Remove compression policies
    compression_tables = ['trades', 'candles', 'wallet_transactions']
    for table_name in compression_tables:
        try:
            op.execute(sa.text(f"""
                SELECT remove_compression_policy('{table_name}', if_exists => TRUE)
            """))
        except:
            pass
    
    # Remove retention policies
    retention_tables = ['trades', 'candles', 'wallet_transactions']
    for table_name in retention_tables:
        try:
            op.execute(sa.text(f"""
                SELECT remove_retention_policy('{table_name}', if_exists => TRUE)
            """))
        except:
            pass
