# Frequently Asked Questions (FAQ)

## Getting Started

### Q: What is CryptoOrchestrator?
**A**: CryptoOrchestrator is a professional AI-powered cryptocurrency trading platform that combines machine learning, risk management, and automated trading capabilities. It features real-time market analysis, algorithmic trading strategies, and comprehensive portfolio management tools.

### Q: Do I need programming experience to use CryptoOrchestrator?
**A**: No! While advanced users can customize strategies with Python, the platform provides an intuitive graphical interface for:
- Creating and managing trading bots
- Setting up automated strategies
- Monitoring performance
- Managing portfolios

### Q: Is CryptoOrchestrator free?
**A**: We offer a freemium model:
- **Free Tier**: Paper trading, basic analytics, community support
- **Premium Tier**: Live trading, advanced analytics, priority support
- **Enterprise Tier**: Custom integrations, dedicated support, SLA guarantees

### Q: What cryptocurrencies does it support?
**A**: Major cryptocurrencies across multiple blockchain networks:
- Bitcoin (BTC), Ethereum (ETH), and other major altcoins
- Support for 100+ trading pairs
- Integration with Kraken, Binance, Coinbase, and other exchanges

## Account and Security

### Q: How secure is my data?
**A**: We implement bank-level security:
- End-to-end encryption for all data
- Multi-factor authentication (MFA)
- Secure wallet management (custodial and non-custodial)
- Regular security audits
- GDPR compliance

### Q: What happens if I lose my 2FA device?
**A**: We provide multiple recovery options:
- Backup codes generated during setup (save these securely!)
- Email-based recovery for verified accounts
- Phone support for account verification
- Temporary access codes for urgent situations

### Q: Can I use the same account on multiple devices?
**A**: Yes, with these limitations:
- Maximum 3 concurrent sessions
- Automatic logout after 30 minutes of inactivity
- Session management in account settings
- Device management and security alerts

## Trading and Bots

### Q: What's the difference between paper trading and live trading?
**A**:
- **Paper Trading**: Simulated trading with virtual money
  - Risk-free learning and testing
  - Unlimited practice funds
  - Real market data and conditions
- **Live Trading**: Real money trading
  - Requires blockchain wallet (no API keys needed)
  - Actual financial risk
  - Real-time execution

### Q: How do I create my first trading bot?
**A**: Follow these steps:
1. Click "Create New Bot" in the dashboard
2. Choose "Paper Trading" mode for safety
3. Select a trading pair (e.g., BTC/USD)
4. Pick a strategy (start with "ML Adaptive")
5. Set risk parameters (1-2% per trade recommended)
6. Click "Start Bot"

### Q: What strategies are available?
**A**:
- **ML Adaptive**: AI-powered strategy using machine learning
- **Momentum**: Follows market trends
- **Mean Reversion**: Trades against extreme price movements
- **Arbitrage**: Exploits price differences across DEXs and chains
- **Scalping**: High-frequency small trades

### Q: How much should I risk per trade?
**A**: Risk management guidelines:
- **Conservative**: 0.5-1% of portfolio per trade
- **Moderate**: 1-2% of portfolio per trade
- **Aggressive**: 2-5% of portfolio per trade
- **Never risk more than you can afford to lose**

### Q: Why did my bot stop trading?
**A**: Common reasons:
- **Risk Limits Hit**: Stop-loss or daily loss limits reached
- **Circuit Breaker**: Excessive losses triggered safety shutdown
- **Exchange Issues**: API connectivity problems
- **Market Hours**: Outside configured trading hours
- **Manual Stop**: User or system intervention

Check the bot logs and health dashboard for specific reasons.

## Performance and Analytics

### Q: How do I interpret performance metrics?
**A**:
- **Win Rate**: Percentage of profitable trades (>60% is excellent)
- **Sharpe Ratio**: Risk-adjusted returns (>1.5 is good)
- **Maximum Drawdown**: Largest peak-to-trough decline (<20% is manageable)
- **Profit Factor**: Gross profits divided by gross losses (>1.5 is good)

