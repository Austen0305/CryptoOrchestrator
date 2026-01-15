# Backend API Reference

## Core Endpoints

The backend is served via **Granian** and uses **FastAPI**.

### Market Data
`GET /api/market/ticker/{symbol}`
- Returns real-time price info.
- Powered by `server_fastapi/services/market_data_service.py` (Polars).

### Trading
`POST /api/trade/execute`
- Executes a trade.
- Requires `idempotency_key`.
- Protected by `RiskManager`.

### Privacy
`POST /api/privacy/rotate-key`
- Rotates the user's Data Encryption Key (DEK).
- Part of GDPR "Crypto Shredding".

::: server_fastapi.main
