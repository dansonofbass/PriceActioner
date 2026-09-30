import { fetchPublicMarket } from './public-market';
import { measure } from './local-analysis';

export type BookLevel = { price: number; quantity: number; notional: number };
export type OrderBook = { bids: BookLevel[]; asks: BookLevel[]; spread: number; spreadBps: number; bidShare: number; bidTotal: number; askTotal: number; time: number; updateId: number };
export type Fundamentals = { price: number; marketCap: number | null; dilutedCap: number | null; circulating: number | null; total: number | null; max: number | null; time: number };
export type Derivatives = { openInterest: number | null; openInterestValue: number | null; interestTime: number | null; change5m: number | null; changeTime: number | null; funding: number | null; fundingTime: number | null; nextFunding: number | null; issues: string[] };
export type Fear = { value: number; classification: string; time: number };
export type Technical = { score: number; time: number; missing: string[]; frames: { timeframe: string; state: string; rsi: number; signal: number }[] };

function object(value: unknown): Record<string, unknown> {
 if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Invalid provider response.');
 return value as Record<string, unknown>;
}
export function numeric(value: unknown): number | null {
 if (value === null || value === undefined || value === '' || typeof value === 'boolean') return null;
 const result = Number(value);
 return Number.isFinite(result) ? result : null;
}
function positive(value: unknown): number {
 const result = numeric(value);
 if (result === null || result <= 0) throw new Error('Invalid or missing market value.');
 return result;
}
function optionalPositive(value: unknown) { const n = numeric(value); return n !== null && n > 0 ? n : null; }
export async function publicJson(url: string, signal?: AbortSignal): Promise<unknown> {
 const response = await fetch(url, { credentials: 'omit', cache: 'no-store', signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(12000)]) : AbortSignal.timeout(12000) });
 if (!response.ok) throw new Error(response.status === 429 ? 'Provider rate limit; waiting for the next refresh.' : `Provider unavailable (HTTP ${response.status}).`);
 return response.json();
}

