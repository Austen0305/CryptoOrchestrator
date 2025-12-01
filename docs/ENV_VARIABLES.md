# Environment Variables Documentation

Complete documentation of all environment variables used in CryptoOrchestrator.

---

## 📋 Quick Reference

### Required Variables (Production)
- `DATABASE_URL` - Database connection string
- `JWT_SECRET` - Secret key for JWT tokens
- `EXCHANGE_KEY_ENCRYPTION_KEY` - Key for encrypting exchange API keys

### Optional Variables
- `REDIS_URL` - Redis connection string (for caching and rate limiting)
- `SENTRY_DSN` - Sentry error tracking DSN
- Exchange API keys (for real trading)

---

## 🔧 Application Settings

### `NODE_ENV`
- **Type:** String
- **Values:** `development`, `production`, `test`
- **Default:** `development`
- **Description:** Application environment mode
- **Required:** No

### `PORT`
- **Type:** Integer
- **Default:** `8000`
- **Description:** Port number for FastAPI server
- **Required:** No

### `API_BASE_URL`
- **Type:** String (URL)
- **Default:** `http://localhost:8000`
- **Description:** Base URL for API requests
- **Required:** No

### `WS_BASE_URL`
- **Type:** String (WebSocket URL)
- **Default:** `ws://localhost:8000`
- **Description:** Base URL for WebSocket connections
- **Required:** No

---

## 🗄️ Database Configuration

### `DATABASE_URL`
- **Type:** String (Database URL)
- **Format:** `postgresql+asyncpg://user:password@host:port/database` or `sqlite+aiosqlite:///path/to/db.db`
- **Default:** `sqlite+aiosqlite:///./crypto_orchestrator.db`
- **Description:** Database connection string
- **Required:** Yes (for production)
- **Examples:**
  - PostgreSQL: `postgresql+asyncpg://crypto_user:password@localhost:5432/cryptoorchestrator`
  - SQLite: `sqlite+aiosqlite:///./crypto_orchestrator.db`

---

## 🔴 Redis Configuration

### `REDIS_URL`
- **Type:** String (Redis URL)
- **Format:** `redis://host:port/db` or `redis://:password@host:port/db`
- **Default:** `redis://localhost:6379/0`
- **Description:** Redis connection string for caching and rate limiting
- **Required:** No (optional, but recommended for production)
- **Examples:**
  - Local: `redis://localhost:6379/0`
  - With password: `redis://:password@localhost:6379/0`
  - Remote: `redis://redis.example.com:6379/0`

### `REDIS_POOL_SIZE`
- **Type:** Integer
- **Default:** `10`
- **Description:** Redis connection pool size
- **Required:** No

### `REDIS_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable Redis features (caching, rate limiting)
- **Required:** No

---

## 🔒 Authentication & Security

### `JWT_SECRET`
- **Type:** String
- **Min Length:** 32 characters
- **Default:** `your-secret-key-change-in-production`
- **Description:** Secret key for signing JWT tokens
- **Required:** Yes (must be changed in production!)
- **Security:** Use a strong, random secret key in production

### `JWT_ALGORITHM`
- **Type:** String
- **Default:** `HS256`
- **Description:** Algorithm for JWT token signing
- **Required:** No

### `JWT_EXPIRATION_MINUTES`
- **Type:** Integer
- **Default:** `15`
- **Description:** JWT access token expiration time in minutes
- **Required:** No

### `JWT_REFRESH_EXPIRATION_DAYS`
- **Type:** Integer
- **Default:** `7`
- **Description:** JWT refresh token expiration time in days
- **Required:** No

### `EXCHANGE_KEY_ENCRYPTION_KEY`
- **Type:** String
- **Min Length:** 32 characters
- **Default:** `your-encryption-key-change-in-production`
- **Description:** Key for encrypting exchange API keys at rest
- **Required:** Yes (must be changed in production!)
- **Security:** Use a strong, random encryption key

---

## 🌐 CORS Configuration

