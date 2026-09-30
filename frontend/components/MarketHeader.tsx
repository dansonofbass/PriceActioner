import { standalone } from '@/lib/mode';
import BrandLogo from './BrandLogo';
export default function MarketHeader({ status, updated }: { status: string; updated?: number }) {
 return <><header className="topbar"><BrandLogo/><span className="app-tag">PRICE ACTION WORKSTATION</span><div className="top-status"><span>BTC / USDT</span><span className="status-label"><i/> {status}</span>{!standalone && (process.env.NODE_ENV === 'development' || process.env.NEXT_PUBLIC_SHOW_ADMIN === 'true') && <a className="admin-link" href="/admin">ADMIN ↗</a>}</div></header><div className="desktop-caption"><span>WORKSPACE / BTC SPOT</span><span>{updated ? `LAST UPDATE ${new Date(updated).toLocaleTimeString()} · YOUR TIMEZONE` : 'PUBLIC MARKET DATA · NO ACCOUNT REQUIRED'}</span></div></>;
}
