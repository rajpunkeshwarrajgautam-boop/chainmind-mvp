# Developer orchestration runbook (local → PR → pilot)

Single checklist for **leadership + engineering**: same quality gates every time, no silent scope creep.

## Phase 0 — Environment

| Step | Action |
|------|--------|
| 0.1 | **Python 3.12+** on PATH (not only the Windows Store stub). Confirm: `python -c "import sys; print(sys.executable)"`. |
| 0.2 | **Venv** in repo root: `python -m venv .venv` → activate (POSIX: `source .venv/bin/activate`, Windows: `.\.venv\Scripts\Activate.ps1`). |
| 0.3 | **Install deps:** prefer `python -m pip install -r requirements.txt` if `pip.exe` is blocked by Application Control / WDAC (see [CONTRIBUTING.md](../../CONTRIBUTING.md)). |
| 0.4 | **`.env`** from `.env.example`; never commit `.env`. |

## Phase 1 — Quality gates (must all pass before PR)

Run in order; fix failures before proceeding.

| Gate | Command | Purpose |
|------|---------|---------|
| **1.1 API full suite** | See [CONTRIBUTING.md](../../CONTRIBUTING.md) — `pytest tests/ -q` with test env vars | Regression + governance |
| **1.2 Pilot contract** | `pytest tests/ -m "mvp_vertical_slice or extended_stub" -q` (same env vars) | README slice + stub honesty |
| **1.3 Vertical slice script** | `python scripts/verify_vertical_slice.py --in-process` | End-to-end slice without HTTP |
| **1.4 Web** | `cd web && npm ci && npm run lint && npm run build` | Next shell still builds |

## Phase 2 — Scope & topology (do not skip for pilot)

| Artifact | Link |
|----------|------|
| **What “MVP” vs “stub” means** | [docs/qa/pilot-scope-boundaries.md](../qa/pilot-scope-boundaries.md) |
| **Render API + Vercel web + env matrix** | [docs/deployment/environment-matrix.md](../deployment/environment-matrix.md) |
| **Cursor / Playwright capture hygiene** | [cursor-workspace-hygiene.md](./cursor-workspace-hygiene.md) |
| **Schema discipline (Alembic vs `create_tables`)** | [CONTRIBUTING.md](../../CONTRIBUTING.md) — “Single source of truth after MVP” |

## Phase 3 — Evidence (optional, customer-facing)

| When | Command |
|------|---------|
| Pilot deploy proof | `CHAINMIND_BASE_URL=https://api… python scripts/verify_vertical_slice.py --evidence-dir pilot-evidence/<label>` |

## Escalation

- **Policy blocks `pip.exe`:** use `python -m pip`; if still blocked, IT must allow the venv `Scripts` path or the Python install prefix.
- **Tests pass locally but fail in CI:** align Python version and env vars with the workflow file.

**Definition of done for “orchestration complete”:** Phase 1 gates green + Phase 2 links reviewed for your release (pilot vs production).
