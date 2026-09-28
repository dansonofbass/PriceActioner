'use client';
import { useEffect, useState } from 'react';
export default function LocalClock(){
 const [label,setLabel]=useState('LOCAL TIME');
 useEffect(()=>{const update=()=>setLabel(new Intl.DateTimeFormat('en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit',hourCycle:'h23'}).format(new Date())+' · '+Intl.DateTimeFormat().resolvedOptions().timeZone);update();const timer=setInterval(update,1000);return()=>clearInterval(timer);},[]);
 return <span>{label}</span>;
}
