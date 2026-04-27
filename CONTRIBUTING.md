# Contributing

**Orchestrated checklist (all phases):** [docs/engineering/developer-orchestration-runbook.md](docs/engineering/developer-orchestration-runbook.md)

## Local setup

1. Python **3.12+** and Node **18.17+** (for `web/`).
2. Create a venv (`python -m venv .venv`) and activate it.
3. Install deps: `python -m pip install -r requirements.txt` (use **`python -m pip`** if Windows **Application Control** blocks `pip.exe`).
4. Copy `.env.example` to `.env` and set at least `JWT_SECRET` (32+ chars) and `DATABASE_URL` (SQLite path is fine for dev).

## Checks before opening a PR

### API (cmd.exe)

```bat
set PYTHONPATH=.
set ENVIRONMENT=test
set DATABASE_URL=sqlite:///:memory:
set JWT_SECRET=ci-jwt-secret-minimum-32-characters-long
set CELERY_TASK_ALWAYS_EAGER=true
set TRUSTED_HOSTS=
pytest tests/ -q
pytest tests/ -m "mvp_vertical_slice or extended_stub" -q
python scripts/verify_vertical_slice.py --in-process
```

### API (PowerShell)

```powershell
$env:PYTHONPATH="."
$env:ENVIRONMENT="test"
$env:DATABASE_URL="sqlite:///:memory:"
$env:JWT_SECRET="ci-jwt-secret-minimum-32-characters-long"
$env:CELERY_TASK_ALWAYS_EAGER="true"
$env:TRUSTED_HOSTS=""
python -m pytest tests/ -q
python -m pytest tests/ -m "mvp_vertical_slice or extended_stub" -q
python scripts/verify_vertical_slice.py --in-process
```

Optional context: **pilot scope markers** — [docs/qa/pilot-scope-boundaries.md](docs/qa/pilot-scope-boundaries.md).

### Web

```bash
cd web
npm ci
npm run lint
npm run build
```

## Database migrations (Alembic)

Alembic lives under `alembic/`. **Strategy (MVP):** the app still calls `create_tables()` on every boot so a single process can stand up an empty database without a separate migrate step.

- **`20260426_0001`** — empty baseline.
- **`20260426_0002_initial_schema`** — if the `tenants` table does not exist yet, applies `Base.metadata.create_all` for the current ORM models; if tables already exist (normal after first API boot), this revision is a no-op. Offline `--sql` mode is not supported for `0002`.

```bash
set PYTHONPATH=.
alembic upgrade head
```

For the next schema change, add a new revision (typically `alembic revision --autogenerate -m "..."` against a DB whose dialect matches production) and review the generated ops before merging.

**Render / production:** after wiring Postgres, follow [docs/deployment/render-blueprint.md](docs/deployment/render-blueprint.md) to sync the Blueprint and set `DATABASE_URL` in the dashboard.

### Single source of truth after MVP (production discipline)

| Phase | Schema mechanism |
|-------|-------------------|
| **Bootstrap / demos** | `create_tables()` on API boot + optional `alembic upgrade head` on empty DB — both converge to the same ORM metadata (see revision `0002`). |
| **Ongoing production** | **Alembic only** for DDL: run `alembic upgrade head` in your release pipeline **before** rolling new code. Relying on `create_tables()` for *new* columns is a foot-gun once multiple instances exist — new revisions should carry additive DDL. |

`create_tables()` remains safe as a **no-op when tables exist** (SQLAlchemy skips existing tables); it does not drop or alter stray columns. Removing it entirely is a separate hardening task — until then, treat **Alembic as the authority for intentional schema evolution** and keep models + migrations in lockstep in PR review.

## Style

Match existing formatting and imports. Keep changes focused on one concern per PR.
