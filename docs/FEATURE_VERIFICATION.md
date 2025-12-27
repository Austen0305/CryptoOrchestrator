# CryptoOrchestrator - Feature Verification Guide

Complete guide to verifying all features work correctly.

## Overview

CryptoOrchestrator has 84+ API routes across multiple feature categories. This guide helps you verify all features work perfectly.

## Quick Verification

Run the comprehensive feature verification script:

```bash
npm run setup:verify
# Or:
python scripts/verification/comprehensive_feature_verification.py
```

This will test all major feature categories and generate a report.

## Feature Categories

### 1. Authentication & Authorization

**Endpoints to Test:**
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user
- `POST /api/auth/refresh` - Refresh token
- `POST /api/auth/forgot-password` - Password reset request
- `POST /api/auth/reset-password` - Password reset
- `/api/2fa/*` - Two-factor authentication

**Verification Steps:**
1. Register a new user
2. Login with credentials
3. Verify JWT token is returned
4. Access protected endpoint with token
5. Test logout
6. Test token refresh
7. Test password reset flow
8. Test 2FA setup and verification

### 2. Bot Management

**Endpoints to Test:**
- `GET /api/bots` - List all bots
- `POST /api/bots` - Create bot
- `GET /api/bots/{id}` - Get bot details
- `PATCH /api/bots/{id}` - Update bot
- `DELETE /api/bots/{id}` - Delete bot
- `POST /api/bots/{id}/start` - Start bot
- `POST /api/bots/{id}/stop` - Stop bot
- `/api/bot-learning/*` - Bot learning features

**Verification Steps:**
1. Create a bot with valid configuration
2. List bots and verify created bot appears
3. Get bot details
4. Update bot configuration
5. Start bot execution
6. Verify bot status updates
7. Stop bot execution
8. Delete bot

### 3. Trading Operations

**Endpoints to Test:**
- `GET /api/trades` - List trades
- `POST /api/trades` - Create trade
- `GET /api/trades/{id}` - Get trade details
- `/api/advanced-orders/*` - Advanced order types
- `/api/dca-trading/*` - DCA trading
- `/api/grid-trading/*` - Grid trading
- `/api/infinity-grid/*` - Infinity grid
- `/api/futures-trading/*` - Futures trading
- `/api/copy-trading/*` - Copy trading
- `/api/trailing-bot/*` - Trailing bot
- `/api/sl-tp/*` - Stop-loss/Take-profit

**Verification Steps:**
1. Create a trade (paper mode)
2. Verify trade appears in list
3. Get trade details
4. Test advanced orders (stop-loss, take-profit)
5. Test DCA strategy creation
6. Test grid trading setup
7. Test copy trading functionality

### 4. DEX Trading

**Endpoints to Test:**
- `GET /api/dex-trading/quote` - Get swap quote
- `POST /api/dex-trading/swap` - Execute swap
- `GET /api/dex-trading/swap/{tx_hash}` - Get swap status
- `/api/dex-positions/*` - DEX positions
- `/api/mev-protection/*` - MEV protection
- `/api/transaction-monitoring/*` - Transaction monitoring

**Verification Steps:**
1. Get swap quote for a token pair
2. Verify price impact calculation
3. Execute swap (paper mode or testnet)
4. Monitor transaction status
5. Check DEX positions
6. Verify MEV protection status

### 5. Portfolio Management

**Endpoints to Test:**
- `GET /api/portfolio` - Get portfolio
- `GET /api/portfolio/performance` - Portfolio performance
- `/api/portfolio-rebalance/*` - Portfolio rebalancing
- `/api/analytics/*` - Portfolio analytics

**Verification Steps:**
1. Get portfolio data
2. Verify balance calculations
3. Check portfolio performance metrics
4. Test rebalancing functionality
5. View analytics and charts

### 6. Wallet Management

**Endpoints to Test:**
- `GET /api/wallets` - List wallets
- `POST /api/wallets` - Create wallet
- `GET /api/wallet/{id}` - Get wallet details
- `GET /api/wallet/{id}/balance` - Get balance
- `POST /api/wallet/deposit` - Generate deposit address
- `POST /api/withdrawals` - Create withdrawal
- `/api/crypto-transfer/*` - Crypto transfers

