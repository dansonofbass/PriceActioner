from app.schemas.candle import Candle, available


def pivots(candles: list[Candle], cutoff_timestamp: int, left: int = 5, right: int = 5) -> list[dict]:
    bars = available(candles, cutoff_timestamp)
    result = []
    for i in range(left, len(bars)-right):
        neighbors = bars[i-left:i] + bars[i+1:i+right+1]
        for kind, price in [('high', bars[i].high), ('low', bars[i].low)]:
            is_pivot = all(price > c.high for c in neighbors) if kind == 'high' else all(price < c.low for c in neighbors)
            if is_pivot:
                result.append({'kind': kind, 'price': price, 'timestamp': bars[i].timestamp,
                               'confirmed_at': bars[i+right].close_timestamp, 'index': i})
    return result


def classic_pivots(candles: list[Candle], cutoff_timestamp: int) -> dict:
    bars = available(candles, cutoff_timestamp)
    if not bars:
        return {}
    c = bars[-1]  # last completed period, never current open period
    p = (c.high+c.low+c.close)/3
    return {'P': p, 'R1': 2*p-c.low, 'S1': 2*p-c.high, 'R2': p+c.high-c.low,
            'S2': p-c.high+c.low, 'source_close_timestamp': c.close_timestamp}
