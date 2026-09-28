def market_structure(points: list[dict]) -> dict:
    highs, lows, sequence = [], [], []
    for point in points:
        series = highs if point['kind'] == 'high' else lows
        label = None
        if series:
            label = ('HH' if point['price'] > series[-1]['price'] else 'LH' if point['price'] < series[-1]['price'] else 'EH') if point['kind'] == 'high' else ('HL' if point['price'] > series[-1]['price'] else 'LL' if point['price'] < series[-1]['price'] else 'EL')
        series.append(point)
        sequence.append({**point, 'label': label})
    state = 'transition'
    if len(highs) >= 2 and len(lows) >= 2:
        up_h, up_l = highs[-1]['price'] > highs[-2]['price'], lows[-1]['price'] > lows[-2]['price']
        down_h, down_l = highs[-1]['price'] < highs[-2]['price'], lows[-1]['price'] < lows[-2]['price']
        state = 'bullish' if up_h and up_l else 'bearish' if down_h and down_l else 'range' if down_h and up_l else 'transition'
    return {'state': state, 'last_swing_high': highs[-1] if highs else None, 'last_swing_low': lows[-1] if lows else None,
            'previous_swing_high': highs[-2] if len(highs)>1 else None, 'previous_swing_low': lows[-2] if len(lows)>1 else None,
            'sequence': sequence[-12:]}
