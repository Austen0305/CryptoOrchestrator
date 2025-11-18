# CryptoOrchestrator - SaaS Platform

**Professional cryptocurrency trading automation platform with AI-powered bots, advanced strategies, and comprehensive risk management.**

## 🚀 Quick Start

### For SaaS Deployment

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Crypto-Orchestrator
   ```

2. **Set up environment**:
   ```bash
   cp .env.prod.example .env.prod
   # Edit .env.prod with your production values
   ```

3. **Deploy with Docker**:
   ```bash
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

4. **Run migrations**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

See [SaaS Setup Guide](docs/SAAS_SETUP.md) for detailed instructions.

---

## 📚 Documentation

- **[SaaS Setup Guide](docs/SAAS_SETUP.md)** - Complete setup instructions
- **[API Documentation](docs/api.md)** - API reference
- **[Architecture](docs/architecture.md)** - System architecture
- **[Privacy Policy](docs/PRIVACY_POLICY.md)** - Privacy policy
- **[Terms of Service](docs/TERMS_OF_SERVICE.md)** - Terms of service
- **[Pricing](docs/PRICING.md)** - Subscription plans

---

# CryptoOrchestrator - Professional AI-Powered Crypto Trading Platform

> A production-ready cryptocurrency trading platform featuring AI-powered machine learning, multi-exchange support, comprehensive risk management, and intelligent automation. Built with FastAPI backend, React frontend, Electron desktop app, and React Native mobile support.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![Electron](https://img.shields.io/badge/Electron-25+-purple.svg)](https://electronjs.org/)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Development](#development)
- [Deployment](#deployment)
- [Documentation](#documentation)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)
- [Disclaimer](#disclaimer)

## 🎯 Overview

CryptoOrchestrator is an advanced cryptocurrency trading platform that combines artificial intelligence, machine learning, and comprehensive risk management to provide professional-grade trading automation. The platform supports multiple exchanges, advanced backtesting, real-time analytics, and intelligent automation features.

### Key Highlights

- ✅ **Production Ready** - Fully tested and deployed-ready
- ✅ **267 API Routes** - Comprehensive REST API
- ✅ **AI-Powered** - Machine learning models for trading predictions
- ✅ **Multi-Exchange** - Support for 5+ major exchanges
- ✅ **Desktop & Mobile** - Electron app + React Native mobile
- ✅ **Complete Monetization** - Stripe integration + licensing system

## 🚀 Features

### Advanced Machine Learning
- **Neural Network Engine** - Deep learning with 9+ technical indicators
- **Ensemble Prediction System** - Combines LSTM, GRU, Transformer, and XGBoost models
- **AutoML System** - Automated hyperparameter optimization
- **Reinforcement Learning** - Adaptive trading strategies
- **Sentiment AI** - Market sentiment analysis from news and social media
- **Market Regime Detection** - Bull/Bear/Sideways/Volatile classification

### Comprehensive Risk Management
- **Professional Metrics** - Sharpe Ratio, Sortino Ratio, VaR, CVaR
- **Drawdown Kill Switch** - Automatic trading halt on excessive losses
- **Circuit Breaker System** - Protects against catastrophic losses
- **Portfolio Heat Monitoring** - Real-time risk exposure tracking
- **Monte Carlo Simulations** - Risk scenario analysis

### Trading Capabilities
- **Multi-Exchange Support** - Binance, Kraken, Coinbase, KuCoin, Bybit
- **Smart Routing** - Best price execution across exchanges
- **Arbitrage Tools** - Multi-exchange arbitrage detection
- **Paper Trading** - Risk-free strategy testing
- **Live Trading** - Production-ready execution with safety guardrails

### AI Copilot & Automation
- **AI Copilot** - Intelligent trading assistant
- **Auto-Rebalancing** - Portfolio rebalancing automation
- **Auto-Hedging** - Dynamic hedging strategies
- **Strategy Switching** - Automatic strategy changes based on market regime
- **Smart Alerts** - AI-powered alert generation

### Monetization & Licensing
- **Stripe Integration** - Complete payment processing
- **Licensing System** - Secure software licensing with machine binding
- **Subscription Tiers** - Free, Basic, Pro, Enterprise
- **Demo Mode** - Feature-limited trial mode

## 🛠 Tech Stack

### Backend
- **Python 3.8+** - Core language
- **FastAPI** - High-performance async web framework
- **SQLAlchemy** - ORM for database operations
- **Alembic** - Database migrations
- **PostgreSQL/SQLite** - Database options
- **Redis** - Caching and session storage
- **Celery** - Background task processing

### Frontend
- **React 18+** - UI framework
- **TypeScript** - Type-safe JavaScript
- **Vite** - Fast build tool
- **TailwindCSS** - Utility-first CSS
- **shadcn/ui** - Beautiful UI components

### Desktop
- **Electron** - Cross-platform desktop app
- **Auto-updater** - Automatic update system

### Mobile
- **React Native** - Cross-platform mobile app
- **Expo** - Development tooling

### ML & Data
- **TensorFlow/Keras** - Deep learning
- **scikit-learn** - Machine learning utilities
- **pandas** - Data manipulation
- **numpy** - Numerical computing

## 🏗 Architecture

The platform follows a modular architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  React   │  │ Electron │  │  Mobile  │             │
│  │   Web    │  │  Desktop │  │   App    │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
└───────┼──────────────┼──────────────┼───────────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │ REST API / WebSocket
┌──────────────────────▼───────────────────────────────────┐
│                   FastAPI Backend                        │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐        │
│  │   Routes   │  │  Services  │  │  Models    │        │
│  └────────────┘  └────────────┘  └────────────┘        │
└───────┬────────────────┬──────────────────┬─────────────┘
        │                │                  │
┌───────▼────┐  ┌────────▼────────┐  ┌──────▼──────┐
│ PostgreSQL │  │      Redis      │  │  Exchanges  │
│  Database  │  │      Cache      │  │     API     │
└────────────┘  └─────────────────┘  └─────────────┘
```

For detailed architecture documentation, see [docs/architecture.md](docs/architecture.md).

## 📦 Installation

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+
- **PostgreSQL** 15+ (optional, SQLite supported for development)
- **Redis** (optional, for caching)

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/CryptoOrchestrator.git
cd CryptoOrchestrator

# Install Node.js dependencies
npm install --legacy-peer-deps

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration

# Run database migrations (if using PostgreSQL)
alembic upgrade head

# Start development server
npm run dev:fastapi  # Backend
npm run dev          # Frontend
```

For detailed installation instructions, see [docs/installation.md](docs/installation.md).

## 💻 Development

### Running the Application

#### Option 1: Electron Desktop App (Recommended)
```bash
npm run electron
```

#### Option 2: Web Development
```bash
# Terminal 1: Start FastAPI backend
npm run dev:fastapi

# Terminal 2: Start React frontend
npm run dev
```

### Project Structure

```
CryptoOrchestrator/
├── client/                 # React frontend
│   ├── src/
│   │   ├── components/    # UI components
│   │   ├── pages/         # Page components
│   │   ├── hooks/         # Custom React hooks
│   │   └── lib/           # Utilities
│   └── public/            # Static assets
├── server_fastapi/        # FastAPI backend
│   ├── routes/            # API routes
│   ├── services/          # Business logic
│   ├── models/            # Database models
│   ├── middleware/        # Custom middleware
│   └── main.py            # Application entry point
├── electron/              # Electron configuration
│   ├── index.js           # Main process
│   └── preload.js         # Preload script
├── mobile/                # React Native app
├── docs/                  # Documentation
├── tests/                 # Test suites
└── scripts/               # Utility scripts
```

### Available Scripts

```bash
# Development
npm run dev              # Start React dev server
npm run dev:fastapi      # Start FastAPI dev server
npm run electron         # Start Electron app

# Building
npm run build            # Build React app
npm run build:electron   # Build Electron app

# Testing
npm test                 # Run frontend tests
pytest                   # Run backend tests
npm run test:e2e         # Run end-to-end tests

# Code Quality
npm run lint             # Lint frontend code
black server_fastapi/    # Format Python code
prettier --write .       # Format frontend code
```

## 🚀 Deployment

### Free Hosting (Recommended for Getting Started)

**Deploy your app for free on Render, Railway, or Fly.io!**

- 📖 **[Quick Start Guide](QUICK_START_FREE_HOSTING.md)** - Deploy in 10 minutes
- 📚 **[Complete Free Hosting Guide](FREE_HOSTING_GUIDE.md)** - All free hosting options
- 📋 **[Free Hosting Summary](FREE_HOSTING_SUMMARY.md)** - Overview and recommendations
- ✅ **[Pre-Deployment Checklist](PRE_DEPLOYMENT_CHECKLIST.md)** - What to test before deploying

### Docker Deployment (Recommended for Production)

```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment

For detailed deployment instructions, see [docs/deployment.md](docs/deployment.md).

Key deployment options:
- **Free Hosting** - Render, Railway, Fly.io (see [FREE_HOSTING_GUIDE.md](FREE_HOSTING_GUIDE.md))
- **Docker Compose** - One-command deployment
- **PM2** - Process management for Node.js
- **Systemd** - Linux service management
- **Cloud Platforms** - AWS, Azure, GCP guides

## 📚 Documentation

Comprehensive documentation is available in the `/docs` directory:

- **[Installation Guide](docs/installation.md)** - Step-by-step setup
- **[Deployment Guide](docs/deployment.md)** - Production deployment
- **[API Reference](docs/api.md)** - Complete API documentation
- **[Architecture Guide](docs/architecture.md)** - System architecture
- **[Licensing Guide](docs/licensing.md)** - Stripe/Licensing implementation
- **[User Guide](docs/USER_GUIDE.md)** - End-user documentation

API documentation is also available via OpenAPI:
- Interactive docs: `http://localhost:8000/docs`
- JSON schema: `docs/openapi.json` (auto-generated on startup)

## 🧪 Testing

```bash
# Run all tests
pytest                    # Backend tests
npm test                  # Frontend tests
npm run test:e2e          # End-to-end tests

# Run with coverage
pytest --cov=server_fastapi
npm run test:coverage

# Run specific test suites
pytest server_fastapi/tests/test_bots.py
npm test -- --testNamePattern="Button"
```

Test reports and documentation: [TEST_REPORT.md](TEST_REPORT.md)

## 🤝 Contributing

Contributions are welcome! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

**IMPORTANT**: This software is for educational purposes only. Cryptocurrency trading carries substantial risk of loss. Past performance does not guarantee future results.

- **Never invest more than you can afford to lose**
- **Always start with paper trading**
- **Thoroughly backtest strategies before live trading**
- **Monitor your bots regularly**
- **Use appropriate position sizing**

The developers are not responsible for any financial losses incurred through the use of this software.

## 📞 Support

- 📧 Email: support@cryptoorchestrator.com
- 💬 Discord: [Join our community](https://discord.gg/cryptoorchestrator)
- 📖 Documentation: [docs.cryptoorchestrator.com](https://docs.cryptoorchestrator.com)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/CryptoOrchestrator/issues)

## 🙏 Acknowledgments

- [ccxt](https://github.com/ccxt/ccxt) - Cryptocurrency exchange library
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful UI components
- [React](https://reactjs.org/) - UI framework
- [Electron](https://electronjs.org/) - Desktop framework

---

**Built with ❤️ by traders, for traders**

For the latest updates, star ⭐ this repository!
