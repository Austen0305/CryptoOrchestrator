import asyncio
import pytest

try:
    from ..jesse_adapter import JesseManager, respond
    jesse_available = True
except ImportError:
    jesse_available = False
    JesseManager = None
    respond = None

pytestmark = []
if not jesse_available:
    pytestmark.append(pytest.mark.skip(reason="jesse adapter unavailable; skipping tests"))


@pytest.mark.asyncio
async def test_jesse_predict():
    mgr = JesseManager()
    await mgr.initialize()
    res = await mgr.predict({'symbol': 'BTC/USDT'})
    assert isinstance(res, dict)
    assert res['source'] == 'jesse'


def test_jesse_respond_ping(capsys):
    # respond is synchronous (it handles async internally), so just call it
    req = {'action': 'ping', 'id': 'ping2'}
    respond(req)
    out = capsys.readouterr().out
    assert 'ping2' in out
