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

## 2) Vercel (new project)

1. Sign in at [https://vercel.com/new](https://vercel.com/new).
2. **Import** the GitHub repository.
3. **Root Directory:** set to `web` (monorepo).
4. **Framework preset:** Next.js (auto).
5. **Build & Output:** defaults (`next build` / `.next`).
6. **Environment variables** (Production + Preview as needed):

   | Name | Example | Purpose |
   |------|---------|---------|
   | `API_ORIGIN` | `https://api.your-domain.com` | Server-side rewrite target for `/api/*` |
   | `NEXT_PUBLIC_API_ORIGIN` | same as API | Link to OpenAPI `/docs` in the UI |

7. Deploy. After first deploy, open the Vercel URL and confirm the smoke page loads; API calls succeed only if `API_ORIGIN` is reachable from Vercel’s edge (your API must allow that host in CORS — set `CORS_ORIGINS` on the API to include your `*.vercel.app` preview URL and production web URL).

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
