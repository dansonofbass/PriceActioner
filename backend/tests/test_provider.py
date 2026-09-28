import asyncio
import httpx
import pytest
from app.providers.binance import BinanceProvider
from app.config import INTERVAL_MS


def setup_transport(monkeypatch,handler,now):
    original=httpx.AsyncClient
    transport=httpx.MockTransport(handler)
    monkeypatch.setattr('app.providers.binance.httpx.AsyncClient',lambda **kwargs:original(transport=transport,**kwargs))
    monkeypatch.setattr('app.providers.binance.time.time',lambda:now/1000)
    monkeypatch.setattr('app.providers.binance.event',lambda *args,**kwargs:None)


def klines():
    step=INTERVAL_MS['15m']
    return [[i*step,'100','110','90','105','10',(i+1)*step-1,'1050',42,'6','630','0'] for i in range(4)]


def test_provider_public_only_normalization_and_cache(monkeypatch):
    calls=[]
    def handler(request):
        calls.append(request)
        assert request.method=='GET'
        assert request.url.host=='data-api.binance.vision'
        assert request.url.path=='/api/v3/klines'
        assert request.url.params['symbol']=='BTCUSDT'
        assert 'authorization' not in request.headers and 'x-mbx-apikey' not in request.headers
        return httpx.Response(200,json=klines())
    setup_transport(monkeypatch,handler,3*INTERVAL_MS['15m']+100)
    async def run():
        provider=BinanceProvider()
        first=await provider.fetch('15m')
        second=await provider.fetch('15m')
        assert first==second and len(calls)==1
        assert first['candles'][-1]['closed'] is False
        assert first['candles'][-2]['closed'] is True
        assert first['raw']==klines()
    asyncio.run(run())


def test_provider_failure_does_not_serve_cached_data(monkeypatch):
    failed=False
    def handler(request):return httpx.Response(403 if failed else 200,json={} if failed else klines())
    setup_transport(monkeypatch,handler,3*INTERVAL_MS['15m']+100)
    async def run():
        nonlocal failed
        provider=BinanceProvider()
        await provider.fetch('15m')
        failed=True
        with pytest.raises(ValueError,match='MARKET DATA UNAVAILABLE'):await provider.fetch('15m',refresh=True)
        assert '15m' not in provider.cache and provider.failures['15m']
        with pytest.raises(ValueError):await provider.fetch('15m')
    asyncio.run(run())


@pytest.mark.parametrize('case',['duplicate','gap','stale','invalid'])
def test_provider_rejects_bad_data(monkeypatch,case):
    rows=klines();now=3*INTERVAL_MS['15m']+100
    if case=='duplicate':rows.append(rows[-1])
    if case=='gap':rows.pop(1)
    if case=='stale':now=10*INTERVAL_MS['15m']
    if case=='invalid':rows[-1][2]='50'
    setup_transport(monkeypatch,lambda request:httpx.Response(200,json=rows),now)
    with pytest.raises(ValueError,match='MARKET DATA UNAVAILABLE'):asyncio.run(BinanceProvider().fetch('15m'))
