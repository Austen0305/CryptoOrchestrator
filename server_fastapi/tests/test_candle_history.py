from fastapi.testclient import TestClient
from server_fastapi.main import app
from server_fastapi.database import async_session, init_database
from sqlalchemy import delete
from server_fastapi.models.candle import Candle
import asyncio

client = TestClient(app)

async def seed():
    await init_database()
    async with async_session() as session:
        # Make test idempotent: clear any pre-existing rows for this symbol/timeframe
        await session.execute(
            delete(Candle).where(Candle.symbol == 'BTC/USD', Candle.timeframe == '1m')
        )
        session.add_all([
            Candle(symbol='BTC/USD', timeframe='1m', ts=1700000000000, open=100, high=110, low=90, close=105, volume=1),
            Candle(symbol='BTC/USD', timeframe='1m', ts=1700000060000, open=105, high=115, low=95, close=110, volume=2),
        ])
        await session.commit()


def test_history_seed_then_fetch():
    # seed first (ensures tables exist and data present)
    asyncio.get_event_loop().run_until_complete(seed())
    resp = client.get('/api/markets/BTC/USD/history?timeframe=1m&limit=10')
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data['pair'] == 'BTC/USD'
    assert data['timeframe'] == '1m'
    assert len(data['candles']) >= 2
    assert data['candles'][0]['ts'] < data['candles'][-1]['ts']
