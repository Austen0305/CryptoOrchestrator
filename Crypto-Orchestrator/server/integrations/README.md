# Integration adapters for Freqtrade and Jesse

This folder contains lightweight Python adapter scripts that provide a simple newline-delimited JSON stdin/stdout protocol so the Node.js server can interact with Freqtrade and Jesse tooling (or with simple mock logic if the frameworks aren't installed).

## Quick setup

1. Create a Python virtual environment and activate it. On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Install optional dependencies (the adapters include placeholder logic and do not require the full frameworks to run; install the real packages to integrate fully):

```powershell
pip install -r requirements.txt
```

3. Start adapters (for development) using the helper script (PowerShell):

```powershell
.\server\integrations\start_adapters.ps1
```

4. Run the Node server as usual (from repo root):

```powershell
npm run dev
```

## Protocol

Adapters read newline-delimited JSON messages from stdin. Each message should be an object like:

```json
{ "id": "unique-id", "action": "predict", "payload": { ... } }
```

Adapters respond with a single-line JSON message containing the same `id` and either a `result` or `error` field.

Supported actions in the placeholder adapters:

- `ping` — health check; returns `{ ok: true }`.
- `predict` — returns a simple pseudo-prediction `{ action: 'buy'|'sell'|'hold', confidence: number }`.
- `backtest` — returns a simple summary `{ trades: number, profit_pct: number }`.

Example (Node side): send JSON terminated by `\n` to the child process stdin and read lines from stdout.

## Notes

- The included adapters provide deterministic placeholder behavior so they work without the full Freqtrade or Jesse frameworks. To integrate real frameworks, replace the placeholder logic in `freqtrade_adapter.py` and `jesse_adapter.py` with calls into those libraries and adapt inputs/outputs.
- Use the `/api/integrations/*` HTTP endpoints exposed by the server for quick manual testing:
  - `POST /api/integrations/predict` — optional auth. Body: `{}` or payload with marketData.
  - `POST /api/integrations/backtest` — requires auth.
  - `GET /api/integrations/ping` — no auth.

## Live mode and environment variables

To enable live exchange mode for the Freqtrade adapter, set the following environment variables (do NOT commit secrets to source control):

- `FREQTRADE_EXCHANGE_MODE` = `live` to attempt connecting to a real exchange (default: `mock`).
- `FREQTRADE_EXCHANGE_NAME` = exchange id (e.g., `binance`).
- `FREQTRADE_API_KEY` and `FREQTRADE_API_SECRET` = API credentials for the exchange.

When `exchange.mode` is `live`, the adapter will attempt to initialize a CCXT-backed exchange. If initialization fails (network, sandbox restrictions, missing credentials), the adapter will automatically fall back to the `MockExchange` so the service remains operational.

## CI

A GitHub Actions workflow is included at `.github/workflows/integrations.yml`. It runs a lightweight python smoke-test and TypeScript typecheck on push/PR to `main`.
