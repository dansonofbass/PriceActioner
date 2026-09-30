import type { Candle, Intent, Market, Result, Zone } from './types';
import { fetchPublicMarket } from './public-market';

const mean=(xs:number[])=>xs.reduce((a,b)=>a+b,0)/xs.length;
const last=(xs:number[])=>xs[xs.length-1];
export function ema(xs:number[], period:number){let value=xs[0];return xs.map(x=>value=value+(x-value)*2/(period+1));}
export function measure(input:Candle[],cutoff:number){
 const bars=input.filter(c=>c.closed&&c.close_timestamp<cutoff);
 if(bars.length<205)throw new Error('At least 205 closed candles are required.');
 const prices=bars.map(c=>c.close), price=last(prices), e20=ema(prices,20),e50=ema(prices,50),e200=ema(prices,200);
 const fast=ema(prices,12),slow=ema(prices,26),macd=fast.map((x,i)=>x-slow[i]),hist=last(macd)-last(ema(macd,9));
 let gain=0,loss=0,atr=mean(bars.slice(0,14).map((c,i)=>i?Math.max(c.high-c.low,Math.abs(c.high-bars[i-1].close),Math.abs(c.low-bars[i-1].close)):c.high-c.low));
 for(let i=1;i<prices.length;i++){const d=prices[i]-prices[i-1];if(i<=14){gain+=Math.max(d,0)/14;loss+=Math.max(-d,0)/14;}else{gain=(gain*13+Math.max(d,0))/14;loss=(loss*13+Math.max(-d,0))/14;}
 if(i>=14){const c=bars[i];atr=(atr*13+Math.max(c.high-c.low,Math.abs(c.high-prices[i-1]),Math.abs(c.low-prices[i-1])))/14;}}
 const rsi=loss===0?(gain===0?50:100):100-100/(1+gain/loss);
 const highs:number[]=[],lows:number[]=[];
 for(let i=5;i<bars.length-5;i++){const peers=bars.slice(i-5,i+6).filter((_,j)=>j!==5);if(peers.every(c=>c.high<bars[i].high))highs.push(bars[i].high);if(peers.every(c=>c.low>bars[i].low))lows.push(bars[i].low);}
 const state=highs.length<2||lows.length<2?'transition':last(highs)>highs.at(-2)!&&last(lows)>lows.at(-2)!?'bullish':last(highs)<highs.at(-2)!&&last(lows)<lows.at(-2)!?'bearish':'range';
 function zone(values:number[],kind:string):Zone|null{const candidates=values.filter(x=>kind==='support'?x<price:x>price).sort((a,b)=>Math.abs(a-price)-Math.abs(b-price));if(!candidates.length)return null;const center=candidates[0],cluster=values.filter(x=>Math.abs(x-center)<=atr*.5),midpoint=mean(cluster);return {low:Math.min(...cluster)-atr*.1,high:Math.max(...cluster)+atr*.1,midpoint,strength:Math.min(100,30+cluster.length*10),touches:cluster.length,major:false,zone_type:kind,breakdown:{touches:cluster.length}};}
 const support=zone(lows,'support'),resistance=zone(highs,'resistance'),avgVolume=mean(bars.slice(-21,-1).map(c=>c.volume)),ratio=avgVolume?bars.at(-1)!.volume/avgVolume:null;
 const returns=prices.slice(-31).slice(1).map((p,i)=>Math.log(p/prices.slice(-31)[i])),sd=Math.sqrt(mean(returns.map(x=>(x-mean(returns))**2)));
 const prior=bars.slice(-21,-1),upper=Math.max(...prior.map(c=>c.high)),lower=Math.min(...prior.map(c=>c.low));
 return {bars,price,atr,sd,state,support,resistance,ratio,events:price>upper?[{event:'20_bar_breakout',level:upper}]:price<lower?[{event:'20_bar_breakdown',level:lower}]:[],momentum:{rsi14:rsi,ema20:last(e20),ema50:last(e50),ema200:last(e200),macd:last(macd),macd_histogram:hist,ema20_slope:last(e20)>e20.at(-6)!?'rising':last(e20)<e20.at(-6)!?'falling':'flat'},signal:Math.max(-1,Math.min(1,((price-last(e50))/Math.max(atr,price*.00001))*.15+(rsi-50)/100+(state==='bullish'?.25:state==='bearish'?-.25:0)))};
}
export function buildAnalysis(intent:Intent,markets:Record<string,Market>,cutoff=Date.now()):Result{
 const horizon=intent.action==='sell'?Math.max(intent.action_timing_days,1):Math.max(intent.holding_period_days||1,intent.action_timing_days);
 const primary=horizon<=1?'15m':horizon<=7?'4h':'1d';
 const weights:Record<string,number>=primary==='15m'?{'5m':.2,'15m':.5,'1h':.3}:primary==='4h'?{'5m':.1,'1h':.2,'4h':.5,'1d':.2}:{'5m':.05,'4h':.2,'1d':.5,'1w':.25};
 const measures:Record<string,ReturnType<typeof measure>>={};
 for(const [tf,m] of Object.entries(markets)){try{measures[tf]=measure(m.candles,cutoff);}catch{/* Report missing rather than manufacture measurements. */}}
 if(!measures[primary]||!measures['5m'])throw new Error('Fresh 5m and primary timeframe data are required. Check your Binance connection and analyze again.');
 const p=measures[primary],context:Result['context']={current_price:measures['5m'].price,user_intent:intent,generated_at:new Date(cutoff).toISOString(),analysis_plan:{requested_horizon_days:horizon,primary_timeframe:primary,secondary_timeframe:primary==='15m'?'5m':'4h',context_timeframe:primary==='1d'?'1w':'1d',timeframe_weights:weights},market_structures:{},support_resistance:{},momentum:{},volume:{},volatility:{},price_action:{},deterministic_evidence:{bullish_evidence:0,bearish_evidence:0,uncertain:0,breakdown:{}},thesis_invalidation:{current_structure_valid_while:p.state==='bullish'?`Closed ${primary} candles hold above confirmed support ${p.support?.low.toFixed(2)??'(not established)'}.`:p.state==='bearish'?`Closed ${primary} candles remain below resistance ${p.resistance?.high.toFixed(2)??'(not established)'}.`:'No confirmed directional structure; watch a close beyond the range.',weakening_conditions:['Momentum turns against the structure.','A breakout fails to hold on a closed candle.','Breakout volume stays below its previous 20-bar average.'],strong_invalidation:p.state==='bullish'&&p.support?{condition:'close below support',level:p.support.low,structure_condition:`${primary} closed candle`}:p.state==='bearish'&&p.resistance?{condition:'close above resistance',level:p.resistance.high,structure_condition:`${primary} closed candle`}:null}};
 const durations:Record<string,number>={'5m':5,'15m':15,'1h':60,'4h':240,'1d':1440,'1w':10080};
 for(const [tf,m] of Object.entries(measures)){context.market_structures[tf]={state:m.state,sequence:[]};context.support_resistance[tf]={nearest_support:m.support,nearest_resistance:m.resistance};context.momentum[tf]=m.momentum;context.volume[tf]={volume_ratio:m.ratio,taker_buy_ratio:null,classification:m.ratio===null?'unavailable':m.ratio>1.5?'high':m.ratio<.7?'low':'normal'};context.volatility[tf]={atr14:m.atr,atr_percent:m.atr/m.price*100,historical_volatility_annualized_pct:m.sd*Math.sqrt(365*1440/durations[tf])*100,classification:m.atr/m.price>.03?'high':'normal'};context.price_action[tf]={events:m.events,volume_confirmed:m.events.length>0&&(m.ratio??0)>1.5};}
 let signed=0;for(const [tf,weight] of Object.entries(weights)){const signal=measures[tf]?.signal??0,bullish=Math.max(signal,0)*weight*100,bearish=Math.max(-signal,0)*weight*100,uncertain=weight*100-bullish-bearish;context.deterministic_evidence.breakdown[tf]={weight,signal,bullish,bearish,uncertain};context.deterministic_evidence.bullish_evidence+=bullish;context.deterministic_evidence.bearish_evidence+=bearish;context.deterministic_evidence.uncertain+=uncertain;signed+=signal*weight;}
 const missing=Object.keys(weights).filter(tf=>!measures[tf]);return {analysis_id:crypto.randomUUID(),timestamp:context.generated_at,context,alignment:{alignment_score:Math.abs(signed)*100,alignment_direction:signed>.1?'bullish':signed<-.1?'bearish':'mixed'},status:missing.length?'PARTIAL DATA':'COMPLETE',missing_timeframes:missing,engine_version:'browser-1.0',jev_mode:'disabled',price_basis:'Latest closed 5m candle; live market quote is shown separately'};
}
export async function analyzeLocally(intent:Intent,signal?:AbortSignal){
 const frames=['5m','15m','1h','4h','1d','1w'];
 const responses=await Promise.allSettled(frames.map(tf=>fetchPublicMarket(tf,signal)));
 if(signal?.aborted)throw new Error('Analysis cancelled.');
 const markets:Record<string,Market>={};responses.forEach((r,i)=>{if(r.status==='fulfilled')markets[frames[i]]=r.value;});
 return buildAnalysis(intent,markets);
}
