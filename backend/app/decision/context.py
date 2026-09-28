from datetime import datetime, timezone
from app.config import ENGINE_CONFIG, INTERVAL_MS, settings
from app.schemas.candle import Candle, available
from app.schemas.intent import UserIntent
from app.schemas.decision import DecisionContext
from app.analysis.horizon import plan_for
from app.analysis.indicators import indicators, atr_value
from app.analysis.pivots import pivots, classic_pivots
from app.analysis.market_structure import market_structure
from app.analysis.support_resistance import zones, confirm_higher, nearest
from app.analysis.breakouts import breakouts
from app.analysis.volume import volume
from app.analysis.volatility import volatility
from app.analysis.confluence import confluence
from app.analysis.evidence import alignment, evidence
from app.analysis.invalidation import invalidation
from app.decision.human_preview import human_preview
from app.jev.request_builder import build_request

SOURCE_MAP={
    'analysis_plan':'analysis/horizon.py: holding period; otherwise max(1, action timing)',
    'market_structures':'analysis/market_structure.py: last two confirmed highs and lows',
    'price_action':'analysis/pivots.py + analysis/breakouts.py: closed bars only',
    'support_resistance':'analysis/support_resistance.py: ATR clusters; weighted touch, recency, rejection, higher-TF and volume scores',
    'momentum':'analysis/indicators.py: ta RSI14, EMA20/50/200, MACD12/26/9; EMA slopes across 5 bars',
    'volume':'analysis/volume.py: current volume / previous 20 mean; taker buy base / base volume',
    'volatility':'analysis/volatility.py: Wilder ATR14; annualized 30 log-return sample standard deviation',
    'confluence':'analysis/confluence.py: ATR proximity to EMA, major swings, classic pivots and higher zones',
    'trend_persistence_features':'decision/context.py: normalized observable features, not duration forecasts',
    'deterministic_evidence':'analysis/evidence.py: signed signals * configured weights; residual uncertainty',
    'thesis_invalidation':'analysis/invalidation.py: nearest major structural zone; direction from major pivots',
}


