'use client';
import { useEffect, useState } from 'react';
import { visitorTime } from '@/lib/visitor-time';
export default function LocalClock(){
 const [clock,setClock]=useState({label:'YOUR TIME —',iso:'',source:'Reading your device timezone'});
 useEffect(()=>{
  const controller=new AbortController();let anchor:{time:number;elapsed:number}|null=null,pending=false;
  const update=()=>{const timestamp=anchor?anchor.time+performance.now()-anchor.elapsed:Date.now();setClock({label:visitorTime(timestamp).label,iso:new Date(timestamp).toISOString(),source:anchor?'Time synchronized with Binance; timezone from your device':'Device clock; network time synchronization unavailable'});};
  async function synchronize(){
   if(pending||controller.signal.aborted||document.visibilityState==='hidden')return;
   pending=true;const start=performance.now();
   try{const response=await fetch('https://data-api.binance.vision/api/v3/time',{cache:'no-store',credentials:'omit',signal:AbortSignal.any([controller.signal,AbortSignal.timeout(8000)])});if(!response.ok)throw new Error('Time unavailable');const data=await response.json(),end=performance.now();if(typeof data.serverTime!=='number'||!Number.isFinite(data.serverTime)||data.serverTime<=0)throw new Error('Invalid time');if(!controller.signal.aborted){anchor={time:data.serverTime+(end-start)/2,elapsed:end};update();}}
   catch{if(!controller.signal.aborted)update();}finally{pending=false;}
  }
  update();void synchronize();const timer=setInterval(update,1000),syncTimer=setInterval(()=>void synchronize(),60000);
  const resume=()=>{if(document.visibilityState==='visible'){update();void synchronize();}};
  document.addEventListener('visibilitychange',resume);
  return()=>{controller.abort();clearInterval(timer);clearInterval(syncTimer);document.removeEventListener('visibilitychange',resume);};
 },[]);
 return <time dateTime={clock.iso||undefined} title={clock.source}>{clock.label}</time>;
}
