'use client';
import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import LocalClock from './LocalClock';
import MarketHeader from './MarketHeader';
import RetroWindow from './RetroWindow';
import AnalysisForm from './AnalysisForm';
import { fetchPublicMarket, timeframes } from '@/lib/public-market';
import { money, number } from '@/lib/api';
import ResultPanels from './ResultPanels';
import { analyzeLocally } from '@/lib/local-analysis';
import { useLiveQuote } from '@/lib/live-quote';
import { useMarketOverview, captureOverview, type Overview } from '@/lib/use-market-overview';
import MarketInsights from './MarketInsights';
import type { Intent, Market, Result } from '@/lib/types';
const BTCChart=dynamic(()=>import('./BTCChart'),{ssr:false,loading:()=> <div className="chart-empty">LOADING CHART…</div>});

export default function StandaloneWorkspace(){
 const [tf,setTf]=useState('5m'),[revision,setRevision]=useState(0),[market,setMarket]=useState<Market|null>(null);
 const [loading,setLoading]=useState(true),[error,setError]=useState(''),[result,setResult]=useState<Result|null>(null),[busy,setBusy]=useState(false),[analysisError,setAnalysisError]=useState('');
 const {quote,stale}=useLiveQuote();
 const overview=useMarketOverview(),overviewRef=useRef(overview);
 overviewRef.current=overview;
 const [snapshot,setSnapshot]=useState<Overview|null>(null);
 const analysisController=useRef<AbortController|null>(null);
 useEffect(()=>()=>analysisController.current?.abort(),[]);
 async function analyze(intent:Intent){analysisController.current?.abort();const current=new AbortController();analysisController.current=current;setBusy(true);setAnalysisError('');setResult(null);setSnapshot(null);try{const [data,captured]=await Promise.all([analyzeLocally(intent,current.signal),captureOverview(overviewRef.current,current.signal)]);if(!current.signal.aborted){setSnapshot(captured);setResult(data);setTimeout(()=>document.getElementById('results')?.scrollIntoView({behavior:'smooth',block:'start'}),100);}}catch(e){if(!current.signal.aborted)setAnalysisError((e as Error).message);}finally{if(!current.signal.aborted)setBusy(false);}}
 const controller=useRef<AbortController|null>(null);
 useEffect(()=>{
   controller.current?.abort();const current=new AbortController();controller.current=current;
   let pending=false;
   setMarket(previous=>previous?.timeframe===tf?previous:null);setError('');
   async function refresh(){
    if(pending||current.signal.aborted||document.visibilityState==='hidden')return;
    pending=true;setLoading(true);
    try{const data=await fetchPublicMarket(tf,current.signal);if(!current.signal.aborted){setMarket(data);setError('');}}
    catch(e){if(!current.signal.aborted)setError((e as Error).message);}
    finally{pending=false;if(!current.signal.aborted)setLoading(false);}
   }
   void refresh();
   const timer=setInterval(()=>void refresh(),5000);
   const resume=()=>{if(document.visibilityState==='visible')void refresh();};
   document.addEventListener('visibilitychange',resume);window.addEventListener('focus',resume);
   return()=>{current.abort();clearInterval(timer);document.removeEventListener('visibilitychange',resume);window.removeEventListener('focus',resume);};
 },[tf,revision]);
 const previous=market?.candles.at(-2);
 const change=quote&&previous?(quote.price/previous.close-1)*100:null;
 return <><MarketHeader status={stale?'QUOTE DELAYED': 'LIVE BINANCE'} updated={quote?.time}/>
 <main className="workspace"><div className="usage-banner"><div><strong>MARKET FIRST. THEN YOUR DECISION.</strong><p>Explore live liquidity, key stats and sentiment. Complete your plan to see what the evidence means for your decision.</p></div><a className="guide-button" href="/docs">USER GUIDE ↗</a></div>
 <div className="main-grid"><div className="plan-column" id="plan"><AnalysisForm onSubmit={analyze} busy={busy} note="YOUR PLAN / MARKET EVIDENCE / CLEAR SCENARIOS"/></div>
 <div className="market-column"><RetroWindow title="MARKET.BTC" status="BINANCE / SPOT">
 <div className="market-heading"><div><span className="eyebrow">BITCOIN / TETHER</span><div className="market-price">{money(quote?.price)}</div></div><div className="price-change"><span>{change==null?'—':`${change>=0?'+':''}${number(change)}%`}</span><small>VS PREVIOUS {tf.toUpperCase()} CLOSE</small></div></div>
 <div className="chart-toolbar"><div className="timeframes" aria-label="Chart timeframe">{timeframes.map(value=><button key={value} aria-pressed={tf===value} className={tf===value?'active':''} onClick={()=>setTf(value)}>{value.toUpperCase()}</button>)}</div><button disabled={loading} onClick={()=>setRevision(n=>n+1)}>REFRESH ↻</button></div>
 {market?<BTCChart key={tf} candles={market.candles} zones={result?[result.context.support_resistance[tf]?.nearest_support,result.context.support_resistance[tf]?.nearest_resistance].filter(z=>z!=null):[]}/>:<div className="chart-empty" role="status"><strong>{loading?'FETCHING BTC DATA…':'MARKET DATA UNAVAILABLE'}</strong><p>{loading?'Loading Binance public candles and volume.':error}</p>{!loading&&<a className="guide-button" href="/docs">USER GUIDE</a>}</div>}
 {error&&market&&<p role="alert">Update failed. Showing the last successful snapshot. {error}</p>}<div className="chart-caption"><span>PRICE + VOLUME · {market?.candles.length||0} CANDLES</span><span>YOUR TIMEZONE / REFRESH 5S</span></div></RetroWindow>
 <RetroWindow title="ANALYSIS.STATUS" status={busy?'PROCESSING':result?'COMPLETE':'READY'}><p role="status" aria-live="polite">{busy?'Fetching fresh Binance candles and analyzing six timeframes...':result?'Your complete analysis is below. Analyze again to refresh the report.':'Fill in your plan and select ANALYZE BTC.'}</p>{analysisError&&<p role="alert" className="notice error">{analysisError} <a className="guide-button" href="/docs">USER GUIDE</a></p>}</RetroWindow>
 {stale&&<p className="notice">Live quote is unavailable or delayed. Last trade: {quote?new Date(quote.time).toLocaleString():'not received'}.</p>}
 </div></div>
 <MarketInsights overview={result&&snapshot?snapshot:overview} result={result} onReset={()=>{setResult(null);setSnapshot(null);}}/>
 {result&&<ResultPanels result={result}/>}
 <footer><div className="system-bar"><span>MARKET: {error?'UPDATE FAILED':market?'ONLINE':loading?'CONNECTING':'UNAVAILABLE'}</span><LocalClock/><span>LIVE MARKET / DECISION SNAPSHOT</span><a className="guide-button" href="/docs">USER GUIDE</a></div><p>Market data and scenario analysis are informational. No trades are placed.</p><a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">Charts by TradingView Lightweight Charts™</a></footer></main></>;
}
