"""add_timescaledb_hypertables

Convert trades and candles tables to TimescaleDB hypertables for time-series optimization.
This migration enables TimescaleDB extension and creates hypertables with continuous aggregates.

Revision ID: 20251208_timescaledb
Revises: 20251208_hot_path_indexes
Create Date: 2025-12-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20251208_timescaledb'
down_revision = '20251208_hot_path_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    
    # Only run for PostgreSQL databases
    if bind.dialect.name != 'postgresql':
        print("TimescaleDB migration skipped (not PostgreSQL)")
        return
    
    # Check if TimescaleDB extension is available (Railway doesn't have it)
    try:
        result = bind.execute(sa.text("""
            SELECT COUNT(*) FROM pg_available_extensions 
            WHERE name = 'timescaledb'
        """))
        if result.scalar() == 0:
            print("⚠️  TimescaleDB extension not available - SKIPPING all TimescaleDB features")
            print("    This is normal for Railway/managed PostgreSQL without TimescaleDB")
            print("    Your app will work fine with regular PostgreSQL!")
            return
    except Exception as e:
        print(f"⚠️  Cannot check for TimescaleDB - SKIPPING: {e}")
        return
    
    # Enable TimescaleDB extension (only if available)
    try:
        op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
    except Exception as e:
        print(f"⚠️  TimescaleDB extension not available - SKIPPING: {e}")
        return
    
    # Convert trades table to hypertable (using created_at as time column)
    # Check if hypertable already exists
    result = bind.execute(sa.text("""
        SELECT COUNT(*) FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'trades'
    """))
    if result.scalar() == 0:
        op.execute(sa.text("""
            SELECT create_hypertable('trades', 'created_at', if_not_exists => TRUE)
        """))
        print("Converted trades table to TimescaleDB hypertable")
    else:
        print("Trades table already a hypertable")
    
    # Convert candles table to hypertable (using ts as time column, but need to convert to timestamp)
    # First check if we need to add a timestamp column or use existing
    result = bind.execute(sa.text("""
        SELECT COUNT(*) FROM timescaledb_information.hypertables 
        WHERE hypertable_name = 'candles'
    """))
    if result.scalar() == 0:
        # Check if timestamp column exists (for TimescaleDB, we need a timestamp)
        # Since candles uses ts (epoch ms), we'll create a generated column or use created_at
        # For now, use created_at if it exists, otherwise create a computed column
        try:
            # Try to use created_at if it exists
            op.execute(sa.text("""
                SELECT create_hypertable('candles', 'created_at', if_not_exists => TRUE)
            """))
        except Exception:
            # If created_at doesn't work, create a timestamp column from ts
            op.execute(sa.text("""
                ALTER TABLE candles 
                ADD COLUMN IF NOT EXISTS ts_timestamp TIMESTAMP 
                GENERATED ALWAYS AS (to_timestamp(ts / 1000.0)) STORED
            """))
            op.execute(sa.text("""
                SELECT create_hypertable('candles', 'ts_timestamp', if_not_exists => TRUE)
            """))
        print("Converted candles table to TimescaleDB hypertable")
    else:
        print("Candles table already a hypertable")
    
    # Create continuous aggregate for hourly trade stats
    # Check if materialized view already exists
    result = bind.execute(sa.text("""
        SELECT COUNT(*) FROM pg_matviews 
        WHERE matviewname = 'hourly_trade_stats'
    """))
    if result.scalar() == 0:
        op.execute(sa.text("""
            CREATE MATERIALIZED VIEW IF NOT EXISTS hourly_trade_stats
            WITH (timescaledb.continuous) AS
            SELECT
                time_bucket('1 hour', created_at) AS bucket,
                user_id,
                COUNT(*) AS trade_count,
                SUM(amount * price) AS total_volume,
                AVG(price) AS avg_price,
                SUM(pnl) AS total_pnl,
                COUNT(CASE WHEN pnl > 0 THEN 1 END) AS winning_trades,
                COUNT(CASE WHEN pnl < 0 THEN 1 END) AS losing_trades
            FROM trades
            GROUP BY bucket, user_id
        """))
        
        # Add refresh policy (refresh every hour)
        op.execute(sa.text("""
            SELECT add_continuous_aggregate_policy('hourly_trade_stats',
                start_offset => INTERVAL '3 hours',
                end_offset => INTERVAL '1 hour',
                schedule_interval => INTERVAL '1 hour',
                if_not_exists => TRUE)
        """))
        print("Created hourly_trade_stats continuous aggregate")
    else:
        print("hourly_trade_stats continuous aggregate already exists")
    
    # Create continuous aggregate for daily candle stats (optional)
    result = bind.execute(sa.text("""
        SELECT COUNT(*) FROM pg_matviews 
        WHERE matviewname = 'daily_candle_stats'
    """))
    if result.scalar() == 0:
        # Use created_at or ts_timestamp depending on what was used for hypertable
        try:
            op.execute(sa.text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS daily_candle_stats
                WITH (timescaledb.continuous) AS
                SELECT
                    time_bucket('1 day', created_at) AS bucket,
                    symbol,
                    timeframe,
                    COUNT(*) AS candle_count,
                    AVG(volume) AS avg_volume,
                    MAX(high) AS max_high,
                    MIN(low) AS min_low,
                    AVG((high + low + close) / 3.0) AS avg_price
                FROM candles
                GROUP BY bucket, symbol, timeframe
            """))
            
            # Add refresh policy (refresh daily)
            op.execute(sa.text("""
                SELECT add_continuous_aggregate_policy('daily_candle_stats',
                    start_offset => INTERVAL '2 days',
                    end_offset => INTERVAL '1 day',
                    schedule_interval => INTERVAL '1 day',
                    if_not_exists => TRUE)
            """))
            print("Created daily_candle_stats continuous aggregate")
        except Exception as e:
            print(f"Could not create daily_candle_stats: {e}")


def downgrade() -> None:
    bind = op.get_bind()
    
    # Only run for PostgreSQL databases
    if bind.dialect.name != 'postgresql':
        return
    
    # Drop continuous aggregates
    try:
        op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS daily_candle_stats CASCADE"))
    except Exception:
        pass
    
    try:
        op.execute(sa.text("DROP MATERIALIZED VIEW IF EXISTS hourly_trade_stats CASCADE"))
    except Exception:
        pass
    
    # Convert hypertables back to regular tables
    # Note: This is a destructive operation and may require data migration
    try:
        op.execute(sa.text("SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'candles'"))
        # Drop hypertable (this doesn't delete data, just removes TimescaleDB metadata)
        op.execute(sa.text("SELECT drop_hypertable('candles', if_exists => TRUE)"))
    except Exception:
        pass
    
    try:
        op.execute(sa.text("SELECT * FROM timescaledb_information.hypertables WHERE hypertable_name = 'trades'"))
        op.execute(sa.text("SELECT drop_hypertable('trades', if_exists => TRUE)"))
    except Exception:
        pass
    
    # Note: We don't drop the TimescaleDB extension as it might be used by other tables



