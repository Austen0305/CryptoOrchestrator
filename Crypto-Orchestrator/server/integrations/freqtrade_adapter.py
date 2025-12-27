#!/usr/bin/env python3
"""
Freqtrade adapter using the actual Freqtrade framework.

Reads newline-delimited JSON from stdin and writes JSON responses to stdout.
Requires Freqtrade to be installed: pip install freqtrade
"""
import sys
import json
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime, timedelta

# Freqtrade imports
try:
    from freqtrade.configuration import Configuration
    from freqtrade.data.history import load_pair_history
    from freqtrade.resolvers import StrategyResolver
    from freqtrade.optimize.backtesting import Backtesting
    from freqtrade.data.dataprovider import DataProvider
    from freqtrade.exchange import Exchange
    from freqtrade.exceptions import OperationalException
    freqtrade_available = True
except ImportError:
    # Provide light-weight stand ins so tests can still import this module
    freqtrade_available = False
    class Configuration:  # type: ignore
        @classmethod
        def from_files(cls, files):
            return {}
    class StrategyResolver:  # type: ignore
        @staticmethod
        def load_strategy(config):
            class DummyStrategy:
                def populate_indicators(self, df, meta): return df
                def populate_buy_trend(self, df, meta): df['buy'] = 0; return df
                def populate_sell_trend(self, df, meta): df['sell'] = 0; return df
                def advise_all_indicators(self, data): return data
            return DummyStrategy()
    class Backtesting:  # type: ignore
        def __init__(self, config): self.config = config
        def load_bt_data(self, symbols, timeframe='5m', timerange=None): return {}
        def backtest(self, processed, start_date=None, end_date=None, timerange=None): return []
        def generate_trading_stats(self, results): return {'profit_total_pct': 0.0}
    class DataProvider:  # type: ignore
        def __init__(self, config, exchange): self.config = config; self.exchange = exchange
        def ohlcv_to_dataframe(self, market_data):
            import pandas as _pd
            if not market_data:
                return _pd.DataFrame({'open':[], 'high':[], 'low':[], 'close':[], 'volume':[]})
            return _pd.DataFrame(market_data)
    class Exchange:  # type: ignore
        def __init__(self, config): self.config = config
    class OperationalException(Exception): pass
import pandas as pd
import numpy as np


def get_default_config() -> dict:
    """Return a minimal default configuration dict used by the adapter.

    The configuration is intentionally small and contains sane defaults for
    offline development. Users can enable live mode by setting
    `exchange.mode` to 'live' and providing API credentials under
    `exchange.ccxt_config` / `exchange.ccxt_async_config`.
    """
    import os

    cfg = {
        'stake_currency': 'USDT',
        'dry_run': True,
        'dry_run_wallet': 1000.0,
        'timeframe': '5m',
        'startup_candle_count': 100,
        'exchange': {
            # mode: 'mock' | 'live'
            'mode': 'mock',
            'name': os.environ.get('FREQTRADE_EXCHANGE_NAME', 'binance'),
            'pair_whitelist': ['BTC/USDT'],
            'ccxt_config': {
                'key': os.environ.get('FREQTRADE_API_KEY', ''),
                'secret': os.environ.get('FREQTRADE_API_SECRET', ''),
            },
            'ccxt_async_config': {},
        },
        'entry_pricing': {'order_adjustment': 0.0},
        'exit_pricing': {'order_adjustment': 0.0},
    }

    # Allow overriding mode via env var
    mode = os.environ.get('FREQTRADE_EXCHANGE_MODE')
    if mode in ('live', 'mock'):
        cfg['exchange']['mode'] = mode

    return cfg