### Q: Why is my bot not profitable?
**A**: Common reasons and solutions:
- **Over-optimization**: Strategies that work in backtests but fail live
- **Transaction Costs**: High fees eating into profits
- **Slippage**: Orders executing at worse prices than expected
- **Market Conditions**: Strategy not suited to current market
- **Risk Management**: Taking too much risk per trade

### Q: How often should I check my bots?
**A**: Monitoring frequency depends on strategy:
- **Scalping Bots**: Daily monitoring required
- **Swing Bots**: Weekly reviews sufficient
- **Long-term Bots**: Monthly performance reviews
- **All Bots**: Set up email alerts for significant events

## Technical Issues

### Q: The application won't start. What should I do?
**A**: Try these solutions in order:
1. Restart the application
2. Check system requirements (RAM, disk space)
3. Verify internet connection
4. Update to the latest version
5. Check firewall/antivirus settings
6. Contact support if issues persist

### Q: Why is the application running slowly?
**A**: Performance issues may be caused by:
- Insufficient RAM (8GB+ recommended)
- Too many bots running simultaneously
- Large amounts of historical data
- Network connectivity issues
- Background processes consuming resources

### Q: How do I update the application?
**A**: The application auto-updates, but you can also:
1. Check for updates in Settings > About
2. Download the latest version from our website
3. Follow the installation prompts
4. Your settings and data will be preserved

### Q: Can I run multiple instances?
**A**: Not recommended due to:
- Resource conflicts
- Database locking issues
- DEX aggregator rate limit management
- Difficulty managing multiple portfolios

## Integration and API

### Q: How do I set up a wallet for trading?
**A**: Wallet setup steps (no API keys needed!):
1. Go to Settings > Wallets
2. Click "Create Wallet"
3. Select blockchain network (Ethereum, Base, Arbitrum, etc.)
4. Choose wallet type:
   - **Custodial**: Platform-managed wallet (recommended for beginners)
   - **Non-Custodial**: Connect your own wallet (MetaMask, WalletConnect, etc.)
5. For custodial wallets, the platform creates and manages the wallet
6. For non-custodial, connect your existing wallet
7. Start paper trading first to test strategies!

### Q: Do I need exchange API keys?
**A**: **No!** The platform uses blockchain/DEX trading exclusively:
- ✅ **No API keys required** - Trade directly on blockchains
- ✅ **Lower fees** - No exchange fees, only blockchain gas + DEX fees
- ✅ **Better privacy** - No need to share API credentials
- ✅ **Multi-chain support** - Trade on Ethereum, Base, Arbitrum, Polygon, and more

**Note**: Exchange API keys are deprecated as of December 2025. Use blockchain wallets instead.

### Q: How do I use the REST API?
**A**: Basic API usage:
```bash
# Get authentication token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"password"}'

# Use token for authenticated requests
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/bots/
```

### Q: Can I integrate with other trading platforms?
**A**: Yes, through our API:
- **Python SDK**: Full programmatic access
- **Webhooks**: Real-time event notifications
- **REST API**: Complete platform integration
- **Third-party integrations**: Freqtrade, Jesse, etc.

## Billing and Payments

### Q: How does billing work?
**A**:
- **Free Tier**: No payment required
- **Premium**: Monthly subscription ($49/month)
- **Enterprise**: Custom pricing based on usage
- **Payment Methods**: Credit card, PayPal, wire transfer
- **Billing Cycle**: Monthly on the anniversary date

### Q: Can I cancel my subscription?
**A**: Yes, you can cancel anytime:
- Settings > Billing > Cancel Subscription
- Access continues until the end of the billing period
- No cancellation fees
- Reactivate anytime within 6 months

### Q: Do you offer refunds?
**A**: Refund policy:
- **30-day money-back guarantee** for new subscriptions
- **Pro-rated refunds** for billing errors
- **No refunds** for partial months or usage-based fees
- Contact support for refund requests

