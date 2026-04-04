# Trishul Frontend

Unified Next.js frontend for all repository UI surfaces.

## Backend integration status

- ✅ Auth-first wiring implemented (`/auth`)
- ✅ Operations wired to backend scan APIs (`/api/v1/scans/start`, `/api/v1/scans/{scan_id}`)
- ✅ Reports route implemented and wired (`/reports`) with `/api/v1/stats` and `/api/v1/reports/generate`
- ✅ JWT token persistence and authenticated API client added
- ✅ Loading/error/empty states added for API-backed flows
- ✅ Header search connected to backend DB tracking for attacked websites
- ✅ Rich backend endpoints added for operations/reports analytics

## Current UX structure

- Landing
- Operations Dashboard
- Reports/Analytics

## Design profile

- Monochrome palette (white/black/space gray)
- Inter as single type family
- Subtle scroll animations with reduced-motion support
- No cyberpunk visuals

## Getting started

```bash
cd frontend
npm install
# set backend base URL if not default localhost:8000
export NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Required backend

Run FastAPI backend from repo root:

```bash
./start_api.sh
```

Then:
1. Open `/auth` and sign in/register.
2. Start scans from `/operations`.
3. Generate report summaries from `/reports` using a scan id.
4. Use header search to query attacked websites tracked per-user.

## New backend endpoints used by frontend

- `GET /api/v1/operations/overview` (scans + events stream)
- `GET /api/v1/reports/analytics` (KPI analytics)
- `GET /api/v1/search/attacked-sites?query=...`
- `GET /api/v1/search/recent`

Per-user tracking behavior:
- Search and attacked-site history is isolated by JWT user identity.
- A site is counted as "attacked" only when scan reaches terminal status (`completed` / `failed`).

## Key files

```text
frontend/src/app/auth/page.tsx
frontend/src/app/operations/page.tsx
frontend/src/app/reports/page.tsx
frontend/src/components/navigation/*
frontend/src/components/landing/*
frontend/src/components/operations/*
frontend/src/lib/api-client.ts
frontend/src/lib/api-contract.ts
frontend/src/lib/auth.ts
frontend/src/lib/types.ts
frontend/src/styles/globals.css
```
