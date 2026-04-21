# ChainMind MVP

FastAPI service with optional Next.js shell. **Production path is API-first:** register → JWT → sample or CSV upload → forecast → list or fetch job.

## Run locally without Docker (recommended if you have no Docker)

You need **Python 3.12+** (3.14 works if dependencies install). Redis and Postgres are optional for a minimal dev loop.

### 1. Install dependencies

```bash
cd chainmind-mvp
python -m venv .venv
```

**Windows (PowerShell):** `.venv\Scripts\Activate.ps1`  
**macOS/Linux:** `source .venv/bin/activate`

```bash
pip install -r requirements.txt
```

### 2. Environment

Copy `.env.example` to `.env` and either:

- **Minimal (SQLite file, no separate DB server):** set  
  `DATABASE_URL=sqlite:///./chainmind-local.db`  
  `CELERY_TASK_ALWAYS_EAGER=true`  
  and a long random `JWT_SECRET` (32+ characters).

- **Or** keep the default Postgres URL if you already run Postgres locally.

### 3. Start the API

**Windows:**

```powershell
.\scripts\run_local.ps1
```

**macOS/Linux:**

```bash
chmod +x scripts/run_local.sh
./scripts/run_local.sh
```

**Manual (any OS):**

```bash
set DATABASE_URL=sqlite:///./chainmind-local.db
set CELERY_TASK_ALWAYS_EAGER=true
set JWT_SECRET=your-long-random-secret-at-least-32-chars
python -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

(PowerShell uses `$env:DATABASE_URL='...'` instead of `set`.)

- **API / Swagger:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **`/health`** — always useful.
- **`/ready`** — may return **503** if Redis is not running (`redis: false`). The API still serves forecasts; install [Redis for Windows](https://redis.io/docs/latest/operate/oss_and_stack/install/install-redis/install-redis-on-windows/) or ignore `/ready` for local dev.

### 4. Verify

In another terminal (with the same venv):

```bash
python scripts/verify_vertical_slice.py
```

No server at all (CI-style): `python scripts/verify_vertical_slice.py --in-process`

---

## Optional: full stack with Docker

If you install Docker later:

```bash
cd chainmind-mvp
docker compose up --build
```

- API: `http://localhost:8000`
- OpenAPI: `http://localhost:8000/docs`
- In `ENVIRONMENT=production` (as in compose for `api`), the legacy HTML `/` dashboard redirects to `/docs`; CSV flows use the authenticated endpoints below.

### Automated smoke (against running server)

```bash
python scripts/verify_vertical_slice.py
```

Optional: `CHAINMIND_BASE_URL=http://127.0.0.1:8765 python scripts/verify_vertical_slice.py`  
Without any server: `python scripts/verify_vertical_slice.py --in-process` (same checks as CI).

Then open `http://localhost:8000/docs` (or your port), **Authorize** with `Bearer <token>` from register/login, and exercise `POST /api/v1/forecast/sample` and `GET /api/v1/forecast/jobs/{job_id}`.

## Vertical slice (curl)

Replace `slug`, email, and password. (On Windows, use PowerShell `Invoke-RestMethod` or Git Bash instead of `jq`/`tee` if needed.)

```bash
BASE=http://localhost:8000

curl -sS -X POST "$BASE/api/v1/auth/register" -H "Content-Type: application/json" \
  -d '{"tenant_slug":"demo-co","tenant_name":"Demo","email":"you@example.com","password":"longpassword123"}' | tee /tmp/reg.json
TOKEN=$(jq -r .access_token /tmp/reg.json)

curl -sS -X POST "$BASE/api/v1/forecast/sample" -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"days_ahead":14}' | tee /tmp/sample.json
JOB=$(jq -r .job_id /tmp/sample.json)

curl -sS "$BASE/api/v1/forecast/jobs/$JOB" -H "Authorization: Bearer $TOKEN" | jq .

curl -sS "$BASE/api/v1/forecast/jobs?limit=5" -H "Authorization: Bearer $TOKEN" | jq .
```

### CSV upload (authenticated)

Preview:

```bash
curl -sS -X POST "$BASE/api/v1/uploads/preview" -H "Authorization: Bearer $TOKEN" -F "file=@your.csv" | jq .
```

Forecast + persist `Upload` + `ForecastJob` (multipart form field `days_ahead` optional, default 30):

```bash
curl -sS -X POST "$BASE/api/v1/uploads/forecast" -H "Authorization: Bearer $TOKEN" \
  -F "file=@your.csv" -F "days_ahead=30" | jq .
```

## Async jobs (Celery)

`POST /api/v1/forecast/jobs` enqueues work; poll `GET /api/v1/forecast/jobs/{id}`.

- **Without Docker:** set `CELERY_TASK_ALWAYS_EAGER=true` so tasks run in the API process (no separate worker). No Redis required for that mode.
- **With Docker:** run the `worker` service, or run `celery -A app.workers.celery_app worker` locally with `REDIS_URL` pointing at a running Redis.

## Next.js shell (optional)

```bash
cd web
npm install
# Proxies /api/* to the backend (see web/next.config.mjs)
API_ORIGIN=http://127.0.0.1:8000 npm run dev
```

Open `http://localhost:3000` for a minimal register / sample / job smoke UI.

## Pilot sales positioning

- **Safe claim:** Paid pilot / early access for selected customers.
- **Avoid claim:** Enterprise-ready / certified / production SLA.
- Before charging, complete `docs/runbooks/pilot-go-live-checklist.md`.
- Contract language starter: `docs/legal/pilot-sow-template.md`.
- Stripe cutover runbook: `docs/runbooks/stripe-live-cutover-check.md`.
- Evidence bundle from a real host:

  ```powershell
  $env:CHAINMIND_BASE_URL = "https://api.your-domain.com"
  python scripts\verify_vertical_slice.py --evidence-dir pilot-evidence\deploy-2026-04-21
  ```

  Attach the generated folder (or zip) to your ticket; use `docs/runbooks/pilot-deployment-evidence-log.md` as the cover sheet.

## Completion checklist (no Docker)

1. **Python venv** — create, activate, `pip install -r requirements.txt`.
2. **`.env`** — `DATABASE_URL=sqlite:///./chainmind-local.db`, `CELERY_TASK_ALWAYS_EAGER=true`, `JWT_SECRET` (32+ chars).
3. **Run API** — `.\scripts\run_local.ps1` or `./scripts/run_local.sh` or `uvicorn` command above.
4. **Health** — browser or `Invoke-WebRequest http://127.0.0.1:8000/health` (PowerShell).
5. **Smoke** — `python scripts/verify_vertical_slice.py`.
6. **Swagger** — [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) → **Authorize** → `POST /api/v1/forecast/sample` → `GET /api/v1/forecast/jobs/{job_id}`.
7. **Optional Next** — `cd web && npm install && API_ORIGIN=http://127.0.0.1:8000 npm run dev`.

## Completion checklist (with Docker, optional)

1. **Copy env** — `cp .env.example .env`, set `JWT_SECRET` (32+ chars).
2. **Docker** — `docker compose up --build -d`.
3. **Wait for health** — `curl -s http://localhost:8000/health` → `{"status":"ok",...}`.
4. **Automated slice** — `python scripts/verify_vertical_slice.py`.
5. **Swagger** — same as above.
6. **Optional Next** — `cd web && npm install && API_ORIGIN=http://127.0.0.1:8000 npm run dev`.
7. **Async path** — worker container or local Celery worker + Redis; poll jobs until `completed`.

## Stripe (optional, test mode)

Set `STRIPE_SECRET_KEY`, `STRIPE_PRICE_ID_STARTER`, and for webhooks `STRIPE_WEBHOOK_SECRET`. Without them, `/api/v1/billing/*` returns **501** — the app runs without paid plans.

## OIDC SSO

See `docs/deployment/oidc-scope-groups.md`. JWT remains the primary integration for automation.

## Deploy Next.js to Vercel + GitHub

See `docs/deployment/vercel-and-github.md` (root directory **`web`**, set `API_ORIGIN` + `NEXT_PUBLIC_API_ORIGIN`). The Python API must be hosted separately.
