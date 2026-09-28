'use client';
import { useState } from 'react';
import RetroWindow from './RetroWindow';
import type { Result } from '@/lib/types';

export default function RequestPreview({ result }: { result: Result }) {
 const [view,setView]=useState('READABLE'),[copied,setCopied]=useState(false),[copyError,setCopyError]=useState('');
 const preview=result.request_preview;
 if(!preview)return null;
 const content=view==='READABLE'?result.human_preview:view==='STATE'?JSON.stringify(preview.payload.state,null,2):view==='QUESTIONS'?JSON.stringify(preview.payload.questions,null,2):preview.serialized_request;
 return <RetroWindow title="REQUEST.PREVIEW" status="YOUR ANALYSIS INPUT"><details className="request-preview"><summary>SEE HOW YOUR FORM BECOMES A STRUCTURED REQUEST</summary><p>Your form supplies the user intent. Python adds market evidence to the state. Six fixed questions ask how to interpret that state. No prompt writing is needed.</p><p className="source-note">This is a local draft for inspection. Nothing has been sent to an AI service. The live provider request format has not yet been verified.</p><div className="admin-tabs-inline">{['READABLE','STATE','QUESTIONS','FULL REQUEST'].map(label=><button type="button" key={label} aria-pressed={view===label} className={view===label?'active':''} onClick={()=>setView(label)}>{label}</button>)}</div><pre>{content}</pre><div className="admin-tools"><button type="button" onClick={async()=>{try{await navigator.clipboard.writeText(preview.serialized_request);setCopied(true);setCopyError('');}catch{setCopyError('Select and copy the FULL REQUEST text above.');}}}>{copied?'COPIED FULL REQUEST':'COPY FULL REQUEST'}</button><span>{preview.character_count.toLocaleString()} characters · ≈{preview.approximate_token_count.toLocaleString()} tokens (estimate)</span></div>{copyError&&<p role="status">{copyError}</p>}<p className="source-note">The full request contains exactly the same state and questions shown here, serialized as JSON. It contains no API key.</p></details></RetroWindow>;
}
