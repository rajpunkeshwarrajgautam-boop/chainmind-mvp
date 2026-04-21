# Deploy the Next.js shell to Vercel + GitHub (fresh)

The **FastAPI backend is not deployed by this flow** — Vercel hosts the `web/` Next app only. Point `API_ORIGIN` at wherever your API runs (Render, Fly.io, Railway, VM, etc.).

## 1) GitHub (new repo)

1. Create a repository (empty or with README — you will push from local).
2. From `chainmind-mvp` on your machine:

   ```powershell
   cd "D:\ai company\chainmind-mvp"
   git init
   git add -A
   git commit -m "Initial import: ChainMind MVP"
   git branch -M main
   git remote add origin https://github.com/<you>/<repo>.git
   git push -u origin main
   ```

   Or with GitHub CLI (if logged in):

   ```powershell
   gh repo create <you>/chainmind-mvp --public --source=. --remote=origin --push
   ```

   If push fails with **OAuth App cannot update workflow** errors, refresh scopes and restore workflows per `docs/deployment/github-workflows-restore.md`.

## 2) Vercel (new project)

1. Sign in at [https://vercel.com/new](https://vercel.com/new).
2. **Import** the GitHub repository.
3. **Root Directory:** set to `web` (monorepo).
4. **Framework preset:** Next.js (auto).
5. **Build & Output:** defaults (`next build` / `.next`).
6. **Team scope (CLI):** if `vercel` asks for a scope in non-interactive mode, pass `--scope <your-team-slug>` (example: `rajpunkeshwarrajgautam-boops-projects`).
7. **Environment variables** (Production + Preview as needed):

   | Name | Example | Purpose |
   |------|---------|---------|
   | `API_ORIGIN` | `https://api.your-domain.com` | Server-side rewrite target for `/api/*` |
   | `NEXT_PUBLIC_API_ORIGIN` | same as API | Link to OpenAPI `/docs` in the UI |

8. Deploy. After first deploy, open the Vercel URL and confirm the smoke page loads; API calls succeed only if `API_ORIGIN` is reachable from Vercel’s edge (your API must allow that host in CORS — set `CORS_ORIGINS` on the API to include your `*.vercel.app` preview URL and production web URL).

**If the page loads but API calls fail:** set `API_ORIGIN` and `NEXT_PUBLIC_API_ORIGIN` in the Vercel project to your real API base URL, then redeploy. Until then, rewrites may still point at the default `http://127.0.0.1:8000` from build config.

**Monorepo Git + Vercel:** run `vercel link` and `vercel git connect` from the repository root (where `.git` lives) so Vercel sees the GitHub repo. Set **Root Directory** to `web` in the project settings (or PATCH the project via the REST API). Production and Preview should both define `API_ORIGIN` / `NEXT_PUBLIC_API_ORIGIN`; if the CLI refuses Preview without a branch, use the REST API `POST /v10/projects/{id}/env?upsert=true` with `"target":["preview"]` and no `gitBranch` so the variables apply to all preview branches.

## 3) CORS on the API

Add your Vercel domain(s) to the API env, e.g.:

`CORS_ORIGINS=https://chainmind-xxx.vercel.app,https://app.your-domain.com`

## 4) CLI alternative

From `web/` after `npm install`:

```powershell
cd web
npx vercel login
npx vercel --prod
```

Link picks up `vercel.json` if present; set env vars in the Vercel dashboard or `npx vercel env add`.

## 5) Verify API URL, rewrites, and CORS

After the API is actually deployed (Render shows a **Web Service**, not an empty hostname), run:

```powershell
cd "D:\ai company\chainmind-mvp"
.\scripts\verify_vercel_api_connectivity.ps1
# or, against another API:
.\scripts\verify_vercel_api_connectivity.ps1 -ApiOrigin "https://your-api.example.com"
```

The script fails fast if Render returns `x-render-routing: no-server` (no service at that URL). It then checks an OPTIONS preflight and a GET through the Vercel `/api/*` rewrite.
