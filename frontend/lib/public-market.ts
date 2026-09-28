import type { Candle, Market } from './types';

export const timeframes = ['5m','15m','1h','4h','1d','1w'];
export function normalizeCandles(raw: unknown, now = Date.now()): Candle[] {
  if (!Array.isArray(raw) || !raw.length) throw new Error('Binance returned no candles.');
  let previous=-1;
  return raw.map((row:unknown) => {
    if (!Array.isArray(row) || row.length<7) throw new Error('Invalid market data.');
    const [timestamp,open,high,low,close,volume,close_timestamp]=row.slice(0,7).map(Number);
    if (![timestamp,open,high,low,close,volume,close_timestamp].every(Number.isFinite)
      || timestamp<=previous || timestamp<0 || close_timestamp<timestamp || low<=0 || volume<0
      || high<Math.max(open,close) || low>Math.min(open,close)) throw new Error('Invalid candle data.');
    previous=timestamp;
    return {timestamp,open,high,low,close,volume,close_timestamp,closed:close_timestamp<now};
  });
}
export async function fetchPublicMarket(timeframe:string, signal?:AbortSignal):Promise<Market> {
  if (!timeframes.includes(timeframe)) throw new Error('Unsupported timeframe.');
  const controller=new AbortController();
  const abort=()=>controller.abort();
  if(signal?.aborted)controller.abort();
  signal?.addEventListener('abort',abort,{once:true});
  const timer=setTimeout(abort,15000);
  try {
    const query=new URLSearchParams({symbol:'BTCUSDT',interval:timeframe,limit:'500'});
    // No private API, cookies, account credentials, Redis or Python service.
    const response=await fetch(`https://data-api.binance.vision/api/v3/klines?${query}`,{
      signal:controller.signal,credentials:'omit',cache:'no-store',
    });
    if(!response.ok)throw new Error(`Binance market data unavailable (HTTP ${response.status}).`);
    const fetched_at=Date.now();
    return {candles:normalizeCandles(await response.json(),fetched_at),fetched_at,timeframe,status:'LIVE'};
  } catch(error) {
    if(signal?.aborted)throw error;
    if(controller.signal.aborted)throw new Error('Market request timed out. Retry the connection to Binance.');
    if(error instanceof TypeError)throw new Error('Cannot reach Binance public data from this network. Check your connection and retry.');
    throw error;
  } finally {clearTimeout(timer);signal?.removeEventListener('abort',abort);}
}
