import type { CSSProperties } from 'react';
import RetroWindow from './RetroWindow';
import type { Overview, Feed } from '@/lib/use-market-overview';
import type { BookLevel } from '@/lib/market-overview';
import type { Result } from '@/lib/types';
import { number } from '@/lib/api';

const compact = (value:number|null|undefined,unit='') => value == null ? 'Unavailable' : `${new Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(value)}${unit?` ${unit}`:''}`;
const price = (value:number) => new Intl.NumberFormat('en-US',{minimumFractionDigits:2,maximumFractionDigits:2}).format(value);
const percent = (value:number|null|undefined,digits=2) => value == null ? 'Unavailable' : `${value>=0?'+':''}${value.toFixed(digits)}%`;
const stamp = (time:number|null|undefined) => time ? new Date(time).toLocaleString() : 'Waiting for data';
const directionLabel = (score:number) => score<30?'Strong bearish pressure':score<45?'Bearish pressure':score<=55?'Mixed / range conditions':score<=70?'Bullish pressure':'Strong bullish pressure';

function FeedNote<T>({feed,source,href,time,stale=false}:{feed:Feed<T>;source:string;href:string;time?:number|null;stale?:boolean}) {
 return <p className="feed-note"><a href={href} target="_blank" rel="noreferrer">{source}</a><span>{feed.loading?'Loading…':`${stale||feed.error?'DELAYED / ':''}${stamp(time??feed.received)}`}</span>{feed.error&&<span role="status">{feed.error}{feed.data?' Last successful snapshot shown.':''}</span>}</p>;
}
export function Gauge({value,label,left,right,description}:{value:number|null;label:string;left:string;right:string;description:string}) {
 const safe=value==null?null:Math.max(0,Math.min(100,value));
 const point=(degrees:number,radius:number) => {const a=degrees*Math.PI/180;return [140+radius*Math.cos(a),128-radius*Math.sin(a)];};
 const needle = safe==null?null:point(180-safe*1.8,84);
 const colors=['#252525','#555555','#888888','#bbbbbb','#f1f1f1'];
 return <div className="market-gauge"><h3>{label}</h3><svg viewBox="0 0 280 175" role="img" aria-label={`${label}: ${safe==null?'unavailable':`${Math.round(safe)} out of 100`}. ${description}`}>
  <path d="M 35 128 A 105 105 0 0 1 245 128" stroke="#080808" strokeWidth="23" fill="none"/>
  {colors.map((color,i)=>{const from=point(180-i*36-1,105),to=point(180-(i+1)*36+1,105);return <path key={color} d={`M ${from[0]} ${from[1]} A 105 105 0 0 1 ${to[0]} ${to[1]}`} stroke={safe==null?'#b4b4b4':color} strokeWidth="20" fill="none"/>;})}
  <text x="22" y="154" textAnchor="middle">0</text><text x="140" y="14" textAnchor="middle">50</text><text x="258" y="154" textAnchor="middle">100</text>
  {needle&&<><line x1="140" y1="128" x2={needle[0]} y2={needle[1]} stroke="#111" strokeWidth="4" strokeLinecap="round"/><circle cx="140" cy="128" r="7" fill="#111"/></>}
  <text className="gauge-value" x="140" y="167" textAnchor="middle">{safe==null?'—':Math.round(safe)}</text>
 </svg><div className="gauge-labels"><span>{left}</span><span>{right}</span></div><strong>{description}</strong></div>;
}
function BookSide({levels,side}:{levels:BookLevel[];side:'bids'|'asks'}) {
 const max=Math.max(...levels.map(row=>row.quantity));
 return <div className={`book-side ${side}`}><h3>{side==='bids'?'BUY ORDERS / BIDS':'SELL ORDERS / ASKS'}</h3><table><thead><tr><th>Price / USDT</th><th>BTC</th></tr></thead><tbody>{levels.slice(0,8).map(row=><tr key={row.price} style={{'--depth':`${row.quantity/max*100}%`} as CSSProperties}><td>{price(row.price)}</td><td>{number(row.quantity,5)}</td></tr>)}</tbody></table></div>;
}
function Stat({label,value,note}:{label:string;value:string;note?:string}) {
 return <div className="key-stat"><dt>{label}</dt><dd>{value}</dd>{note&&<small>{note}</small>}</div>;
}

