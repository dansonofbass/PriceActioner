import BrandLogo from './BrandLogo';
export default function MarketHeader({ status, updated }: { status: string; updated?: number }) {
 return <><header className="topbar"><BrandLogo/><span className="app-tag">PRICE ACTION WORKSTATION</span><div className="top-status"><a className="admin-link" href="/docs">DOCS</a><span>BTC / USDT</span><span className="status-label"><i/> {status}</span>{(process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_SHOW_ADMIN === 'true') && <a className="admin-link" href="/admin">ADMIN ↗</a>}</div></header><div className="desktop-caption"><span>WORKSPACE / BTC SPOT</span><span>{updated ? `LAST FETCH ${new Date(updated).toLocaleTimeString()} · LOCAL` : 'PUBLIC MARKET DATA · NO ACCOUNT REQUIRED'}</span></div></>;
}
