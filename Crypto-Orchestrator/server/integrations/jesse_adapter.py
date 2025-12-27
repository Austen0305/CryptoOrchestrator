#!/usr/bin/env python3
"""
Jesse adapter (offline-first).

This file provides a small async-friendly manager for Jesse-style strategy
testing. It keeps a simple stdin/stdout wrapper for compatibility with the
existing adapters but implements a small `JesseManager` with a mock data
provider for offline development.
"""
import sys
import json
import uuid
import logging
from typing import Dict, Any
from datetime import datetime
import pandas as pd
import numpy as np

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('jesse_adapter')


def _synthetic_candles(limit: int = 100, seed: int = 42) -> pd.DataFrame:
    end = datetime.now()
    dates = pd.date_range(end=end, periods=limit, freq='5T')
    rng = np.random.default_rng(seed=seed)
    base = 50000.0
    steps = rng.normal(0, 50, size=limit)
    close = base + steps.cumsum()
    open_ = np.concatenate(([close[0] - steps[0]], close[:-1]))
    high = np.maximum(open_, close) + np.abs(rng.normal(0, 10, size=limit))
    low = np.minimum(open_, close) - np.abs(rng.normal(0, 10, size=limit))
    volume = np.abs(rng.normal(1.0, 0.5, size=limit)) * 10
    df = pd.DataFrame({'date': dates, 'open': open_, 'high': high, 'low': low, 'close': close, 'volume': volume})
    df.set_index('date', inplace=True)
    return df


class JesseManager:
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._initialized = False

    async def initialize(self):
        self._initialized = True

    async def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            candles = payload.get('marketData')
            if not candles:
                df = _synthetic_candles(100)
            else:
                df = pd.DataFrame(candles)
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)

            df['sma_short'] = df['close'].rolling(window=7, min_periods=1).mean()
            df['sma_long'] = df['close'].rolling(window=21, min_periods=1).mean()
            last = df.iloc[-1]
            prev = df.iloc[-2]
            action = 'hold'
            if prev['sma_short'] <= prev['sma_long'] and last['sma_short'] > last['sma_long']:
                action = 'buy'
            elif prev['sma_short'] >= prev['sma_long'] and last['sma_short'] < last['sma_long']:
                action = 'sell'

            return {'action': action, 'confidence': 0.6 if action != 'hold' else 0.4, 'source': 'jesse'}
        except Exception as e:
            logger.error(f"Jesse prediction error: {e}", exc_info=True)
            return {'action': 'hold', 'confidence': 0.0, 'source': 'jesse', 'error': str(e)}

    async def backtest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            df = _synthetic_candles(200)
            df['sma_short'] = df['close'].rolling(window=7, min_periods=1).mean()
            df['sma_long'] = df['close'].rolling(window=21, min_periods=1).mean()
            df['signal'] = 0
            df.loc[(df['sma_short'] > df['sma_long']), 'signal'] = 1
            df.loc[(df['sma_short'] < df['sma_long']), 'signal'] = -1
            trades = ((df['signal'].shift(1) != df['signal']) & (df['signal'] != 0)).sum()
            profit_pct = np.random.default_rng(seed=1).uniform(-0.05, 0.2)
            return {'trades': int(trades), 'profit_pct': float(profit_pct), 'source': 'jesse'}
        except Exception as e:
            logger.error(f"Jesse backtest error: {e}", exc_info=True)
            return {'trades': 0, 'profit_pct': 0.0, 'source': 'jesse', 'error': str(e)}


def respond(req: Dict[str, Any]):
    action = req.get('action')
    req_id = req.get('id') or str(uuid.uuid4())
    payload = req.get('payload', {})

    try:
        manager = JesseManager()
        # Synchronous wrapper: call predict/backtest via event loop when needed
        import asyncio
        if action == 'predict':
            result = asyncio.get_event_loop().run_until_complete(manager.predict(payload))
        elif action == 'backtest':
            result = asyncio.get_event_loop().run_until_complete(manager.backtest(payload))
        elif action == 'ping':
            result = {'ok': True}
        else:
            result = {'error': f'unknown action {action}'}

        out = {'id': req_id, 'result': result}
    except Exception as e:
        out = {'id': req_id, 'error': str(e)}

    sys.stdout.write(json.dumps(out) + '\n')
    sys.stdout.flush()


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        respond(req)


if __name__ == '__main__':
    main()
