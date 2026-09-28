import type { Metadata } from 'next';
import { standalone } from '@/lib/mode';
import BrandLogo from '@/components/BrandLogo';
import RetroWindow from '@/components/RetroWindow';

export const metadata: Metadata = { title: 'priceactioner - User Guide' };

export default function Docs() {
 return <main className="guide-page">
  <header className="admin-header"><BrandLogo/><a href="/">BACK TO WORKSPACE</a></header>
  <RetroWindow title="DOCS / QUICK START" status={standalone ? 'MARKET VIEW' : 'USER GUIDE'}>
   <article className="guide-body" lang="en" dir="ltr">
    <h1>{standalone ? 'Explore the BTC market' : 'From your form to your first result'}</h1>
    {standalone ? <>
     <p>View BTC/USDT price candles and volume using public Binance market data. The chart starts at 5 minutes and refreshes every 5 seconds while the page is visible. Use REFRESH for an immediate update. Chart labels use your device timezone; candle timestamps remain unchanged. The current open candle may change.</p>
     <p>Fill in your plan and select PREVIEW MY FORM to inspect your input as JSON. This mode does not run automated analysis or generate a complete Jev request. Admin access, saved history and daily analysis limits are paused.</p>
     <p>If the chart cannot load, check your connection to Binance public data and select RETRY. Missing market data is never replaced with made-up candles.</p>
    </> : <p>You do not need to write a prompt. Complete the form to inspect market structure and technical evidence. Selecting BUY or SELL never places a trade.</p>}

    <h2>1. Try an example</h2>
    <p>This example explains the form; it is not a recommendation to buy.</p>
    <ol>
     <li>What are you considering? Select BUY BTC.</li>
     <li>When do you plan to act? Select NOW.</li>
     <li>How long do you plan to hold? Select 7 DAYS.</li>
     <li>Risk tolerance: select BALANCED.</li>
     <li>Priority: select AVOID A BAD ENTRY.</li>
     <li>Leave I already own BTC unchecked if you do not own Bitcoin.</li>
     <li>{standalone ? 'Select PREVIEW MY FORM to see your input.' : 'Select ANALYZE BTC and wait for the result.'}</li>
    </ol>

    <h2>2. Understand the fields</h2>
    <dl className="guide-fields">
     <div><dt>Action</dt><dd>BUY BTC considers buying. SELL BTC considers selling. ALREADY OWN BTC considers holding an existing position. WAIT FOR ENTRY describes waiting before entering.</dd></div>
     <div><dt>Action timing</dt><dd>When you plan to make your decision. NOW means immediately; WITHIN 3 DAYS means during the next three days.</dd></div>
     <div><dt>Holding period</dt><dd>How long you intend to hold after entering. This differs from action timing. In full analysis mode, it determines the analysis horizon and timeframe weights. For selling, action timing supplies the horizon instead.</dd></div>
     <div><dt>Risk tolerance</dt><dd>CONSERVATIVE means cautious, BALANCED means moderate, and AGGRESSIVE means more willing to take risk.</dd></div>
     <div><dt>Priority</dt><dd>AVOID A BAD ENTRY emphasizes entry quality. CATCH TREND EARLY emphasizes the start of a trend. BALANCED represents a balance between them.</dd></div>
     <div><dt>Ownership and entry price</dt><dd>Select ownership if you already hold BTC. Entry price is optional and expressed in USDT; leave it empty if unknown. ALREADY OWN BTC enables ownership automatically.</dd></div>
    </dl>
    <p>Risk tolerance, priority and entry price are included in your input. They do not change objective market calculations or create a personalized recommendation.</p>

    {!standalone && <>
     <h2>3. Read the result</h2>
     <ul>
      <li>ANALYSIS.RESULT: market structure and your selected horizon. The reference price uses a closed candle and may differ from the chart snapshot.</li>
      <li>LEVELS.SR: support and resistance zones with strength scores. No level is invented when data is insufficient.</li>
      <li>MOMENTUM / VOLUME / VOLATILITY: momentum indicators, trading activity and price variation.</li>
      <li>TECHNICAL.EVIDENCE: bullish, bearish and uncertain evidence sum to 100. These scores are not calibrated probabilities.</li>
      <li>THESIS.VALIDITY: conditions that weaken or invalidate the current structure.</li>
     </ul>
     <h2>4. Inspect the exact request</h2>
     <p>After an analysis, open REQUEST.PREVIEW:</p>
     <ol>
      <li>READABLE: a readable summary of the form and analysis.</li>
      <li>STATE: JSON containing your intent, analysis horizon and Python calculations.</li>
      <li>QUESTIONS: six fixed questions about direction, horizon fit, trend persistence, evidence quality, risk and support for your plan.</li>
      <li>FULL REQUEST: the exact serialized JSON for that analysis. COPY FULL REQUEST copies it without API keys.</li>
     </ol>
     <p>The draft contains model, state and questions. Your form appears in state.user_intent. Market calculations supply the remaining context. If no model is configured, model is null.</p>
     <p>This is an inspection draft. Nothing is sent to Jev, and compatibility with its live API contract has not been verified.</p>
     <p>In the admin workspace, select an analysis in HISTORY and open FORM.PROMPT to inspect the form, calculated context and request. LOGS can filter events for the selected analysis.</p>
     <h2>5. Daily allowance and history</h2>
     <p>The allowance is three successful analyses per browser per UTC day, resetting at 00:00 UTC. Ordinary analysis failures refund the reservation. Chart refreshes and guide views do not consume the allowance. A storage outage or interrupted process may prevent a refund.</p>
     <p>This is a browser-based allowance, not verified identity enforcement. Another browser or cleared cookies can bypass it.</p>
     <p>Online Redis history retains up to 100 analyses and 2,000 log events for at most seven days. Local JSON history does not automatically expire.</p>
    </>}
    <a className="guide-start" href="/">{standalone ? 'BACK TO THE CHART AND FORM' : 'BACK TO THE ANALYSIS FORM'}</a>
   </article>
  </RetroWindow>
 </main>;
}
