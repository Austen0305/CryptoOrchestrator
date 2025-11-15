# 🔌 Real-Time Features Guide

This document explains the live data architecture now powering CryptoOrchestrator.

## Endpoints (FastAPI `server_fastapi/routes/ws.py`)

| Endpoint | Purpose | Auth | Message Types |
|----------|---------|------|---------------|
| `/ws/market-data` | Live ticks, market updates | Required (JWT) | `auth_success`, `market_data`, `error` |
| `/ws/bot-status` | Bot lifecycle/status updates | Required | `auth_success`, `bot_status`, `pong`, `error` |
| `/ws/notifications` | Push user notifications | Required | `auth_success`, `notification`, `initial_notifications`, `error` |
| `/ws/performance-metrics` | Backend performance snapshot + ping RTT | Required | `auth_success`, `metrics`, `pong`, `error` |

All endpoints expect an initial JSON auth message:

```json
{ "type": "auth", "token": "<jwt>" }
```

If auth fails, the server responds with `{ "error": "Authentication required" }` then closes.

## Client Hooks Overview

| Hook | File | Responsibility |
|------|------|----------------|
| `useWebSocket` | `client/src/hooks/useWebSocket.ts` | Core market socket, symbol subscriptions, query invalidations, provides latest market map. |
| `useBotStatus` | `client/src/hooks/useBotStatus.ts` | Tracks per-bot statuses & running count via `/ws/bot-status`. |
| `useNotifications` | `client/src/hooks/useNotifications.ts` | Push notification ingestion (falls back to polling). |
| `PerformanceMonitor` | `client/src/components/PerformanceMonitor.tsx` | Connects to performance metrics WS and displays FPS, memory, RTT, backend metrics. |

## Live Price Chart

`PriceChart` subscribes to its `pair` via `useWebSocket.subscribeSymbols()`. Incoming ticks update a rolling in-memory series (max 300 points) for smooth real-time plotting.

Fallback: When disconnected, it displays last known static data. Reconnection auto-resubscribes.

## Offline & Reconnect UX

`OfflineBanner` shows when:

1. Browser `navigator.onLine` is false (offline).
2. WebSocket is disconnected (attempting reconnection).

Provides one-click refresh.

## Design Principles

1. Stateless reconnection: hooks re-authenticate with stored JWT automatically.
2. Bounded memory: live series limited to recent points.
3. Query invalidation: market & bot updates trigger React Query cache refresh for dependent components.
4. Graceful degradation: polling continues for notifications if live channel unavailable.
5. Security: no wide-open unauthenticated streams; token required for all user-specific channels.

## Extending Real-Time Streaming

To add a new channel:

1. Create a WebSocket endpoint in `ws.py` with auth handshake.
2. Emit `auth_success` first, then domain-specific messages.
3. Add a dedicated hook (or extend `useWebSocket` if domain overlaps markets).
4. Surface minimal connection state (`isConnected` + domain map).
5. Update docs & add a fast unit test for JWT decode path.

## Testing Notes

Unit tests validate JWT handling (`test_ws_auth.py`). Full handshake & streaming validated in integration/E2E environments (skipped in CI for speed).

## Future Enhancements

- Batched tick compression for high-frequency pairs.
- Historical gap fill after reconnect (request missing candles).
- Server-side alert push for threshold breaches.

## Client-Side Throttling (Implemented)

When the browser tab is hidden, market query invalidations are throttled to reduce churn and CPU usage. The UI still shows latest prices from the in-memory cache but refreshes React Query at a lower rate. When the tab becomes visible, invalidations resume at a higher cadence for responsiveness.

## Backfill (Implemented)

After a reconnect, the client sends a `backfill_request` message including subscribed symbols and the timestamp of last received tick:

```json
{ "type": "backfill_request", "symbols": ["BTC/USD"], "since": 1731283200000 }
```

Server responds with a batched array:

```json
{ "type": "backfill", "symbol": "BTC/USD", "candles": [ [ts, open, high, low, close, volume], ... ] }
```

The client merges missing candles and updates the chart series, then resumes live streaming with visibility-aware throttling.

---
Real-time architecture now provides a foundation for truly responsive trading experiences.
