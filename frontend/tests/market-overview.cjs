const ts=require('typescript'),fs=require('node:fs'),path=require('node:path'),Module=require('node:module'),assert=require('node:assert/strict');
for(const ext of ['.ts','.tsx']) require.extensions[ext]=(module,file)=>module._compile(ts.transpileModule(fs.readFileSync(file,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022,jsx:ts.JsxEmit.ReactJSX,esModuleInterop:true}}).outputText,file);
const resolve=Module._resolveFilename;
Module._resolveFilename=function(request,...args){return resolve.call(this,request.startsWith('@/')?path.join(__dirname,'..',request.slice(2)):request,...args);};
const {parseBook,parseFear,parseFundamentals,fetchDerivatives,numeric}=require('../lib/market-overview.ts');
const {buildAnalysis}=require('../lib/local-analysis.ts');
const {captureOverview}=require('../lib/use-market-overview.ts');
const React=require('react'),{renderToStaticMarkup}=require('react-dom/server'),MarketInsights=require('../components/MarketInsights.tsx').default;
const now=Date.now(),book=parseBook({lastUpdateId:1,bids:[['99','2'],['100','1']],asks:[['102','3'],['101','1']]},now);
assert.equal(book.bids[0].price,100);assert.equal(book.asks[0].price,101);assert.equal(book.spread,1);assert.equal(book.bidTotal,298);assert.equal(book.askTotal,407);assert.equal(book.bidShare,298/705*100);
assert.throws(()=>parseBook({lastUpdateId:1,bids:[['103','1']],asks:[['101','1']]}));
assert.throws(()=>parseBook({lastUpdateId:1,bids:[['100','0']],asks:[['101','1']]}));
assert.equal(numeric(null),null);assert.equal(numeric(''),null);assert.equal(numeric('0'),0);
assert.equal(parseFear({data:[{value:'0',value_classification:'Extreme Fear',timestamp:now/1000}]}).value,0);
assert.throws(()=>parseFear({data:[{value:'101',value_classification:'Greed',timestamp:1}]}));
const fundamentals=parseFundamentals([{id:'bitcoin',current_price:100,market_cap:2000,max_supply:21,total_supply:20,circulating_supply:20,last_updated:new Date(now).toISOString()}]);
assert.equal(fundamentals.dilutedCap,2100);assert.equal(parseFundamentals([{id:'bitcoin',current_price:100,last_updated:new Date(now).toISOString()}]).max,null);
const feed=data=>({data,error:'',loading:false,received:now});
const overview={now,book:feed(book),fundamentals:feed(fundamentals),fear:feed({value:71,classification:'Greed',time:now}),technical:feed({score:62,time:now,missing:[],frames:[]}),derivatives:feed({openInterest:10,openInterestValue:1000,interestTime:now,change5m:1,changeTime:now,funding:.0001,fundingTime:now,nextFunding:now+60000,issues:[]})};
const render=result=>renderToStaticMarkup(React.createElement(MarketInsights,{overview,result,onReset:()=>{}}));
const before=render(null);assert.match(before,/Inside the BTC market/);assert.match(before,/ORDER BOOK/);assert.match(before,/KEY STATS/);assert.match(before,/MARKET MOOD/);assert.equal((before.match(/<svg /g)||[]).length,2);assert.match(before,/Liquidations \/ 24h/);assert.match(before,/Unavailable/);
const bars=Array.from({length:300},(_,i)=>({timestamp:now-(301-i)*300000,close_timestamp:now-(300-i)*300000-1,open:100,high:101,low:99,close:100,volume:1,closed:true}));
const markets=Object.fromEntries(['5m','15m','1h','4h','1d','1w'].map(timeframe=>[timeframe,{timeframe,candles:bars,status:'LIVE',fetched_at:now}]));
for(const action of ['buy','sell','hold','wait']){
 const result=buildAnalysis({action,action_timing_days:0,holding_period_days:7,risk_profile:'balanced',priority:'balanced',owns_btc:action==='hold',entry_price:null},markets,now);
 const html=render(result);assert.match(html,/DECISION SNAPSHOT/);assert.match(html,/PLAN \/ CONFIRMATION/);assert.doesNotMatch(html,/Inside the BTC market/);
 if(action==='buy'||action==='wait')assert.match(html,/market buy meets the ask at 101.00/);
 if(action==='sell')assert.match(html,/market sell meets the bid at 100.00/);
 if(action==='hold')assert.match(html,/do not validate holding on their own/);
}
const empty=Object.fromEntries(Object.keys(overview).filter(k=>k!=='now').map(k=>[k,{data:null,error:'Offline',loading:false,received:null}]));
const unavailable=renderToStaticMarkup(React.createElement(MarketInsights,{overview:{...empty,now},result:null,onReset:()=>{}}));assert.doesNotMatch(unavailable,/NaN|undefined/);assert.equal((unavailable.match(/<line /g)||[]).length,0);
async function asyncChecks(){
 const original=global.fetch;
 try{
  global.fetch=async url=>new Response(JSON.stringify(url.includes('openInterestHist')?[{symbol:'BTCUSDT',sumOpenInterest:'100',timestamp:now-300000},{symbol:'BTCUSDT',sumOpenInterest:'110',timestamp:now}]:url.includes('premiumIndex')?{symbol:'BTCUSDT',markPrice:'100',lastFundingRate:'0.0001',time:now,nextFundingTime:now+60000}:{symbol:'BTCUSDT',openInterest:'110',time:now}));
  const derivatives=await fetchDerivatives();assert.equal(derivatives.openInterestValue,11000);assert.ok(Math.abs(derivatives.change5m-10)<1e-10);assert.equal(derivatives.funding*100,.01);
  global.fetch=async()=>{throw new Error('Offline');};
  const captured=await captureOverview({...empty,now},new AbortController().signal);
  for(const key of ['book','fundamentals','fear','derivatives']){assert.equal(captured[key].loading,false);assert.ok(captured[key].error);}
  const delayed=renderToStaticMarkup(React.createElement(MarketInsights,{overview:{...overview,now:now+180000},result:null,onReset:()=>{}}));assert.match(delayed,/DELAYED/);
 }finally{global.fetch=original;}
 console.log('PASS: depth math and validation, supply/FDV, fear bounds, derivatives units, all four decision views, loading failures and stale-data labels');
}
asyncChecks().catch(error=>{console.error(error);process.exitCode=1;});
