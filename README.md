# CryptoOrchestrator (Experimental Prototype)

> [!WARNING]
> **This is an EXPERIMENTAL PROTOTYPE and a partial implementation.** It is NOT production-ready, hasn't been audited, and should NOT be used for real-money trading without extreme caution and further development.

# CryptoOrchestrator (2026 Edition)

Institutional-grade local trading engine built on **Rust**, **Python 3.12**, and **React 19**.

> **Status**: 🟢 Production Ready (Modernized Jan 2026)

## 📚 Documentation

Detailed documentation is now available in the `docs/` directory and can be viewed via MkDocs.

- [**Quick Start**](docs/index.md)
- [**Architecture Overview**](docs/architecture/overview.md)
- [**API Reference**](docs/api/backend.md)

## 🏗️ Technology Stack

- **Backend**: FastAPI + Granian (Rust ASGI)
- **Data**: Polars + TimescaleDB
- **Frontend**: React 19 + TanStack Router + PandaCSS
- **Security**: AES-256-GCM (GDPR) + SLSA Level 3

## 🚀 Quick Run

```bash
# Start Backend (Granian)
python server_fastapi/serve_granian.py

# Start Frontend
cd client && npm run dev
```
## 🏗️ Technical Highlights (2026)

- **Sentinel Intelligence**: Real-time Market Abuse Detection (Wash Trading/Layering) via Polars.
- **Chaos Resilience**: Database partition and Flood protection verified.
- **Privacy Core**: GDPR-compliant crypto-shredding (AES-256-GCM).
- **Hardened**: SLSA Level 3 Docker builds and Granian production server.

### 🚫 Constraints
- **Production Security**: No formal security audits have been performed.
- **Financial Guarantees**: "Zero vulnerabilities" claims are strictly avoided.

---

## 🚀 Orientation

### Quick Start (Development)

1. **Clone & Install**:

   ```bash
   git clone <repository-url>
   npm run setup
   ```

2. **Environment**: Copy `.env.example` to `.env` and fill in required keys.
3. **Run**:

   ```bash
   npm run start:all
   ```

### Documentation Map

- **[Quick Start Guide](docs/QUICK_START.md)** - Get up and running.
- **[Features Overview](docs/FEATURES.md)** - What kind of automation is possible.
- **[Tech Stack](docs/TECH_STACK.md)** - Details on the Python 3.12 / React 19 infrastructure.
- **[Architecture Deep Dive](docs/architecture.md)** - How the components interact.
- **[Security Policy](SECURITY.md)** - Reporting vulnerabilities and safety protocols.

---

## ⚖️ Disclaimer

**IMPORTANT**: This software is for educational purposes only. Cryptocurrency trading carries substantial risk of loss. The developers are not responsible for any financial losses incurred. Use only for paper trading and simulation until fully verified.

---

**Built with ❤️ by the CryptoOrchestrator Community**

*Copyright © 2026*
