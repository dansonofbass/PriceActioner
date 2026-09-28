'use client';
import { useState } from 'react';
export default function BrandLogo() {
 const [missing, setMissing] = useState(false);
 return <a href="/" className="brand" aria-label="priceactioner home">{missing ? <span>priceactioner</span> : <img src="/brand/priceactioner-logo.png" alt="priceactioner" width={216} height={72} onError={() => setMissing(true)} />}</a>;
}
