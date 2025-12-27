# Binance.US Setup Guide for US Users

## Overview

This guide explains how to configure CryptoOrchestrator to use **Binance.US** for users in the United States.

## Important Notes

⚠️ **Binance.US does NOT have a testnet/sandbox environment**

- Unlike Binance.com (international), Binance.US does not offer a testnet
- **Use paper trading mode** for testing and development
- Paper trading mode uses mock data and doesn't require API keys
- Safe for testing without real funds

## Differences from Binance.com

| Feature | Binance.com (International) | Binance.US (United States) |
|---------|----------------------------|---------------------------|
| Testnet Available | ✅ Yes | ❌ No |
| Spot Trading | ✅ Yes | ✅ Yes |
| Futures Trading | ✅ Yes | ❌ No (Spot only) |
| Available Assets | More | Limited (regulatory compliance) |
| API Base URL | `https://api.binance.com` | `https://api.binance.us` |
| Exchange ID in ccxt | `binance` | `binanceus` |

## Setup Instructions

### Step 1: Create Binance.US Account

1. Visit https://www.binance.us
2. Create an account (US residents only)
3. Complete KYC verification if required

### Step 2: Generate API Keys

1. Log in to your Binance.US account
2. Go to **Account** → **API Management**
3. Click **Create API Key**
4. Set appropriate permissions:
   - **Enable Reading** (required for balance/price checks)
   - **Enable Spot & Margin Trading** (if you want to place orders)
   - **Disable Withdrawals** (recommended for security)
5. Save your API key and secret securely

### Step 3: Configure in .env File

Add your Binance.US API keys to your `.env` file:

```env
# Binance.US API Keys (Production)
BINANCEUS_API_KEY=your-api-key-here
BINANCEUS_API_SECRET=your-api-secret-here
BINANCEUS_BASE_URL=https://api.binance.us

# Use paper trading mode for testing (since no testnet)
DEFAULT_TRADING_MODE=paper
ENABLE_MOCK_DATA=true
```

### Step 4: Test Connection

**For Testing (Paper Trading Mode):**
- No API keys needed
- Set `DEFAULT_TRADING_MODE=paper` and `ENABLE_MOCK_DATA=true`
- All trading operations will use mock data
- Safe for testing

**For Production:**
- Set `DEFAULT_TRADING_MODE=real` (or remove the variable)
- Set `ENABLE_MOCK_DATA=false` (or remove the variable)
- Ensure API keys are configured
- Test with small amounts first

## Using Binance.US Service

The application includes a dedicated Binance.US service:

**Service:** `server_fastapi/services/exchange/binanceus_service.py`

**Features:**
- Spot trading only (no futures)
- Automatic connection handling
- Error handling and logging
- Paper trading mode support

**Usage in Code:**
```python
from server_fastapi.services.exchange.binanceus_service import BinanceUSService

# Initialize service
service = BinanceUSService(
    api_key="your-key",
    api_secret="your-secret"
)

# Connect
await service.connect()

# Get price
price = await service.get_market_price("BTC/USD")

# Get balance
balance = await service.get_balance()

# Place order
order = await service.place_order(
    symbol="BTC/USD",
    side="buy",
    order_type="market",
    amount=0.001
)
```

## Paper Trading Mode (Recommended for Testing)

Since Binance.US has no testnet, use paper trading mode:

**Configuration:**
```env
DEFAULT_TRADING_MODE=paper
ENABLE_MOCK_DATA=true
```

**Benefits:**
- No API keys required
- No rate limits
- Safe for testing
- Works offline
- No risk of real trades

**How It Works:**
- All trading operations use mock data
- Prices are simulated
- Orders are simulated
- Balances are simulated
- Perfect for development and testing

## Security Best Practices

1. **Never commit API keys to git**
   - Keep `.env` file in `.gitignore`
   - Use environment variables in production

2. **Use minimal permissions**
   - Enable only what you need
   - Disable withdrawals if possible

3. **Rotate keys regularly**
   - Generate new keys periodically
   - Revoke old keys

4. **Use IP whitelisting** (if available)
   - Restrict API access to specific IPs
   - Reduces risk if keys are compromised

5. **Test with paper trading first**
   - Always test strategies in paper mode
   - Verify everything works before using real funds

## Troubleshooting

### Issue: "Exchange client not available"

**Solution:**
- Check API keys are correct in `.env`
- Verify keys are active in Binance.US account
- Check internet connection
- Use paper trading mode if testing

### Issue: "Invalid API key"

**Solution:**
- Verify API key and secret are correct
- Check for extra spaces or quotes
- Ensure keys are active in Binance.US account
- Regenerate keys if needed

### Issue: "Rate limit exceeded"

**Solution:**
- Binance.US has rate limits
- Use paper trading mode for testing
- Implement request throttling
- Cache price data when possible

### Issue: "Symbol not found"

**Solution:**
- Binance.US has limited trading pairs
- Check available pairs: `await service.get_trading_pairs()`
- Use correct symbol format (e.g., "BTC/USD")
- Some pairs may not be available on Binance.US

## Available Trading Pairs

Binance.US has fewer trading pairs than Binance.com due to regulatory compliance. Common pairs include:

- BTC/USD
- ETH/USD
- ADA/USD
- SOL/USD
- DOT/USD
- And others (check Binance.US website for full list)

## API Rate Limits

Binance.US has rate limits:
- **Weight-based limits** (varies by endpoint)
- **Request rate limits** (requests per second)
- Use paper trading mode to avoid rate limits during testing

## Migration from Binance.com

If you were using Binance.com and need to switch to Binance.US:

1. **Update exchange name:**
   - Change from `binance` to `binanceus`
   - Update API keys in `.env`

2. **Update trading pairs:**
   - Some pairs may not be available
   - Check available pairs on Binance.US

3. **Remove futures trading:**
   - Binance.US only supports spot trading
   - Remove any futures-related code

4. **Test thoroughly:**
   - Use paper trading mode first
   - Verify all features work
   - Test with small amounts

## References

- **Binance.US Website:** https://www.binance.us
- **Binance.US API Docs:** Check Binance.US support for API documentation
- **ccxt Binance.US:** https://docs.ccxt.com/en/latest/manual.html#binanceus
- **Paper Trading Guide:** See [LOCAL_DEVELOPMENT.md](./LOCAL_DEVELOPMENT.md)

---

**Last Updated:** 2025-01-XX  
**Version:** 1.0.0