export function parseBook(raw: unknown, time = Date.now()): OrderBook {
 const value = object(raw);
 function levels(rawLevels: unknown, direction: number) {
  if (!Array.isArray(rawLevels) || !rawLevels.length) throw new Error('Empty order book.');
  return rawLevels.map(row => { if (!Array.isArray(row) || row.length < 2) throw new Error('Invalid book level.'); const price = positive(row[0]), quantity = positive(row[1]); return { price, quantity, notional: price * quantity }; }).sort((a,b) => direction * (a.price-b.price)).slice(0,20);
 }
 const bids = levels(value.bids, -1), asks = levels(value.asks, 1);
 const spread = asks[0].price-bids[0].price;
 if (spread < 0) throw new Error('Crossed order book; waiting for a valid snapshot.');
 const bidTotal = bids.reduce((sum, row) => sum+row.notional,0), askTotal = asks.reduce((sum,row) => sum+row.notional,0);
 return { bids, asks, spread, spreadBps: spread / ((asks[0].price+bids[0].price)/2)*10000, bidTotal, askTotal, bidShare: bidTotal/(bidTotal+askTotal)*100, time, updateId: positive(value.lastUpdateId) };
}
export function parseFundamentals(raw: unknown): Fundamentals {
 if (!Array.isArray(raw)) throw new Error('Invalid market statistics.');
 const value = object(raw.find(row => row?.id === 'bitcoin'));
 const price = positive(value.current_price), max = optionalPositive(value.max_supply), time = Date.parse(String(value.last_updated));
 if (!Number.isFinite(time)) throw new Error('Missing statistics timestamp.');
 return { price, marketCap: optionalPositive(value.market_cap), dilutedCap: max === null ? null : price*max, circulating: optionalPositive(value.circulating_supply), total: optionalPositive(value.total_supply), max, time };
}
export function parseFear(raw: unknown): Fear {
 const rows = object(raw).data;
 if (!Array.isArray(rows) || !rows.length) throw new Error('Fear & Greed is unavailable.');
 const row = object(rows[0]), value = numeric(row.value), time = positive(row.timestamp)*1000;
 if (value === null || value < 0 || value > 100 || typeof row.value_classification !== 'string') throw new Error('Invalid sentiment reading.');
 return { value, classification: row.value_classification, time };
}
export async function fetchBook(signal?: AbortSignal) { return parseBook(await publicJson('https://data-api.binance.vision/api/v3/depth?symbol=BTCUSDT&limit=20',signal)); }
export async function fetchFundamentals(signal?: AbortSignal) { return parseFundamentals(await publicJson('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=bitcoin&sparkline=false',signal)); }
export async function fetchFear(signal?: AbortSignal) { return parseFear(await publicJson('https://api.alternative.me/fng/?limit=1',signal)); }
export async function fetchDerivatives(signal?: AbortSignal): Promise<Derivatives> {
 const paths = ['/fapi/v1/openInterest?symbol=BTCUSDT','/fapi/v1/premiumIndex?symbol=BTCUSDT','/futures/data/openInterestHist?symbol=BTCUSDT&period=5m&limit=2'];
 const responses = await Promise.allSettled(paths.map(path => publicJson(`https://fapi.binance.com${path}`,signal)));
 const result: Derivatives = { openInterest:null,openInterestValue:null,interestTime:null,change5m:null,changeTime:null,funding:null,fundingTime:null,nextFunding:null,issues:[] };
 let mark: number | null = null;
 const labels = ['Open interest','Funding rate','5m open-interest change'];
 responses.forEach((response,index) => {
  try {
   if (response.status !== 'fulfilled') throw new Error('Unavailable');
   if (index === 2) {
    if (!Array.isArray(response.value) || response.value.length < 2) throw new Error('Missing history');
    const previous = object(response.value[0]), current = object(response.value[1]);
    const time = positive(current.timestamp), previousTime = positive(previous.timestamp);
    if (current.symbol !== 'BTCUSDT' || time-previousTime !== 300000) throw new Error('Invalid history interval');
    result.change5m = (positive(current.sumOpenInterest)/positive(previous.sumOpenInterest)-1)*100; result.changeTime = time;
   } else {
    const value = object(response.value);
    if (value.symbol !== 'BTCUSDT') throw new Error('Wrong contract');
    if (index === 0) { result.openInterest = positive(value.openInterest); result.interestTime = positive(value.time); }
    else { mark = positive(value.markPrice); result.funding = numeric(value.lastFundingRate); result.fundingTime = positive(value.time); result.nextFunding = positive(value.nextFundingTime); }
   }
  } catch { result.issues.push(`${labels[index]} unavailable`); }
 });
 if (result.openInterest !== null && mark !== null) result.openInterestValue = result.openInterest*mark;
 if (result.openInterest === null && result.funding === null) throw new Error('Binance futures data is unavailable from this network.');
 return result;
}
export async function fetchTechnical(signal?: AbortSignal): Promise<Technical> {
 const frames = ['1h','4h','1d'], weights = [.2,.5,.3], time = Date.now();
 const responses = await Promise.allSettled(frames.map(async timeframe => { const market = await fetchPublicMarket(timeframe,signal); return measure(market.candles,time); }));
 const available: Technical['frames'] = [], missing: string[] = []; let signed = 0;
 responses.forEach((r,i) => { if (r.status === 'fulfilled') { signed += r.value.signal*weights[i]; available.push({timeframe:frames[i],state:r.value.state,rsi:r.value.momentum.rsi14,signal:r.value.signal}); } else missing.push(frames[i]); });
 if (!available.length) throw new Error('Market direction needs fresh Binance candles.');
 return { score:50+signed*50,time,missing,frames:available };
}
export const fetchers = { book:fetchBook, fundamentals:fetchFundamentals, derivatives:fetchDerivatives, fear:fetchFear, technical:fetchTechnical };
export const refreshIntervals = { book:5000, fundamentals:300000, derivatives:30000, fear:300000, technical:60000 };