## Legal and Compliance

### Q: Is cryptocurrency trading legal in my country?
**A**: Cryptocurrency regulations vary by country:
- **United States**: Legal in most states, regulated by SEC/FINRA
- **European Union**: Regulated under MiFID II
- **Other Countries**: Check local regulations
- **Always consult local laws and tax advisors**

### Q: What are the tax implications?
**A**: Tax treatment varies:
- **Capital Gains Tax**: Profits from trading are taxable
- **Record Keeping**: Maintain detailed trading records
- **Tax Forms**: May need to report cryptocurrency transactions
- **Consult a tax professional** for your specific situation

### Q: Do you comply with data protection laws?
**A**: Yes, we are fully compliant with:
- **GDPR** (European Union)
- **CCPA** (California)
- **PIPEDA** (Canada)
- **Data minimization** and **user consent** principles

### Q: What happens to my data if I delete my account?
**A**: Account deletion process:
- **Immediate**: Account disabled and inaccessible
- **30 days**: Data retained for recovery if requested
- **Complete deletion**: All data permanently removed after 30 days
- **No recovery** possible after complete deletion

## Advanced Features

### Q: How do I create custom trading strategies?
**A**: For advanced users:
1. Use our Python SDK
2. Implement strategy logic
3. Test in paper trading mode
4. Deploy to live trading with caution

### Q: Can I backtest strategies?
**A**: Yes, comprehensive backtesting:
- Historical data from 2017+
- Multiple timeframes (1m to 1d)
- Performance metrics and risk analysis
- Walk-forward optimization
- Out-of-sample testing

### Q: What risk management features are available?
**A**: Comprehensive risk controls:
- **Position Sizing**: Fixed amount or percentage-based
- **Stop Losses**: Fixed or trailing stops
- **Take Profits**: Profit target levels
- **Portfolio Limits**: Maximum exposure limits
- **Circuit Breakers**: Automatic shutdown on excessive losses

### Q: How do I set up alerts and notifications?
**A**: Notification configuration:
1. Settings > Notifications
2. Choose notification types:
   - Trade executions
   - Profit/loss thresholds
   - Risk limit breaches
   - System alerts
3. Select delivery methods:
   - In-app notifications
   - Email alerts
   - Push notifications (browser)
   - SMS (premium feature)

### Q: What are push notifications and how do I enable them?
**A**: Push notifications allow you to receive alerts even when the app is closed:
1. Go to Settings > Notifications
2. Enable "Push Notifications"
3. Allow browser permission when prompted
4. You'll receive notifications for important events

**Supported Browsers:**
- Chrome/Edge (Desktop & Mobile)
- Firefox (Desktop)
- Safari (macOS 16+)

**Note**: Push notifications require HTTPS and browser permission.

### Q: Can I use the app offline?
**A**: Yes! CryptoOrchestrator works as a Progressive Web App (PWA) with offline support:
- **View Cached Data**: Access portfolio, bots, and trades offline
- **Queue Actions**: Create trades and bot actions offline (synced when online)
- **Offline Indicator**: Banner shows when you're offline
- **Auto-Sync**: Actions automatically sync when connection is restored

**To enable offline support:**
1. Install the PWA (see PWA installation guide)
2. Offline support is enabled by default
3. Data is cached automatically as you use the app

**Limitations:**
- Real-time price updates require internet
- Trading execution requires internet
- New data requires internet connection

## Progressive Web App (PWA)

### Q: What is a Progressive Web App?
**A**: A PWA is a web application that works like a native app:
- **Installable**: Add to home screen/desktop
- **Offline Support**: Works without internet connection
- **Push Notifications**: Receive alerts when app is closed
- **Fast Loading**: Cached assets load instantly
- **App-like Experience**: Full-screen, no browser UI

### Q: How do I install the PWA?
**A**: Installation varies by device:

**Desktop (Chrome/Edge):**
1. Visit cryptoorchestrator.com
2. Click install icon in address bar
3. Click "Install"

