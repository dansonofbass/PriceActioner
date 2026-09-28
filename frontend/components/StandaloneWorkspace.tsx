'use client';
import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import MarketHeader from './MarketHeader';
import RetroWindow from './RetroWindow';
import AnalysisForm from './AnalysisForm';
import { fetchPublicMarket, timeframes } from '@/lib/public-market';
import { money, number } from '@/lib/api';
import type { Intent, Market } from '@/lib/types';
const BTCChart=dynamic(()=>import('./BTCChart'),{ssr:false,loading:()=> <div className="chart-empty">LOADING CHART…</div>});

export default function StandaloneWorkspace(){
 const [tf,setTf]=useState('4h'),[revision,setRevision]=useState(0),[market,setMarket]=useState<Market|null>(null);
 const [loading,setLoading]=useState(true),[error,setError]=useState(''),[intent,setIntent]=useState<Intent|null>(null);
 const controller=useRef<AbortController|null>(null);
 useEffect(()=>{
   controller.current?.abort();const current=new AbortController();controller.current=current;
   setLoading(true);setError('');setMarket(null);
   fetchPublicMarket(tf,current.signal).then(data=>{if(!current.signal.aborted)setMarket(data);})
     .catch(e=>{if(!current.signal.aborted)setError((e as Error).message);})
     .finally(()=>{if(!current.signal.aborted)setLoading(false);});
   return()=>current.abort();
 },[tf,revision]);
 const last=market?.candles.at(-1),previous=market?.candles.at(-2);
 const change=last&&previous?(last.close/previous.close-1)*100:null;
 return <><MarketHeader status={loading?'FETCHING':error?'UNAVAILABLE':'LIVE SNAPSHOT'} updated={market?.fetched_at}/>
 <main className="workspace"><div className="usage-banner"><div><strong>BTC MARKET VIEW</strong><p>Live price and volume charts are available. Automated analysis and admin access are paused. Fill in the form to preview your input.</p></div><a href="/docs">USER GUIDE</a></div>
 <div className="main-grid"><AnalysisForm onSubmit={setIntent} busy={false} submitLabel="PREVIEW MY FORM" note="FORM PREVIEW ONLY. NO ANALYSIS IS SENT."/>
 <div className="market-column"><RetroWindow title="MARKET.BTC" status="BINANCE / SPOT">
 <div className="market-heading"><div><span className="eyebrow">BITCOIN / TETHER</span><div className="market-price">{money(last?.close)}</div></div><div className="price-change"><span>{change==null?'—':`${change>=0?'+':''}${number(change)}%`}</span><small>VS PREVIOUS {tf.toUpperCase()} CLOSE</small></div></div>
 <div className="chart-toolbar"><div className="timeframes" aria-label="Chart timeframe">{timeframes.map(value=><button key={value} aria-pressed={tf===value} className={tf===value?'active':''} onClick={()=>setTf(value)}>{value.toUpperCase()}</button>)}</div><button disabled={loading} onClick={()=>setRevision(n=>n+1)}>REFRESH ↻</button></div>
 {market?<BTCChart candles={market.candles}/>:<div className="chart-empty" role="status"><strong>{loading?'FETCHING BTC DATA…':'MARKET DATA UNAVAILABLE'}</strong><p>{loading?'Loading Binance public candles and volume.':error}</p>{!loading&&<button onClick={()=>setRevision(n=>n+1)}>RETRY</button>}</div>}
 <div className="chart-caption"><span>PRICE + VOLUME · {market?.candles.length||0} CANDLES</span><span>UTC · OPEN CANDLE MAY CHANGE</span></div></RetroWindow>
 <RetroWindow title="FORM.PREVIEW" status="LOCAL PREVIEW">{intent?<><p>This is your form input only. No market analysis or complete Jev request has been generated.</p><pre>{JSON.stringify(intent,null,2)}</pre></>:<p>Fill in your plan and select PREVIEW MY FORM to inspect your input.</p>}</RetroWindow>
 </div></div><footer><div className="system-bar"><span>MARKET: {market?'ONLINE':loading?'CONNECTING':'UNAVAILABLE'}</span><span>MODE: MARKET VIEW</span><a href="/docs">USER GUIDE</a></div><p>Market data is informational. No trades or AI requests are made.</p><a href="https://www.tradingview.com/" target="_blank" rel="noreferrer">Charts by TradingView Lightweight Charts™</a></footer></main></>;
}
