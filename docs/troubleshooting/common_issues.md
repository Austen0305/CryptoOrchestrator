# Troubleshooting Common Issues

## Bot Management Issues

### Bot Won't Start

**Problem**: Trading bot fails to start after configuration.

**Symptoms**:
- Bot status shows "Error" in the dashboard
- Console logs show startup failures
- Bot appears stuck in "Starting" state

**Solutions**:

1. **Check Exchange Credentials**
   ```bash
   # Verify API key permissions
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/integrations/exchanges/test
   ```

2. **Validate Bot Configuration**
   ```json
   {
     "required_fields": ["name", "tradingPair", "strategy"],
     "valid_ranges": {
       "riskPerTrade": "0.1-5.0",
       "maxPositionSize": "1-100"
     }
   }
   ```

3. **Check System Resources**
   ```bash
   # Monitor system resources
   top -p $(pgrep -f "python.*bot")
   free -h
   df -h
   ```

4. **Review Logs**
   ```bash
   # Check application logs
   tail -f logs/fastapi.log | grep -i "bot"

   # Check bot-specific logs
   tail -f logs/bot_123.log
   ```

### Bot Stops Unexpectedly

**Problem**: Running bot suddenly stops trading.

**Symptoms**:
- Bot status changes from "Running" to "Stopped"
- No new trades executed
- Error messages in logs

**Solutions**:

1. **Circuit Breaker Activation**
   ```bash
   # Check circuit breaker status
   curl http://localhost:8000/api/health/detailed
   ```
   Look for `circuit_breaker` status in the response.

2. **Risk Limit Breached**
   ```bash
   # Check risk metrics
   curl -H "Authorization: Bearer TOKEN" \
        http://localhost:8000/api/analytics/risk
   ```

3. **Exchange Connectivity**
   ```bash
   # Test exchange connection
   curl http://localhost:8000/api/health/external-apis
   ```

### Bot Performance Issues

**Problem**: Bot is running but performing poorly.

**Symptoms**:
- Lower than expected win rate
- High slippage on orders
- Delayed trade execution

**Diagnostics**:

1. **Check Network Latency**
   ```bash
   # Test API response times
   curl -w "@curl-format.txt" -o /dev/null http://localhost:8000/api/health
   ```

2. **Analyze Trading Patterns**
   ```bash
   # Get recent trades
   curl -H "Authorization: Bearer TOKEN" \
        "http://localhost:8000/api/trades/?botId=BOT_ID&limit=50"
   ```

3. **Review Strategy Parameters**
   ```json
   {
     "optimization_check": {
       "timeframe": "Should match market volatility",
       "indicators": "Verify indicator calculations",
       "thresholds": "Check entry/exit signal thresholds"
     }
   }
   ```

## API Connectivity Issues

### Authentication Failures

**Problem**: API requests return 401 Unauthorized.

**Symptoms**:
- "Invalid token" or "Token expired" errors
- Unable to access protected endpoints
- Session timeout issues

**Solutions**:

1. **Token Refresh**
   ```bash
   # Refresh access token
   curl -X POST http://localhost:8000/api/auth/refresh \
        -H "Content-Type: application/json" \
        -d '{"refreshToken": "YOUR_REFRESH_TOKEN"}'
   ```

2. **Token Validation**
   ```bash
   # Check token validity
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        http://localhost:8000/api/auth/profile
   ```

3. **MFA Issues**
   - Verify MFA code generation
   - Check device time synchronization
   - Regenerate backup codes if needed

### Rate Limiting

**Problem**: API requests return 429 Too Many Requests.

**Symptoms**:
- Requests blocked by rate limiter
- Intermittent API failures
- "Rate limit exceeded" messages

**Solutions**:

1. **Check Rate Limits**
   ```bash
   # Monitor rate limit headers
   curl -I http://localhost:8000/api/markets
   ```
   Look for `X-RateLimit-*` headers.

2. **Implement Request Batching**
   ```javascript
   // Batch API requests
   const batchRequests = async (requests) => {
     const results = [];
     for (const request of requests) {
       const result = await makeRequest(request);
       results.push(result);
       await delay(100); // Add delay between requests
     }
     return results;
   };
   ```