**iOS (Safari):**
1. Visit website in Safari
2. Tap Share button
3. Select "Add to Home Screen"

**Android (Chrome):**
1. Visit website
2. Tap menu (three dots)
3. Select "Add to Home Screen" or "Install App"

### Q: What can I do offline?
**A**: Offline capabilities:
- View cached portfolio data
- View cached bot status
- View cached trade history
- Queue new trades (execute when online)
- Queue bot actions (execute when online)
- View cached market data

**Requires Internet:**
- Real-time price updates
- Executing trades
- Fetching new data
- WebSocket connections

### Q: How do push notifications work?
**A**: Push notifications work like this:
1. **Enable**: Settings → Notifications → Enable Push Notifications
2. **Permission**: Browser asks for notification permission (allow)
3. **Receive**: Get notifications even when app is closed
4. **Manage**: Control notification types in Settings

**Notification Types:**
- Trade executions
- Bot status changes
- Risk limit breaches
- System alerts

### Q: Why aren't my push notifications working?
**A**: Common issues:
- **Permission Denied**: Check browser notification settings
- **Not Installed**: PWA must be installed (not just bookmarked)
- **Browser Support**: Some browsers don't support push notifications
- **HTTPS Required**: Push notifications require HTTPS connection
- **Settings Disabled**: Check app notification settings

**Solutions:**
1. Check browser notification permissions
2. Re-enable notifications in app settings
3. Unsubscribe and resubscribe
4. Clear browser cache
5. Reinstall PWA if needed

## Mobile App

### Q: Is there a mobile app?
**A**: Yes! CryptoOrchestrator has a React Native mobile app for iOS and Android:
- **Native Performance**: Fast and responsive
- **Biometric Security**: Face ID, Touch ID, Fingerprint
- **Real-time Updates**: WebSocket integration
- **Offline Support**: View cached data offline
- **Full Features**: All desktop features available

### Q: How do I install the mobile app?
**A**: Installation options:

**App Stores (Coming Soon):**
- iOS: App Store
- Android: Google Play Store

**Development Build:**
- See [Mobile App Guide](./MOBILE_APP_GUIDE.md) for setup instructions
- Requires development environment setup
- For developers and beta testers

### Q: What features are available on mobile?
**A**: Mobile app includes:
- **Dashboard**: Real-time portfolio tracking
- **Bot Management**: Create, start, stop bots
- **Trading**: Execute trades on the go
- **Portfolio**: View holdings and performance
- **Settings**: Account and app preferences
- **Biometric Auth**: Secure login with Face ID/Touch ID

### Q: Is the mobile app secure?
**A**: Yes, security features include:
- **Biometric Authentication**: Face ID, Touch ID, Fingerprint
- **Encrypted Storage**: Sensitive data encrypted at rest
- **Secure API**: All API calls use HTTPS
- **Token Management**: Secure JWT token storage
- **No Private Keys**: Private keys never stored on device

## Support and Community

### Q: How do I get help?
**A**: Multiple support channels:
- **Documentation**: Comprehensive online docs
- **Community Forum**: User-to-user support
- **Email Support**: support@cryptoorchestrator.com
- **Live Chat**: Available during business hours
- **Video Tutorials**: Step-by-step guides
- **Mobile App Guide**: [docs/MOBILE_APP_GUIDE.md](./MOBILE_APP_GUIDE.md)

### Q: What's the response time for support?
**A**:
- **Urgent Issues**: Response within 1 hour
- **Technical Issues**: Response within 4 hours
- **General Questions**: Response within 24 hours
- **Premium Support**: Priority response times

### Q: Do you offer training or education?
**A**: Educational resources:
- **Getting Started Guide**: Basic platform usage
- **Trading Tutorials**: Strategy explanations
- **Video Courses**: In-depth training modules
- **Webinars**: Live educational sessions
- **Community Events**: User meetups and workshops
- **Mobile App Guide**: Complete mobile setup instructions

---

Can't find what you're looking for? Contact our support team - we're here to help!