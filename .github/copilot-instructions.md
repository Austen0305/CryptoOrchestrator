# CryptoOrchestrator – AI Assistant Working Rules

Concise, project‑specific guidance to make an AI agent productive immediately. Keep answers grounded in THESE patterns; do not invent undocumented architectures.

## 1. High‑Level Architecture
- Monorepo style: React + Vite frontend (`client/`), FastAPI backend (`server_fastapi/`), Electron wrapper (`electron/`), shared types (`shared/`), Python trading/integration adapters (`server_fastapi/services` + `server/integrations` legacy path).
- FastAPI is authoritative backend. Legacy Express/Node server code exists (e.g. `server/routes/*.ts`) mainly for reference; prefer Python implementations under `server_fastapi/routes/`.
- Electron launches FastAPI (script in `package.json` `dev:fastapi`) and serves the built frontend via `file://` or development server.
- Services layered: route → service (in `server_fastapi/services/`) → external libs (ccxt, ML libs, adapters). ML, risk, analytics, trading orchestration live in Python.

## 2. Key Directories & Their Roles
- `server_fastapi/main.py`: App factory & middleware: CORS (Electron aware), security headers, rate limiting (SlowAPI), Redis init, DB pool.
- `server_fastapi/routes/`: Thin endpoint definitions. Follow existing style: pydantic models, dependency injection, JWT stub in `integrations.py`.
- `server_fastapi/services/`: Business logic modules (trading orchestration, integration_service, risk, analytics, backtesting). Keep stateless where possible; long‑running processes tracked inside specific service (e.g., `integration_service` maintains `self.integrations`).
- `client/src/lib/api.ts`: Canonical mapping of frontend REST calls. Hooks in `client/src/hooks/useApi.ts` wrap these with React Query (5.x) using 5s polling for status resources.
- `shared/`: Cross‑language schemas/types; keep additions backward compatible.
- `electron/`: Main & preload; ensure any new IPC channels enforce contextIsolation and validate payloads.

## 3. Conventions & Patterns
- Backend route prefixes: always mounted under `/api/<domain>` (see `main.py`). For new groups, add router + prefix + tag. Do not mirror legacy Node path names if Python already diverged.
- Error handling: Raise `HTTPException`; generic exceptions logged and converted by global handler. Keep detailed trace only in development (`NODE_ENV=development`).
- Pydantic models: Provide `json_schema_extra` with an `example` for complex POST bodies (see `PredictRequest`).
- Long operations (backtests, ML) return immediate structured JSON; consider background tasks only if existing pattern emerges (none yet).
- Integration management uses `IntegrationService` async methods; always `await` service APIs in routes (some existing code already async). Maintain idempotency for start/stop.
- Security headers middleware already adds CSP. When adding external scripts/styles, update CSP accordingly.
- React Query keys: structure as `['domain', subKey?]`. Invalidate with exact key object; follow examples in `useApi.ts`.
- Polling intervals: 5000ms for status‑like queries to avoid UI thrash; match existing usage unless strong justification.
- Logging: Use `logging.getLogger(__name__)` in Python modules; don't configure logging again (configured globally in `main.py`).

## 4. Developer Workflows
- Start backend (dev): `npm run dev:fastapi` (reload enabled). Frontend: `npm run dev` (Vite). Electron unified environment: `npm run electron`.
- Build web prod: `npm run build` (Vite + server bundle). Desktop package: `npm run build:electron`.
- Tests (Python): `npm test` invokes `pytest` with coverage for `server_fastapi`. Add new tests under `server_fastapi/tests/` prefixed with `test_*.py`.
- Lint/format Python: `npm run lint:py` / `npm run format:py`.
- Type check TS: `npm run check` (tsc no‑emit). Keep path aliases (`@/*`, `@shared/*`) consistent when moving files.
- Migrations: Alembic via `npm run migrate` / `migrate:create` / `migrate:rollback`.

## 5. Adding New Backend Features
1. Create Pydantic request/response models (with examples) in the route file or a `schemas` module if reused broadly.
2. Inject required services via small dependency functions (see `get_trading_orchestrator`).
3. Validate inputs explicitly (e.g., check required fields, date ordering) before delegating to service.
4. Return plain dict / pydantic model; avoid leaking internal objects.
5. Register router in `main.py` with a unique prefix & tag.
6. Add a minimal pytest covering 200 OK + 1 error scenario.

## 6. Adding/Updating Frontend API Calls
- Add endpoint function in `client/src/lib/api.ts` → wrap with a hook in `hooks/useApi.ts` (include `queryKey` & invalidation on mutation success).
- For streaming or WebSocket features, prefer existing WebSocket infra (see `useWebSocket.ts`) instead of ad‑hoc fetch loops.
- Keep UI state ephemeral; use React Query cache as source of truth for server data.

## 7. Integrations & Adapters
- Python adapters (Freqtrade/Jesse) started/stopped via integration routes under `/api/integrations/*`.
- `integration_service` tracks process status and configurations; do not manipulate processes directly from routes—always use service methods.
- Ensemble operations (predict/backtest) orchestrated by `trading_orchestrator` which calls underlying adapters then merges results.

## 8. Performance & Safety Notes
- Expensive ops (ML, backtesting) should not block event loop—if future scaling needed, consider Celery (celery_app exists) but current code runs inline.
- Redis optional: guard feature usage if `redis_available` is false. Do not assume cache presence.
- Rate limiting (SlowAPI) enabled when limiter import succeeds; keep new endpoints compliant (short, idempotent) to avoid misuse.

## 9. Security Practices
- JWT dependency presently a placeholder; when upgrading, replace with real verification—keep function signature stable so callers need no change.
- Validate user inputs, especially symbols, dates, strategy params to avoid downstream command injection in adapters.
- Never add wide `*` CORS origins; follow `validate_origin` pattern if expanding.

## 10. When Unsure
- Prefer existing Python service patterns over reusing deprecated Node logic.
- Search similar route (e.g., `backtesting.py`) and mirror structure.
- If functionality appears in both legacy and new stacks, treat Python as source of truth unless README states otherwise.

## 11. Example: Minimal New Route
```python
# server_fastapi/routes/example.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class EchoRequest(BaseModel):
    message: str

class EchoResponse(BaseModel):
    echoed: str

@router.post('/echo', response_model=EchoResponse)
async def echo(req: EchoRequest):
    if not req.message.strip():
        raise HTTPException(status_code=400, detail='Message cannot be empty')
    return EchoResponse(echoed=req.message)
```
Register in `main.py`:
```python
from .routes import example as example_router
app.include_router(example_router.router, prefix='/api/example', tags=['Example'])
```

## 12. Keep This File Updated
- Update when: new service layer, auth implementation changes, or Electron↔FastAPI startup logic changes.
- Keep under ~60 lines excluding examples; prune stale references promptly.
