# API Keys & Environment Variables Setup Guide

Complete guide for obtaining and configuring all required API keys and environment variables for CryptoOrchestrator.

**Last Updated:** December 5, 2025

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Required API Keys](#required-api-keys)
3. [Optional API Keys](#optional-api-keys)
4. [Infrastructure Services](#infrastructure-services)
5. [Security Secrets](#security-secrets)
6. [Step-by-Step Setup](#step-by-step-setup)
7. [Validation & Testing](#validation--testing)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

**Minimum Required for Development:**
- `DATABASE_URL` (SQLite works for local dev)
- `JWT_SECRET` (generate a random secret)
- `EXCHANGE_KEY_ENCRYPTION_KEY` (generate a 32-byte key)

**Minimum Required for Production:**
- All items above, plus:
- `DATABASE_URL` (PostgreSQL - Neon recommended)
- `REDIS_URL` (Upstash Redis recommended)
- `STRIPE_SECRET_KEY` & `STRIPE_PUBLISHABLE_KEY` (for payments)
- `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` (for SMS)

**For DEX Trading (Recommended - No Exchange API Keys Needed):**
- `ZEROX_API_KEY` (recommended - free tier available)
- `VITE_WALLETCONNECT_PROJECT_ID` (optional but recommended for wallet connections)
- See [DEX Trading API Keys](#dex-trading-api-keys-alternative-to-exchange-api-keys) section below

---

## Required API Keys

### 1. Exchange API Keys (Optional - For Centralized Exchange Trading)

> **Note:** Exchange API keys are **OPTIONAL** if you're using DEX trading. The platform now supports trading directly on blockchain networks via DEX aggregators without requiring exchange API keys. See [DEX Trading API Keys](#dex-trading-api-keys-new---for-dex-trading-feature) below for DEX trading setup.

**Binance.US API Keys** (Optional - Only needed for centralized exchange trading)

1. Go to https://www.binance.us/en/my/settings/api-management
2. Log in to your Binance.US account
3. Click **"Create API"**
4. Choose **"System generated"** (recommended)
5. Set API restrictions:
   - **Enable Reading**: ✅ (required)
   - **Enable Spot & Margin Trading**: ✅ (for trading)
   - **Enable Withdrawals**: ❌ (recommended: disable for security)
6. Complete security verification (2FA, email confirmation)
7. **Save your API Key and Secret Key immediately** - the secret is only shown once!
8. Store securely - these will be encrypted in the database

**Security Best Practices:**
- Use IP whitelisting if available
- Set minimum required permissions
- Never share your API keys
- Rotate keys periodically
- Use separate keys for paper vs real trading

**Optional Exchange APIs:**
- **Kraken**: https://www.kraken.com/u/security/api
- **Coinbase**: https://www.coinbase.com/settings/api
- **KuCoin**: https://www.kucoin.com/account/api
- **Bybit**: https://www.bybit.com/app/user/api-management

---

### 2. RPC Provider API Keys (Required for Blockchain Features)

**RPC Provider Setup** (Alchemy, Infura, or QuickNode)

For blockchain features (DEX trading, deposits, withdrawals), you need an RPC provider API key.

**Option A: Alchemy (Recommended)**

1. Go to https://www.alchemy.com/
2. Sign up for a free account
3. Create a new app for each blockchain you want to support:
   - Ethereum Mainnet
   - Base Mainnet
   - Arbitrum One
   - Polygon Mainnet
   - Optimism Mainnet
   - Avalanche Mainnet
   - BNB Chain
4. Copy the API key from each app
5. Add to `.env`:
   ```env
   RPC_PROVIDER_TYPE=alchemy
   RPC_API_KEY=your-alchemy-api-key
   ```

**Option B: Infura**

1. Go to https://infura.io/
2. Sign up for a free account
3. Create a new project
4. Copy the API key
5. Add to `.env`:
   ```env
   RPC_PROVIDER_TYPE=infura
   RPC_API_KEY=your-infura-api-key
   ```

**Option C: Chain-Specific RPC URLs**

You can also set individual RPC URLs for each chain:
```env
ETHEREUM_RPC_URL=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
BASE_RPC_URL=https://base-mainnet.g.alchemy.com/v2/YOUR_KEY
ARBITRUM_RPC_URL=https://arb-mainnet.g.alchemy.com/v2/YOUR_KEY
POLYGON_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY
OPTIMISM_RPC_URL=https://opt-mainnet.g.alchemy.com/v2/YOUR_KEY
AVALANCHE_RPC_URL=https://api.avax.network/ext/bc/C/rpc
BNB_CHAIN_RPC_URL=https://bsc-dataseed.binance.org
```

**For Development:**
- You can use public RPCs (no API key needed) by setting `RPC_PROVIDER_TYPE=public`
- Note: Public RPCs have rate limits and lower reliability

**See `docs/BLOCKCHAIN_INTEGRATION.md` for complete RPC setup guide.**

---

### 3. Stripe API Keys (Required for Payments)

**Stripe Secret Key & Publishable Key**

1. Go to https://dashboard.stripe.com/register
2. Create a Stripe account (or log in)
3. Go to **Developers** → **API keys**
4. Copy your **Publishable key** (starts with `pk_`)
5. Click **"Reveal test key"** or **"Reveal live key"** to get your **Secret key** (starts with `sk_`)
6. For development, use **Test mode keys** (toggle in top right)
7. For production, use **Live mode keys**

**Stripe Webhook Secret** (Required for webhook verification)

1. Go to **Developers** → **Webhooks**
2. Click **"Add endpoint"**
3. Enter your webhook URL: `https://your-backend-url.com/api/webhooks/stripe`
4. Select events to listen to:
   - `checkout.session.completed`
   - `customer.subscription.created`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.payment_succeeded`
   - `invoice.payment_failed`
5. Click **"Add endpoint"**
6. Click on the endpoint to reveal the **Signing secret** (starts with `whsec_`)

**Environment Variables:**
```env
STRIPE_SECRET_KEY=sk_test_...  # or sk_live_... for production
STRIPE_PUBLISHABLE_KEY=pk_test_...  # or pk_live_... for production
STRIPE_WEBHOOK_SECRET=whsec_...  # Webhook signing secret
```

---

### 3. Twilio API Keys (Required for SMS Notifications)

**Twilio Account SID, Auth Token, and Phone Number**

1. Go to https://www.twilio.com/try-twilio
2. Sign up for a free account (includes $15.50 credit)
3. Verify your phone number
4. Go to **Console** → **Account** → **API keys & tokens**
5. Copy your **Account SID** (starts with `AC`)
6. Copy your **Auth Token** (click "View" to reveal)
7. Go to **Phone Numbers** → **Manage** → **Buy a number**
8. Purchase a phone number (or use the trial number for testing)
9. Copy your **Phone Number** (format: +1234567890)

**Environment Variables:**
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_NUMBER=+1234567890  # Your Twilio phone number
```

**Free Tier Limits:**
- $15.50 credit included
- SMS: ~$0.0075 per message
- ~2,000 SMS messages on free credit

---

## DEX Trading API Keys (Alternative to Exchange API Keys)

> **New Feature:** DEX trading allows you to trade cryptocurrencies directly on blockchain networks without needing exchange API keys. This is the recommended approach for most users as it offers lower fees, better privacy, and no need to connect exchange accounts.

### 1. 0x Swap API Key (Recommended)

**Why:** Largest DEX aggregator (150+ liquidity sources), supports affiliate fees and trade surplus.

1. Go to https://0x.org/
2. Sign up for an account
3. Navigate to API Dashboard
4. Create a new API key
5. Copy the API key

**Environment Variable:**
```env
ZEROX_API_KEY=your-0x-api-key
ZEROX_AFFILIATE_FEE_BPS=0  # 0-1000 (0-10% commission, set to 0 if not using affiliate fees)
```

**Note:** Free tier available. Custom pricing for high volume. Affiliate fees are optional but can generate additional revenue.

### 2. OKX DEX Aggregator API (Optional - Alternative to 0x)

**Why:** 500+ DEXs across 20+ blockchains, competitive rates, good fallback option.

1. Go to https://www.okx.com/
2. Sign up for an account
3. Navigate to API Management
4. Create API credentials (API Key, Secret Key, Passphrase)
5. Copy all three values

**Environment Variables:**
```env
OKX_API_KEY=your-okx-api-key
OKX_SECRET_KEY=your-okx-secret-key
OKX_PASSPHRASE=your-okx-passphrase
```

**Note:** OKX DEX aggregator is used as a fallback if 0x fails or for better rates on specific chains.

### 3. Rubic Cross-Chain API (Optional - For Cross-Chain Swaps)

**Why:** Cross-chain swaps across 100+ blockchains, 360+ DEXs aggregated.

1. Go to https://rubic.exchange/
2. Sign up for an account
3. Navigate to API section
4. Create API key
5. Copy the API key

**Environment Variable:**
```env
RUBIC_API_KEY=your-rubic-api-key
```

**Note:** Required only if you want to support cross-chain swaps. Same-chain swaps work without it.

### 4. WalletConnect Project ID (Optional - For WalletConnect Support)

**Why:** Enables connection to 300+ wallets via WalletConnect protocol.

1. Go to https://cloud.walletconnect.com/
2. Sign up for a free account
3. Create a new project
4. Copy the Project ID

**Environment Variable (Frontend):**
```env
VITE_WALLETCONNECT_PROJECT_ID=your-walletconnect-project-id
```

**Note:** Optional but recommended. Without it, WalletConnect connector won't work, but MetaMask and other injected wallets will still function.

### 5. Platform Wallet Addresses (For Affiliate Fees & Trade Surplus)

**Why:** Platform wallet addresses to receive affiliate fees from DEX aggregators and trade surplus.

**Environment Variables:**
```env
AFFILIATE_FEE_RECIPIENT=0x...  # Platform wallet address for receiving affiliate fees from 0x
TRADE_SURPLUS_RECIPIENT=0x...  # Platform wallet address for receiving trade surplus from 0x
```

**Note:** These are Ethereum addresses (0x format). Create dedicated wallets for receiving fees. Only needed if using 0x affiliate fees or trade surplus features.

### 6. Trading Fee Configuration

**Environment Variables:**
```env
PLATFORM_TRADING_FEE_BPS=20  # 0.2% default platform trading fee (20 basis points)
CUSTODIAL_FEE_BPS=20  # 0.2% fee for custodial trades
NON_CUSTODIAL_FEE_BPS=15  # 0.15% fee for non-custodial trades (lower, users maintain control)
```

**Note:** Fees are in basis points (1 basis point = 0.01%). Default values are already set in `server_fastapi/config/settings.py`.

## Optional API Keys

### 4. Market Data (Free Tier)

**MarketDataService** uses CoinCap (primary) and CoinLore (fallback), which are free and do not require API keys.

1.  **CoinCap**: 200 requests/min (Free)
2.  **CoinLore**: Free public API

No configuration is needed in `.env` for these providers.


---

### 5. Sentry DSN (Optional - For Error Tracking)

**Sentry** provides error tracking and monitoring.

1. Go to https://sentry.io/signup/
2. Create a free account
3. Create a new project:
   - **Platform**: Python
   - **Framework**: FastAPI
4. Copy your **DSN** (looks like: `https://xxx@xxx.ingest.sentry.io/xxx`)

**Environment Variables:**
```env
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
ENABLE_SENTRY=true
```

**Free Tier:**
- 5,000 events/month
- 1 project
- 30-day retention

---

### 6. hCaptcha Keys (Optional - For Bot Protection)

**hCaptcha** provides bot protection for forms.

1. Go to https://www.hcaptcha.com/
2. Sign up for a free account
3. Go to **Sites** → **Add New Site**
4. Enter your site details:
   - **Label**: CryptoOrchestrator
   - **Domains**: your-domain.com, www.your-domain.com
5. Select **hCaptcha** (free tier)
6. Copy your **Site Key** (starts with `10000000-`)
7. Copy your **Secret Key** (starts with `0x`)

**Environment Variables:**
```env
HCAPTCHA_SITE_KEY=10000000-ffff-ffff-ffff-000000000001
HCAPTCHA_SECRET_KEY=0x0000000000000000000000000000000000000000
```

**Free Tier:**
- 100,000 requests/month
- No credit card required

---

## Infrastructure Services

### 7. Neon PostgreSQL (Required for Production Database)

**Neon** provides serverless PostgreSQL with a generous free tier.

1. Go to https://neon.tech
2. Sign up with GitHub (recommended) or email
3. Create a new project: **crypto-orchestrator**
4. Choose a region closest to your users
5. After creating, copy your **Connection String**
   - Format: `postgresql://user:password@ep-xxx-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require`
6. **Enable Connection Pooling** (recommended):
   - Look for "Connection pooling" toggle
   - Pooled connection strings have `-pooler` in hostname
   - Format: `postgresql://user:password@ep-xxx-xxx-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require`

**Convert for Async SQLAlchemy:**
Replace `postgresql://` with `postgresql+asyncpg://`:
```
postgresql+asyncpg://user:password@ep-xxx-xxx-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Environment Variables:**
```env
DATABASE_URL=postgresql+asyncpg://user:password@ep-xxx-xxx-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require
```

**Free Tier:**
- 0.5 GB storage per project
- 20 projects
- Connection pooling included
- Automatic backups

**See:** `docs/FREE_STACK_DEPLOYMENT_GUIDE.md` for detailed setup instructions.

---

### 8. Upstash Redis (Required for Caching/Sessions)

**Upstash** provides serverless Redis with 500K commands/month free.

1. Go to https://upstash.com
2. Sign up with GitHub or email
3. Create a new database: **crypto-orchestrator-cache**
4. Choose **Global** region (or closest to your backend)
5. Select **Regional** database type (free tier)
6. After creating, copy your **Redis URL**
   - Format: `redis://default:password@redis-xxx-xxx.upstash.io:6379`

**Environment Variables:**
```env
REDIS_URL=redis://default:password@redis-xxx-xxx.upstash.io:6379
```

**Free Tier:**
- 500,000 commands/month
- 256 MB storage
- Global edge locations

**See:** `docs/FREE_STACK_DEPLOYMENT_GUIDE.md` for detailed setup instructions.

---

## Security Secrets

### 9. JWT Secret (Required)

**Generate a strong random secret for JWT token signing.**

**Option 1: Using Python**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Option 2: Using OpenSSL**
```bash
openssl rand -base64 32
```

**Option 3: Using Online Generator**
- Go to https://www.lastpass.com/features/password-generator
- Generate a 32+ character random string

**Environment Variables:**
```env
JWT_SECRET=your-super-secret-jwt-key-here-min-32-chars
JWT_REFRESH_SECRET=your-refresh-secret-here-min-32-chars  # Different from JWT_SECRET
JWT_EXPIRATION_HOURS=24  # Optional, default is 24
```

**Security Requirements:**
- Minimum 32 characters
- Use cryptographically secure random generator
- Never commit to git
- Use different secrets for development and production
- Rotate periodically

---

### 10. Exchange Key Encryption Key (Required)

**Generate a 32-byte key for encrypting exchange API keys in the database.**

**Using Python:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Using OpenSSL:**
```bash
openssl rand -base64 32
```

**Environment Variables:**
```env
EXCHANGE_KEY_ENCRYPTION_KEY=your-encryption-key-here-32-chars-exactly
```

**Security Requirements:**
- Exactly 32 bytes (44 characters in base64)
- Use cryptographically secure random generator
- Never commit to git
- Use different keys for development and production
- **Critical:** If you lose this key, you cannot decrypt stored exchange keys

---

## Step-by-Step Setup

### Development Setup

1. **Create `.env` file** in project root:
   ```bash
   cp .env.example .env
   ```

2. **Generate security secrets:**
   ```bash
   # Generate JWT secret
   python -c "import secrets; print('JWT_SECRET=' + secrets.token_urlsafe(32))"
   
   # Generate JWT refresh secret
   python -c "import secrets; print('JWT_REFRESH_SECRET=' + secrets.token_urlsafe(32))"
   
   # Generate encryption key
   python -c "import secrets; print('EXCHANGE_KEY_ENCRYPTION_KEY=' + secrets.token_urlsafe(32))"
   ```

3. **Set database URL** (SQLite for local dev):
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./data/app.db
   ```

4. **Set Redis URL** (local Redis or Upstash):
   ```env
   REDIS_URL=redis://localhost:6379/0  # Local
   # OR
   REDIS_URL=redis://default:password@redis-xxx-xxx.upstash.io:6379  # Upstash
   ```

5. **Add optional API keys** as needed (Stripe, Twilio, etc.)

### Production Setup

1. **Set up Neon PostgreSQL:**
   - Follow instructions in [Infrastructure Services](#infrastructure-services)
   - Copy connection string to `DATABASE_URL`

2. **Set up Upstash Redis:**
   - Follow instructions in [Infrastructure Services](#infrastructure-services)
   - Copy Redis URL to `REDIS_URL`

3. **Generate production secrets:**
   - Use different secrets than development
   - Store securely (use secrets manager if available)

4. **Configure Stripe:**
   - Use **Live mode** keys (not test keys)
   - Set up webhook endpoint
   - Configure webhook secret

5. **Configure Twilio:**
   - Purchase a phone number
   - Set up for production use

6. **Set environment variables** in your hosting platform (Koyeb, Render, etc.)

---

## Validation & Testing

### Validate API Keys

Use the validation script to test all configured keys:

```bash
python scripts/validate_api_keys.py
```

This will:
- Check for required environment variables
- Test connectivity to external services
- Validate API key formats
- Provide clear error messages for missing/invalid keys

### Manual Testing

**Test Database Connection:**
```bash
python -c "
from server_fastapi.database import get_db_url
print(f'Database URL: {get_db_url()}')
"
```

**Test Redis Connection:**
```bash
python -c "
import asyncio
import redis.asyncio as redis

async def test():
    r = redis.from_url('your-redis-url-here')
    await r.set('test', 'hello')
    result = await r.get('test')
    print(f'Redis test: {result}')
    await r.close()

asyncio.run(test())
"
```

**Test Stripe:**
```bash
python -c "
import os
import stripe

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
try:
    account = stripe.Account.retrieve()
    print(f'Stripe connected: {account.id}')
except Exception as e:
    print(f'Stripe error: {e}')
"
```

**Test Twilio:**
```bash
python -c "
import os
from twilio.rest import Client

client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
try:
    account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
    print(f'Twilio connected: {account.friendly_name}')
except Exception as e:
    print(f'Twilio error: {e}')
"
```

---

## Troubleshooting

### Common Issues

**Issue: "JWT_SECRET must be set to a strong random secret"**
- **Solution:** Generate a new secret using the methods above
- **Check:** Ensure secret is at least 32 characters

**Issue: "EXCHANGE_KEY_ENCRYPTION_KEY must be set to a 32-byte key"**
- **Solution:** Generate a 32-byte key (44 characters in base64)
- **Check:** Key must be exactly 32 bytes

**Issue: Database connection fails**
- **Solution:** Check `DATABASE_URL` format
- **For Neon:** Ensure using `postgresql+asyncpg://` prefix
- **Check:** SSL mode is set to `require`

**Issue: Redis connection timeout**
- **Solution:** Check `REDIS_URL` format
- **For Upstash:** Ensure using correct URL format
- **Check:** Network connectivity and firewall settings

**Issue: Stripe webhook verification fails**
- **Solution:** Ensure `STRIPE_WEBHOOK_SECRET` matches your webhook endpoint
- **Check:** Webhook URL is accessible and correct

**Issue: Twilio SMS not sending**
- **Solution:** Verify phone number is verified in Twilio
- **Check:** Account has sufficient credit
- **Check:** Phone number format is correct (+1234567890)

### Getting Help

- **Documentation:** See `docs/FREE_STACK_DEPLOYMENT_GUIDE.md` for deployment help
- **Settings Reference:** See `server_fastapi/config/settings.py` for all available settings
- **Environment Variables:** See `.env.example` for all variables

---

## Security Best Practices

1. **Never commit secrets to git:**
   - Use `.env` file (in `.gitignore`)
   - Use environment variables in production
   - Use secrets manager (AWS Secrets Manager, HashiCorp Vault) for production

2. **Use different secrets for each environment:**
   - Development: Local secrets
   - Staging: Staging secrets
   - Production: Production secrets

3. **Rotate secrets periodically:**
   - JWT secrets: Every 90 days
   - Exchange encryption key: Every 180 days (requires re-encryption)
   - API keys: As needed

4. **Limit API key permissions:**
   - Only enable required permissions
   - Use IP whitelisting when available
   - Disable withdrawals on exchange keys

5. **Monitor API usage:**
   - Check for unusual activity
   - Set up alerts for high usage
   - Review logs regularly

---

## Next Steps

After setting up API keys:

1. **Validate all keys:** Run `python scripts/validate_api_keys.py`
2. **Test locally:** Start the application and test key functionality
3. **Deploy:** Follow `docs/FREE_STACK_DEPLOYMENT_GUIDE.md` for production deployment
4. **Monitor:** Set up monitoring and alerts for API usage

---

**Last Updated:** December 5, 2025  
**Maintained by:** CryptoOrchestrator Team
