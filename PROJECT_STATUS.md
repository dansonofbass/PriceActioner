# priceactioner — handoff state

## Scope and completed product

Milestone 1 implements a BTC/USDT analysis workstation using Next.js, React, TypeScript, Tailwind, Pixelify Sans and FastAPI/Pydantic. The deterministic engine computes normalized closed candles, strict cutoffs, indicators, confirmed pivots, structures, support/resistance strength, events, volume, volatility, confluence, horizon alignment, evidence and invalidation. No trading, wallets, exchange accounts or Binance credentials exist.

The public form, chart, results, Persian /docs walkthrough and REQUEST.PREVIEW are complete. The preview exposes the caller's exact local state/questions draft without secrets. Public disabled Jev labels were removed as requested, but live Jev integration remains unimplemented and JEV_MODE=disabled is enforced. Admin diagnostics state this truthfully.

Admin includes login, salted scrypt hashes, hashed expiring session tokens, origin checks, login throttling, history, filtered logs, raw arrays, indicators, pivots, zones, horizon simulator, decision context, source map and configuration inspection. Production cookies are Secure, HttpOnly and SameSite=Strict.

## Current persistence: no SQL runtime

- Local development: JSON documents under ignored backend/data, protected by an OS file lock and atomic replacement.
- Production/Vercel: MongoDB Atlas via PyMongo. Local JSON mode is rejected in production/Vercel to avoid ephemeral persistence.
- Admins, sessions, analyses, logs, visitors, daily quotas and login-attempt counters use the shared document interface. MongoDB quota reservations use a conditional atomic single-document update.
- SQLAlchemy/SQLite runtime code and dependencies were removed.
- Existing local records were migrated and compared: 1 admin, 1 session, 6 analyses, 333 logs, 2 visitors and 1 daily quota document at migration time. Further local use may add records.
- The original database was moved to ignored artifacts/legacy-sqlite-backup.db for rollback; the running application does not read it. The user's local admin password hash was preserved.
- upload_records.py previews counts by default; --confirm explicitly copies only local analyses/logs to configured MongoDB without overwriting existing IDs. No upload has been performed.

Three successful analyses per UTC day are enforced per browser cookie, with atomic reservations and ordinary-failure refunds. This is not verified per-person enforcement: clearing cookies or using another browser bypasses it. No automatic history retention policy exists.

## Deployment and handoff

One GitHub repository is intended for two Vercel projects, root directories frontend and backend. Backend uses MongoDB Atlas; frontend BACKEND_URL points to backend, and backend PUBLIC_ORIGIN points to frontend. backend/vercel.json and .python-version configure the Python deployment. docs/DEPLOYMENT.fa.md provides the complete Persian folder, GitHub, Atlas, environment-variable, deployment and smoke-test instructions.

The source ZIP script excludes secrets, backend/data, old databases, environments, installed dependencies, caches, logs and build output. It verifies CRC and required/excluded paths. The user's Explorer screenshot showed Access denied for bin but no full path, so the exact Windows permission cause remains unconfirmed.

No GitHub repository, Atlas cluster, Vercel deployment, paid plan or domain has been created. Live Atlas integration is unverified; cloud readiness is based on implementation, official deployment documentation and local tests, not an actual deployment.

## Verification

- 67 Python tests passed after the storage migration. API/auth/history/logs/quota tests run against both real temporary JSON storage and a mocked MongoDB client. Tests cover concurrent reservations across independent store instances, midnight resets, refunds and persistence. Engine tests retain independent indicator recurrences and future-cutoff invariance.
- One upstream Starlette TestClient deprecation warning remains; tests pass.
- Next.js production build, including type checking, passed.
- After migration, local frontend-proxy health, preserved admin login, six existing history records, saved-analysis retrieval, docs, usage and logout all returned HTTP 200. A fresh real multi-timeframe analysis completed READY without missing timeframes; its JSON record and exact serialized preview were verified. Local analysis count is now seven.
- Earlier npm audit reported zero vulnerabilities and Python dependency check passed.
- Browser automation surfaces were unavailable; rendered desktop/mobile visual QA has not been completed.

## Assets and local operation

frontend/public/reference/ui-reference.png was inspected and guides the retro desktop. frontend/public/brand/priceactioner-logo.png is used without alteration. The icon-only asset is still absent; do not invent or crop it from the logo.

Backend runs from backend at 127.0.0.1:8000; frontend is accessed at http://localhost:3000. The local admin username is admin and the user-chosen password remains in force; no plaintext credential is included in source or ZIP. setup_admin.py is available for explicit local password resets/new installations. Cloud accounts are separately bootstrapped from private environment variables, as documented.