# Patch Exchange class to use pure async initialization
class AsyncExchange(Exchange):
    def __init__(self, config):
        # Initialize base attributes without calling parent constructor
        self._config = config
        self._api = None
        self._api_async = None
        self._markets = {}
        self._trading_fees = {}
        self._markets_initialized = False
        # some freqtrade internals expect these attributes to exist
        self._exchange_ws = None
        self._ws_async = None
        # freqtrade Exchange destructor checks the event loop
        self.loop = None
        self._stake_currency = config['stake_currency']
        self._pair_whitelist = config.get('exchange', {}).get('pair_whitelist', [])
        self._dry_run = config.get('dry_run', True)
        self._log = logging.getLogger(__name__)

    def _init_ccxt(self, exchange_config: dict, load_leverage_tiers: bool = False, ccxt_kwargs: dict = None) -> Any:
        """Initialize CCXT with given config.

        Args:
            exchange_config: Exchange configuration in config
            load_leverage_tiers: Fetch leverage tier data
            ccxt_kwargs: Additional ccxt parameters
        """
        # Use default initialization from parent
        return super()._init_ccxt(exchange_config, load_leverage_tiers, ccxt_kwargs)

    def _init_ccxt_async(self, exchange_config: dict, ccxt_async_kwargs: dict = None) -> Any:
        """Initialize async CCXT with given config.

        Args:
            exchange_config: Exchange configuration in config
            ccxt_async_kwargs: Additional async ccxt parameters
        """
        import ccxt.async_support
        name = exchange_config['name']

        # Find matching exchange in CCXT
        try:
            api_async = getattr(ccxt.async_support, name.lower())
        except AttributeError:
            raise OperationalException(f'Exchange {name} is not supported by ccxt')

        # Create instance of async CCXT class
        instance = api_async(ccxt_async_kwargs or {})

        # Configure CCXT instance
        if exchange_config.get('key') and exchange_config.get('secret'):
            instance.apiKey = exchange_config['key']
            instance.secret = exchange_config['secret']

        # Configure additional settings
        if exchange_config.get('password'):
            instance.password = exchange_config['password']
            
        if exchange_config.get('uid'):
            instance.uid = exchange_config['uid']

        if self._dry_run:
            instance.set_sandbox_mode(True)
            
        return instance

    def reload_markets(self, force: bool = False, load_leverage_tiers: bool = False) -> None:
        """Override to skip market loading until async init."""
        pass

    def validate_stakecurrency(self, stake_currency: str) -> None:
        """Override to skip market validation until async init."""
        self._stake_currency = stake_currency

    async def initialize(self):
        """Async initialization."""
        if not self._markets_initialized:
            exchange_conf = self._config.get('exchange', {})
            ccxt_config = exchange_conf.get('ccxt_config', {})
            ccxt_async_config = exchange_conf.get('ccxt_async_config', {})
            
            # Initialize CCXT instance
            self._api = self._init_ccxt(exchange_conf, False, ccxt_config)
            
            # Initialize async CCXT instance
            self._api_async = self._init_ccxt_async(exchange_conf, ccxt_async_config)
            
            # Load markets asynchronously
            await self._api_async.load_markets()
            self._markets = self._api_async.markets
            self._markets_initialized = True


