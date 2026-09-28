'use client';
import { useState } from 'react';
import RetroWindow from './RetroWindow';
import type { Intent } from '@/lib/types';
export default function AnalysisForm({ onSubmit, busy, disabled = false }: { onSubmit: (intent: Intent) => void; busy: boolean; disabled?: boolean }) {
 const [action,setAction]=useState('buy'); const [owns,setOwns]=useState(false);
 return <RetroWindow title="PLAN.BTC" status="01"><form onSubmit={event=>{event.preventDefault();const f=new FormData(event.currentTarget);onSubmit({ action, action_timing_days:Number(f.get('timing')), holding_period_days:action==='sell'?null:Number(f.get('holding')), risk_profile:String(f.get('risk')),priority:String(f.get('priority')), owns_btc:owns,entry_price:owns && f.get('entry')?Number(f.get('entry')):null });}}>
  <div className="panel-intro"><span className="eyebrow">BTC / USDT · ANALYSIS INPUT</span><h1>Your market plan.</h1><p>Set your horizon. Inspect the evidence.</p></div>
  <fieldset><legend><span className="step">01</span> What are you considering?</legend><div className="radio-grid">{[['buy','BUY BTC'],['sell','SELL BTC'],['hold','ALREADY OWN BTC'],['wait','WAIT FOR ENTRY']].map(([value,label])=><label className={`radio-option ${action===value?'selected':''}`} key={value}><input type="radio" name="action" value={value} checked={action===value} onChange={()=>{setAction(value);if(value==='hold')setOwns(true);}}/><span>{label}</span></label>)}</div></fieldset>
  <label className="field"><span><span className="step">02</span> When do you plan to act?</span><select name="timing">{[0,1,3,7,14,30].map(d=><option key={d} value={d}>{d===0?'NOW':d===1?'WITHIN 24 HOURS':`WITHIN ${d} DAYS`}</option>)}</select></label>
  {action!=='sell' && <label className="field"><span><span className="step">03</span> How long do you plan to hold?</span><select name="holding" defaultValue="7">{[1,3,7,14,30].map(d=><option key={d} value={d}>{d===1?'24 HOURS':`${d} DAYS`}</option>)}</select></label>}
  <div className="form-split"><label className="field"><span>Risk tolerance</span><select name="risk" defaultValue="balanced"><option value="conservative">CONSERVATIVE</option><option value="balanced">BALANCED</option><option value="aggressive">AGGRESSIVE</option></select></label><label className="field"><span>Priority</span><select name="priority" defaultValue="avoid_bad_entry"><option value="avoid_bad_entry">AVOID A BAD ENTRY</option><option value="catch_trend_early">CATCH TREND EARLY</option><option value="balanced">BALANCED</option></select></label></div>
  <label className="checkbox-field"><input type="checkbox" checked={owns} disabled={action==='hold'} onChange={e=>setOwns(e.target.checked)}/> I already own BTC</label>
  {owns && <label className="field"><span>Entry price (optional, USDT)</span><input name="entry" type="number" min="0.01" step="0.01" placeholder="e.g. 95000"/></label>}
  <button className="primary-button" type="submit" disabled={busy || disabled}>{busy?'ANALYZING.BTC…':'ANALYZE BTC'}<span aria-hidden="true">↗</span></button><p className="form-note">PRICE ACTION FIRST. NO PROMPT REQUIRED.</p>
 </form></RetroWindow>;
}