### `CORS_ORIGINS`
- **Type:** String (comma-separated)
- **Default:** `http://localhost:3000,http://localhost:5173,http://localhost:8000`
- **Description:** Allowed CORS origins
- **Required:** No
- **Examples:**
  - Multiple: `http://localhost:3000,https://app.example.com`
  - All (development only): `*`

### `CORS_ALLOW_CREDENTIALS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Allow credentials in CORS requests
- **Required:** No

---

## ⚡ Rate Limiting

### `RATE_LIMIT_PER_MINUTE`
- **Type:** Integer
- **Default:** `60`
- **Description:** Maximum requests per minute per user
- **Required:** No

### `RATE_LIMIT_BURST`
- **Type:** Integer
- **Default:** `100`
- **Description:** Burst limit for rate limiting
- **Required:** No

### `RATE_LIMIT_ENABLED`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable rate limiting
- **Required:** No

---

## 🚀 Performance Settings

### `PERF_WORKERS`
- **Type:** Integer
- **Default:** `4` (or CPU count)
- **Description:** Number of worker processes
- **Required:** No

### `PERF_MAX_CONNECTIONS`
- **Type:** Integer
- **Default:** `1000`
- **Description:** Maximum concurrent connections
- **Required:** No

### `PERF_DB_POOL_SIZE`
- **Type:** Integer
- **Default:** `20`
- **Description:** Database connection pool size
- **Required:** No

### `PERF_DB_MAX_OVERFLOW`
- **Type:** Integer
- **Default:** `10`
- **Description:** Maximum overflow connections
- **Required:** No

### `PERF_CACHE_TTL`
- **Type:** Integer (seconds)
- **Default:** `300` (5 minutes)
- **Description:** Default cache time-to-live
- **Required:** No

---

## 📊 Logging

### `LOG_LEVEL`
- **Type:** String
- **Values:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`
- **Default:** `INFO`
- **Description:** Logging level
- **Required:** No

### `LOG_FORMAT`
- **Type:** String
- **Values:** `json`, `text`
- **Default:** `json` (production), `text` (development)
- **Description:** Log format
- **Required:** No

### `LOG_FILE`
- **Type:** String (file path)
- **Default:** `logs/fastapi.log`
- **Description:** Log file path
- **Required:** No

---

## 📈 Monitoring & Observability

### `ENABLE_PROMETHEUS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable Prometheus metrics endpoint
- **Required:** No

### `ENABLE_SENTRY`
- **Type:** Boolean
- **Default:** `false` (development), `true` (production)
- **Description:** Enable Sentry error tracking
- **Required:** No

### `SENTRY_DSN`
- **Type:** String (Sentry DSN)
- **Default:** (empty)
- **Description:** Sentry DSN for error tracking
- **Required:** No (but recommended for production)

### `SENTRY_ENVIRONMENT`
- **Type:** String
- **Default:** `development`
- **Description:** Sentry environment name
- **Required:** No

---

## 🔐 Exchange API Keys

### `BINANCE_API_KEY`
- **Type:** String
- **Description:** Binance API key (for real trading)
- **Required:** No

### `BINANCE_API_SECRET`
- **Type:** String
- **Description:** Binance API secret (for real trading)
- **Required:** No

### `KRAKEN_API_KEY`
- **Type:** String
- **Description:** Kraken API key (for real trading)
- **Required:** No

### `KRAKEN_API_SECRET`
- **Type:** String
- **Description:** Kraken API secret (for real trading)
- **Required:** No

### `COINBASE_API_KEY`
- **Type:** String
- **Description:** Coinbase API key (for real trading)
- **Required:** No

### `COINBASE_API_SECRET`
- **Type:** String
- **Description:** Coinbase API secret (for real trading)
- **Required:** No

---

## 💳 Payment Processing

### `STRIPE_PUBLIC_KEY`
- **Type:** String
- **Description:** Stripe public key
- **Required:** No

### `STRIPE_SECRET_KEY`
- **Type:** String
- **Description:** Stripe secret key
- **Required:** No