# Lightweight offline/mock exchange for local development and testing
class MockExchange:
    """A minimal exchange replacement that doesn't call external APIs.

    Provides async initialize and get_candle_history that returns a pandas
    DataFrame of synthetic OHLCV candles for local backtesting and strategy
    evaluation.
    """
    def __init__(self, config):
        self._config = config
        self._markets_initialized = False
        self._stake_currency = config.get('stake_currency', 'USD')

    async def initialize(self):
        # No network calls; just mark as initialized
        self._markets_initialized = True

    async def get_candle_history(self, pair: str, timeframe: str = '5m', limit: int = 100, timerange: str = None):
        """Return synthetic OHLCV data as a pandas DataFrame.

        Args:
            pair: trading pair string (unused but kept for compatibility)
            timeframe: timeframe string, only '5m' currently used
            limit: number of candles to generate
            timerange: custom timerange string (e.g., '20250101-20250131')

        Returns:
            pandas.DataFrame with columns [open, high, low, close, volume]
        """
        # Handle custom timerange
        end = datetime.now()
        if timerange:
            try:
                # Parse timerange format: YYYYMMDD-YYYYMMDD
                start_str, end_str = timerange.split('-')
                start_date = datetime.strptime(start_str, '%Y%m%d')
                end_date = datetime.strptime(end_str, '%Y%m%d')
                end = end_date
                # Calculate limit based on timerange
                time_diff = end_date - start_date
                total_minutes = int(time_diff.total_seconds() / 60)
                if timeframe == '5m':
                    calculated_limit = total_minutes // 5
                    limit = min(limit, calculated_limit) if calculated_limit > 0 else limit
            except (ValueError, AttributeError):
                logger.warning(f"Invalid timerange format: {timerange}, using default")

        # Create a datetime index ending at specified time, spaced by timeframe
        freq = '5T' if timeframe == '5m' else '5T'  # Default to 5m
        dates = pd.date_range(end=end, periods=limit, freq=freq)

        # Simple random walk around a base price
        base = 50000.0
        rng = np.random.default_rng(seed=42)
        steps = rng.normal(loc=0.0, scale=50.0, size=limit)
        close = base + np.cumsum(steps)
        open_ = np.concatenate(([close[0] - steps[0]], close[:-1]))
        high = np.maximum(open_, close) + np.abs(rng.normal(0, 10, size=limit))
        low = np.minimum(open_, close) - np.abs(rng.normal(0, 10, size=limit))
        volume = np.abs(rng.normal(loc=1.0, scale=0.5, size=limit)) * 10

        df = pd.DataFrame({
            'date': dates,
            'open': open_,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
        df.set_index('date', inplace=True)
        return df

# Patch backtesting class to avoid event loop issues
class AsyncBacktesting(Backtesting):
    def __init__(self, config):
        self.config = config
        self.exchange = AsyncExchange(config)
        self.strategy = None
        self.results = None
        self.trade_id_counter = None
        
        # Initialize required attributes
        self.timeframe = config.get('timeframe', '5m')
        self.timeframe_min = 5  # 5 minute timeframe
        self.timeframe_ms = self.timeframe_min * 60 * 1000
        self.required_startup = config.get('startup_candle_count', 0)
        self.timerange = None
        self.trading_mode = 'spot'
        self.position_stacking = False
        self.start_date = datetime(2025, 1, 1)
        self.end_date = datetime.now()
        
        # Initialize dataprovider
        self.dataprovider = DataProvider(config, self.exchange)
        
        # Initialize strategy
        self.strategy = StrategyResolver.load_strategy(config)
        
        # Initialize backtest
        self.init_backtest()

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('freqtrade_adapter')

class FreqtradeManager:
    def __init__(self):
        logger.info("Initializing FreqtradeManager")
        config = get_default_config()
        # Load freqtrade Configuration wrapper if available, else operate against raw dict
        if freqtrade_available:
            try:
                self.config = Configuration.from_files([])
                # Some freqtrade configs behave like dict; guard update
                try:
                    self.config.update(config)
                except Exception:
                    pass
            except Exception:
                self.config = config
        else:
            self.config = config

        # Initialize components
        # StrategyResolver expects the freqtrade configuration object; try to load safely
        try:
            self.strategy = StrategyResolver.load_strategy(self.config)
        except Exception:
            logger.warning("StrategyResolver.load_strategy failed at init; using dummy strategy")
            self.strategy = StrategyResolver.load_strategy({})

        # Exchange selection: choose based on config.exchange.mode (mock | live)
        mode = None
        try:
            mode = (self.config.get('exchange') or {}).get('mode', 'mock')
        except Exception:
            mode = 'mock'

        if mode == 'live':
            logger.info("Configured exchange.mode=live; assigning AsyncExchange (initialization deferred)")
            self.exchange = AsyncExchange(self.config)
        else:
            logger.info("Configured exchange.mode=mock; assigning MockExchange")
            self.exchange = MockExchange(self.config)

        self.dataprovider = DataProvider(self.config, self.exchange)
        logger.info("DataProvider initialized")

        # Initialize backtesting helper (it will use the configured exchange)
        try:
            self.backtesting = AsyncBacktesting(self.config)
            logger.info("AsyncBacktesting initialized")
        except Exception:
            logger.warning("AsyncBacktesting initialization failed; backtest APIs may be unavailable")
            self.backtesting = None

        # Create user_data directory structure
        Path("user_data/strategies").mkdir(parents=True, exist_ok=True)
        
    async def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Get prediction for current market data."""
        try:
            symbol = payload.get('symbol', 'BTC/USD')
            market_data = payload.get('marketData', [])
            
            # Get recent candles from exchange if no data provided
            if not market_data:
                candles = await self.exchange.get_candle_history(
                    symbol,
                    timeframe='5m',
                    limit=100
                )
            else:
                # Convert provided market data to dataframe
                candles = self.dataprovider.ohlcv_to_dataframe(market_data)
            
            # Run strategy using freqtrade style interface
            # Strategy implements populate_indicators / populate_buy_trend / populate_sell_trend
            meta = { 'pair': symbol }
            candles = self.strategy.populate_indicators(candles, meta)
            candles = self.strategy.populate_buy_trend(candles, meta)
            candles = self.strategy.populate_sell_trend(candles, meta)
            if candles.empty:
                return {'action': 'hold', 'confidence': 0.0, 'source': 'freqtrade', 'signals': {'buy': False, 'sell': False}}

            last = candles.iloc[-1]
            # Handle NaN values in buy/sell columns
            buy_signal = False
            sell_signal = False
            if 'buy' in last.index:
                val = last.get('buy', 0)
                if not pd.isna(val) and val:
                    try:
                        buy_signal = bool(int(val))
                    except Exception:
                        buy_signal = bool(val)
            if 'sell' in last.index:
                val = last.get('sell', 0)
                if not pd.isna(val) and val:
                    try:
                        sell_signal = bool(int(val))
                    except Exception:
                        sell_signal = bool(val)
            signals = {'buy': buy_signal, 'sell': sell_signal}

            # Map signals to action/confidence
            if buy_signal:
                action = 'buy'
                confidence = 0.7
            elif sell_signal:
                action = 'sell'
                confidence = 0.7
            else:
                action = 'hold'
                confidence = 0.5
                
            return {
                'action': action,
                'confidence': confidence,
                'source': 'freqtrade',
                'signals': signals
            }
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}", exc_info=True)
            return {
                'action': 'hold',
                'confidence': 0,
                'source': 'freqtrade',
                'error': str(e)
            }

    async def backtest(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Run backtest on historical data."""
        try:
            symbol = payload.get('symbol', 'BTC/USD')

            # Enhanced custom timerange support
            timerange = payload.get('timerange')
            if timerange:
                # Use provided timerange directly
                pass
            else:
                # Create timerange from start/end dates or use defaults
                start_date = datetime.fromisoformat(payload.get('startDate', '2025-01-01'))
                end_date = datetime.fromisoformat(payload.get('endDate', '2025-10-31'))
                timerange = f"{start_date.strftime('%Y%m%d')}-{end_date.strftime('%Y%m%d')}"

            # Load candle data with custom timerange
            if not self.backtesting:
                return {'trades': 0, 'profit_pct': 0.0, 'source': 'freqtrade', 'error': 'backtesting unavailable'}
            data = self.backtesting.load_bt_data(
                [symbol],
                timeframe='5m',
                timerange=timerange
            )

            # Run backtest with proper timerange handling
            results = self.backtesting.backtest(
                processed=self.strategy.advise_all_indicators(data),
                start_date=start_date,
                end_date=end_date,
                timerange=timerange
            )

            stats = self.backtesting.generate_trading_stats(results)

            return {
                'trades': len(results),
                'profit_pct': float(stats['profit_total_pct']),
                'source': 'freqtrade',
                'stats': stats,
                'timerange': timerange
            }

        except Exception as e:
            logger.error(f"Backtest error: {str(e)}", exc_info=True)
            return {
                'trades': 0,
                'profit_pct': 0,
                'source': 'freqtrade',
                'error': str(e)
            }

# Global manager instance
manager: Optional[FreqtradeManager] = None

async def respond(req: Dict[str, Any]):
    """Process a single request."""
    global manager
    
    action = req.get('action')
    req_id = req.get('id') or str(uuid.uuid4())
    payload = req.get('payload', {})
    out = {}

    try:
        # Initialize manager on first request
        if manager is None:
            manager = FreqtradeManager()
            # Try to initialize the configured exchange; if live init fails, fall back to mock
            try:
                await manager.exchange.initialize()
            except Exception as e:
                logger.error(f"Exchange initialization failed: {e}", exc_info=True)
                # If we were attempting a live exchange, fall back to mock
                try:
                    # Replace with MockExchange and initialize
                    manager.exchange = MockExchange(manager.config)
                    await manager.exchange.initialize()
                    manager.dataprovider = DataProvider(manager.config, manager.exchange)
                    logger.info("Fell back to MockExchange after live-init failure")
                except Exception as e2:
                    logger.error(f"Fallback to MockExchange failed: {e2}", exc_info=True)
                    raise
            
        result = None
        if action == 'predict':
            result = await manager.predict(payload)
        elif action == 'backtest':
            result = await manager.backtest(payload)
        elif action == 'ping':
            result = {'ok': True}
        else:
            result = {'error': f'unknown action {action}'}

        out = {'id': req_id, 'result': result}
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        out = {'id': req_id, 'error': str(e)}
    finally:
        sys.stdout.write(json.dumps(out) + '\n')
        sys.stdout.flush()

async def main():
    """Main loop reading from stdin."""
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
                
            line = line.strip()
            if not line:
                continue
                
            try:
                req = json.loads(line)
                await respond(req)
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON: {line}")
                continue
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            logger.error(f"Main loop error: {str(e)}", exc_info=True)
            continue

async def create_exchange(config):
    """Create and initialize exchange instance."""
    exchange = Exchange(config)
    await exchange._api_reload_markets(reload=True)
    return exchange

def get_default_config():
    return {
        "max_open_trades": 3,
        "stake_currency": "USDT",
        "stake_amount": 100,
        "dry_run": True,
        "dry_run_wallet": 1000,  # Initial wallet balance for backtesting
        "db_url": "sqlite:///",
        "strategy": "SimpleStrategy",  # our custom strategy
        "strategy_path": "./user_data/strategies/",
        "timeframe": "5m",  # explicitly set timeframe
        "startup_candle_count": 30,  # number of candles to warm up indicators
        "exit_pricing": {
            "use_order_book": False,
            "order_book_top": 1,
            "check_depth_of_market": {
                "enabled": False,
                "bids_to_ask_delta": 1
            }
        },
        "entry_pricing": {
            "use_order_book": False,
            "order_book_top": 1,
            "check_depth_of_market": {
                "enabled": False,
                "bids_to_ask_delta": 1
            }
        },
        "exchange": {
            "name": "binanceus",
            "key": "",
            "secret": "",
            "ccxt_config": {
                "enableRateLimit": True,
                "urls": {
                    "api": {
                        "public": "https://api.binance.us/api/v3",
                        "private": "https://api.binance.us/api/v3",
                        "web": "https://www.binance.us"
                    }
                }
            },
            "ccxt_async_config": {
                "enableRateLimit": True,
                "urls": {
                    "api": {
                        "public": "https://api.binance.us/api/v3",
                        "private": "https://api.binance.us/api/v3",
                        "web": "https://www.binance.us"
                    }
                }
            },
            "pair_whitelist": ["BTC/USDT"]  # Use USDT pairs on BinanceUS
        }
    }


if __name__ == '__main__':
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()