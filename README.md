# priceactioner

For sharing a source-only ZIP and deploying this exact project: [Persian deployment guide](docs/DEPLOYMENT.fa.md). Run `python scripts/make_source_zip.py` from the root to package code without credentials, local databases or installed dependencies.

Milestone 1: a BTC/USDT market-analysis workstation with a Next.js frontend, deterministic Python engine, JSON/MongoDB document storage, and authenticated admin inspection. No SQL database is required. **Jev is locked to `disabled`.** No trade execution, exchange accounts, wallet connections, or Binance credentials exist in this application.

## Run locally (Windows / PowerShell)

From the repository root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
cd frontend
npm.cmd ci
cd ..\backend
..\.venv\Scripts\python.exe setup_admin.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

In a second terminal:

```powershell
cd frontend
npm.cmd run dev
```

Open **http://localhost:3000**. Admin: **http://localhost:3000/admin/login**.

Simple Persian walkthrough: **http://localhost:3000/docs** or [the user guide](docs/USER_GUIDE.fa.md). After submitting, open **REQUEST.PREVIEW → FULL REQUEST** to inspect/copy the exact local state/questions payload without admin login.

Public users have **3 successful analyses per UTC day**, persisted in document storage and identified by an HttpOnly browser cookie. Concurrent requests reserve quota atomically; ordinary failures refund it. This is a per-browser MVP allowance, not verified per-person enforcement: another browser or cleared cookies can bypass it. A strict per-person quota requires user accounts. Chart refreshes, docs and preview inspection do not consume analysis quota.

The interactive admin setup asks for your username and password, writes only the salted password hash to document storage, and generates a session-signing secret in ignored `backend/.env`. Run it again to reset an admin password and revoke that admin's sessions. Restart the backend after setup. You can alternatively populate `ADMIN_USERNAME`, `ADMIN_PASSWORD`, and `ADMIN_SECRET_KEY` using environment variables for first-run bootstrap; records never store a plaintext password. There is no default password. Public analysis works before admin setup.

Python 3.11+ and Node 20.9+ are required. The build was tested with Python 3.14 and Node 24. Keep the backend's working directory at `backend` so `.env` and the local data path resolve consistently. In shells with strict cache permissions, use `pip install --no-cache-dir ...` and `npm.cmd ci --cache .npm-cache`.

## Verify

```powershell
cd backend
..\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
..\.venv\Scripts\python.exe -m pytest -q
cd ..\frontend
npm.cmd run build
npm.cmd audit
```

Tests use fixed synthetic fixtures, isolated temporary JSON storage and a mocked MongoDB client. They never require Binance or send Jev requests. They independently check RSI/EMA/MACD/ATR recurrences, normalization, confirmed pivots, future-cutoff invariance, structures, zone strength, breakouts, volume, horizons, alignment, invalidation, context generation, sessions, CSRF, history, logs, failures and concurrent quota reservations across storage instances. Mocked MongoDB tests do not replace a real Atlas deployment smoke test.

## Workspaces

- `/`: structured intent form; Binance candles and volume; deterministic results; support/resistance; momentum; volume; volatility; evidence breakdown; structural invalidation.
- `/docs`: a simple Persian form/output/request-preview walkthrough, with an educational example.
- `/api/usage`: this browser's remaining daily allowance and UTC reset time.
- `/admin/login`: admin-only session login.
- `/admin`: overview, raw arrays and normalized candles, indicators, short/major pivots, S/R score components, horizon simulator, context JSON/readable/source map, unsent Jev draft, paginated history/logs, and configuration snapshots.
- `/api/health`: backend/database status, observed Binance status, engine version, and Jev status without secrets.
- `/api/docs`: development-only FastAPI endpoint documentation.

Frontend API requests use a same-origin Next.js rewrite to `BACKEND_URL` (default `http://127.0.0.1:8000`). Use `PUBLIC_ORIGIN` for the browser origin, default `http://localhost:3000`; mutation requests with another Origin are rejected. The admin shortcut is hidden in production unless `NEXT_PUBLIC_SHOW_ADMIN=true`.