3. **Use WebSocket for Real-time Data**
   ```javascript
   // Switch to WebSocket for market data
   const ws = new WebSocket('ws://localhost:8000/ws/market-data');
   ```

## Market Data Issues

### Delayed or Missing Price Data

**Problem**: Market data appears stale or incomplete.

**Symptoms**:
- Prices don't update in real-time
- Missing data for certain pairs
- WebSocket disconnections

**Solutions**:

1. **Check Exchange Status**
   ```bash
   # Test exchange connectivity
   curl http://localhost:8000/api/health/external-apis
   ```

2. **WebSocket Reconnection**
   ```javascript
   class MarketDataWebSocket {
     constructor() {
       this.connect();
     }

     connect() {
       this.ws = new WebSocket('ws://localhost:8000/ws/market-data');

       this.ws.onopen = () => {
         console.log('Connected to market data');
         this.subscribe();
       };

       this.ws.onclose = () => {
         console.log('Connection lost, reconnecting...');
         setTimeout(() => this.connect(), 5000);
       };

       this.ws.onerror = (error) => {
         console.error('WebSocket error:', error);
       };
     }

     subscribe() {
       this.ws.send(JSON.stringify({
         type: 'subscribe',
         symbols: ['BTC/USD', 'ETH/USD']
       }));
     }
   }
   ```

3. **Data Synchronization**
   ```bash
   # Force data refresh
   curl -X POST http://localhost:8000/api/integrations/exchanges/sync
   ```

### Inaccurate Technical Indicators

**Problem**: Technical indicators show incorrect values.

**Symptoms**:
- RSI readings outside 0-100 range
- MACD calculations don't match other platforms
- Moving averages lag significantly

**Diagnostics**:

1. **Verify Data Source**
   ```bash
   # Check OHLCV data quality
   curl "http://localhost:8000/api/markets/BTC-USD/ohlcv?limit=100"
   ```

2. **Indicator Parameters**
   ```json
   {
     "indicator_validation": {
       "rsi": {"period": 14, "range": "0-100"},
       "macd": {"fast": 12, "slow": 26, "signal": 9},
       "bollinger_bands": {"period": 20, "std_dev": 2}
     }
   }
   ```

## Performance Issues

### High Memory Usage

**Problem**: Application uses excessive system memory.

**Symptoms**:
- System slowdowns
- Out of memory errors
- Application crashes

**Solutions**:

1. **Memory Monitoring**
   ```bash
   # Check memory usage
   ps aux --sort=-%mem | head -10

   # Monitor Python memory
   python -c "import psutil; print(f'Memory usage: {psutil.Process().memory_info().rss / 1024 / 1024:.1f} MB')"
   ```

2. **Memory Optimization**
   ```python
   # Implement memory-efficient data structures
   from collections import deque

   class MemoryEfficientBuffer:
       def __init__(self, max_size=1000):
           self.buffer = deque(maxlen=max_size)

       def add(self, item):
           self.buffer.append(item)

       def get_recent(self, n=100):
           return list(self.buffer)[-n:]
   ```

3. **Garbage Collection Tuning**
   ```python
   import gc

   # Force garbage collection
   gc.collect()

   # Monitor GC stats
   print(gc.get_stats())
   ```

### Slow API Response Times

**Problem**: API endpoints respond slowly.

**Symptoms**:
- Response times > 2 seconds
- Timeout errors
- UI unresponsiveness

**Diagnostics**:

1. **Performance Profiling**
   ```bash
   # Profile API endpoints
   curl -w "@curl-format.txt" -o /dev/null \
        http://localhost:8000/api/analytics/performance
   ```

2. **Database Query Optimization**
   ```sql
   -- Add database indexes
   CREATE INDEX CONCURRENTLY idx_trades_timestamp
   ON trades (timestamp DESC);

   CREATE INDEX CONCURRENTLY idx_trades_bot_id
   ON trades (bot_id, timestamp DESC);
   ```

3. **Caching Implementation**
   ```python
   from functools import lru_cache
   import asyncio
   from typing import Optional

   @lru_cache(maxsize=1000)
   def get_cached_market_data(symbol: str, timeframe: str) -> Optional[dict]:
       # Implement caching logic
       pass
   ```

## Database Issues

