# CryptoOrchestrator - Runtime Troubleshooting Guide

Common runtime issues and solutions.

## Quick Diagnostics

Run automated diagnostics:

```bash
python scripts/diagnostics/runtime_diagnostics.py --auto-fix
```

This will identify and attempt to fix common issues automatically.

## Common Issues

### Environment Issues

**Problem**: Missing .env file

**Symptoms:**
- `DATABASE_URL is required` error
- `JWT_SECRET is required` error
- Application won't start

**Solution:**
```bash
python scripts/setup/create_env_file.py
```

**Problem**: Weak or default secrets in production

**Symptoms:**
- Validation errors on startup
- Security warnings

**Solution:**
```bash
# Generate secure secrets
python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(64))"
python -c "import secrets; print('EXCHANGE_KEY_ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
```

### Database Issues

**Problem**: Database connection failed

**Symptoms:**
- `Could not connect to database` error
- `Connection refused` error
- Timeout errors

**Solutions:**

1. **Check DATABASE_URL in .env**:
   ```bash
   # SQLite (development)
   DATABASE_URL=sqlite+aiosqlite:///./data/app.db
   
   # PostgreSQL
   DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/dbname
   ```

2. **Verify database is running**:
   ```bash
   # PostgreSQL
   pg_isready -h localhost -p 5432
   
   # SQLite (file should exist)
   ls -la data/app.db
   ```

3. **Check database permissions**

**Problem**: Migrations not applied

**Symptoms:**
- `Table does not exist` errors
- `Column does not exist` errors

**Solution:**
```bash
# Run migrations
alembic upgrade head

# Or use setup script
python scripts/setup/init_database.py
```

**Problem**: Migration conflicts

**Symptoms:**
- `Multiple heads detected` error
- Migration downgrade issues

**Solution:**
```bash
# Check migration status
alembic current
alembic heads

# Resolve conflicts (see Alembic docs)
alembic merge -m "merge heads" heads
alembic upgrade head
```

### Dependency Issues

**Problem**: Import errors

**Symptoms:**
- `ModuleNotFoundError`
- `ImportError`

**Solution:**
```bash
# Verify dependencies
python scripts/setup/verify_dependencies.py

# Reinstall if needed
pip install -r requirements.txt
npm install --legacy-peer-deps
```

**Problem**: Python version incompatibility

**Symptoms:**
- `SyntaxError` (if using Python < 3.11)
- TensorFlow errors (if using Python 3.13)

**Solution:**
- Use Python 3.11 or 3.12 (recommended)
- Python 3.13 has TensorFlow compatibility issues

**Problem**: Node.js version incompatibility

**Symptoms:**
- Build errors
- Module resolution errors

**Solution:**
- Use Node.js 18+ (LTS recommended)

### Service Startup Issues

**Problem**: Port already in use

**Symptoms:**
- `Address already in use` error
- `Port 8000 is already in use`

**Solution:**
```bash
# Find what's using the port (Windows)
netstat -ano | findstr :8000

# Find what's using the port (Unix)
lsof -i :8000

# Kill process or change port in .env
PORT=8001  # Change port
```

**Problem**: Backend won't start

**Symptoms:**
- FastAPI startup errors
- Import errors on startup

**Solutions:**

1. **Check logs**: Look for error messages in console
2. **Verify environment**: `python scripts/testing/validate_env_vars.py`
3. **Check database**: Ensure database is accessible
4. **Check dependencies**: `python scripts/setup/verify_dependencies.py`

**Problem**: Frontend won't start

**Symptoms:**
- Vite startup errors
- Port conflicts

**Solutions:**

1. **Clear cache**: `rm -rf node_modules/.vite`
2. **Reinstall dependencies**: `npm install --legacy-peer-deps`
3. **Check port**: Change port in `vite.config.ts` if needed

### API Endpoint Issues

**Problem**: 401 Unauthorized errors

**Symptoms:**
- All API calls return 401
- `Invalid token` errors

**Solutions:**

1. **Login to get new token**: `POST /api/auth/login`
2. **Check token expiration**: Tokens expire after 24 hours
3. **Verify JWT_SECRET**: Must match between requests

**Problem**: 404 Not Found errors

**Symptoms:**
- Endpoint not found
- Route not registered

**Solutions:**

1. **Check route exists**: Verify in `server_fastapi/main.py`
2. **Check prefix**: Ensure correct API prefix (`/api/...`)
3. **Check HTTP method**: Use correct method (GET, POST, etc.)

**Problem**: 422 Validation errors

**Symptoms:**
- Request validation failed
- Missing required fields