## Calculation contract

All timestamps and cutoffs are UTC milliseconds. Candle-based analysis receives normalized `Candle` objects and `cutoff_timestamp`; open candles and candles closing after the cutoff are excluded. Derived modules such as market structure and confluence receive only those filtered outputs. Pivots require 5/5 or 20/20 confirmation bars, including the full right side. Equal extrema are not pivots. Structure is based on the last two major highs/lows, with HH/HL bullish, LH/LL bearish, contracting highs/lows range, and otherwise transition.

The chart may show the current open candle; analysis uses closed candles. The result reference price comes from the most granular available closed candle and is explicitly labeled separately from the chart snapshot. Market snapshots cache for only 15 seconds; failed requests never fall back to stale cached data. Quote refresh is manual. Missing primary timeframes stop analysis; missing other timeframes produce PARTIAL DATA and zero directional alignment contribution without reweighting.

`backend/app/config.py` centralizes weights, horizons, pivot windows, ATR clustering, volume/volatility thresholds, and zone score caps. Every saved analysis includes the version, cutoff, config snapshot, context, technical traces, unsent Jev draft, and no user identity.

See [calculation details](docs/CALCULATIONS.md) for formulas, assumptions, and source references. The source map is also visible in admin. Evidence scores are heuristics, not calibrated probabilities. Risk profile, priority, entry price, and intended action are preserved in the context; they do not alter objective market measurements or manufacture a personalized buy/sell recommendation.

## Jev boundary

`JEV_MODE=disabled` is required. Setting `preview` or `live` causes startup validation to fail. The admin can inspect generated state, six static typed questions, draft serialization, character count, and approximate tokens. The payload is a **local inspection draft**, not a verified live TypeSafe contract. There is no send button, live client, or automatic external AI call. Milestones 2 and 3 remain intentionally unimplemented.

## Brand and reference

The supplied `frontend/public/brand/priceactioner-logo.png` is used without alteration. Missing brand imagery falls back to lowercase **priceactioner** text. The visual reference at `frontend/public/reference/ui-reference.png` guides the dotted blue desktop, compact black title bars, grayscale windows, inset edges and hard shadows; it is not rendered in the product. Pixelify Sans is loaded by `next/font/google` at build time (400/600/700), with no runtime CSS font import.

The icon-only asset has not been supplied. Put the supplied icon at `frontend/app/icon.png` to enable the Next.js favicon; it is deliberately not regenerated or extracted from the full logo.

## Storage and deployment

Local development defaults to `STORAGE_BACKEND=json` with locked, atomically replaced files under ignored `backend/data/`. Production requires `STORAGE_BACKEND=mongodb`, a private `MONGODB_URI` and `MONGODB_DATABASE=priceactioner`. Admins, sessions, analyses, logs, visitors, quotas and login-attempt counters live in the selected store. SQLAlchemy and SQLite are no longer runtime dependencies. JSON mode is rejected on Vercel to prevent relying on ephemeral local files.

Deploy one GitHub repository as two Vercel projects: root `frontend` for Next.js and root `backend` for FastAPI. Connect the backend to MongoDB Atlas. Set backend `APP_ENV=production`, `PUBLIC_ORIGIN` to the frontend HTTPS origin and a strong `ADMIN_SECRET_KEY`. Set frontend `BACKEND_URL` to the backend production origin, then redeploy. The [complete Persian guide](docs/DEPLOYMENT.fa.md) includes every environment variable and verification step.

Production session cookies are Secure, HttpOnly, SameSite=Strict and expire after 8 hours. Login attempts use a persistent limit of 5 per fixed 5-minute window per connection IP and supplied username. Session secrets and `.env` must stay private. History and structured logs have no automatic retention policy; arrange backups and cleanup appropriate to your use. `upload_records.py` previews optional local history/log migration; `--confirm` uploads to configured MongoDB without overwriting existing IDs or transferring credentials. No production hosting, domain or external service has been deployed.

Experimental market-analysis software. Technical and model assessments are informational and are not financial advice.
