# ChainMind MVP — Orchestration Hardening Release Notes

Release date: 2026-04-27

## Highlights

- Added an environment topology contract for API (Render), web (Vercel), and local development in `docs/deployment/environment-matrix.md`.
- Introduced pilot-scope boundary governance with explicit MVP-vs-stub documentation in `docs/qa/pilot-scope-boundaries.md`.
- Added boundary tests in `tests/test_pilot_boundaries.py` and test markers in `pytest.ini`/`tests/test_smoke.py` to keep pilot claims honest.
- Hardened contributor workflow docs in `CONTRIBUTING.md` and added the execution playbook in `docs/engineering/developer-orchestration-runbook.md`.
- Added workspace hygiene policy for MCP browser artifacts in `docs/engineering/cursor-workspace-hygiene.md` and `.gitignore`.
- Updated vertical-slice verification and test warning handling to reduce Authlib deprecation noise in routine runs.

## Verification Results

- `python -m pytest tests/ -q` -> 14 passed
- `python -m pytest tests/ -m "mvp_vertical_slice or extended_stub" -q` -> 11 passed, 3 deselected
- `python scripts/verify_vertical_slice.py --in-process` -> OK (health, auth, forecast, job retrieval)
- `npm --prefix web run lint` -> no lint errors
- `npm --prefix web run build` -> successful production build

## Operational Notes

- Render deployment remains API-first (from `render.yaml`) with dashboard-managed `DATABASE_URL`.
- Vercel deployment remains web-only (`web/` root) and requires `API_ORIGIN` + `NEXT_PUBLIC_API_ORIGIN` in both Production and Preview targets.
