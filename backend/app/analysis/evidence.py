from app.config import ENGINE_CONFIG


def alignment(structures: dict, weights: dict) -> dict:
    terms={tf:{'state':structures[tf]['state'] if tf in structures else 'missing',
               'value':ENGINE_CONFIG['state_values'][structures[tf]['state']] if tf in structures else 0,
               'weight':weight} for tf,weight in weights.items()}
    signed=sum(t['value']*t['weight'] for t in terms.values())
    return {'alignment_score':abs(signed)*100,'signed_score':signed,
            'alignment_direction':'bullish' if signed>0 else 'bearish' if signed<0 else 'mixed',
            'contributing_timeframes':terms,'formula':'abs(sum(state_value * horizon_weight)) * 100; missing = 0; no reweighting'}


def evidence(structure: dict, nearby: dict, events: dict, aligned: dict, vol: dict, momentum: dict, volatility: dict) -> dict:
    state=ENGINE_CONFIG['state_values'][structure['state']]
    support=nearby['nearest_support']; resistance=nearby['nearest_resistance']
    zone_signal=((support['strength'] if support else 0)-(resistance['strength'] if resistance else 0))/100
    signs={'breakout':1,'support_rejection':1,'failed_breakdown':1,'breakdown':-1,'resistance_rejection':-1,'failed_breakout':-1}
    event_values=[signs[e['event']] for e in events['events']]
    event_signal=sum(event_values)/len(event_values) if event_values else 0
    buy=vol['taker_buy_ratio']
    rsi=momentum['rsi14']; histogram=momentum['macd_histogram']
    midpoint=ENGINE_CONFIG['rsi_midpoint']
    momentum_signal=((1 if rsi>midpoint else -1 if rsi<midpoint else 0)+(1 if histogram>0 else -1 if histogram<0 else 0))/2
    stability=max(0,1-volatility['atr_percent']/ENGINE_CONFIG['volatility_atr_bands'][-1])
    signals={'market_structure':state,'support_resistance':zone_signal,'breakout_rejection':event_signal,
             'alignment':aligned['signed_score'],'volume':(buy*2-1) if buy is not None else 0,
             'momentum':momentum_signal,'volatility':state*stability}
    breakdown={name:{'signal':signal,'weight':ENGINE_CONFIG['evidence_weights'][name],
                     'bullish':max(0,signal)*ENGINE_CONFIG['evidence_weights'][name]*100,
                     'bearish':max(0,-signal)*ENGINE_CONFIG['evidence_weights'][name]*100,
                     'uncertain':(1-abs(signal))*ENGINE_CONFIG['evidence_weights'][name]*100} for name,signal in signals.items()}
    bull=round(sum(v['bullish'] for v in breakdown.values()),2); bear=round(sum(v['bearish'] for v in breakdown.values()),2)
    return {'bullish_evidence':bull,'bearish_evidence':bear,'uncertain':round(100-bull-bear,2),
            'label':'Deterministic technical heuristic','breakdown':breakdown,
            'formula':'Each signed signal in [-1,1] splits its weight between direction and uncertainty. Not a probability.'}
