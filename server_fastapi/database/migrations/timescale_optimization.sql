-- TimescaleDB Optimization Policy (2026 Standards)
-- Based on Research Plan Section 15
-- Target Table: market_ticks

-- 1. Enable Hypertable with 1-week chunks
SELECT create_hypertable(
    'market_ticks',
    'time',
    chunk_time_interval => INTERVAL '1 week',
    if_not_exists => TRUE
);

-- 2. Configure Compression Policy (Delta-Delta for time, Dictionary for symbols)
ALTER TABLE market_ticks SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'symbol,exchange',
    timescaledb.compress_orderby = 'time DESC'
);

-- 3. Add Compression Policy (Compress after 2 weeks)
SELECT add_compression_policy('market_ticks', INTERVAL '2 weeks');

-- 4. Add Retention Policy (10 Years WORM compliance)
SELECT add_retention_policy('market_ticks', INTERVAL '10 years');

-- 5. Space Partitioning (Optional: For high-throughput sharding)
-- SELECT add_dimension('market_ticks', 'symbol', number_partitions => 4);
