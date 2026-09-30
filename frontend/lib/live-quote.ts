'use client';
import { useEffect, useState } from 'react';
export function useLiveQuote(){
 const [quote,setQuote]=useState<{price:number;time:number}|null>(null),[now,setNow]=useState(Date.now());
 useEffect(()=>{let disposed=false,socket:WebSocket|null=null,reconnect:ReturnType<typeof setTimeout>;const controller=new AbortController();
 function connect(){if(disposed)return;socket=new WebSocket('wss://data-stream.binance.vision:443/ws/btcusdt@trade');socket.onmessage=event=>{try{const data=JSON.parse(event.data);const price=Number(data.p),time=Number(data.T);if(data.s==='BTCUSDT'&&Number.isFinite(price)&&price>0&&Number.isFinite(time))setQuote(old=>!old||time>=old.time?{price,time}:old);}catch{}};socket.onerror=()=>socket?.close();socket.onclose=()=>{if(!disposed)reconnect=setTimeout(connect,3000);};}
 let pending=false;async function poll(){if(pending||disposed)return;pending=true;try{const r=await fetch('https://data-api.binance.vision/api/v3/trades?symbol=BTCUSDT&limit=1',{cache:'no-store',credentials:'omit',signal:AbortSignal.any([controller.signal,AbortSignal.timeout(10000)])});if(!r.ok)return;const data=await r.json(),price=Number(data[0]?.price),time=Number(data[0]?.time);if(!disposed&&price>0&&Number.isFinite(price)&&Number.isFinite(time))setQuote(old=>!old||time>=old.time?{price,time}:old);}catch{}finally{pending=false;}}
 connect();void poll();const timer=setInterval(()=>{setNow(Date.now());void poll();},5000);return()=>{disposed=true;controller.abort();clearTimeout(reconnect);clearInterval(timer);socket?.close();};
 },[]);
 return {quote,stale:!quote||now-quote.time>15000};
}