def analyze(data: dict[str,list[Candle]], intent: UserIntent, cutoff_timestamp: int, emit=lambda *args,**kwargs:None) -> dict:
    plan=plan_for(intent); emit('horizon_engine_completed','horizon')
    frames={}; missing=[]
    for tf in INTERVAL_MS:
        bars=available(data.get(tf,[]),cutoff_timestamp)
        if len(bars)<ENGINE_CONFIG['minimum_candles']:
            missing.append(tf); continue
        ind=indicators(bars,cutoff_timestamp); emit('indicator_calculation_completed','indicators',timeframe=tf)
        short=pivots(bars,cutoff_timestamp,**ENGINE_CONFIG['pivots']['short'])
        major=pivots(bars,cutoff_timestamp,**ENGINE_CONFIG['pivots']['major'])
        emit('pivot_detection_completed','pivots',timeframe=tf)
        points={(p['timestamp'],p['kind']):{**p,'scale':'short'} for p in short}
        points.update({(p['timestamp'],p['kind']):{**p,'scale':'major'} for p in major})
        struct=market_structure(major); emit('market_structure_completed','structure',timeframe=tf)
        # Zones for event tests must already exist before BOTH event candles.
        prior_cutoff=bars[-3].close_timestamp
        prior_points=[p for p in points.values() if p['confirmed_at']<=prior_cutoff]
        prior_atr=atr_value(bars,prior_cutoff)
        prior_zones=zones(bars,prior_cutoff,prior_points,prior_atr,tf)
        current_zones=zones(bars,cutoff_timestamp,list(points.values()),ind['atr14'],tf)
        emit('support_resistance_completed','zones',timeframe=tf)
        actions=breakouts(bars,cutoff_timestamp,prior_zones); emit('breakout_analysis_completed','breakouts',timeframe=tf)
        vol=volume(bars,cutoff_timestamp); emit('volume_analysis_completed','volume',timeframe=tf)
        frames[tf]={'indicators':ind,'short_pivots':short,'major_pivots':major,'structure':struct,'zones':current_zones,
                    'price_action':actions,'volume':vol,'volatility':volatility(bars,cutoff_timestamp,tf,ind['atr14']),
                    'closed_price':bars[-1].close,'latest_candle_time':bars[-1].close_timestamp,'candle_count':len(bars)}
    if plan.primary_timeframe not in frames: raise ValueError('Primary timeframe unavailable')
    confirm_higher({tf:f['zones'] for tf,f in frames.items()},INTERVAL_MS)
    primary=frames[plan.primary_timeframe]
    # Reference price is from the most granular completed candle, not a future/current open candle.
    price=frames[min(frames,key=INTERVAL_MS.get)]['closed_price']
    structures={tf:f['structure'] for tf,f in frames.items()}
    aligned=alignment(structures,plan.timeframe_weights)
    sr={tf:nearest(f['zones'],price) for tf,f in frames.items()}
    classic=classic_pivots(data.get('1d',[]),cutoff_timestamp)
    conf={tf:sorted(confluence(f['zones'],f['indicators'],f['major_pivots'],classic,f['indicators']['atr14']),key=lambda z:z['strength'],reverse=True)[:ENGINE_CONFIG['context_confluence_limit']] for tf,f in frames.items()}
    ev=evidence(primary['structure'],sr[plan.primary_timeframe],primary['price_action'],aligned,primary['volume'],primary['indicators'],primary['volatility'])
    near=sr[plan.primary_timeframe]; support=near['nearest_support']; resistance=near['nearest_resistance']
    event_names=[e['event'] for e in primary['price_action']['events']]
    directional=ENGINE_CONFIG['state_values'][primary['structure']['state']]
    features={'timeframe_alignment':aligned['alignment_score']/100,'structure_quality':abs(directional),
              'support_quality':support['strength']/100 if support else 0,
              'resistance_headroom':min(1,max(0,(resistance['low']-price)/(primary['indicators']['atr14'] or 1))) if resistance else None,
              'momentum_consistency':abs(ev['breakdown']['momentum']['signal']),
              'volume_confirmation':min(1,(primary['volume']['volume_ratio'] or 0)/ENGINE_CONFIG['volume_threshold']),
              'volatility_stability':max(0,1-primary['volatility']['atr_percent']/ENGINE_CONFIG['volatility_atr_bands'][-1]),
              'recent_failed_breakout':'failed_breakout' in event_names,'recent_failed_breakdown':'failed_breakdown' in event_names,
              'higher_timeframe_conflict':sum(w for tf,w in plan.timeframe_weights.items() if tf in structures and INTERVAL_MS[tf]>INTERVAL_MS[plan.primary_timeframe] and ENGINE_CONFIG['state_values'][structures[tf]['state']]*directional<0)}
    context=DecisionContext(current_price=price,user_intent=intent,analysis_plan=plan,market_structures=structures,
        price_action={tf:f['price_action'] for tf,f in frames.items()},support_resistance=sr,
        momentum={tf:f['indicators'] for tf,f in frames.items()},volume={tf:f['volume'] for tf,f in frames.items()},
        volatility={tf:f['volatility'] for tf,f in frames.items()},confluence=conf,trend_persistence_features=features,
        deterministic_evidence=ev,thesis_invalidation=invalidation(primary['structure'],primary['zones'],price,plan.primary_timeframe),
        generated_at=datetime.fromtimestamp(cutoff_timestamp/1000,timezone.utc)).model_dump(mode='json')
    emit('decision_context_completed','decision')
    preview=build_request(context); emit('jev_request_built','jev')
    return {'context':context,'frames':frames,'alignment':aligned,'classic_pivots':classic,'human_preview':human_preview(context),
            'source_map':SOURCE_MAP,'jev_preview':preview,'jev_mode':'disabled','jev_result':None,
            'engine_version':settings.analysis_engine_version,'config_snapshot':ENGINE_CONFIG,
            'cutoff_timestamp':cutoff_timestamp,'missing_timeframes':missing,'status':'PARTIAL DATA' if missing else 'READY',
            'price_basis':'Most granular available closed candle; live quote is shown separately'}
