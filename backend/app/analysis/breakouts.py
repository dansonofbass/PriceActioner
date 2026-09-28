from app.schemas.candle import Candle, available
from app.config import ENGINE_CONFIG
from .volume import volume


def breakouts(candles: list[Candle], cutoff_timestamp: int, prior_zones: list[dict]) -> dict:
    bars = available(candles, cutoff_timestamp)
    current, previous = bars[-1], bars[-2]
    events = []
    for z in prior_zones:
        if z['zone_type'] == 'resistance':
            if previous.close <= z['high'] < current.close:
                events.append({'event':'breakout','level':z['high']})
            elif previous.close > z['high'] and current.close < z['low']:
                events.append({'event':'failed_breakout','level':z['high']})
            elif current.high >= z['low'] and current.close < z['low']:
                events.append({'event':'resistance_rejection','level':z['low']})
        else:
            if previous.close >= z['low'] > current.close:
                events.append({'event':'breakdown','level':z['low']})
            elif previous.close < z['low'] and current.close > z['high']:
                events.append({'event':'failed_breakdown','level':z['low']})
            elif current.low <= z['high'] and current.close > z['high']:
                events.append({'event':'support_rejection','level':z['high']})
    ratio = volume(bars,cutoff_timestamp)['volume_ratio']
    return {'events': events, 'price_breakout': any(e['event']=='breakout' for e in events),
            'price_breakdown': any(e['event']=='breakdown' for e in events),
            'volume_confirmed': ratio is not None and ratio >= ENGINE_CONFIG['volume_threshold'],
            'volume_ratio': ratio, 'confirmation': 'closed candle', 'zone_source': 'zones known before previous candle'}
