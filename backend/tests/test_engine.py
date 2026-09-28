import json
import copy
import math
import pytest
from pydantic import ValidationError
from app.providers.binance import normalize
from app.schemas.candle import available
from app.analysis.indicators import indicators
from app.analysis.pivots import pivots,classic_pivots
from app.analysis.market_structure import market_structure
from app.analysis.support_resistance import zones,confirm_higher
from app.analysis.breakouts import breakouts
from app.analysis.volume import volume
from app.analysis.volatility import volatility
from app.analysis.horizon import plan_for
from app.analysis.evidence import alignment
from app.analysis.invalidation import invalidation
from app.decision.context import analyze
from app.jev.request_builder import build_request
from app.jev.client import send
from app.config import Settings,ENGINE_CONFIG
from conftest import candle


def test_normalization():
    raw=[0,'100','110','90','105','10',59999,'1050',42,'6','630','0']
    c=normalize(raw,60000)
    assert c.close==105 and c.closed and c.trades==42 and c.taker_buy_base_volume==6
    assert not normalize(raw,100).closed
    with pytest.raises(ValidationError): normalize([0,'100','90','110','105','10',59999,'1050',42,'6','630'],60000)


def ema(values,period):
    value=values[0]; output=[value]; alpha=2/(period+1)
    for v in values[1:]: value=alpha*v+(1-alpha)*value; output.append(value)
    return output


def test_rsi_ema_macd_atr_against_independent_recurrences(bars):
    actual=indicators(bars,bars[-1].close_timestamp)
    prices=[c.close for c in bars]
    gain=loss=0
    for i in range(1,len(prices)):
        d=prices[i]-prices[i-1]; gain=(gain*13+max(d,0))/14; loss=(loss*13+max(-d,0))/14
    assert actual['rsi14']==pytest.approx(100-100/(1+gain/loss))
    for p in (20,50,200): assert actual[f'ema{p}']==pytest.approx(ema(prices,p)[-1])
    fast,slow=ema(prices,12),ema(prices,26)
    macd=[a-b for a,b in zip(fast,slow)]
    signal=ema(macd[25:],9)[-1]
    assert actual['macd']==pytest.approx(macd[-1])
    assert actual['macd_histogram']==pytest.approx(macd[-1]-signal)
    tr=[max(c.high-c.low,abs(c.high-bars[i-1].close),abs(c.low-bars[i-1].close)) if i else c.high-c.low for i,c in enumerate(bars)]
    atr=sum(tr[:14])/14
    for value in tr[14:]: atr=(atr*13+value)/14
    assert actual['atr14']==pytest.approx(atr)
    assert actual['atr_percent']==pytest.approx(atr/prices[-1]*100)


def test_monotonic_rsi_and_constant_atr():
    bars=[candle(i,1000+i) for i in range(250)]
    result=indicators(bars,bars[-1].close_timestamp)
    assert result['rsi14']==100
    assert result['atr14']==4


def test_pivots_require_right_confirmation():
    bars=[candle(i,100+x) for i,x in enumerate([0,1,3,8,4,2,1])]
    assert not pivots(bars,bars[4].close_timestamp,left=2,right=2)
    result=pivots(bars,bars[5].close_timestamp,left=2,right=2)
    assert result[0]['timestamp']==bars[3].timestamp
    assert result[0]['confirmed_at']==bars[5].close_timestamp


@pytest.mark.parametrize('highs,lows,state',[([110,120],[90,100],'bullish'),([120,110],[100,90],'bearish'),([120,110],[90,100],'range'),([110,120],[100,90],'transition')])
def test_structure(highs,lows,state):
    points=[{'kind':kind,'price':price} for kind,price in [('high',highs[0]),('low',lows[0]),('high',highs[1]),('low',lows[1])]]
    s=market_structure(points)
    assert s['state']==state and len(s['sequence'])==4


def test_zones_cluster_and_strength(bars):
    points=[{'kind':'low','price':1000+x,'timestamp':0,'confirmed_at':1,'scale':'major'} for x in [0,1,2,50]]
    result=zones(bars,bars[-1].close_timestamp,points,12,'4h')
    assert len(result)==2 and result[0]['pivot_count']==3
    assert result[0]['atr_tolerance']==3
    assert all(0<=z['strength']<=100 and z['strength']==pytest.approx(sum(z['breakdown'].values())) for z in result)
    other=[{**copy.deepcopy(result[0]),'timeframe':'1d'}]
    confirm_higher({'4h':result,'1d':other},{'4h':4,'1d':24})
    assert result[0]['higher_timeframe_confirmation']
    assert result[0]['breakdown']['higher_tf_score']==25