### `STRIPE_WEBHOOK_SECRET`
- **Type:** String
- **Description:** Stripe webhook secret
- **Required:** No

---

## 📧 Email Configuration

### `SMTP_HOST`
- **Type:** String
- **Default:** `smtp.gmail.com`
- **Description:** SMTP server hostname
- **Required:** No

### `SMTP_PORT`
- **Type:** Integer
- **Default:** `587`
- **Description:** SMTP server port
- **Required:** No

### `SMTP_USER`
- **Type:** String
- **Description:** SMTP username
- **Required:** No

### `SMTP_PASSWORD`
- **Type:** String
- **Description:** SMTP password
- **Required:** No

### `SMTP_FROM_EMAIL`
- **Type:** String (email)
- **Default:** `noreply@cryptoorchestrator.com`
- **Description:** From email address
- **Required:** No

---

## 📱 Mobile App Configuration

### `MOBILE_API_BASE_URL`
- **Type:** String (URL)
- **Default:** `http://localhost:8000`
- **Description:** API base URL for mobile app
- **Required:** No

### `MOBILE_WS_BASE_URL`
- **Type:** String (WebSocket URL)
- **Default:** `ws://localhost:8000`
- **Description:** WebSocket base URL for mobile app
- **Required:** No

---

## 🖥️ Electron Configuration

### `ELECTRON_AUTO_UPDATER_ENABLED`
- **Type:** Boolean
- **Default:** `false`
- **Description:** Enable Electron auto-updater
- **Required:** No

### `ELECTRON_UPDATE_SERVER_URL`
- **Type:** String (URL)
- **Description:** URL for Electron update server
- **Required:** No

---

## 🎛️ Feature Flags

### `ENABLE_ML_PREDICTIONS`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable ML predictions
- **Required:** No

### `ENABLE_ARBITRAGE`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable arbitrage detection
- **Required:** No

### `ENABLE_COPY_TRADING`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable copy trading
- **Required:** No

### `ENABLE_STAKING`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable staking features
- **Required:** No

### `ENABLE_WALLET`
- **Type:** Boolean
- **Default:** `true`
- **Description:** Enable wallet features
- **Required:** No

---

## 🧪 Testing

### `TEST_DATABASE_URL`
- **Type:** String (Database URL)
- **Default:** `sqlite+aiosqlite:///file:pytest_shared?mode=memory&cache=shared`
- **Description:** Test database connection string
- **Required:** No

### `TEST_JWT_SECRET`
- **Type:** String
- **Default:** `test-secret-key-for-testing-only`
- **Description:** JWT secret for testing
- **Required:** No

---

## 🔍 Validation Rules

### Required for Production
1. `DATABASE_URL` - Must be PostgreSQL in production
2. `JWT_SECRET` - Must be at least 32 characters, randomly generated
3. `EXCHANGE_KEY_ENCRYPTION_KEY` - Must be at least 32 characters, randomly generated

### Recommended for Production
1. `REDIS_URL` - For caching and rate limiting
2. `SENTRY_DSN` - For error tracking
3. `STRIPE_SECRET_KEY` - For payment processing
4. Exchange API keys - For real trading

### Security Best Practices
- Never commit `.env` files to version control
- Use strong, randomly generated secrets
- Rotate secrets regularly
- Use different secrets for each environment
- Store production secrets in secure secret management systems

---

## 📝 Example .env Files

### Development
```env
NODE_ENV=development
DATABASE_URL=sqlite+aiosqlite:///./crypto_orchestrator.db
JWT_SECRET=dev-secret-key-minimum-32-characters-long
REDIS_URL=redis://localhost:6379/0
LOG_LEVEL=DEBUG
```

### Production
```env
NODE_ENV=production
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/cryptoorchestrator
JWT_SECRET=<strong-random-32-char-secret>
EXCHANGE_KEY_ENCRYPTION_KEY=<strong-random-32-char-key>
REDIS_URL=redis://redis.example.com:6379/0
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0

