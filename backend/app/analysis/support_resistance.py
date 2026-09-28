from app.schemas.candle import Candle, available
from app.config import ENGINE_CONFIG


def zones(candles: list[Candle], cutoff_timestamp: int, points: list[dict], atr: float, timeframe: str) -> list[dict]:
    bars = available(candles, cutoff_timestamp)
    tolerance = atr * ENGINE_CONFIG['atr_cluster_multiplier']
    result = []
    for kind, zone_type in [('low', 'support'), ('high', 'resistance')]:
        clusters = []
        for p in sorted((p for p in points if p['kind'] == kind and p['confirmed_at'] <= cutoff_timestamp), key=lambda p: p['price']):
            if clusters and p['price'] - clusters[-1][0]['price'] <= tolerance:
                clusters[-1].append(p)
            else:
                clusters.append([p])
        for cluster in clusters:
            low, high = min(p['price'] for p in cluster)-tolerance/2, max(p['price'] for p in cluster)+tolerance/2
            hits = [(i,c) for i,c in enumerate(bars) if c.low <= high and c.high >= low and c.timestamp >= min(p['timestamp'] for p in cluster)]
            # Consecutive bars inside a zone are a single touch episode.
            episodes = [(i,c) for n,(i,c) in enumerate(hits) if n == 0 or i > hits[n-1][0]+1]
            last_index = hits[-1][0] if hits else 0
            rejection = max((max(0, c.close-low) if kind == 'low' else max(0, high-c.close) for _,c in hits), default=0)
            window = ENGINE_CONFIG['volume_window']
            average = sum(c.volume for c in bars[-window:])/min(window,len(bars))
            touch_volume = sum(c.volume for _,c in hits)/len(hits) if hits else 0
            w = ENGINE_CONFIG['zone_weights']
            breakdown = {'touch_score': min(1,len(episodes)/ENGINE_CONFIG['zone_touch_cap'])*w['touch_score'],
                         'recency_score': max(0,1-(len(bars)-1-last_index)/ENGINE_CONFIG['recency_bars'])*w['recency_score'],
                         'rejection_score': min(1,rejection/(atr*ENGINE_CONFIG['rejection_atr_cap']))*w['rejection_score'] if atr else 0,
                         'higher_tf_score': 0,
                         'volume_score': min(1,touch_volume/(average*ENGINE_CONFIG['volume_threshold']))*w['volume_score'] if average else 0}
            breakdown = {k:round(v,3) for k,v in breakdown.items()}
            result.append({'zone_type': zone_type, 'low': low, 'high': high, 'midpoint': (low+high)/2,
                           'touches': len(episodes), 'last_touch_timestamp': hits[-1][1].timestamp if hits else None,
                           'pivot_count': len(cluster), 'atr_tolerance': tolerance, 'timeframe': timeframe,
                           'major': any(p.get('scale') == 'major' for p in cluster),
                           'higher_timeframe_confirmation': False, 'breakdown': breakdown,
                           'strength': round(sum(breakdown.values()),3)})
    return sorted(result, key=lambda z:z['midpoint'])


def confirm_higher(zones_by_tf: dict, intervals: dict):
    for tf, items in zones_by_tf.items():
        for zone in items:
            matches = [other_tf for other_tf, others in zones_by_tf.items() if intervals[other_tf] > intervals[tf]
                       and any(z['zone_type'] == zone['zone_type'] and z['low'] <= zone['high'] and z['high'] >= zone['low'] for z in others)]
            zone['higher_timeframe_confirmation'] = bool(matches)
            zone['confirming_timeframes'] = matches
            zone['breakdown']['higher_tf_score'] = ENGINE_CONFIG['zone_weights']['higher_tf_score'] if matches else 0
            zone['strength'] = round(sum(zone['breakdown'].values()),3)


def nearest(items: list[dict], price: float) -> dict:
    support = [z for z in items if z['zone_type']=='support' and z['high'] <= price]
    resistance = [z for z in items if z['zone_type']=='resistance' and z['low'] >= price]
    return {'nearest_support': max(support,key=lambda z:z['high']) if support else None,
            'nearest_resistance': min(resistance,key=lambda z:z['low']) if resistance else None}