**Solutions:**

1. **Check request format**: See API docs at `/docs`
2. **Verify required fields**: Check request model
3. **Check data types**: Ensure correct types (string, number, etc.)

### WebSocket Issues

**Problem**: WebSocket connection fails

**Symptoms:**
- `WebSocket connection failed`
- Connection timeout

**Solutions:**

1. **Check WebSocket URL**: Use `ws://localhost:8000/ws` (not `http://`)
2. **Verify backend is running**: Check health endpoint
3. **Check CORS**: Verify ALLOWED_ORIGINS includes your frontend URL

**Problem**: WebSocket disconnects frequently

**Symptoms:**
- Frequent reconnections
- Connection drops

**Solutions:**

1. **Check ping/pong interval**: Configure in `.env` (`WS_PING_INTERVAL`)
2. **Verify network stability**
3. **Check backend logs**: Look for WebSocket errors

### Performance Issues

**Problem**: Slow API responses

**Symptoms:**
- High response times
- Timeout errors

**Solutions:**

1. **Enable Redis caching**: Set `REDIS_URL` in `.env`
2. **Check database queries**: Use eager loading to prevent N+1 queries
3. **Enable connection pooling**: Already configured, verify pool size
4. **Check external API calls**: DEX aggregators, blockchain RPC may be slow

**Problem**: High memory usage

**Symptoms:**
- Memory leaks
- Out of memory errors

**Solutions:**

1. **Check for connection leaks**: Ensure database sessions are closed
2. **Limit cache size**: Configure `CACHE_MAX_SIZE`
3. **Check background tasks**: Ensure Celery tasks complete

### Blockchain/DEX Issues

**Problem**: DEX trading not working

**Symptoms:**
- No quotes returned
- Swap execution fails

**Solutions:**

1. **Check RPC URLs**: Ensure blockchain RPC URLs are configured
2. **Check API keys**: Verify DEX aggregator API keys (optional)
3. **Check network**: Ensure RPC endpoints are accessible
4. **Verify feature flag**: `ENABLE_DEX_TRADING=true`

**Problem**: Blockchain RPC errors

**Symptoms:**
- `RPC connection failed`
- Timeout errors

**Solutions:**

1. **Use multiple RPC providers**: Configure fallback RPCs
2. **Check RPC rate limits**: Some public RPCs have limits
3. **Verify network connectivity**: Test RPC URLs directly
4. **Use private RPC**: Consider Alchemy, Infura, or QuickNode

## Diagnostic Commands

**Check system status:**
```bash
# Health check
python scripts/setup/health_check.py

# Service status
npm run check:services

# Runtime diagnostics
python scripts/diagnostics/runtime_diagnostics.py
```

**Check logs:**
```bash
# Backend logs
tail -f logs/fastapi.log

# Check for errors
grep -i error logs/fastapi.log

# Check recent errors
tail -100 logs/fastapi.log | grep -i error
```

**Database checks:**
```bash
# Check connection
python -c "from server_fastapi.database import get_async_session; import asyncio; asyncio.run(get_async_session().__aenter__())"

# Check migrations
alembic current
alembic heads

# Verify tables
python -c "from server_fastapi.database import get_async_session; from sqlalchemy import text; import asyncio; asyncio.run((lambda: get_async_session().__aenter__())().execute(text('SELECT name FROM sqlite_master WHERE type=\"table\"')))"
```

## Getting Help

If issues persist:

1. **Run full diagnostics**: `python scripts/diagnostics/runtime_diagnostics.py --auto-fix`
2. **Check logs**: Review error logs for specific error messages
3. **Verify setup**: Re-run `npm run setup` to ensure everything is configured
4. **Check GitHub issues**: Look for similar issues in repository
5. **Review documentation**: See other docs in `docs/` directory

## Prevention

To prevent runtime issues:

1. **Use automated setup**: `npm run setup`
2. **Run diagnostics regularly**: `python scripts/diagnostics/runtime_diagnostics.py`
3. **Monitor health checks**: `npm run setup:health`
4. **Keep dependencies updated**: `npm update` and `pip install --upgrade -r requirements.txt`
5. **Test migrations**: Always test migrations in development first
6. **Use environment validation**: `npm run validate:env`

## Additional Resources

- **Complete Setup Guide**: `docs/COMPLETE_SETUP_GUIDE.md`
- **Feature Verification**: `docs/FEATURE_VERIFICATION.md`
- **API Documentation**: http://localhost:8000/docs
- **Environment Setup**: `docs/ENVIRONMENT_SETUP.md`