**Verification Steps:**
1. Create wallet on supported chain
2. Verify wallet address generation
3. Check wallet balance
4. Generate deposit address
5. Test withdrawal flow (if configured)
6. Transfer between wallets

### 7. Staking

**Endpoints to Test:**
- `GET /api/staking` - Get staking info
- `POST /api/staking/stake` - Stake tokens
- `POST /api/staking/unstake` - Unstake tokens
- `GET /api/staking/rewards` - Get rewards

**Verification Steps:**
1. Get available staking options
2. Stake tokens
3. Check staking status
4. View rewards
5. Unstake tokens

### 8. Market Data

**Endpoints to Test:**
- `GET /api/markets` - Get markets
- `GET /api/markets/prices` - Get prices
- `/api/price-alerts/*` - Price alerts
- `/api/sentiment/*` - Sentiment analysis

**Verification Steps:**
1. Get market list
2. Fetch price data
3. Create price alert
4. View sentiment analysis

### 9. Strategies & Backtesting

**Endpoints to Test:**
- `GET /api/strategies` - List strategies
- `GET /api/strategies/{id}` - Get strategy
- `POST /api/backtesting-enhanced/run` - Run backtest
- `GET /api/backtesting-enhanced/results` - Get results

**Verification Steps:**
1. List available strategies
2. Get strategy details
3. Run backtest with parameters
4. View backtest results

### 10. Notifications

**Endpoints to Test:**
- `GET /api/notifications` - List notifications
- `PATCH /api/notifications/{id}/read` - Mark as read
- `/api/alerting/*` - Alerting system

**Verification Steps:**
1. View notifications
2. Mark notification as read
3. Create alerts
4. Test notification preferences

### 11. Settings & Preferences

**Endpoints to Test:**
- `GET /api/preferences` - Get preferences
- `PATCH /api/preferences` - Update preferences
- `GET /api/trading-mode` - Get trading mode
- `POST /api/trading-mode/switch` - Switch mode

**Verification Steps:**
1. Get user preferences
2. Update preferences
3. Get current trading mode
4. Switch between paper/real mode

## WebSocket Verification

**Endpoints to Test:**
- `WS /ws` - Main WebSocket connection
- `/api/websocket-portfolio/*` - Portfolio updates
- `/api/websocket-wallet/*` - Wallet updates

**Verification Steps:**
1. Connect to WebSocket
2. Subscribe to portfolio updates
3. Subscribe to wallet updates
4. Verify real-time data updates
5. Test reconnection handling

## E2E Test Execution

Run all E2E tests to verify complete user flows:

```bash
npm run test:e2e:complete
```

This will run:
- Playwright E2E tests (36+ tests)
- Puppeteer critical flow tests
- Generate combined reports

## Manual Testing Checklist

Use the feature checklist for manual verification:

```bash
# View checklist
cat scripts/verification/feature_checklist.md
```

## Verification Reports

After running verification, check reports:

- **Feature Verification**: `feature_verification_report.json`
- **E2E Test Reports**: `test-results/combined-report.html`
- **Health Check**: Console output from `npm run setup:health`

## Troubleshooting

If features fail verification:

1. **Check logs**: `tail -f logs/fastapi.log`
2. **Run diagnostics**: `python scripts/diagnostics/runtime_diagnostics.py --auto-fix`
3. **Verify services**: `npm run check:services`
4. **Check database**: Ensure migrations are applied
5. **Verify environment**: `npm run validate:env`

## Continuous Verification

For ongoing verification:

1. Run feature verification in CI/CD
2. Monitor health checks
3. Run E2E tests regularly
4. Check for breaking changes in API

## Additional Resources

- **Complete Setup Guide**: `docs/COMPLETE_SETUP_GUIDE.md`
- **Troubleshooting Guide**: `docs/TROUBLESHOOTING_RUNTIME.md`
- **API Documentation**: http://localhost:8000/docs
- **Feature Checklist**: `scripts/verification/feature_checklist.md`
