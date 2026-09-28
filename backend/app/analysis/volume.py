from app.schemas.candle import Candle, available
from app.config import ENGINE_CONFIG


def volume(candles: list[Candle], cutoff_timestamp: int) -> dict:
    bars = available(candles, cutoff_timestamp)
    previous = bars[-ENGINE_CONFIG['volume_window']-1:-1]
    average = sum(c.volume for c in previous)/len(previous) if previous else 0
    last = bars[-1]
    ratio = last.volume/average if average else None
    buy = last.taker_buy_base_volume/last.volume if last.volume else None
    bands = ENGINE_CONFIG['volume_bands']
    label = ['very_low','low','normal','high','very_high'][sum(ratio >= b for b in bands)] if ratio is not None else 'unavailable'
    return {'average_volume_20': average, 'volume_ratio': ratio, 'taker_buy_ratio': buy,
            'taker_sell_ratio': 1-buy if buy is not None else None, 'classification': label,
            'source': 'Binance BTCUSDT spot only', 'sample_size': len(previous)}
