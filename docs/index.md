# CryptoOrchestrator 2026

**Status**: 🟢 Production Ready (Phase 9 Complete)

Welcome to the **CryptoOrchestrator** documentation. This system is a local-first, high-frequency trading engine built on **Rust**, **Python 3.12**, and **React 19**.

## Core Pillars

1.  **Safety**: "Rust Wall" ensures no private keys touch Python memory.
2.  **Compliance**: Native MiCA & ISO 20022 support.
3.  **Privacy**: GDPR "Crypto Shredding" by default.

## Getting Started

```bash
# Backend
python server_fastapi/serve_granian.py

# Frontend
cd client && npm run dev
```

## Architecture

See [Architecture Overview](architecture/overview.md) for the "Rust Bridge" design.
