import type { ReactNode } from 'react';
export default function RetroWindow({ title, children, actions, status, className = '' }: { title: string; children: ReactNode; actions?: ReactNode; status?: string; className?: string }) {
 return <section className={`retro-window ${className}`}><header className="window-title"><span className="window-dot" aria-hidden="true"/><h2>{title}</h2>{status && <span className="window-status">{status}</span>}<div className="window-actions">{actions}<span aria-hidden="true">━ □</span></div></header><div className="window-body">{children}</div></section>;
}
