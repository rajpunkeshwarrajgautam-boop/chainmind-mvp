# Contributing

## Local setup

1. Python **3.12+** and Node **18.17+** (for `web/`).
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set at least `JWT_SECRET` (32+ chars) and `DATABASE_URL` (SQLite path is fine for dev).

## Checks before opening a PR

```bash
# API
set PYTHONPATH=.
set ENVIRONMENT=test
set DATABASE_URL=sqlite:///:memory:
set JWT_SECRET=ci-jwt-secret-minimum-32-characters-long
set CELERY_TASK_ALWAYS_EAGER=true
pytest tests/ -q
python scripts/verify_vertical_slice.py --in-process
```

```bash
# Web
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

## Style

Match existing formatting and imports. Keep changes focused on one concern per PR.