export default function MarketInsights({overview,result,onReset}:{overview:Overview;result:Result|null;onReset:()=>void}) {
 const {book,fundamentals,derivatives,fear,technical,now}=overview;
 const b=book.data,f=fundamentals.data,d=derivatives.data,g=fear.data,t=technical.data;
 const bookStale=!!b&&(!!book.error||now-b.time>15000),technicalStale=!!t&&(!!technical.error||now-t.time>120000);
 const fundamentalStale=!!f&&(!!fundamentals.error||now-f.time>900000),fearStale=!!g&&(!!fear.error||now-g.time>172800000);
 const derivativeStale=!!d&&(!!derivatives.error||now-(d.interestTime??d.fundingTime??0)>90000);
 const intent=result?.context.user_intent, action=intent?.action;
 const isEntry=action==='buy'||action==='wait';
 const score=result?50+(result.context.deterministic_evidence.bullish_evidence-result.context.deterministic_evidence.bearish_evidence)/2:t?.score??null;
 const direction=score==null?'Waiting for market data':directionLabel(score);
 const bookUsable=!!b&&!bookStale,derivativesUsable=!!d&&!derivativeStale,fearUsable=!!g&&!fearStale;
 const primary=result?.context.analysis_plan.primary_timeframe;
 const sr=primary?result?.context.support_resistance[primary]:null;
 const actionName=action==='hold'?'HOLD':action==='wait'?'WAIT FOR ENTRY':action?.toUpperCase();
 const conclusion=score==null?'Market evidence is unavailable.':Math.abs(score-50)<=5?'Evidence is mixed; your plan needs a clearer trigger.':action==='sell'?(score<45?'Downward pressure supports watching exit conditions.':'Upward pressure is a counterpoint to your planned sale.'):isEntry?(score>55?'Upward pressure supports the direction of a potential entry.':'Downward pressure challenges an immediate entry.'):score>55?'Upward pressure supports the current holding thesis.':'Downward pressure weakens the holding thesis.';
 return <div className={`market-insights ${result?'decision-view':''}`} id="market-context">
  <div className="insights-heading"><div><span className="eyebrow">{result?'YOUR DECISION / MARKET CONTEXT':'BEFORE YOU DECIDE'}</span><h2>{result?`${actionName} / ${result.context.analysis_plan.requested_horizon_days} DAY PLAN`:'Inside the BTC market'}</h2><p>{result?conclusion:'Live liquidity, market size and sentiment — independent of your form.'}</p>{result&&<small>Decision snapshot · {stamp(overview.now)}. Refresh the analysis for a new snapshot.</small>}</div>{result&&<button type="button" onClick={onReset}>BACK TO LIVE MARKET</button>}</div>

  <RetroWindow title={result?'PLAN / KEY STATS':'KEY STATS'} status={result?'DECISION SNAPSHOT':'BTC / MARKET + FUTURES'} className="key-stats-window">
   {result&&<div className="decision-explanation"><strong>{action==='sell'?'Position exit context':action==='hold'?'Position monitoring context':'Entry context'}</strong><p>Market capitalization and supply describe Bitcoin’s scale and issuance; they do not confirm an entry or exit. {derivativesUsable&&d.funding!=null?(d.funding>0?'Positive funding means longs pay shorts at the quoted funding rate.':d.funding<0?'Negative funding means shorts pay longs at the quoted funding rate.':'Funding is currently neutral.'):'Funding is unavailable or delayed, so leverage pressure cannot be assessed.'} {derivativesUsable&&d.change5m!=null&&d.changeTime!=null&&now-d.changeTime<900000?`Open contracts ${d.change5m>=0?'increased':'decreased'} ${Math.abs(d.change5m).toFixed(2)}% over the latest two 5m samples; this measures participation, not trade direction.`:''}</p></div>}
   <dl className="key-stats-grid">
    <Stat label="Market capitalization" value={compact(f?.marketCap,'USD')} note="Bitcoin / global market"/>
    <Stat label="Fully diluted market cap" value={compact(f?.dilutedCap,'USD')} note="Reference USD price × maximum supply"/>
    <Stat label="Circulating supply" value={compact(f?.circulating,'BTC')}/>
    <Stat label="Max supply" value={compact(f?.max,'BTC')}/>
    <Stat label="Total supply" value={compact(f?.total,'BTC')}/>
    <Stat label="Open interest" value={compact(d?.openInterestValue,'USDT')} note={`Binance BTCUSDT perpetual only${d?.openInterest!=null?` · ${compact(d.openInterest,'BTC')}`:''}`}/>
    <Stat label="Open interest change / 5m" value={percent(d?.change5m)} note={`Contract quantity · ${d?.changeTime?stamp(d.changeTime):'Awaiting two historical samples'}`}/>
    <Stat label="Liquidations / 24h" value="Unavailable" note="A complete 24h history needs an aggregate liquidation data provider."/>
    <Stat label="Funding rate" value={d?.funding==null?'Unavailable':percent(d.funding*100,4)} note={`Latest Binance rate${d?.nextFunding?` · next funding ${stamp(d.nextFunding)}`:''}`}/>
   </dl>
   {d?.issues.length? <p className="feed-warning">{d.issues.join(' · ')}</p>:null}
   <div className="stats-sources"><FeedNote feed={fundamentals} source="CoinGecko / supply & valuation" href="https://www.coingecko.com/en/coins/bitcoin" time={f?.time} stale={fundamentalStale}/><FeedNote feed={derivatives} source="Binance / BTCUSDT perpetual" href="https://www.binance.com/en/futures/BTCUSDT" time={d?.interestTime??d?.fundingTime} stale={derivativeStale}/></div>
   <p className="source-note">Global USD valuation and Binance USDT futures have different coverage. Open interest is not an all-exchange total. Liquidations unavailable does not mean zero.</p>
  </RetroWindow>

  <RetroWindow title={result?'PLAN / CONFIRMATION':'MARKET MOOD'} status={result?`${primary?.toUpperCase()} / YOUR HORIZON`:'INDEPENDENT MARKET VIEW'} className="mood-window">
   <div className="gauges"><Gauge value={score} label={result?'Your horizon / bear–bull':'Market direction / bear–bull'} left="BEARISH" right="BULLISH" description={direction}/><Gauge value={g?.value??null} label="Fear & Greed Index" left="EXTREME FEAR" right="EXTREME GREED" description={g?.classification??'Waiting for sentiment data'}/></div>
   <p className="market-explainer">{result?`The direction gauge uses the closed-candle evidence for your ${result.context.analysis_plan.requested_horizon_days}-day horizon.`:'The direction gauge combines closed 1h, 4h and 1d candles (20% / 50% / 30%).'} Below 45 means bearish pressure, 45–55 mixed, above 55 bullish. It measures technical direction, not the probability of profit.</p>
   {result?<div className="decision-explanation"><strong>{actionName} / confirmation to watch</strong><p>{isEntry?(sr?.nearest_resistance?`Watch a ${primary} close above ${price(sr.nearest_resistance.high)} USDT and a held retest; support failure at ${sr?.nearest_support?price(sr.nearest_support.low):'an unconfirmed level'} would challenge entry.`:'No confirmed resistance trigger is available for this horizon.'):sr?.nearest_support?`Watch whether ${primary} closes hold ${price(sr.nearest_support.low)} USDT support. A break would weaken the holding thesis or strengthen the exit case.`:'No confirmed support trigger is available for this horizon.'}</p><p>{fearUsable?(g.value>=75?'Extreme greed can increase the risk of chasing an extended move.':g.value<=25?'Extreme fear can accompany sharp volatility; it does not guarantee a rebound.':g.value>50?'Greed shows stronger risk appetite; confirmation still depends on price and volume.':'Fear shows cautious sentiment; it does not establish a bottom.'):'Sentiment is missing or delayed and is excluded from the interpretation.'}</p><p>{intent?.risk_profile==='conservative'?'For the conservative preference, prioritize a closed-candle confirmation and a retest.':intent?.risk_profile==='aggressive'?'For the aggressive preference, recognize that earlier signals can fail before confirmation.':'For the balanced preference, weigh confirmation against distance to the invalidation level.'}</p></div>:<p className="market-explainer">Fear & Greed is a separate daily sentiment index. Fear describes caution, greed stronger risk appetite; neither is a standalone buy or sell signal.</p>}
   {!result&&t&&<div className="mood-timeframes">{t.frames.map(frame=><span key={frame.timeframe}>{frame.timeframe.toUpperCase()}<strong>{frame.state.toUpperCase()}</strong><small>RSI {number(frame.rsi,0)}</small></span>)}</div>}
   {!result&&t?.missing.length?<p className="feed-warning">Missing: {t.missing.join(', ')}. Missing weights stay neutral; direction is less complete.</p>:null}
   {!result&&<FeedNote feed={technical} source="Binance / closed-candle technical direction" href="https://www.binance.com/en/trade/BTC_USDT?type=spot" time={t?.time} stale={technicalStale}/>}
   <FeedNote feed={fear} source="Fear & Greed Index by Alternative.me" href="https://alternative.me/crypto/fear-and-greed-index/" time={g?.time} stale={fearStale}/>
  </RetroWindow>
  <RetroWindow title={result?'PLAN / LIQUIDITY':'ORDER BOOK'} status="BINANCE BTC/USDT SPOT" className="order-book-window">
   {result&&<div className="decision-explanation"><strong>{action==='sell'?'What matters for an exit':action==='hold'?'Liquidity around your position':'What matters for an entry'}</strong><p>{bookUsable?isEntry?`A market buy meets the ask at ${price(b.asks[0].price)} USDT first. The visible 20 ask levels total ${compact(b.askTotal,'USDT')}; larger orders can move beyond this snapshot.`:action==='sell'?`A market sell meets the bid at ${price(b.bids[0].price)} USDT first. The visible 20 bid levels total ${compact(b.bidTotal,'USDT')}; displayed depth is not a guaranteed fill.`:`The visible bid share is ${number(b.bidShare,1)}%. Resting orders can be cancelled and do not validate holding on their own.`:'Liquidity data is missing or delayed; execution quality cannot be assessed.'}</p></div>}
   {b?<><div className="book-spread"><span>SPREAD <strong>{price(b.spread)} USDT</strong></span><span>{number(b.spreadBps,3)} bps</span></div><div className="book-columns"><BookSide levels={b.bids} side="bids"/><BookSide levels={b.asks} side="asks"/></div><div className="book-balance" aria-label={`Visible bid notional ${number(b.bidShare,1)} percent, ask notional ${number(100-b.bidShare,1)} percent`}><span style={{width:`${b.bidShare}%`}}/></div><div className="book-totals"><span>BIDS {number(b.bidShare,1)}%<strong>{compact(b.bidTotal,'USDT')}</strong></span><span>ASKS {number(100-b.bidShare,1)}%<strong>{compact(b.askTotal,'USDT')}</strong></span></div><p className="market-explainer">{b.bidShare>55?'More visible resting buy value than sell value.':b.bidShare<45?'More visible resting sell value than buy value.':'Visible buy and sell depth is broadly balanced.'} This is the nearest 20 levels on each side, not executed buying or selling. Orders can disappear.</p></>:<div className="overview-empty">{book.loading?'Loading Binance orders…':'Order book unavailable. Reconnecting automatically.'}</div>}
   <FeedNote feed={book} source="Binance / 20 levels per side · refresh 5s" href="https://www.binance.com/en/trade/BTC_USDT?type=spot" time={b?.time} stale={bookStale}/>
  </RetroWindow>
 </div>;
}