### Connection Problems

**Problem**: Database connection failures.

**Symptoms**:
- "Connection refused" errors
- Timeout errors
- Database unavailable messages

**Solutions**:

1. **Connection Pooling**
   ```python
   from sqlalchemy import create_engine
   from sqlalchemy.pool import QueuePool

   engine = create_engine(
       DATABASE_URL,
       poolclass=QueuePool,
       pool_size=10,
       max_overflow=20,
       pool_timeout=30,
       pool_recycle=3600
   )
   ```

2. **Connection Health Checks**
   ```bash
   # Test database connectivity
   curl http://localhost:8000/api/health/database
   ```

3. **Backup and Recovery**
   ```bash
   # Create database backup
   pg_dump -U cryptobot -h localhost cryptoorchestrator > backup.sql

   # Restore from backup
   psql -U cryptobot -h localhost cryptoorchestrator < backup.sql
   ```

### Data Corruption

**Problem**: Database data appears corrupted.

**Symptoms**:
- Inconsistent trade records
- Missing historical data
- Invalid calculations

**Recovery**:

1. **Data Validation**
   ```python
   def validate_trade_data():
       """Validate trade data integrity"""
       trades = get_all_trades()

       for trade in trades:
           if not validate_trade_record(trade):
               log_error(f"Invalid trade record: {trade.id}")
               quarantine_record(trade)
   ```

2. **Integrity Checks**
   ```sql
   -- Check table integrity
   SELECT schemaname, tablename, attname, n_distinct, correlation
   FROM pg_stats
   WHERE schemaname = 'public';

   -- Validate foreign key constraints
   SELECT conname, conrelid::regclass, confrelid::regclass
   FROM pg_constraint
   WHERE contype = 'f';
   ```

## Network and Connectivity Issues

### Firewall Blocking

**Problem**: Firewall blocks application traffic.

**Symptoms**:
- Connection timeouts
- "Network unreachable" errors
- Intermittent connectivity

**Solutions**:

1. **Firewall Configuration**
   ```bash
   # Check firewall status
   sudo ufw status

   # Allow necessary ports
   sudo ufw allow 8000/tcp  # FastAPI
   sudo ufw allow 5432/tcp  # PostgreSQL (if external)
   sudo ufw allow 6379/tcp  # Redis (if external)
   ```

2. **Proxy Configuration**
   ```nginx
   # Nginx proxy configuration
   server {
       listen 80;
       server_name yourdomain.com;

       location /api/ {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### DNS Resolution Issues

**Problem**: DNS resolution failures.

**Symptoms**:
- "Name resolution failure" errors
- Unable to reach external services
- Slow application startup

**Solutions**:

1. **DNS Configuration**
   ```bash
   # Check DNS resolution
   nslookup api.kraken.com

   # Update DNS servers
   echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
   ```

2. **DNS Caching**
   ```python
   import dns.resolver
   import asyncio
   from cachetools import TTLCache

   class DNSCache:
       def __init__(self):
           self.cache = TTLCache(maxsize=1000, ttl=300)  # 5 minute TTL

       async def resolve(self, hostname: str) -> str:
           if hostname in self.cache:
               return self.cache[hostname]

           try:
               answers = dns.resolver.resolve(hostname, 'A')
               ip = str(answers[0])
               self.cache[hostname] = ip
               return ip
           except Exception as e:
               raise DNSResolutionError(f"Failed to resolve {hostname}: {e}")
   ```

## Emergency Procedures

### System Down Emergency

**Immediate Actions**:
1. Stop all trading bots
2. Notify affected users
3. Switch to backup systems
4. Begin root cause analysis

**Recovery Steps**:
1. Assess system damage
2. Restore from backups
3. Validate system integrity
4. Gradually resume operations
5. Communicate with stakeholders

### Data Loss Emergency

**Immediate Actions**:
1. Stop all write operations
2. Assess data loss scope
3. Activate backup restoration
4. Notify compliance team

**Recovery Steps**:
1. Restore from most recent backup
2. Validate data integrity
3. Reconcile transactions
4. Resume normal operations
5. Document incident

---

For additional support, contact our technical support team or visit our community forums. Most issues can be resolved by following these troubleshooting steps.