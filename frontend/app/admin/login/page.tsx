'use client';
import AdminUnavailable from '@/components/AdminUnavailable';
import { standalone } from '@/lib/mode';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import RetroWindow from '@/components/RetroWindow';
import BrandLogo from '@/components/BrandLogo';
import { api } from '@/lib/api';
export default function Login(){const router=useRouter();const [busy,setBusy]=useState(false),[error,setError]=useState('');if(standalone)return <AdminUnavailable/>;return <main className="login-page"><RetroWindow title="ADMIN.LOGIN" status="RESTRICTED"><BrandLogo/><h1>Enter the workspace.</h1><form onSubmit={async e=>{e.preventDefault();const f=new FormData(e.currentTarget);setBusy(true);setError('');try{await api('/admin/login',{method:'POST',body:JSON.stringify({username:f.get('username'),password:f.get('password')})});router.replace('/admin');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}><label className="field">Username<input autoComplete="username" name="username" required maxLength={100}/></label><label className="field">Password<input autoComplete="current-password" type="password" name="password" required maxLength={1024}/></label>{error&&<p role="alert" className="inline-error">{error}</p>}<button className="primary-button" disabled={busy}>{busy?'AUTHENTICATING…':'LOGIN'}<span>↗</span></button></form><p className="login-note">ADMIN ACCESS ONLY · JEV DISABLED</p><a href="/">← BACK TO BTC WORKSPACE</a></RetroWindow></main>;}
