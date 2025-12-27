import asyncio
import json
import sys
try:
    from .freqtrade_adapter import FreqtradeManager, MockExchange, freqtrade_available
except Exception:
    FreqtradeManager = None
    MockExchange = None
    freqtrade_available = False
try:
    from .jesse_adapter import JesseManager
except Exception:
    JesseManager = None


async def run():
    print('Starting smoke tests...')
    # FreqtradeManager predict (mock)
    if not freqtrade_available or not FreqtradeManager or not MockExchange:
        print(json.dumps({"skipped_freqtrade": True, "reason": "freqtrade missing"}))
    else:
        mgr = FreqtradeManager()
        mgr.exchange = MockExchange(mgr.config)
        await mgr.exchange.initialize()
        res = await mgr.predict({'symbol': 'BTC/USDT'})
        print('Freqtrade predict ->', json.dumps(res))

    if not JesseManager:
        print(json.dumps({"skipped_jesse": True, "reason": "jesse missing"}))
    else:
        jmgr = JesseManager()
        await jmgr.initialize()
        jres = await jmgr.predict({'symbol': 'BTC/USDT'})
        print('Jesse predict ->', json.dumps(jres))


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(run())
