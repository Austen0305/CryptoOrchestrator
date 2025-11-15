# 🎯 Quick Start Guide - New Features

## Testing the Enhancements

### 1. Run Existing Tests
```powershell
# Run all tests
npm test

# Run specific test file
python -m pytest server_fastapi/tests/test_bots_integration.py -v

# Check coverage
python -m pytest --cov=server_fastapi --cov-report=html
```

### 2. Test Circuit Breakers
```powershell
# Start the server
npm run dev:fastapi

# Check circuit breaker stats (new endpoint)
curl http://localhost:8000/api/circuit-breakers/stats | jq

# Reset a circuit breaker
curl -X POST http://localhost:8000/api/circuit-breakers/exchange_api/reset
```

### 3. Test Rate Limiting
```powershell
# Enable distributed rate limiting
$env:ENABLE_DISTRIBUTED_RATE_LIMIT="true"

# Make rapid requests to test limiting
1..150 | ForEach-Object { curl http://localhost:8000/api/markets/BTC-USD }

# Check rate limit headers
curl -I http://localhost:8000/api/markets/BTC-USD
```

### 4. Test WebSocket Market Data
```javascript
// In browser console or Node.js
const ws = new WebSocket('ws://localhost:8000/api/ws/market-stream');

ws.onopen = () => {
  console.log('Connected!');
  ws.send(JSON.stringify({
    type: 'subscribe',
    channel: 'market:BTC/USDT'
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### 5. Test AI Analysis
```powershell
# Get AI analysis for a bot
curl http://localhost:8000/api/ai-analysis/bot/123 | jq

# Get market sentiment
curl http://localhost:8000/api/ai-analysis/symbol/BTC-USDT/sentiment | jq
```

### 6. Test Cache Management
```powershell
# Get cache info
curl http://localhost:8000/api/cache/info | jq

# Get cache stats
curl http://localhost:8000/api/cache/stats | jq

# Clear specific pattern
curl -X POST http://localhost:8000/api/cache/invalidate/pattern \
  -H "Content-Type: application/json" \
  -d '{"pattern": "market_data:*"}'

# Clear all cache
curl -X POST http://localhost:8000/api/cache/clear
```

### 7. Test Metrics & Monitoring
```powershell
# Get current metrics
curl http://localhost:8000/api/metrics/current | jq

# Get health score
curl http://localhost:8000/api/metrics/health-score | jq

# Get active alerts
curl http://localhost:8000/api/metrics/alerts | jq

# Get alert thresholds
curl http://localhost:8000/api/metrics/alerts/thresholds | jq
```

## Frontend Integration

### Using AI Analysis Component

**In your bot detail page:**
```tsx
import { AITradeAnalysis } from '@/components/AITradeAnalysis';

export function BotDetailPage({ botId }: { botId: string }) {
  return (
    <div className="space-y-6">
      <BotHeader botId={botId} />
      <AITradeAnalysis botId={botId} />
      <BotMetrics botId={botId} />
    </div>
  );
}
```

### Using WebSocket for Real-Time Data

**Create a custom hook:**
```typescript
// hooks/useMarketData.ts
import { useState, useEffect } from 'react';

export function useMarketData(symbol: string) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/api/ws/market-stream`);

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({
        type: 'subscribe',
        channel: `market:${symbol}`
      }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'data') {
        setData(message.data);
      }
    };

    ws.onclose = () => setConnected(false);

    return () => ws.close();
  }, [symbol]);

  return { data, connected };
}
```

## Monitoring Dashboard

### View All System Health
```powershell
# Open Swagger UI
start http://localhost:8000/docs

# Navigate to:
# - Circuit Breakers section
# - Cache Management section  
# - Metrics & Monitoring section
```

### Key Metrics to Watch

**System Health:**
- Overall health score > 80 = healthy
- CPU < 80%
- Memory < 90%
- Cache hit rate > 70%

**Circuit Breakers:**
- All should be in "closed" state
- Health scores > 80

**WebSocket:**
- Active connections tracking
- No idle connections piling up

**Cache:**
- Hit rate > 70%
- No excessive memory usage

## Configuration

### .env Settings
```bash
# Redis (required for advanced features)
REDIS_URL=redis://localhost:6379/0

# Enable distributed rate limiting
ENABLE_DISTRIBUTED_RATE_LIMIT=true

# Application mode
NODE_ENV=production
```

### Redis Setup (Windows)
```powershell
# Using Docker (recommended)
docker run -d --name redis -p 6379:6379 redis:alpine

# Or use Windows Redis
# Download from: https://github.com/microsoftarchive/redis/releases
.\redis-server.exe
```

## Troubleshooting

### Issue: Redis Connection Failed
```powershell
# Check Redis status
redis-cli ping

# Should return: PONG

# If not running, start it:
docker start redis
```

### Issue: WebSocket Not Connecting
```powershell
# Check if port is available
netstat -an | findstr 8000

# Check WebSocket stats
curl http://localhost:8000/api/ws/stats
```

### Issue: High Memory Usage
```powershell
# Check cache size
curl http://localhost:8000/api/cache/info

# Clear cache if needed
curl -X POST http://localhost:8000/api/cache/clear
```

### Issue: Tests Failing
```powershell
# Ensure test database is configured
$env:DATABASE_URL="sqlite:///./test.db"

# Run tests with verbose output
python -m pytest server_fastapi/tests/ -v -s

# Check pytest output for specific failures
```

## Performance Tips

1. **Enable Redis** - 10x performance improvement for cache and rate limiting
2. **Enable Cache Warming** - Proactively refresh hot data
3. **Monitor Circuit Breakers** - Prevent cascade failures
4. **Use WebSocket** - Reduce polling overhead
5. **Watch Metrics** - Identify bottlenecks early

## Security Notes

- Rate limiting is enabled by default (SlowAPI)
- Distributed rate limiting requires Redis
- WebSocket connections are automatically cleaned up
- All endpoints validate input
- Circuit breakers prevent resource exhaustion

## Next Steps

1. ✅ Review the new endpoints in Swagger UI
2. ✅ Test WebSocket connectivity
3. ✅ Enable Redis for production
4. ✅ Configure alerting thresholds
5. ✅ Add AI Analysis component to your UI
6. ✅ Monitor circuit breaker health
7. ✅ Set up automated health checks

---

**All features are production-ready and fully tested!** 🚀
