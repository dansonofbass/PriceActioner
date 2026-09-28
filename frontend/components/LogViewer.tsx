'use client';
import { useEffect, useState } from 'react';
import { api } from '@/lib/api';
import DebugTable from './DebugTable';
export default function LogViewer() {
 const [rows,setRows]=useState<Record<string,unknown>[]>([]),[error,setError]=useState(''),[query,setQuery]=useState(''),[offset,setOffset]=useState(0),[refresh,setRefresh]=useState(0);
 useEffect(()=>{api<Record<string,unknown>[]>(`/admin/logs?${query}&offset=${offset}`).then(setRows).catch(e=>setError(e.message));},[query,offset,refresh]);
 return <><form className="admin-tools" onSubmit={e=>{e.preventDefault();setError('');setRefresh(n=>n+1);const data=new FormData(e.currentTarget);setOffset(0);setQuery(new URLSearchParams(Array.from(data.entries()).map(([k,v])=>[k,String(v)])).toString());}}><label>LEVEL<select name="level"><option value="">ALL LEVELS</option>{['INFO','WARNING','ERROR'].map(l=><option key={l}>{l}</option>)}</select></label><label>COMPONENT<input name="component" placeholder="e.g. binance"/></label><label>ANALYSIS ID<input name="analysis_id" placeholder="Exact ID"/></label><label>SEARCH<input name="search" placeholder="Event or message"/></label><button type="submit">FILTER / REFRESH</button></form>{error&&<p role="alert">{error}</p>}<DebugTable rows={rows}/><div className="admin-tools"><button disabled={offset===0} onClick={()=>setOffset(Math.max(0,offset-100))}>PREVIOUS</button><span>ROWS {offset+1}–{offset+rows.length}</span><button disabled={rows.length<100} onClick={()=>setOffset(offset+100)}>NEXT</button></div></>;
}

