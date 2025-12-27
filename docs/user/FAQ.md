# Frequently Asked Questions (FAQ)

**Last Updated**: December 12, 2025

## General

### What is CryptoOrchestrator?

CryptoOrchestrator is an AI-powered cryptocurrency trading platform that provides automated trading bots, portfolio management, DEX trading, and advanced analytics.

### Is CryptoOrchestrator free?

Yes, CryptoOrchestrator offers a free tier with core features. Enterprise features are available for enterprise customers.

### What cryptocurrencies are supported?

CryptoOrchestrator supports trading on multiple blockchain networks including Ethereum, Base, Arbitrum, Polygon, Optimism, Avalanche, and BNB Chain.

---

## Account & Setup

### How do I create an account?

1. Visit [app.cryptoorchestrator.com](https://app.cryptoorchestrator.com)
2. Click "Sign Up"
3. Enter your email and password
4. Verify your email
5. Complete your profile

### How do I enable 2FA?

1. Go to Settings → Security
2. Click "Enable 2FA"
3. Scan QR code with authenticator app
4. Enter verification code
5. Save backup codes

### How do I generate API keys?

1. Go to Settings → API Keys
2. Click "Create New Key"
3. Set permissions and rate limits
4. Copy and save your API key (shown only once)

---

## Trading

### What order types are supported?

Supported order types:
- Market orders
- Limit orders
- Stop-loss orders
- Take-profit orders
- Trailing stop orders
- OCO (One-Cancels-Other) orders

### How do I place a trade?

1. Navigate to Trading → Place Order
2. Select trading pair
3. Choose order type
4. Enter amount and price (if limit order)
5. Review and confirm

### What is paper trading?

Paper trading allows you to practice trading with virtual funds without risking real money. All trades are simulated.

### How do I switch between paper and live trading?

Go to Settings → Trading Mode and select "Paper Trading" or "Live Trading".

---

## API & Integration

### How do I authenticate API requests?

Use your API key in the `X-API-Key` header:
```bash
curl -H "X-API-Key: your-api-key" https://api.cryptoorchestrator.com/api/bots/
```

### What are the API rate limits?

Default rate limits:
- Free tier: 100 requests/hour
- Professional: 1,000 requests/hour
- Enterprise: Custom limits

### How do I set up webhooks?

1. Go to Settings → Webhooks
2. Click "Create Webhook"
3. Enter webhook URL
4. Select events to subscribe to
5. Save webhook secret

### What API version should I use?

- **v1**: Stable, production-ready
- **v2**: Beta, enhanced features

See [API Versioning Guide](/docs/developer/API_VERSIONING.md) for details.

---

## Bots & Automation

### How do I create a trading bot?

1. Go to Bots → Create Bot
2. Select strategy
3. Configure parameters
4. Set risk limits
5. Activate bot

### What trading strategies are available?

Available strategies:
- DCA (Dollar Cost Averaging)
- Grid Trading
- Trailing Bot
- Infinity Grid
- Futures Trading
- Yield Farming

### How do I backtest a strategy?

1. Go to Backtesting → New Backtest
2. Select strategy
3. Choose time period
4. Configure parameters
5. Run backtest
6. Review results

---

## Portfolio & Analytics

### How do I view my portfolio?

Navigate to Portfolio → Overview to see:
- Total portfolio value
- Asset allocation
- P&L summary
- Performance metrics

### What analytics are available?

Available analytics:
- Portfolio performance
- Trading analytics
- Risk metrics
- User analytics
- Business metrics

### How do I export my data?

1. Go to Settings → Privacy
2. Click "Export Data"
3. Select data types
4. Download export file

---

## Security

### How secure is CryptoOrchestrator?

CryptoOrchestrator implements:
- Multi-factor authentication
- API key authentication
- Rate limiting
- Security monitoring
- Audit logging
- Encryption at rest and in transit

### What should I do if my account is compromised?

1. Immediately change your password
2. Revoke all API keys
3. Enable 2FA (if not enabled)
4. Contact support: security@cryptoorchestrator.com
5. Review account activity

### How do I secure my API keys?

- Store keys securely (environment variables, secrets manager)
- Never commit keys to version control
- Rotate keys regularly
- Use different keys for different environments
- Revoke unused keys

---

## Troubleshooting

### I'm getting authentication errors

**Solutions**:
1. Verify API key is correct
2. Check API key is active
3. Verify key permissions
4. Check rate limits
5. Review API version

### Trades are not executing

**Check**:
1. Account balance
2. Trading pair availability
3. Order parameters
4. Market status
5. Network connectivity

### API requests are timing out

**Solutions**:
1. Check internet connection
2. Verify API endpoint URL
3. Check firewall settings
4. Review rate limits
5. Try again later

### I can't connect to the platform

**Troubleshooting**:
1. Check internet connection
2. Verify platform status: `/api/health`
3. Clear browser cache
4. Try different browser
5. Check firewall/proxy settings

---

## Billing & Pricing

### What are the pricing tiers?

- **Free**: Core features, basic API access
- **Professional**: Enhanced features, higher limits
- **Enterprise**: Custom features, dedicated support

### How do I upgrade my plan?

1. Go to Settings → Billing
2. Click "Upgrade Plan"
3. Select tier
4. Complete payment

### What payment methods are accepted?

Accepted methods:
- Credit/debit cards
- Cryptocurrency
- Bank transfer (Enterprise)

---

## Privacy & Data

### What data do you collect?

We collect:
- Account information
- Trading data
- Usage analytics
- Technical data (for support)

See [Privacy Policy](/docs/legal/PRIVACY_POLICY.md) for details.

### How do I delete my account?

1. Go to Settings → Privacy
2. Click "Delete Account"
3. Confirm deletion
4. Account will be deleted within 30 days

### Can I export my data?

Yes, you can export your data:
1. Go to Settings → Privacy
2. Click "Export Data"
3. Select data types
4. Download export

---

## Support

### How do I get help?

**Self-Service**:
- Documentation
- FAQ
- Community forums
- Video tutorials

**Direct Support**:
- Email: support@cryptoorchestrator.com
- Community: [community.cryptoorchestrator.com](https://community.cryptoorchestrator.com)

### What are support response times?

- Documentation: Immediate (self-service)
- Community: < 24 hours
- Email: < 48 hours
- Enterprise: < 4 hours

---

## Additional Resources

- [Getting Started Guide](/docs/user/GETTING_STARTED.md)
- [Troubleshooting Guide](/docs/user/TROUBLESHOOTING.md)
- [API Documentation](/docs/api)
- [Community Forums](https://community.cryptoorchestrator.com)

---

**Last Updated**: December 12, 2025
