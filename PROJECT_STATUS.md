# PRICEACTIONER current handoff

## Current requested architecture

FastAPI performs deterministic BTC analysis and builds an unsent Jev state/questions draft. Next.js provides public forms/results and authenticated admin inspection. No live Jev calls or trades exist.

MongoDB runtime, dependencies and environment variables have been removed. Production uses Upstash Redis over HTTPS, with UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN. Local development retains JSON files and the existing local admin. MongoDB data is not migrated or deleted remotely.

Redis stores salted admin hashes, hashed session tokens, anonymous visitor records, atomic daily quota counters, login throttles and bounded inspection records. It retains at most 100 analyses and 2000 log events, for at most seven days. Native expiries handle sessions (8 hours), daily counters (2 days), login throttles (10 minutes) and visitor records (1 year). Admin hashes do not expire. Large documents are compressed losslessly. Local JSON has no automatic retention.

Lua scripts make quota increments/refunds and record/index writes atomic. HTTPS transport never logs tokens or returns upstream secrets. No automatic write retries are used because ambiguous network responses could otherwise double-count reservations. Redis eviction should remain disabled. Ordinary failures refund quota; a storage outage or hard process termination can leave a reservation until UTC reset. Log persistence is best effort during outages.

ASGI startup does not contact Redis; /api/health reports OFFLINE and a safe diagnostic when credentials are missing or service is unavailable. Admin is bootstrapped on login. Quota-dependent requests fail closed with a clear 503; no ephemeral counter fallback exists.

## Admin inspection

FORM.PROMPT replaces JEV.PREVIEW and explicitly displays original form, calculated readable context, state/questions and exact serialized draft. HISTORY opens this panel for the selected analysis. LOGS can filter to the selected analysis. Existing calculation/indicator/pivot/context tabs remain available. Overview displays storage type/status and retention limits.

## Deployment

Existing frontend: https://price-actioner.vercel.app
Existing backend: https://price-actioner-api.vercel.app
One repository, two Vercel projects, root directories frontend and backend. backend/vercel.json explicitly selects fastapi. Backend PUBLIC_ORIGIN points to frontend; frontend BACKEND_URL points to backend (without /api).

Private backend/.env.production was updated to redis while preserving the latest cloud admin password and session secret. Its two Redis credentials are blank and must be supplied by the user from Upstash. This is not yet a deployable authenticated Redis connection. Old MongoDB variables must also be removed from Vercel dashboard. No service/account was created, no remote records changed, and no push or deployment was performed in this change.

Source ZIP excludes .env variants, local records, credentials, artifacts, installations and caches. Documentation: docs/DEPLOYMENT.fa.md and docs/USER_GUIDE.fa.md. Optional upload_records.py imports only local analysis/log records with --confirm.

## Verification

72 Python tests passed, including JSON and Redis emulator API/auth/history/preview/quota tests, actual Lua execution, concurrent reservations, retention caps, TTL preservation, compression, REST command transport, secret-safe errors and startup without Redis credentials. One upstream Starlette test-client deprecation warning remains. Next.js production build and type checking passed. Live Upstash connection is unverified until credentials are supplied.

User-provided logo/reference remain unchanged. Icon-only asset is absent. Browser-rendered visual QA has not been performed in this session.

Local post-change smoke test: updated services are running; preserved admin login and seven previous history records verified. A new real Binance analysis returned READY, with original form, exact serialized preview and analysis-filtered log retrieval verified through the frontend proxy. Source ZIP scanned for private environment values; none found.
