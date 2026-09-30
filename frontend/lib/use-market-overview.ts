'use client';
import { useEffect, useState } from 'react';
import { fetchers, refreshIntervals } from './market-overview';

export type Feed<T> = { data:T|null; error:string; loading:boolean; received:number|null };
export function useFeed<T>(fetcher:(signal?:AbortSignal)=>Promise<T>,interval:number):Feed<T> {
 const [feed,setFeed] = useState<Feed<T>>({data:null,error:'',loading:true,received:null});
 useEffect(() => {
  const controller = new AbortController(); let pending = false, lastAttempt = 0;
  async function refresh() {
   if (pending || controller.signal.aborted || document.visibilityState === 'hidden') return;
   pending = true; lastAttempt = Date.now();
   try { const data = await fetcher(controller.signal); if (!controller.signal.aborted) setFeed({data,error:'',loading:false,received:Date.now()}); }
   catch (e) { if (!controller.signal.aborted) setFeed(old => ({...old,error:e instanceof Error?e.message:'Data unavailable.',loading:false})); }
   finally { pending = false; }
  }
  void refresh(); const timer = setInterval(()=>void refresh(),interval);
  const resume = () => { if(Date.now()-lastAttempt>=interval) void refresh(); };
  document.addEventListener('visibilitychange',resume); window.addEventListener('focus',resume);
  return () => { controller.abort(); clearInterval(timer); document.removeEventListener('visibilitychange',resume); window.removeEventListener('focus',resume); };
 },[fetcher,interval]);
 return feed;
}
export function useMarketOverview() {
 const book = useFeed(fetchers.book,refreshIntervals.book);
 const fundamentals = useFeed(fetchers.fundamentals,refreshIntervals.fundamentals);
 const derivatives = useFeed(fetchers.derivatives,refreshIntervals.derivatives);
 const fear = useFeed(fetchers.fear,refreshIntervals.fear);
 const technical = useFeed(fetchers.technical,refreshIntervals.technical);
 const [now,setNow] = useState(Date.now());
 useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),5000);return()=>clearInterval(timer);},[]);
 return {book,fundamentals,derivatives,fear,technical,now};
}
export type Overview = ReturnType<typeof useMarketOverview>;
// Reuse fresh feeds and settle missing ones before freezing a decision snapshot.
export async function captureOverview(current:Overview,signal:AbortSignal):Promise<Overview> {
 async function settled<T>(feed:Feed<T>,fetcher:(signal?:AbortSignal)=>Promise<T>,maxAge:number):Promise<Feed<T>> {
  if (feed.data&&!feed.error&&feed.received&&Date.now()-feed.received<maxAge) return feed;
  try { return {data:await fetcher(signal),error:'',loading:false,received:Date.now()}; }
  catch(e) { return {...feed,loading:false,error:e instanceof Error?e.message:'Data unavailable at analysis time.'}; }
 }
 const [book,fundamentals,derivatives,fear] = await Promise.all([
  settled(current.book,fetchers.book,5000),settled(current.fundamentals,fetchers.fundamentals,300000),
  settled(current.derivatives,fetchers.derivatives,30000),settled(current.fear,fetchers.fear,300000),
 ]);
 return {...current,book,fundamentals,derivatives,fear,now:Date.now()};
}
