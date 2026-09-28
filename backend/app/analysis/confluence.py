from app.config import ENGINE_CONFIG


def confluence(items: list[dict], momentum: dict, major: list[dict], classic: dict, atr: float) -> list[dict]:
    tolerance = atr*ENGINE_CONFIG['confluence_atr_multiplier']
    result=[]
    for z in items:
        factors=['support/resistance']
        factors.extend(name for name in ['ema20','ema50','ema200'] if momentum.get(name) is not None and abs(momentum[name]-z['midpoint'])<=tolerance)
        if any(abs(p['price']-z['midpoint'])<=tolerance for p in major): factors.append('major swing')
        if z['higher_timeframe_confirmation']: factors.append('higher timeframe zone')
        factors.extend('classic '+name for name,value in classic.items() if name!='source_close_timestamp' and abs(value-z['midpoint'])<=tolerance)
        if len(factors)>1:
            result.append({'low':z['low'],'high':z['high'],'factors':factors,
                           'timeframes':[z['timeframe']]+z.get('confirming_timeframes',[]),
                           'strength':round(min(100,len(factors)/ENGINE_CONFIG['confluence_factor_cap']*100),2),
                           'formula':f"min(100, factor_count / {ENGINE_CONFIG['confluence_factor_cap']} * 100)"})
    return result
