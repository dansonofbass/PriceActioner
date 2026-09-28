def invalidation(structure: dict, items: list[dict], price: float, timeframe: str) -> dict:
    state=structure['state']
    bullish=state=='bullish'
    if state not in ('bullish','bearish'):
        return {'current_structure_valid_while':'No directional thesis established.', 'weakening_conditions':[], 'strong_invalidation':None}
    candidates=[z for z in items if z['major'] and (z['zone_type']=='support' and z['high']<price if bullish else z['zone_type']=='resistance' and z['low']>price)]
    zone=(max(candidates,key=lambda z:z['high']) if bullish else min(candidates,key=lambda z:z['low'])) if candidates else None
    level=(zone['low'] if bullish else zone['high']) if zone else None
    condition=f'{timeframe.upper()} confirmed close '+('below major support' if bullish else 'above major resistance')
    return {'current_structure_valid_while':f'{state.capitalize()} major structure persists'+(f' and closed price stays {"above" if bullish else "below"} {level:.2f}.' if level is not None else '; no confirmed major zone available.'),
            'weakening_conditions':['Lower high on primary timeframe' if bullish else 'Higher low on primary timeframe',
                                    'Short-term support loss' if bullish else 'Short-term resistance reclaim','Falling directional alignment'],
            'strong_invalidation':{'condition':condition,'level':level,'structure_condition':'Major structure turns '+('bearish' if bullish else 'bullish')}}
