import asyncio
import time
import httpx
from app.config import settings, INTERVAL_MS, ENGINE_CONFIG
from app.schemas.candle import Candle
from app.logging.events import event


def normalize(raw: list, cutoff_timestamp: int) -> Candle:
    if len(raw)<11: raise ValueError('Incomplete Binance kline')
    return Candle(timestamp=int(raw[0]),open=float(raw[1]),high=float(raw[2]),low=float(raw[3]),close=float(raw[4]),
                  volume=float(raw[5]),close_timestamp=int(raw[6]),quote_volume=float(raw[7]),trades=int(raw[8]),
                  taker_buy_base_volume=float(raw[9]),taker_buy_quote_volume=float(raw[10]),closed=int(raw[6])<=cutoff_timestamp)


class BinanceProvider:
    def __init__(self):
        self.cache={}
        self.locks={tf:asyncio.Lock() for tf in INTERVAL_MS}
        self.last_error=None
        self.last_fetch=None
        self.failures={}

    async def fetch(self,timeframe: str,refresh=False) -> dict:
        if timeframe not in INTERVAL_MS: raise ValueError('Unsupported timeframe')
        async with self.locks[timeframe]:
            cached=self.cache.get(timeframe)
            if not refresh and cached and time.time()*1000-cached['fetched_at']<ENGINE_CONFIG['cache_ttl_ms']:
                return cached
            started=time.perf_counter()
            event('binance_fetch_started','binance',timeframe=timeframe)
            try:
                async with httpx.AsyncClient(base_url=settings.binance_base_url,timeout=12,follow_redirects=False) as client:
                    for attempt in range(2):
                        response=await client.get('/api/v3/klines',params={'symbol':'BTCUSDT','interval':timeframe,'limit':300 if timeframe=='1w' else 500})
                        if response.status_code<500 or attempt==1: break
                        await asyncio.sleep(.3)
                    response.raise_for_status()
                    raw=response.json()
                now=int(time.time()*1000)
                candles=[normalize(row,now) for row in raw]
                if not candles or len({c.timestamp for c in candles})!=len(candles): raise ValueError('Empty or duplicate candles')
                candles.sort(key=lambda c:c.timestamp)
                if any(b.timestamp-a.timestamp!=INTERVAL_MS[timeframe] for a,b in zip(candles,candles[1:])): raise ValueError('Missing candle intervals')
                if now-candles[-1].timestamp>INTERVAL_MS[timeframe]+ENGINE_CONFIG['freshness_grace_ms']: raise ValueError('Stale Binance data')
                snapshot={'timeframe':timeframe,'raw':raw,'candles':[c.model_dump() for c in candles],'fetched_at':now,'source':'Binance public spot','status':'LIVE'}
                self.cache[timeframe]=snapshot
                self.last_fetch=now
                self.failures.pop(timeframe,None)
                self.last_error=next(iter(self.failures.values()),None)
                event('candle_normalized','binance',timeframe=timeframe,count=len(candles))
                event('binance_fetch_completed','binance',duration_ms=(time.perf_counter()-started)*1000,timeframe=timeframe,count=len(candles))
                return snapshot
            except (httpx.HTTPError,ValueError,TypeError,IndexError) as exc:
                self.last_error=type(exc).__name__
                self.failures[timeframe]=self.last_error
                self.cache.pop(timeframe,None)
                event('binance_fetch_failed','binance',level='ERROR',timeframe=timeframe,error=self.last_error)
                raise ValueError('MARKET DATA UNAVAILABLE') from exc


provider=BinanceProvider()