@pytest.mark.parametrize('previous,current,kind,event',[(99,103,'resistance','breakout'),(103,98,'resistance','failed_breakout'),(103,98,'support','breakdown'),(98,103,'support','failed_breakdown')])
def test_breakout_events(previous,current,kind,event):
    bars=[candle(i,100) for i in range(22)]
    bars[-2]=candle(20,previous);bars[-1]=candle(21,current,volume=150)
    result=breakouts(bars,bars[-1].close_timestamp,[{'zone_type':kind,'low':99,'high':101}])
    assert event in [e['event'] for e in result['events']]
    assert result['volume_confirmed']
    assert result['price_breakout']==(event=='breakout')


def test_volume_excludes_current_from_average():
    bars=[candle(i,100,100) for i in range(20)]+[candle(20,100,200)]
    v=volume(bars,bars[-1].close_timestamp)
    assert v['average_volume_20']==100 and v['volume_ratio']==2
    assert v['taker_buy_ratio']==.6 and v['taker_sell_ratio']==.4
    bars[-1]=candle(20,100,0)
    assert volume(bars,bars[-1].close_timestamp)['taker_buy_ratio'] is None


@pytest.mark.parametrize('days,weights',[(1,{'15m':.25,'1h':.45,'4h':.3}),(3,{'1h':.3,'4h':.45,'1d':.25}),(7,{'1h':.15,'4h':.45,'1d':.4}),(14,{'4h':.3,'1d':.5,'1w':.2}),(30,{'4h':.1,'1d':.55,'1w':.35})])
def test_horizon(intent,days,weights):
    plan=plan_for(intent.model_copy(update={'holding_period_days':days}))
    assert plan.timeframe_weights==weights
    assert sum(weights.values())==pytest.approx(1)
    assert plan.primary_timeframe==max(weights,key=weights.get)


def test_alignment_missing_retains_uncertainty():
    a=alignment({'1h':{'state':'bullish'},'4h':{'state':'bearish'}},{'1h':.3,'4h':.5,'1d':.2})
    assert a['signed_score']==pytest.approx(-.2)
    assert a['alignment_score']==pytest.approx(20)
    assert a['contributing_timeframes']['1d']['value']==0


def test_context_and_no_future_leakage(bars,intent):
    cutoff=bars[290].close_timestamp
    original=analyze({tf:bars for tf in ['15m','1h','4h','1d','1w']},intent,cutoff)
    trimmed=analyze({tf:bars[:291] for tf in ['15m','1h','4h','1d','1w']},intent,cutoff)
    assert original==trimmed
    ev=original['context']['deterministic_evidence']
    assert ev['bullish_evidence']+ev['bearish_evidence']+ev['uncertain']==pytest.approx(100)
    assert 'candles' not in json.dumps(original['context']).replace('input_candles_count','')
    assert original['jev_mode']=='disabled'
    assert original['context']['generated_at'].startswith('1970')
    json.dumps(original,allow_nan=False)


def test_open_candles_excluded(bars):
    altered=bars+[candle(360,90000).model_copy(update={'closed':False})]
    assert indicators(altered,10**15)==indicators(bars,10**15)
    assert len(available(altered,10**15))==len(bars)


def test_invalidation_major_support():
    result=invalidation({'state':'bullish'},[{'major':True,'zone_type':'support','low':95,'high':97}],100,'4h')
    assert result['strong_invalidation']['level']==95
    assert 'below major support' in result['strong_invalidation']['condition']
    assert invalidation({'state':'range'},[],100,'4h')['strong_invalidation'] is None


def test_jev_generation_never_sends():
    result=build_request({'asset':'BTC/USDT'})
    assert len(result['payload']['questions'])==6
    assert json.loads(result['serialized_request'])==result['payload']
    assert result['character_count']==len(result['serialized_request'])
    with pytest.raises(RuntimeError): send(result)
    with pytest.raises(ValidationError): Settings(jev_mode='live')


def test_classic_pivots_use_completed_only():
    bars=[candle(0,100,high=110,low=90),candle(1,999)]
    p=classic_pivots(bars,59999)
    assert p['P']==100 and p['R1']==110 and p['S2']==80


def test_volatility_formula(bars):
    values=[math.log(b.close/a.close) for a,b in zip(bars[-31:],bars[-30:])]
    mean=sum(values)/30
    expected=math.sqrt(sum((v-mean)**2 for v in values)/29)*math.sqrt(365*24)*100
    assert volatility(bars,bars[-1].close_timestamp,'1h',10)['historical_volatility_annualized_pct']==pytest.approx(expected)
