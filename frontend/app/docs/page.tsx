import type { Metadata } from 'next';
import BrandLogo from '@/components/BrandLogo';
import RetroWindow from '@/components/RetroWindow';

export const metadata:Metadata={title:'priceactioner — User Guide',description:'How to read the Bitcoin market overview, complete your plan and interpret your decision report.'};

export default function Docs(){return <main className="guide-page">
 <header className="admin-header"><BrandLogo/><a href="/">BACK TO WORKSPACE</a></header>
 <RetroWindow title="USER GUIDE" status="QUICK START">
  <article className="guide-body" lang="en" dir="ltr">
   <h1>From the market to your decision</h1>
   <p>Explore Bitcoin market data, complete your plan, and select ANALYZE BTC to see the evidence for your chosen horizon. No prompt or API key is needed. Selecting BUY or SELL does not place a trade.</p>

   <h2>1. Explore the market before filling in the form</h2>
   <p>The chart and three market windows are available before you submit a plan:</p>
   <ul>
    <li><strong>KEY STATS:</strong> market capitalization, fully diluted market cap, circulating supply, maximum supply, total supply, open interest, its 5-minute change, funding, and the availability of 24-hour liquidation data.</li>
    <li><strong>ORDER BOOK:</strong> resting BTC/USDT buy and sell orders on Binance Spot. Eight price levels per side are displayed; totals and balance use the nearest 20 levels on each side. The spread is the best ask minus the best bid.</li>
    <li><strong>MARKET MOOD:</strong> two separate gauges for technical direction and the daily Fear &amp; Greed Index. Read the labels and values; the monochrome shading does not represent profit or loss.</li>
   </ul>
   <p>The direction gauge combines closed 1-hour, 4-hour and daily candles with weights of 20%, 50% and 30%. Below 45 indicates bearish pressure, 45–55 mixed conditions, and above 55 bullish pressure. The Fear &amp; Greed Index comes from Alternative.me and measures daily sentiment. Neither gauge is a probability of profit or a standalone trade signal.</p>

   <h2>2. Complete your plan</h2>
   <ol>
    <li><strong>Action:</strong> choose BUY BTC, SELL BTC, ALREADY OWN BTC, or WAIT FOR ENTRY.</li>
    <li><strong>Action timing:</strong> specify when you expect to decide. NOW means immediately; WITHIN 3 DAYS means during the next three days.</li>
    <li><strong>Holding period:</strong> specify how long you intend to hold. The analysis horizon uses the longer of action timing and holding period. For a sale, it uses action timing, with a minimum one-day horizon.</li>
    <li><strong>Risk tolerance and priority:</strong> describe what matters to you. These preferences shape the explanation without changing objective market measurements.</li>
    <li><strong>Ownership:</strong> indicate whether you already hold BTC. You can optionally enter your entry price in USDT. ALREADY OWN BTC enables ownership automatically.</li>
    <li>Select <strong>ANALYZE BTC</strong>. The page moves to your decision context when the report is ready.</li>
   </ol>
   <p>A one-day horizon uses 15-minute candles as the primary timeframe; horizons up to seven days use 4-hour candles; longer horizons use daily candles. Every analysis also checks 5-minute data. Changing the chart timeframe does not change an existing report.</p>
   <p><strong>Example:</strong> choose BUY BTC, NOW, 7 DAYS, BALANCED risk and AVOID A BAD ENTRY. Submit the form to explore a seven-day report. This example explains the form, not a recommendation to buy.</p>

   <h2>3. Read your decision context</h2>
   <p>After submission, the three overview windows become a timestamped decision snapshot. Their explanations reflect your action:</p>
   <ul>
    <li><strong>Buy or wait:</strong> inspect ask-side liquidity, nearby resistance, and the price confirmation needed for an entry.</li>
    <li><strong>Sell:</strong> inspect bid-side liquidity, support failure, and evidence that challenges or supports an exit.</li>
    <li><strong>Hold:</strong> monitor support, weakening momentum, and structural invalidation around your position.</li>
   </ul>
   <p>The technical gauge now uses your selected horizon. Funding, sentiment and order-book values remain market facts; choosing a different action does not change them. Resting orders may be cancelled, so visible depth does not guarantee an execution price.</p>
   <p>Select BACK TO LIVE MARKET to restore the general overview. Submit the form again to refresh your decision snapshot. The main quote and chart continue updating separately.</p>

   <h2>4. Read the full report</h2>
   <p>The full report follows the decision windows, including on mobile. It contains market structure, bullish/bearish/range scenarios, support and resistance, RSI, EMA, MACD, volume, volatility and invalidation conditions.</p>
   <p>Technical calculations use closed candles. The reference price is the latest closed 5-minute candle, so it can differ from the current trade price above the chart. Evidence percentages describe the balance of technical signals; they are not calibrated outcome probabilities. An entry-price comparison excludes fees and is not realized profit.</p>
   <p>Missing optional timeframes are identified as partial data. Without fresh 5-minute and primary-timeframe data, analysis stops instead of inventing a report.</p>

   <h2>5. Understand the sources and units</h2>
   <ul>
    <li><strong>Price and candles:</strong> Binance BTC/USDT Spot. Compare with the same exchange, pair and market, rather than Futures or BTC/USD. Candles refresh every five seconds while the page is visible; trade prices use a live stream with a polling fallback.</li>
    <li><strong>Valuation and supply:</strong> CoinGecko. Fully diluted market cap is its USD reference price multiplied by maximum supply. These global figures are refreshed every five minutes and have their own provider timestamp.</li>
    <li><strong>Open interest and funding:</strong> Binance BTCUSDT perpetual futures only, refreshed every 30 seconds. Open-interest value is contract quantity multiplied by mark price, in USDT. The change compares two 5-minute quantity samples; it does not measure price direction. Positive funding means longs pay shorts; negative funding means shorts pay longs at the quoted rate.</li>
    <li><strong>Liquidations / 24h:</strong> a complete aggregate history requires a separate data provider. Unavailable does not mean zero.</li>
    <li><strong>Fear &amp; Greed:</strong> the daily index from <a href="https://alternative.me/crypto/fear-and-greed-index/" target="_blank" rel="noreferrer">Alternative.me</a>. The app checks for updates every five minutes; the source updates daily.</li>
   </ul>
   <p>Each feed has its own coverage and timestamp. Global USD valuation and Binance USDT futures totals are not interchangeable. Snapshots with a failed or overdue refresh are marked DELAYED.</p>

   <h2>6. Your time and timezone</h2>
   <p>The footer shows YOUR TIME, the UTC offset and the timezone reported by your browser. It synchronizes the clock with Binance when available and otherwise uses your device clock. It updates every second and rechecks network time every minute.</p>
   <p>Chart labels and report dates use your device timezone. If it does not match where you are, correct the timezone in your device settings. No GPS location permission is needed.</p>

   <h2>7. Troubleshoot a connection</h2>
   <p>Check your network access to data-api.binance.vision, data-stream.binance.vision, fapi.binance.com, api.coingecko.com and api.alternative.me. Select REFRESH for a new chart request. Failed overview feeds retry automatically at their normal refresh interval.</p>
   <p>Provider outages, network restrictions or rate limits can affect individual panels. A failed feed does not replace real market data with simulated values. Read the timestamp and the availability message before using a snapshot.</p>
   <a className="guide-start guide-button" href="/">BACK TO THE ANALYSIS WORKSPACE</a>
  </article>
 </RetroWindow>
</main>;}
