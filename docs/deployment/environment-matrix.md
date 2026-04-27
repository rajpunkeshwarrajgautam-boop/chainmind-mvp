# Environment matrix — API (Render) vs web (Vercel) vs local

This document is the **single cross-environment checklist** for deployment topology. Detailed procedures stay in:

- [render-blueprint.md](./render-blueprint.md) — Render Blueprint sync, Redis, `DATABASE_URL`, smoke checks.
- [vercel-and-github.md](./vercel-and-github.md) — Vercel import, root directory `web`, CORS, connectivity script.

## Topology (authoritative)

| Layer | Hosts | Notes |
|-------|--------|--------|
| **API** | Render Web Service from root `render.yaml` (`chainmind-mvp` service) + managed Postgres (`DATABASE_URL` in dashboard) + Key Value Redis | Next.js is **not** deployed here. |
| **Browser UI** | Vercel project with **Root Directory = `web`** | FastAPI is **not** deployed here; UI proxies `/api/*` to the API. |
| **Local dev** | `uvicorn` on `127.0.0.1:8000` (or script) + optional `npm run dev` in `web/` | Same env *names* as prod where applicable; values point at localhost. |

## Variable matrix

| Variable | Where set | Local dev | Render (API) | Vercel Production | Vercel Preview (all branches) |
|----------|-----------|-----------|--------------|-------------------|------------------------------|
| **`DATABASE_URL`** | API only | SQLite or local Postgres from `.env` | **Dashboard** (`sync: false` in `render.yaml`) | *N/A* | *N/A* |
| **`JWT_SECRET`** | API only | `.env` | `generateValue` in `render.yaml` or override in dashboard | *N/A* | *N/A* |
| **`REDIS_URL`**, **`CELERY_*`** | API only | `.env` or Docker | From Key Value connection in `render.yaml` | *N/A* | *N/A* |
| **`CELERY_TASK_ALWAYS_EAGER`** | API only | `true` for no worker | `true` in `render.yaml` (MVP tradeoff) | *N/A* | *N/A* |
| **`CORS_ORIGINS`** / **`CORS_ORIGIN_REGEX`** | API only | Include `http://localhost:3000` and production web URL | Set in `render.yaml` (update if web hostname changes) | *N/A* | *N/A* |
| **`API_ORIGIN`** | **Vercel + local Next** | `API_ORIGIN=http://127.0.0.1:8000` when running `web/` (optional; matches `next.config.mjs` default) | *N/A* | **Required** — public `https://…` API base **without** trailing slash | **Required** — set for Preview target (see below) |
| **`NEXT_PUBLIC_API_ORIGIN`** | **Vercel + local Next** | Same as API for OpenAPI/docs links in UI | Same as production API URL | **Required** — usually **same value** as `API_ORIGIN` | **Required** for previews (see below) |

### Vercel Preview vs Production

- **Production:** set `API_ORIGIN` and `NEXT_PUBLIC_API_ORIGIN` to your stable API hostname (e.g. Render service URL).
- **Preview:** each deployment must resolve `/api/*` rewrites to a running API. Options:
  1. **Shared staging API** — set Preview env vars to the same staging `https://api-staging…` (simplest).
  2. **Per-branch APIs** — only if you operate matching API previews; keep CORS (`CORS_ORIGIN_REGEX` on the API) aligned with `*.vercel.app`.

If Preview env vars are missing, `web/next.config.mjs` falls back to `http://127.0.0.1:8000` at **build time**, which breaks hosted previews — see [vercel-and-github.md §2](./vercel-and-github.md).

## Verification commands

| Check | Command / action |
|-------|------------------|
| API vertical slice | `CHAINMIND_BASE_URL=https://your-api… python scripts/verify_vertical_slice.py` |
| API in CI (no server) | `python scripts/verify_vertical_slice.py --in-process` |
| Vercel → API rewrite + CORS | `.\scripts\verify_vercel_api_connectivity.ps1` (from repo root on Windows) |

## Pilot honesty rule

Only treat **billing** and **ERP integrations** as production-capable after env + implementation work described in `.env.example` and [../qa/pilot-scope-boundaries.md](../qa/pilot-scope-boundaries.md). Until then, automated **boundary** tests lock expected stub behaviour.
